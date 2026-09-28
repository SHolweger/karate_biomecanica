"""
diagnostico_video.py — Por qué el sistema no detecta pose en una grabación.

Responde, sobre un video concreto, las preguntas que una medición de
rendimiento deja abiertas cuando las etapas de análisis salen en cero: ¿se está
leyendo el archivo?, ¿llega derecho o rotado?, ¿MediaPipe encuentra a la
persona?, ¿con qué visibilidad llegan las articulaciones que el sistema evalúa?

No forma parte de la suite (pytest solo recoge tests/): es una herramienta de
diagnóstico, como test_camaras.py.

Uso:
    python3 diagnostico_video.py "ruta/al/video.mp4" [n_fotogramas]
"""
import os
import sys

import cv2

from vision.camera import Camera
from vision.tracker import PoseTracker

# Las cuatro articulaciones que el sistema experto evalúa, con el índice que
# MediaPipe les asigna. Si estas no se ven, no hay diagnóstico posible.
ARTICULACIONES = {"codo izq": 13, "codo der": 14, "rodilla izq": 25, "rodilla der": 26}
UMBRAL_VISIBILIDAD = 0.65


def diagnosticar(ruta, n_fotogramas=60, carpeta="evidencias"):
    if not os.path.exists(ruta):
        print(f"No existe el archivo: {ruta}")
        return

    cam = Camera(ruta, espejo=False, verificar=True)
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    os.makedirs(carpeta, exist_ok=True)

    ancho, alto = cam.resolucion
    orientacion = "vertical" if alto > ancho else "horizontal"
    print(f"\nArchivo:     {os.path.basename(ruta)}")
    print(f"Resolución:  {ancho}×{alto} px ({orientacion})")

    con_pose = 0
    visibles = {nombre: 0 for nombre in ARTICULACIONES}
    guardados = []
    leidos = 0

    while leidos < n_fotogramas:
        frame = cam.get_frame()
        if frame is None:
            break
        leidos += 1
        resultado = tracker.process_frame(frame, int(cam.marca_de_tiempo_ms()))

        if resultado.pose_landmarks:
            con_pose += 1
            puntos = resultado.pose_landmarks[0]
            for nombre, indice in ARTICULACIONES.items():
                if puntos[indice].visibility >= UMBRAL_VISIBILIDAD:
                    visibles[nombre] += 1

        # Se guardan tres fotogramas repartidos para poder mirarlos: si el video
        # viene rotado, se ve de inmediato y no hay que deducirlo de las cifras.
        if leidos in (1, n_fotogramas // 2, n_fotogramas) and len(guardados) < 3:
            destino = os.path.join(carpeta, f"diagnostico_f{leidos:04d}.png")
            cv2.imwrite(destino, frame)
            guardados.append(destino)

    cam.release()
    tracker.close()

    print(f"Fotogramas leídos: {leidos}")
    if leidos == 0:
        print("\nEl archivo no entregó ningún fotograma: OpenCV no pudo decodificarlo.")
        return

    porcentaje = 100.0 * con_pose / leidos
    print(f"Con pose detectada: {con_pose} ({porcentaje:.0f} %)")

    if con_pose == 0:
        print("\nMediaPipe no encontró a nadie en ningún fotograma. Causas frecuentes,")
        print("en orden de probabilidad:")
        print("  1. El video viene rotado. Los teléfonos guardan la orientación como")
        print("     metadato y OpenCV no siempre la aplica: el detector recibe a la")
        print("     persona acostada y no la reconoce. Mira los PNG guardados.")
        print("  2. La persona ocupa muy poco del cuadro, o sale cortada.")
        print("  3. Contraste insuficiente contra el fondo.")
    else:
        print(f"\n{'Articulación':<16}{'Visible':>10}{'% de los detectados':>22}")
        for nombre, veces in visibles.items():
            print(f"{nombre:<16}{veces:>10}{100.0 * veces / con_pose:>21.0f} %")
        if min(visibles.values()) == 0:
            print("\nHay articulaciones que nunca superan el umbral de visibilidad:")
            print("el sistema las declara no visibles y su veredicto queda nulo.")

    print("\nFotogramas guardados para inspección visual:")
    for ruta_png in guardados:
        print(f"  {ruta_png}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    diagnosticar(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60)
