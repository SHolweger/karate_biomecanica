import cv2
import time

# Importamos nuestros módulos (Nuestra Arquitectura Modular)
from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer
from expert_system.analyzer import TechniqueAnalyzer
from expert_system.knowledge_base import KarateRules, UMBRALES_LITERATURA
from persistence.database import Database
from persistence.cli_auth import login_o_registro, elegir_o_crear_perfil
from persistence.medicion_logger import MedicionLogger

def main():
    print("Iniciando componentes del sistema experto...")

    # 0. Acceso: entrenador (RF-08) y perfil de atleta (estilo Netflix), antes
    # de tocar la cámara — no tiene sentido inicializar MediaPipe si el login falla.
    db = Database()
    # Los umbrales viven en la base de datos (RF-08). La siembra es idempotente:
    # si el entrenador ya recalibro alguno, no se sobrescribe.
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    entrenador = login_o_registro(db)
    atleta = elegir_o_crear_perfil(db)
    id_sesion = db.iniciar_sesion(atleta["id_atleta"], entrenador["id_entrenador"])
    logger_mediciones = MedicionLogger(db, id_sesion)
    print(f"\nSesión iniciada: {entrenador['nombre']} entrenando a {atleta['nombre']}. 'q' para terminar.\n")

    # 1. Inicialización de Objetos
    cam = Camera(source=2)
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    reglas = KarateRules(db.cargar_umbrales_vigentes())
    analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65, reglas=reglas)

    start_time = time.time()
    
    # 2. Bucle Principal
    while True:
        frame = cam.get_frame()
        if frame is None: break
            
        timestamp_ms = int((time.time() - start_time) * 1000)
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
    db.close()
    cam.release()
    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()