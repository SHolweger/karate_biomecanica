"""
Punto de entrada del sistema (Shotokan AI).

    python main.py              Interfaz gráfica — la forma normal de usarlo
    python main.py --consola    Versión de terminal con ventana de OpenCV

Ambas vías comparten el mismo motor de análisis (Camera, PoseTracker,
SkeletonRenderer, TechniqueAnalyzer): lo único que cambia es cómo se muestran
los resultados y cómo se inicia la sesión.

La versión de consola se conserva porque fue —y sigue siendo— la herramienta
con la que se depuran los algoritmos: permite ejercitar el pipeline sin cargar
la interfaz gráfica. No es la vía de uso del dojo.
"""
import argparse
import sys

# Este módulo es un despachador: elige entre la interfaz gráfica y la versión de
# terminal. Las dependencias pesadas (OpenCV, MediaPipe, CustomTkinter) se
# importan DENTRO de cada vía, no aquí arriba, por tres razones concretas:
# mostrar la ayuda no debería exigir tenerlas instaladas; `--consola` no debería
# exigir un entorno gráfico; y así el punto de entrada se puede verificar en el
# entorno de integración continua, que no tiene ninguna de las dos.


def _resumir_sesion(db, id_sesion, atleta):
    """
    Qué concluyó el sistema, impreso al terminar.

    Analizar una grabación de tres minutos y no ver nada al final obligaría a
    abrir la interfaz solo para saber si sirvió de algo. El resumen responde en
    el acto la pregunta con la que se corre el análisis: ¿qué vio y qué juzgó?

    Cuenta solo evaluaciones cerradas (`correcto IS NOT NULL`): los estados
    transitorios y las articulaciones no visibles no son aciertos ni fallos.
    """
    detalle = db.detalle_sesion(id_sesion)
    print(f"\n=== SESIÓN {id_sesion} · {atleta['nombre']} ===")

    if detalle is None or not detalle["evaluaciones"]:
        print("Sin evaluaciones cerradas: el sistema no llegó a juzgar ninguna técnica.")
        print("  · Si las etapas de análisis y renderizado salieron en cero, no se")
        print("    detectó pose en ningún fotograma. Revisa que el ejecutante aparezca")
        print("    de cuerpo completo y que el video no venga rotado.")
        print("  · Una articulación por debajo del umbral de visibilidad no se evalúa.")
        return

    print(f"Evaluaciones cerradas: {detalle['evaluaciones']}  "
          f"(aciertos: {detalle['aciertos']}, precisión: {detalle['precision']:.0f} %)")

    print(f"\n{'Técnica':<22}{'Evaluaciones':>14}{'Aciertos':>10}{'Precisión':>11}{'Áng. medio':>12}")
    for fila in db.resumen_por_tecnica(atleta["id_atleta"], id_sesion):
        angulo = f"{fila['angulo_medio']:.0f}°" if fila["angulo_medio"] is not None else "—"
        print(f"{fila['nombre_tecnica']:<22}{fila['evaluaciones']:>14}"
              f"{fila['aciertos']:>10}{fila['precision']:>10.0f} %{angulo:>12}")

    errores = db.errores_frecuentes(id_sesion)
    if errores:
        print("\nErrores más repetidos:")
        for fila in errores:
            print(f"  {fila['veces']:>3} ×  {fila['diagnostico']}")


def main_consola(fuente_pedida=None):
    """
    Análisis por terminal. `fuente_pedida` gana sobre la fuente configurada.

    Poder apuntar a un archivo desde la línea de comandos es lo que convierte
    una grabación en una sesión analizada y registrada —con sus veredictos por
    técnica y su reporte— sin tener que reconfigurar la cámara en la interfaz
    para luego devolverla a su sitio.
    """
    # Importamos nuestros módulos (Nuestra Arquitectura Modular)
    
    import cv2

    from vision.camera import Camera, CamaraNoDisponible, describir, listar_camaras
    from vision.tracker import PoseTracker
    from biomechanics.renderer import SkeletonRenderer
    from expert_system.analyzer import TechniqueAnalyzer
    from expert_system.knowledge_base import (CORRECCIONES_LITERATURA, KarateRules,
                                              UMBRALES_LITERATURA)
    from persistence.database import Database
    from persistence.cli_auth import login_o_registro, elegir_o_crear_perfil
    from persistence.medicion_logger import MedicionLogger

    print("Iniciando componentes del sistema experto...")

    # 0. Acceso: entrenador (RF-08) y perfil de atleta (estilo Netflix), antes
    # de tocar la cámara — no tiene sentido inicializar MediaPipe si el login falla.
    db = Database()
    # Los umbrales viven en la base de datos (RF-08). La siembra es idempotente:
    # si el entrenador ya recalibro alguno, no se sobrescribe.
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    db.corregir_umbrales_de_literatura(CORRECCIONES_LITERATURA)
    entrenador = login_o_registro(db)
    atleta = elegir_o_crear_perfil(db)
    id_sesion = db.iniciar_sesion(atleta["id_atleta"], entrenador["id_entrenador"])
    logger_mediciones = MedicionLogger(db, id_sesion)
    print(f"\nSesión iniciada: {entrenador['nombre']} entrenando a {atleta['nombre']}. 'q' para terminar.\n")

    # 1. Inicialización de Objetos.
    # La fuente de video es la que quedó configurada desde la interfaz gráfica
    # (RF-01). Si no abre, se informa qué cámaras sí están disponibles en vez
    # de dejar la ventana en negro sin explicación.
    fuente = fuente_pedida if fuente_pedida is not None else db.leer_config("fuente_video", 0)
    try:
        cam = Camera(fuente)
    except CamaraNoDisponible as error:
        print(f"\n{error}")
        disponibles = listar_camaras()
        if disponibles:
            print("Cámaras detectadas en este equipo:")
            for c in disponibles:
                print(f"  - índice {c['indice']}  ({c['ancho']}x{c['alto']} px)")
            print("Configúrala desde la interfaz gráfica (python gui/app.py > Cámara).")
        else:
            print("No se detectó ninguna cámara conectada.")
        db.close()
        return
    print(f"Fuente de video: {describir(fuente)}")
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    reglas = KarateRules(db.cargar_umbrales_vigentes())
    analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65, reglas=reglas)

    
    # 2. Bucle Principal
    while True:
        frame = cam.get_frame()
        if frame is None: break
            
        # La marca la da la fuente y no el reloj de pared: sobre una grabación
        # el reloj mide cuánto tarda este equipo en analizar, no cuánto duró la
        # ejecución, y la misma grabación daría velocidades angulares distintas
        # en computadoras distintas (ver Camera.marca_de_tiempo_ms).
        timestamp_ms = int(cam.marca_de_tiempo_ms())
        h, w, _ = frame.shape
        
        # A. Visión: Extraer el esqueleto
        result = tracker.process_frame(frame, timestamp_ms)
        
        # B. Renderizado Base: Dibujar líneas y nodos
        frame = renderer.draw(frame, result.pose_landmarks)
        
        # C. Inteligencia: Analizar y mostrar diagnósticos
        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            
            # Le pedimos al analista que evalúe ambos brazos
            diagnostico_tsuki = analyzer.analyze_tsuki(landmarks, w, h)
            diagnostico_postura = analyzer.analyze_stance(landmarks, w, h) # <--- NUEVA LÍNEA
            diagnostico_patada = analyzer.analyze_mae_geri(landmarks, w, h, timestamp_ms)

            # Le pedimos al dibujante que ponga los resultados en pantalla
            frame = renderer.draw_diagnostics(frame, diagnostico_tsuki)
            frame = renderer.draw_diagnostics(frame, diagnostico_postura)
            frame = renderer.draw_diagnostics(frame, diagnostico_patada)

            # Persistencia: solo guarda cuando el diagnóstico de una categoría
            # CAMBIA respecto al anterior (ver MedicionLogger) — no en cada frame.
            logger_mediciones.registrar(diagnostico_tsuki, timestamp_ms)
            logger_mediciones.registrar(diagnostico_postura, timestamp_ms)
            logger_mediciones.registrar(diagnostico_patada, timestamp_ms)
        
        # D. Salida: Mostrar ventana
        cv2.imshow('Karate AI - Vision Directa', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 3. Limpieza
    db.cerrar_sesion(id_sesion)
    _resumir_sesion(db, id_sesion, atleta)
    db.close()
    cam.release()
    tracker.close()
    cv2.destroyAllWindows()

def main_grafico():
    """
    Abre la interfaz gráfica. El import va dentro de la función a propósito:
    así `python main.py --consola` no exige tener CustomTkinter instalado ni un
    entorno gráfico disponible.
    """
    from gui.app import App

    App().mainloop()


def main():
    analizador = argparse.ArgumentParser(
        prog="main.py",
        description="Sistema experto de análisis biomecánico del Karate-Do Shotokan.")
    analizador.add_argument(
        "--consola", action="store_true",
        help="usa la versión de terminal con ventana de OpenCV, en vez de la interfaz gráfica")
    analizador.add_argument(
        "--fuente", metavar="FUENTE",
        help="índice de cámara, dirección de cámara IP o ruta de un video grabado. "
             "Solo con --consola; sin este argumento se usa la fuente que quedó "
             "configurada desde la interfaz gráfica")
    argumentos = analizador.parse_args()

    if argumentos.fuente is not None and not argumentos.consola:
        # Fallar aquí, y no ignorarlo en silencio, evita que alguien crea que la
        # interfaz gráfica está analizando el video que le pasó por la terminal.
        analizador.error("--fuente solo se puede usar junto con --consola")

    if argumentos.consola:
        main_consola(argumentos.fuente)
        return

    try:
        main_grafico()
    except ImportError as error:
        # Falta una dependencia de la interfaz. Se explica cómo seguir en vez
        # de mostrar una traza que no le dice nada a quien opera el sistema.
        print(f"No se pudo abrir la interfaz gráfica: {error}")
        print("Instala las dependencias con:  pip install -r requirements.txt")
        print("O usa la versión de terminal:  python main.py --consola")
        sys.exit(1)


if __name__ == "__main__":
    main()