"""
test_antijitter.py — Verificación objetiva del filtro Anti-Jitter.

Muestra EN VIVO el ángulo del codo crudo vs filtrado (lado a lado),
registra ambas señales y, al salir con 'q', genera en evidencias/:
  - un CSV con las dos señales frame a frame
  - una gráfica comparativa PNG con métricas (para la tesis)

Uso:
    ./venv/bin/python test_antijitter.py [indice_camara]   (default: 2)

Protocolo de prueba sugerido:
    1. Brazo extendido (tsuki) COMPLETAMENTE QUIETO ~15 segundos.
    2. Luego 2-3 tsukis lentos y 2-3 explosivos.
    3. Presiona 'q' y revisa la gráfica generada.
"""
import sys
import csv
import os
import time
from datetime import datetime

import cv2

from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.geometry import BiomechanicsMath
from biomechanics.filters import MovingAverageFilter

UMBRAL_VISIBILIDAD = 0.65
# Colores BGR consistentes con la gráfica: crudo gris, filtrado azul (#2a78d6)
COLOR_CRUDO = (170, 170, 170)
COLOR_FILTRADO = (214, 120, 42)


def capturar(source):
    """Bucle de cámara: calcula ángulo crudo y filtrado del codo y los registra."""
    cam = Camera(source=source)
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    filtro = MovingAverageFilter(window=5)  # misma configuración que producción

    registros = []  # (t_segundos, angulo_crudo, angulo_filtrado)
    start = time.time()

    print("Grabando... Manten el brazo QUIETO 15s, luego lanza tsukis. 'q' para terminar.")
    while True:
        frame = cam.get_frame()
        if frame is None:
            break
        t = time.time() - start
        result = tracker.process_frame(frame, int(t * 1000))
        h, w, _ = frame.shape

        if result.pose_landmarks:
            lms = result.pose_landmarks[0]
            hombro, codo, muneca = lms[11], lms[13], lms[15]

            if min(hombro.visibility, codo.visibility, muneca.visibility) > UMBRAL_VISIBILIDAD:
                p_hombro = (int(hombro.x * w), int(hombro.y * h))
                p_codo = (int(codo.x * w), int(codo.y * h))
                p_muneca = (int(muneca.x * w), int(muneca.y * h))

                crudo = BiomechanicsMath.calculate_angle(p_hombro, p_codo, p_muneca)
                filtrado = filtro.update(crudo)
                registros.append((t, crudo, filtrado))

                cv2.line(frame, p_hombro, p_codo, COLOR_FILTRADO, 2)
                cv2.line(frame, p_codo, p_muneca, COLOR_FILTRADO, 2)
                cv2.putText(frame, f"CRUDO:    {crudo:6.1f}", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.1, COLOR_CRUDO, 2)
                cv2.putText(frame, f"FILTRADO: {filtrado:6.1f}", (20, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.1, COLOR_FILTRADO, 2)
            else:
                filtro.reset()
                cv2.putText(frame, "BRAZO NO VISIBLE", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
        else:
            filtro.reset()
            cv2.putText(frame, "SIN DETECCION", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)

        cv2.putText(frame, f"t = {t:5.1f}s   ('q' termina)", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow('Prueba Anti-Jitter: crudo vs filtrado', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    tracker.close()
    cv2.destroyAllWindows()
    return registros


def guardar_evidencia(registros, carpeta="evidencias"):
    """Genera CSV + gráfica comparativa + métricas de jitter."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(carpeta, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")

    ruta_csv = os.path.join(carpeta, f"antijitter_{sello}.csv")
    with open(ruta_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_segundos", "angulo_crudo", "angulo_filtrado"])
        writer.writerows([(f"{t:.3f}", f"{c:.2f}", f"{fl:.2f}") for t, c, fl in registros])

    tiempos = [r[0] for r in registros]
    crudos = [r[1] for r in registros]
    filtrados = [r[2] for r in registros]

    # Métrica de jitter: cambio absoluto promedio entre frames consecutivos.
    # (La desviación estándar total mezclaría el movimiento real con el ruido.)
    def jitter_medio(serie):
        deltas = [abs(b - a) for a, b in zip(serie, serie[1:])]
        return sum(deltas) / len(deltas)

    j_crudo = jitter_medio(crudos)
    j_filtrado = jitter_medio(filtrados)
    reduccion = (1 - j_filtrado / j_crudo) * 100 if j_crudo else 0

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(tiempos, crudos, color="#9aa0a6", linewidth=1.0, label="Señal cruda (MediaPipe)")
    ax.plot(tiempos, filtrados, color="#2a78d6", linewidth=2.0,
            label="Señal filtrada (Media Móvil, ventana 5)")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Ángulo del codo (grados)")
    ax.set_title("Verificación Anti-Jitter: señal cruda vs filtrada")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(True, alpha=0.25, linewidth=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.02, 0.04,
            f"Jitter medio entre frames — crudo: {j_crudo:.2f}°  |  "
            f"filtrado: {j_filtrado:.2f}°  |  reducción: {reduccion:.0f}%",
            transform=ax.transAxes, fontsize=9, color="#333333",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f1f3f4", edgecolor="none"))

    ruta_png = os.path.join(carpeta, f"antijitter_{sello}.png")
    fig.tight_layout()
    fig.savefig(ruta_png, dpi=150)
    plt.close(fig)

    print(f"\n=== RESULTADOS ({len(registros)} frames, {tiempos[-1]:.1f}s) ===")
    print(f"Jitter medio crudo:    {j_crudo:.2f} grados/frame")
    print(f"Jitter medio filtrado: {j_filtrado:.2f} grados/frame")
    print(f"Reducción del ruido:   {reduccion:.0f}%")
    print(f"CSV:     {ruta_csv}")
    print(f"Gráfica: {ruta_png}")


if __name__ == "__main__":
    source = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    registros = capturar(source)
    if len(registros) < 30:
        print("Muy pocos datos registrados (¿la cámara/brazo no se veía?). Intenta de nuevo.")
    else:
        guardar_evidencia(registros)
