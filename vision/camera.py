"""
Adquisición de video (RF-01).

La fuente dejó de estar escrita a mano en el código. Hasta la versión anterior
el índice 2 —el iPhone por Continuity del equipo de desarrollo— estaba fijo en
`main.py` y en `live_screen.py`; en cualquier otro equipo ese índice no existe
y el fallo era mudo: `get_frame()` devolvía None, la ventana quedaba en negro y
el sistema no informaba la causa. Ahora la fuente se elige, se verifica y, si no
abre, se dice por qué.

La interpretación de una fuente (índice del sistema o dirección de cámara IP)
vive en `vision/fuentes.py`, que no importa OpenCV y por eso puede verificarse
en el entorno de integración continua. Aquí queda solo lo que necesita hardware.
"""
import contextlib
import os
import sys
import time

import cv2

from vision.fuentes import (CamaraNoDisponible, describir, es_archivo, es_url,
                            marca_de_grabacion_ms, normalizar)
from vision.nombres_camara import nombres_del_sistema

# Cuántos índices se sondean al enumerar. Seis cubre con holgura un equipo con
# webcam integrada, una o dos cámaras USB y un par de cámaras virtuales.
MAX_INDICES = 6

__all__ = ["Camera", "CamaraNoDisponible", "describir", "es_url",
           "listar_camaras", "normalizar", "MAX_INDICES"]


@contextlib.contextmanager
def _sin_ruido_de_opencv():
    """
    Silencia lo que se escribe en la terminal mientras se sondean cámaras.

    Preguntar por un índice inexistente hace que el backend de captura imprima
    mensajes como:

        OpenCV: out device of bound (0-2): 3
        OpenCV: camera failed to properly initialize!
        [WARN] VIDEOIO/FFMPEG: Failed list devices for backend avfoundation

    No son errores del sistema —sondear índices vacíos es precisamente cómo se
    descubre cuáles existen— pero llenan la consola y hacen creer al usuario que
    algo se rompió.

    Se silencia al nivel del DESCRIPTOR de archivo, no con `cv2.setLogLevel`:
    esos mensajes los emite el backend nativo (AVFoundation en macOS) con
    `fprintf` directo a la salida de error, por debajo del sistema de bitácora
    de OpenCV, de modo que bajar el nivel no los alcanza.

    El silencio dura solo el sondeo. Un error durante el análisis en vivo sí
    debe verse.
    """
    try:
        nivel_previo = cv2.getLogLevel()
        cv2.setLogLevel(0)              # 0 = SILENT, para lo que sí pasa por OpenCV
    except AttributeError:
        nivel_previo = None             # versiones sin control de bitácora

    copia_stderr = None
    try:
        sys.stderr.flush()
        copia_stderr = os.dup(2)        # se guarda el destino real de la salida de error
        with open(os.devnull, "w") as nulo:
            os.dup2(nulo.fileno(), 2)
        yield
    finally:
        if copia_stderr is not None:
            sys.stderr.flush()
            os.dup2(copia_stderr, 2)    # se restaura antes de devolver el control
            os.close(copia_stderr)
        if nivel_previo is not None:
            cv2.setLogLevel(nivel_previo)


def listar_camaras(maximo=MAX_INDICES):
    """
    Sondea los índices del sistema y devuelve los que entregan imagen.

    Se exige leer un fotograma de verdad, no basta con que `isOpened()` diga que
    sí: en macOS un dispositivo puede abrirse y no entregar nada cuando otra
    aplicación lo tiene tomado, y una lista que ofrece cámaras muertas es peor
    que no ofrecer ninguna.

    El sondeo se detiene tras dos índices consecutivos sin cámara. Abrir un
    dispositivo tarda entre medio segundo y varios segundos según el sistema, y
    recorrer siempre los seis índices dejaba la ventana congelada sin necesidad:
    los dispositivos se numeran de forma correlativa, así que dos huecos
    seguidos significan que ya no hay más.

    Devuelve una lista de dicts con 'indice', 'ancho', 'alto', 'nombre' (el que
    reporta el sistema operativo, o None) y 'muestra' (el fotograma leido para
    verificarla, que la pantalla usa como miniatura: ver la imagen de cada
    camara es la unica forma inequivoca de saber cual es cual).
    """
    encontradas = []
    fallos_seguidos = 0

    with _sin_ruido_de_opencv():
        for indice in range(maximo):
            if fallos_seguidos >= 2:
                break

            captura = cv2.VideoCapture(indice)
            try:
                leido, frame = (False, None)
                if captura.isOpened():
                    leido, frame = captura.read()

                if not leido or frame is None:
                    fallos_seguidos += 1
                    continue

                alto, ancho = frame.shape[:2]
                encontradas.append({"indice": indice, "ancho": ancho, "alto": alto,
                                    "muestra": frame.copy()})
                fallos_seguidos = 0
            finally:
                captura.release()

    # El nombre que da el sistema operativo ("FaceTime HD Camera", "C920") es lo
    # que permite distinguir tres dispositivos que, por indice y resolucion,
    # parecen intercambiables. Se pide una sola vez para todos los indices: en
    # macOS cuesta una llamada a system_profiler, que tarda.
    nombres = nombres_del_sistema([c["indice"] for c in encontradas])
    for camara in encontradas:
        camara["nombre"] = nombres.get(camara["indice"])

    return encontradas




class Camera:
    """
    Fuente de video con espejo horizontal.

    El espejo no es decorativo: el karateka se ve como en el espejo del dojo, y
    es lo que permite que 'izquierda' en pantalla coincida con su izquierda. El
    analizador invierte los landmarks en consecuencia (ver analyzer.py).
    """

    def __init__(self, source=0, espejo=True, verificar=True):
        self.fuente = normalizar(source)
        self.espejo = espejo
        self.cap = cv2.VideoCapture(self.fuente)

        # De dónde sale el tiempo de cada fotograma. Ver marca_de_tiempo_ms().
        self._es_grabacion = es_archivo(source)
        self._inicio = time.monotonic()
        self._marca_ms = 0.0

        if verificar and not self.cap.isOpened():
            self.cap.release()
            raise CamaraNoDisponible(
                f"No se pudo abrir la {describir(source).lower()}. "
                f"Verifica que esté conectada y que ninguna otra aplicación la esté usando.")

    def get_frame(self):
        """Un fotograma listo para analizar, o None si la fuente dejó de entregar."""
        leido, frame = self.cap.read()
        if not leido:
            return None

        if self._es_grabacion:
            # La posición se consulta DESPUÉS de leer, y no antes, porque este
            # backend la informa con un fotograma de retraso: consultada antes,
            # el primer y el segundo fotograma declaran ambos el milisegundo
            # cero y el intervalo entre ellos sale nulo. Medido sobre un archivo
            # de 30 fps, consultarla después devuelve 0, 33.3, 66.7…, que es
            # exactamente el instante del fotograma recién entregado.
            #
            # `POS_FRAMES` queda apuntando al SIGUIENTE fotograma, de ahí el -1
            # para el respaldo por índice.
            marca = marca_de_grabacion_ms(
                self.cap.get(cv2.CAP_PROP_POS_MSEC),
                self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 1,
                self.cap.get(cv2.CAP_PROP_FPS))
            # Si el contenedor no informa ninguna de las dos referencias se
            # conserva la marca anterior antes que inventar uno nuevo: un salto
            # hacia atrás produciría una velocidad angular negativa o enorme.
            if marca is not None:
                self._marca_ms = marca
        else:
            self._marca_ms = (time.monotonic() - self._inicio) * 1000.0

        return cv2.flip(frame, 1) if self.espejo else frame

    def marca_de_tiempo_ms(self):
        """
        Instante del último fotograma entregado, en milisegundos.

        La referencia depende de la fuente, y la distinción no es cosmética.
        Con una cámara en vivo el reloj de pared mide el intervalo real entre
        fotogramas y es la única referencia disponible. Con una grabación no: el
        análisis avanza a la velocidad que permite la estimación de pose
        —alrededor de 100 ms por fotograma— mientras el archivo puede contener
        un fotograma cada 33 ms.

        De ahí que el tiempo de una grabación lo dicte el video y no la máquina
        que lo procesa. La máquina de estados del Mae Geri deriva la velocidad
        angular dividiendo el cambio de ángulo entre este intervalo, de modo que
        usar el reloj de pared sobre un archivo dividiría toda velocidad por el
        factor entre ambos ritmos, e informaría «FALTA EXPLOSIVIDAD» en patadas
        correctas. El error no sería aleatorio sino sistemático.
        """
        return self._marca_ms

    @property
    def resolucion(self):
        """(ancho, alto) declarados por el dispositivo. (0, 0) si no los informa."""
        return (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    def release(self):
        self.cap.release()
