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
import cv2

from vision.fuentes import CamaraNoDisponible, describir, es_url, normalizar

# Cuántos índices se sondean al enumerar. Seis cubre con holgura un equipo con
# webcam integrada, una o dos cámaras USB y un par de cámaras virtuales.
MAX_INDICES = 6

__all__ = ["Camera", "CamaraNoDisponible", "describir", "es_url",
           "listar_camaras", "normalizar", "MAX_INDICES"]


def listar_camaras(maximo=MAX_INDICES):
    """
    Sondea los índices del sistema y devuelve los que entregan imagen.

    Se exige leer un fotograma de verdad, no basta con que `isOpened()` diga que
    sí: en macOS un dispositivo puede abrirse y no entregar nada cuando otra
    aplicación lo tiene tomado, y una lista que ofrece cámaras muertas es peor
    que no ofrecer ninguna.

    Devuelve una lista de dicts con 'indice', 'ancho' y 'alto'.
    """
    encontradas = []
    for indice in range(maximo):
        captura = cv2.VideoCapture(indice)
        try:
            if not captura.isOpened():
                continue
            leido, frame = captura.read()
            if not leido or frame is None:
                continue
            alto, ancho = frame.shape[:2]
            encontradas.append({"indice": indice, "ancho": ancho, "alto": alto})
        finally:
            captura.release()
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
        return cv2.flip(frame, 1) if self.espejo else frame

    @property
    def resolucion(self):
        """(ancho, alto) declarados por el dispositivo. (0, 0) si no los informa."""
        return (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    def release(self):
        self.cap.release()
