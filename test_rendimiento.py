"""
test_rendimiento.py — Medición de latencia y tasa de procesamiento (prueba 3.9.14).

Ejecuta el pipeline REAL de producción (Camera -> PoseTracker -> SkeletonRenderer
-> TechniqueAnalyzer -> despliegue) instrumentado etapa por etapa, y contrasta el
resultado contra dos criterios de aceptación del Capítulo 3:

    RNF-01  tiempo de cómputo por fotograma  < 500 ms
    RF-01   tasa de procesamiento sostenida  >= 30 fps

Al terminar genera en evidencias/ un CSV con el detalle por fotograma y una
gráfica con la composición del tiempo de cómputo.

Uso:
    python3 test_rendimiento.py [fuente] [n_fotogramas] [--desde SEG] [--sin-ventana]

    fuente        índice de cámara, dirección de cámara IP o ruta a un video
    n_fotogramas  cuántos medir antes de cortar. Default: 300
    --desde SEG   descarta los primeros SEG segundos de una grabación antes de
                  empezar a medir
    --sin-ventana no abre la ventana de OpenCV: mide el encadenamiento de
                  análisis sin el costo de dibujarla

Protocolo: situarse en cuadro de cuerpo completo y ejecutar técnicas
normalmente durante la medición, para que el analizador trabaje sobre landmarks
reales y no sobre un encuadre vacío.

Dos advertencias que nacieron de mediciones equivocadas:

  * **Sobre una grabación, usa `--desde`.** Los primeros segundos de un video
    que uno se graba a sí mismo son el tramo en que la persona todavía camina
    hacia su sitio. Medir ahí describe el arranque, no la ejecución.
  * **`--sin-ventana` no es hacer trampa, es separar dos preguntas.** En una
    medición real sobre video vertical de 2,1 MP, `cv2.imshow` se llevó 20,4 de
    los 42,3 ms por fotograma: más que la estimación de pose. Esa ventana es de
    depuración y la interfaz del dojo no la usa, así que conviene reportar las
    dos cifras y decir cuál es cuál.
"""
import csv
import os
import sys
from datetime import datetime

import cv2

from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer
from biomechanics.metrics import PerformanceMonitor
from expert_system.analyzer import TechniqueAnalyzer

# Criterios de aceptación definidos en el Capítulo 3. Viven aquí, en la prueba,
# y no dentro del monitor: la instrumentación es genérica, el criterio es de tesis.
UMBRAL_RNF01_MS = 500.0
UMBRAL_RF01_FPS = 30.0

ETAPAS = ["captura", "estimacion_pose", "analisis", "renderizado", "despliegue"]


def medir(fuente, n_fotogramas, desde_s=0.0, con_ventana=True):
    cam = Camera(source=fuente)
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65)
    monitor = PerformanceMonitor(descartar_iniciales=5)

    # Se descartan los primeros segundos ANTES de empezar a cronometrar, leyendo
    # fotogramas sin medirlos. No se puede saltar con una búsqueda en el archivo
    # porque el decodificador tendría que recolocarse y el primer fotograma tras
    # el salto costaría un tiempo que no representa al resto.
    if desde_s > 0:
        print(f"Descartando los primeros {desde_s:.0f} s...")
        while cam.marca_de_tiempo_ms() < desde_s * 1000:
            if cam.get_frame() is None:
                print("La grabación terminó antes del punto de inicio pedido.")
                cam.release()
                tracker.close()
                return monitor

    print(f"Midiendo {n_fotogramas} fotogramas"
          f"{' sin ventana' if not con_ventana else ''}... ('q' corta antes de tiempo)")
    procesados = 0

    while procesados < n_fotogramas:
        monitor.iniciar_frame()

        frame = cam.get_frame()
        monitor.marcar("captura")
        if frame is None:
            break

        h, w, _ = frame.shape
        # La marca la da la fuente, no el contador. Suponer 30 fps falseaba al
        # doble los tiempos de una grabación a 60, y de ahí salen la velocidad
        # angular del Kime y los plazos de la máquina de estados del Mae Geri.
        timestamp_ms = int(cam.marca_de_tiempo_ms())

        result = tracker.process_frame(frame, timestamp_ms)
        monitor.marcar("estimacion_pose")

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            diagnosticos = [
                analyzer.analyze_tsuki(landmarks, w, h),
                analyzer.analyze_stance(landmarks, w, h),
                analyzer.analyze_mae_geri(landmarks, w, h, timestamp_ms),
            ]
        else:
            diagnosticos = []
        monitor.marcar("analisis")

        frame = renderer.draw(frame, result.pose_landmarks)
        for d in diagnosticos:
            frame = renderer.draw_diagnostics(frame, d)
        monitor.marcar("renderizado")

        corta = False
        if con_ventana:
            cv2.putText(frame, f"Midiendo {procesados + 1}/{n_fotogramas}", (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow('Prueba de rendimiento (RNF-01 / RF-01)', frame)
            corta = cv2.waitKey(1) & 0xFF == ord('q')
        monitor.marcar("despliegue")

        monitor.cerrar_frame()
        procesados += 1
        if corta:
            break

    cam.release()
    tracker.close()
    cv2.destroyAllWindows()
    return monitor


def reportar(monitor, carpeta="evidencias"):
    total = monitor.resumen_total()
    fps = monitor.resumen_fps()
    etapas = monitor.resumen_etapas()

    if total is None or fps is None:
        print("Datos insuficientes: se midieron muy pocos fotogramas.")
        return

    os.makedirs(carpeta, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---- CSV con el detalle por fotograma ----
    ruta_csv = os.path.join(carpeta, f"rendimiento_{sello}.csv")
    presentes = [e for e in ETAPAS if e in monitor.etapas]
    with open(ruta_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["fotograma"] + [f"{e}_ms" for e in presentes] + ["total_ms"])
        for i, t in enumerate(monitor.totales):
            fila = [i] + [f"{monitor.etapas[e][i]:.3f}" if i < len(monitor.etapas[e]) else ""
                          for e in presentes] + [f"{t:.3f}"]
            writer.writerow(fila)

    # ---- Tabla en consola ----
    print(f"\n=== COMPOSICIÓN DEL TIEMPO DE CÓMPUTO ({total['n']} fotogramas estables) ===")
    print(f"{'Etapa':<20}{'Media':>9}{'Mediana':>10}{'P95':>9}{'Máx':>9}   (ms)")
    for e in presentes:
        s = etapas[e]
        print(f"{e:<20}{s['media']:>9.1f}{s['mediana']:>10.1f}{s['p95']:>9.1f}{s['max']:>9.1f}")
    print(f"{'-' * 57}")
    print(f"{'TOTAL':<20}{total['media']:>9.1f}{total['mediana']:>10.1f}"
          f"{total['p95']:>9.1f}{total['max']:>9.1f}")

    print(f"\n=== TASA DE PROCESAMIENTO ===")
    print(f"Sostenida (media): {fps['medio']:.1f} fps")
    print(f"Peor fotograma:    {fps['minimo']:.1f} fps")
    print(f"Duración medida:   {fps['duracion_s']:.1f} s")

    cumple_rnf01 = total["p95"] < UMBRAL_RNF01_MS
    cumple_rf01 = fps["medio"] >= UMBRAL_RF01_FPS
    print(f"\n=== CRITERIOS DE ACEPTACIÓN ===")
    print(f"RNF-01  cómputo < {UMBRAL_RNF01_MS:.0f} ms   -> P95 = {total['p95']:.1f} ms   "
          f"{'CUMPLE' if cumple_rnf01 else 'NO CUMPLE'}")
    print(f"RF-01   procesamiento >= {UMBRAL_RF01_FPS:.0f} fps -> {fps['medio']:.1f} fps      "
          f"{'CUMPLE' if cumple_rf01 else 'NO CUMPLE'}")

    # ---- Gráfica ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.6))

    nombres = [e.replace("_", " ") for e in presentes]
    medias = [etapas[e]["media"] for e in presentes]
    ax1.barh(nombres, medias, color="#2a78d6")
    ax1.invert_yaxis()
    ax1.set_xlabel("Tiempo medio (ms)")
    ax1.set_title("Composición del tiempo de cómputo por fotograma")
    ax1.grid(True, axis="x", alpha=0.25, linewidth=0.5)
    ax1.spines[["top", "right"]].set_visible(False)
    for i, v in enumerate(medias):
        ax1.text(v, i, f" {v:.1f}", va="center", fontsize=9, color="#333333")

    estables = monitor.totales[monitor.descartar_iniciales:]
    ax2.plot(range(len(estables)), estables, color="#2a78d6", linewidth=1.2,
             label="Tiempo por fotograma")
    ax2.axhline(UMBRAL_RNF01_MS, color="#d0455a", linestyle="--", linewidth=1.4,
                label=f"Límite RNF-01 ({UMBRAL_RNF01_MS:.0f} ms)")
    ax2.set_ylim(0, max(UMBRAL_RNF01_MS * 1.08, total["max"] * 1.2))
    ax2.set_xlabel("Fotograma")
    ax2.set_ylabel("Tiempo de cómputo (ms)")
    ax2.set_title("Latencia por fotograma frente al límite exigido")
    ax2.legend(frameon=False, loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.25, linewidth=0.5)
    ax2.spines[["top", "right"]].set_visible(False)
    # La anotacion va arriba a la izquierda: abajo taparia la propia serie,
    # que se dibuja pegada al eje por la holgura frente al limite de 500 ms.
    ax2.text(0.02, 0.86,
             f"Media {total['media']:.1f} ms  |  P95 {total['p95']:.1f} ms  |  "
             f"{fps['medio']:.1f} fps sostenidos",
             transform=ax2.transAxes, fontsize=9, color="#333333",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#f1f3f4", edgecolor="none"))

    ruta_png = os.path.join(carpeta, f"rendimiento_{sello}.png")
    fig.tight_layout()
    fig.savefig(ruta_png, dpi=150)
    plt.close(fig)

    print(f"\nCSV:     {ruta_csv}")
    print(f"Gráfica: {ruta_png}")


def fuente_por_defecto():
    """
    La cámara que el entrenador dejó configurada en la aplicación.

    Antes este valor era el índice 2 escrito a mano, que correspondía al iPhone
    por Continuity del equipo de desarrollo. En cualquier otro equipo ese índice
    no existe, de modo que la medición fallaba en la máquina donde más importa
    hacerla: la del dojo.

    Si no hay base de datos todavía, se usa el índice 0, que es la cámara
    integrada en prácticamente todo equipo portátil.
    """
    try:
        from persistence.database import Database
        db = Database()
        try:
            return db.leer_config("fuente_video", 0)
        finally:
            db.close()
    except Exception:
        return 0


if __name__ == "__main__":
    import argparse

    analizador = argparse.ArgumentParser(
        prog="test_rendimiento.py",
        description="Mide la latencia por etapa y la tasa de procesamiento "
                    "(RNF-01 y RF-01) sobre el encadenamiento real.")
    # `normalizar` (vision/fuentes.py) decide si lo recibido es un índice, una
    # dirección de cámara IP o un archivo de video; aquí no hay que interpretarlo.
    analizador.add_argument("fuente", nargs="?", default=None,
                            help="índice de cámara, cámara IP o ruta de un video")
    analizador.add_argument("n_fotogramas", nargs="?", type=int, default=300,
                            help="cuántos fotogramas medir (por defecto 300)")
    analizador.add_argument("--desde", type=float, default=0.0, metavar="SEG",
                            help="descarta los primeros SEG segundos de la grabación")
    analizador.add_argument("--sin-ventana", action="store_true",
                            help="no abre la ventana de OpenCV durante la medición")
    args = analizador.parse_args()

    reportar(medir(args.fuente if args.fuente is not None else fuente_por_defecto(),
                   args.n_fotogramas, desde_s=args.desde,
                   con_ventana=not args.sin_ventana))
