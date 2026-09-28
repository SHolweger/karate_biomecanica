"""
diagnostico_video.py — Por qué el sistema no ve lo que debería ver en un video.

Responde, sobre una grabación concreta, las preguntas que una medición de
rendimiento deja abiertas: ¿se decodifica el archivo?, ¿en qué parte del video
encuentra a la persona?, ¿con qué visibilidad llegan las cuatro articulaciones
que el sistema experto evalúa?

**Muestrea el video entero, no su principio.** La primera versión leía los
primeros sesenta fotogramas y concluyó que las rodillas no se veían nunca en una
grabación donde sí se ven. Dos segundos de un video que uno se graba a sí mismo
son justamente el tramo en que la persona todavía está caminando hacia su sitio
después de pulsar grabar: el peor trozo posible para sacar conclusiones, y el
único que aquella versión miraba.

No forma parte de la suite (pytest solo recoge tests/): es una herramienta de
diagnóstico, como test_camaras.py.

Uso:
    python3 diagnostico_video.py "ruta/al/video.mp4" [n_muestras]
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

# En cuántos tramos se divide el video para informar. Con cuatro se distingue el
# arranque —donde la persona suele estar entrando en cuadro— del resto.
TRAMOS = 4
MUESTRAS_POR_DEFECTO = 160


def _barra(porcentaje, ancho=20):
    llenos = int(round(porcentaje / 100 * ancho))
    return "█" * llenos + "·" * (ancho - llenos)


def diagnosticar(ruta, muestras=MUESTRAS_POR_DEFECTO, carpeta="evidencias"):
    if not os.path.exists(ruta):
        print(f"No existe el archivo: {ruta}")
        return

    cam = Camera(ruta, espejo=False, verificar=True)
    tracker = PoseTracker()
    os.makedirs(carpeta, exist_ok=True)

    ancho, alto = cam.resolucion
    total = int(cam.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cam.cap.get(cv2.CAP_PROP_FPS) or 30.0
    # Se analiza uno de cada `paso` fotogramas, repartidos por todo el video.
    paso = max(1, total // muestras) if total > 0 else 1

    print(f"\nArchivo:     {os.path.basename(ruta)}")
    print(f"Resolución:  {ancho}×{alto} px ({'vertical' if alto > ancho else 'horizontal'})")
    if total > 0:
        print(f"Duración:    {total / fps:.0f} s  ({total} fotogramas a {fps:.0f} fps)")
    print(f"Se analiza 1 de cada {paso} fotogramas, a lo largo de todo el video.\n")

    analizados = []          # (indice, hay_pose, {articulacion: visibilidad})
    guardados = []
    leidos = 0

    while True:
        frame = cam.get_frame()
        if frame is None:
            break
        indice = leidos
        leidos += 1
        if indice % paso:
            continue

        resultado = tracker.process_frame(frame, int(cam.marca_de_tiempo_ms()))
        if resultado.pose_landmarks:
            puntos = resultado.pose_landmarks[0]
            visibilidades = {n: puntos[i].visibility for n, i in ARTICULACIONES.items()}
        else:
            visibilidades = None
        analizados.append((indice, visibilidades))

        # Tres fotogramas repartidos, para poder mirarlos. Nunca del arranque:
        # es el tramo menos representativo de una grabación casera.
        if total > 0 and indice in {total // 4, total // 2, (3 * total) // 4}:
            destino = os.path.join(carpeta, f"diagnostico_f{indice:05d}.png")
            cv2.imwrite(destino, frame)
            guardados.append(destino)

    cam.release()
    tracker.close()

    if not analizados:
        print("El archivo no entregó ningún fotograma: OpenCV no pudo decodificarlo.")
        return

    con_pose = [v for _, v in analizados if v is not None]
    print(f"Fotogramas analizados: {len(analizados)} (de {leidos} leídos)")
    print(f"Con pose detectada:    {len(con_pose)} "
          f"({100.0 * len(con_pose) / len(analizados):.0f} %)\n")

    # ---- Dónde encuentra a la persona, a lo largo del video ----
    print("Detección por tramo del video:")
    por_tramo = [[] for _ in range(TRAMOS)]
    for posicion, (_, visibilidades) in enumerate(analizados):
        por_tramo[min(TRAMOS - 1, posicion * TRAMOS // len(analizados))].append(visibilidades)
    for i, tramo in enumerate(por_tramo):
        if not tramo:
            continue
        pct = 100.0 * sum(v is not None for v in tramo) / len(tramo)
        etiqueta = f"{i * 100 // TRAMOS}-{(i + 1) * 100 // TRAMOS} %"
        print(f"  {etiqueta:<10}{_barra(pct)}  {pct:>3.0f} %")

    if not con_pose:
        print("\nNo se encontró a nadie en ningún fotograma del video.")
        return

    # ---- Visibilidad de lo que el sistema evalúa ----
    print(f"\n{'Articulación':<16}{'Media':>9}{'Sobre 0,65':>13}{'':>3}")
    flojas = []
    for nombre in ARTICULACIONES:
        valores = [v[nombre] for v in con_pose]
        media = sum(valores) / len(valores)
        sobre = 100.0 * sum(x >= UMBRAL_VISIBILIDAD for x in valores) / len(valores)
        print(f"{nombre:<16}{media:>9.2f}{sobre:>12.0f} %  {_barra(sobre, 14)}")
        if sobre < 50:
            flojas.append(nombre)

    if flojas:
        print(f"\nPor debajo del umbral la mayor parte del tiempo: {', '.join(flojas)}.")
        print("El sistema las declara no visibles y su veredicto queda nulo. Si en el")
        print("video se ven bien, revisa los PNG guardados: puede ser encuadre, ropa")
        print("del mismo tono que el fondo, o poca luz sobre esa parte del cuerpo.")
    else:
        print("\nLas cuatro articulaciones que el sistema evalúa se ven con holgura.")

    if guardados:
        print("\nFotogramas guardados para inspección visual:")
        for ruta_png in guardados:
            print(f"  {ruta_png}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    diagnosticar(sys.argv[1],
                 int(sys.argv[2]) if len(sys.argv) > 2 else MUESTRAS_POR_DEFECTO)
