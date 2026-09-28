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


def validar_grabacion(ruta):
    """
    ¿Sirve esta ruta como fuente de análisis? Devuelve (sirve, motivo).

    `es_archivo` responde otra pregunta —qué se pidió— y lo hace por extensión,
    sin tocar el disco, porque debe poder verificarse en integración continua.
    Esta función es la que se usa cuando el entrenador elige un archivo en la
    pantalla de cámara, y ahí sí conviene mirar si existe: enterarse de que la
    grabación no está en el momento de elegirla es muy distinto a enterarse
    cuando la sesión ya arrancó.

    El motivo se redacta para quien lo va a leer. "Errno 2" no le dice nada a un
    sensei; "el archivo ya no está en esa carpeta" sí.
    """
    if ruta is None or not str(ruta).strip():
        return False, "No se eligió ningún archivo de video."

    texto = str(ruta).strip()

    if es_url(texto):
        return False, ("Eso es una dirección de red, no un archivo. "
                       "Usa la opción de cámara IP para un flujo en vivo.")

    if not es_archivo(texto):
        extensiones = ", ".join(EXTENSIONES_VIDEO)
        return False, (f"'{os.path.basename(texto)}' no tiene una extensión de video "
                       f"reconocida. Se aceptan: {extensiones}.")

    if not os.path.exists(texto):
        return False, (f"No se encontró '{os.path.basename(texto)}'. "
                       f"Puede haberse movido o estar en un disco desconectado.")

    if not os.path.isfile(texto):
        return False, f"'{os.path.basename(texto)}' es una carpeta, no un archivo de video."

    if os.path.getsize(texto) == 0:
        return False, (f"'{os.path.basename(texto)}' está vacío. "
                       f"Puede ser una grabación que se interrumpió al escribirse.")

    return True, ""


def motivo_fuente_no_abre(fuente):
    """
    Por qué no se pudo abrir una fuente, redactado según lo que era.

    Hasta el 28-sep-2026, `Camera` respondía lo mismo a todo: «Verifica que
    esté conectada y que ninguna otra aplicación la esté usando». Para una
    cámara es el consejo correcto; para un archivo que no existe es un consejo
    absurdo —no hay nada que conectar— y manda a buscar el problema donde no
    está. Ocurrió con una ruta mal escrita: el mensaje hablaba de una cámara
    ocupada y el archivo sencillamente no estaba ahí.

    El diagnóstico bueno ya existía en `validar_grabacion`, pero solo lo usaba
    el selector de archivos de la interfaz. Toda fuente abierta por código
    —las herramientas de medición, `main.py --fuente`, el re-análisis de una
    grabación— caía en el mensaje genérico. Esto es lo que lo reparte.
    """
    if es_archivo(fuente):
        sirve, motivo = validar_grabacion(fuente)
        if not sirve:
            return motivo
        # El archivo está y tiene contenido, así que lo que falla es leerlo.
        return (f"'{os.path.basename(str(fuente).strip())}' existe pero no se pudo "
                f"leer. Puede estar dañado o venir en un formato que este equipo no "
                f"abre; prueba a reproducirlo antes de analizarlo.")

    if es_url(fuente):
        return (f"No se pudo conectar con la cámara IP ({fuente}). Verifica la "
                f"dirección y que el equipo esté en la misma red.")

    return (f"No se pudo abrir la cámara del sistema (índice {fuente}). Verifica "
            f"que esté conectada y que ninguna otra aplicación la esté usando.")


def marca_de_grabacion_ms(pos_msec, indice_frame, fps):
    """
    Instante de un fotograma DENTRO de la grabación, en milisegundos.

    Por qué existe
    --------------
    Con una cámara en vivo, el tiempo transcurrido en el reloj de pared ES el
    tiempo real entre fotogramas, y sirve para derivar velocidades angulares.

    Con una grabación no mide nada de eso: mide cuánto tarda ESTE equipo en
    analizar, que no guarda relación con cuánto duró la ejecución. El cociente
    entre ambos ritmos depende de la máquina, de la resolución y de la velocidad
    del archivo, y puede caer de cualquiera de los dos lados —un video de 60 fps
    se analiza algo más lento que su propia duración; uno de 30 fps, más rápido—.

    Lo que importa no es el tamaño del error sino su naturaleza: es sistemático,
    y cambia de un equipo a otro. La velocidad angular del Kime se deriva de este
    intervalo, de modo que la MISMA grabación analizada en dos computadoras
    distintas produciría velocidades distintas y, cruzando el umbral de los
    400 °/s, veredictos distintos sobre la misma patada.

    Eso destruiría exactamente la propiedad por la que este módulo acepta
    archivos: sobre una grabación la entrada es idéntica en cada corrida, así
    que una diferencia en el resultado solo puede provenir del código. Con el
    reloj de pared, también podría provenir de la computadora.

    Cómo se calcula
    ---------------
    Se prefiere la marca que declara el contenedor de video (`CAP_PROP_POS_MSEC`)
    porque respeta la velocidad real del archivo, incluida la velocidad variable.
    Cuando el contenedor no la informa —algunos formatos y algunos backends
    devuelven cero— se deduce del número de fotograma y la velocidad declarada.

    Devuelve None si ninguna de las dos vías da un valor utilizable, para que
    quien llama decida qué hacer en vez de recibir un cero que parecería válido.
    """
    if pos_msec is not None and pos_msec > 0:
        return float(pos_msec)

    # El primer fotograma de una grabación está legítimamente en el milisegundo
    # cero, así que un índice 0 con pos_msec 0 no es un fallo.
    if indice_frame is not None and indice_frame >= 0 and fps and fps > 0:
        return indice_frame * 1000.0 / fps

    return None
