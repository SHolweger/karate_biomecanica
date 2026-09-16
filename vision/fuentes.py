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
    conecta un teléfono por la red local sin cables ni software propietario;
  * la ruta de un archivo de video grabado ('sesion.mp4'), que es lo que permite
    repetir un análisis sobre exactamente la misma ejecución.

Ese tercer caso existe por una razón de método. Medir el rendimiento del sistema
contra una cámara en vivo mezcla dos variables: lo que tarda el sistema y lo que
hizo el karateka en ese momento. Sobre una grabación la entrada es idéntica en
cada corrida, de modo que una diferencia en el resultado solo puede provenir del
código. `test_rendimiento.py` depende de ello.
"""
import os

PREFIJOS_URL = ("http://", "https://", "rtsp://", "rtmp://", "udp://", "tcp://")

# Extensiones que se aceptan como grabación. Se reconoce por extensión y no
# comprobando si el archivo existe: esta regla debe poder verificarse en
# integración continua, donde no hay ningún video que abrir, y porque un archivo
# ausente es un problema del momento de abrirlo —que `Camera` informa con su
# propio mensaje— y no de interpretar qué se pidió.
EXTENSIONES_VIDEO = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg")


class CamaraNoDisponible(RuntimeError):
    """La fuente indicada no se pudo usar. El mensaje explica cuál y por qué."""


def es_url(fuente):
    """Distingue una cámara de red de un índice de dispositivo local."""
    return isinstance(fuente, str) and fuente.strip().lower().startswith(PREFIJOS_URL)


def es_archivo(fuente):
    """
    ¿La fuente es la ruta de un video grabado?

    Una URL con extensión de video NO cuenta: `http://…/stream.mp4` es una
    transmisión de red, y confundirla con un archivo local produciría un mensaje
    de error que apunta al lugar equivocado.
    """
    if not isinstance(fuente, str) or es_url(fuente):
        return False
    return os.path.splitext(fuente.strip().lower())[1] in EXTENSIONES_VIDEO


def normalizar(fuente):
    """
    Convierte la fuente al tipo que espera OpenCV: int para dispositivos
    locales, str para cámaras de red y para archivos.

    La distinción entre int y str es por tipo, no por valor: con el entero 2
    OpenCV abre la tercera cámara del equipo, pero con la cadena "2" busca un
    archivo de video llamado "2". Como el valor llega desde un formulario de la
    interfaz, siempre viene en texto, y sin esta conversión la cámara elegida
    nunca se abriría.
    """
    if es_url(fuente) or es_archivo(fuente):
        return str(fuente).strip()
    try:
        return int(fuente)
    except (TypeError, ValueError):
        raise CamaraNoDisponible(
            f"'{fuente}' no es un índice de cámara, una dirección de cámara IP "
            f"ni un archivo de video")


def describir(fuente):
    """Nombre legible de una fuente, para la interfaz y la bitácora."""
    if es_url(fuente):
        return f"Cámara IP ({fuente})"
    if es_archivo(fuente):
        return f"Video grabado ({fuente})"
    return f"Cámara del sistema (índice {fuente})"
