"""
Resolución de la fuente de video (RF-01).

Vive separado de `camera.py` por la misma razón que `gui/validacion_umbrales.py`
vive separado de la pantalla: aquí no se importa OpenCV, así que la regla que
decide cómo se interpreta una fuente se verifica en la suite automatizada
incluso en un entorno sin cámara ni dependencias de visión —que es justamente
el entorno de integración continua.

Una fuente puede ser:
  * un índice entero del sistema (0, 1, 2…): webcam integrada, cámara USB,
    OBS Virtual Camera o Camo, que macOS expone como dispositivos normales;
  * una URL de cámara IP ('http://192.168.1.50:8080/video'), que es como se
    conecta un teléfono por la red local sin cables ni software propietario.
"""

PREFIJOS_URL = ("http://", "https://", "rtsp://", "rtmp://", "udp://", "tcp://")


class CamaraNoDisponible(RuntimeError):
    """La fuente indicada no se pudo usar. El mensaje explica cuál y por qué."""


def es_url(fuente):
    """Distingue una cámara de red de un índice de dispositivo local."""
    return isinstance(fuente, str) and fuente.strip().lower().startswith(PREFIJOS_URL)


def normalizar(fuente):
    """
    Convierte la fuente al tipo que espera OpenCV: int para dispositivos
    locales, str para cámaras de red.

    La distinción es por tipo, no por valor: con el entero 2 OpenCV abre la
    tercera cámara del equipo, pero con la cadena "2" busca un archivo de video
    llamado "2". Como el valor llega desde un formulario de la interfaz, siempre
    viene en texto, y sin esta conversión la cámara elegida nunca se abriría.
    """
    if es_url(fuente):
        return str(fuente).strip()
    try:
        return int(fuente)
    except (TypeError, ValueError):
        raise CamaraNoDisponible(
            f"'{fuente}' no es un índice de cámara ni una dirección de cámara IP")


def describir(fuente):
    """Nombre legible de una fuente, para la interfaz y la bitácora."""
    if es_url(fuente):
        return f"Cámara IP ({fuente})"
    return f"Cámara del sistema (índice {fuente})"
