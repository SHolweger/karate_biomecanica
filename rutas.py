"""
Dónde están el modelo y la base de datos, sin depender de desde dónde se lanzó.

Vive en la raíz y no dentro de una capa porque cruza dos: el modelo de pose es
de `vision/` y la base de datos de `persistence/`, y ninguna de las dos debe
resolver las rutas de la otra. No importa OpenCV, MediaPipe ni sqlite3, así que
la integración continua puede verificarlo entero.

---------------------------------------------------------------------------
POR QUÉ HACE FALTA
---------------------------------------------------------------------------

Hasta ahora el modelo se pedía como `'pose_landmarker_full.task'` —una ruta
relativa, resuelta contra el **directorio de trabajo**— en seis sitios, y la
base de datos como `'karate_sistema.db'` en uno. Eso funciona mientras se
ejecute `python3 main.py` desde la carpeta del proyecto, que es lo que se ha
hecho todo el desarrollo.

Deja de funcionar en cuanto la aplicación se empaqueta, que es justo lo que
falta para llevarla al dojo. Un `.command` abierto con doble clic arranca con
el directorio de trabajo en la carpeta personal del usuario, no en la del
programa; un ejecutable congelado con PyInstaller descomprime sus datos en una
carpeta temporal distinta en cada arranque. En ambos casos el modelo «no
existe» y el error que produce MediaPipe no dice por qué.

---------------------------------------------------------------------------
LA BASE DE DATOS NO VA DONDE VA EL MODELO
---------------------------------------------------------------------------

Y esa distinción es la que evita perder el historial del dojo.

El modelo es **parte del programa**: se instala con él, no cambia, y en un
ejecutable congelado vive dentro del paquete, que es de solo lectura.

La base de datos es **del usuario**: se escribe en cada sesión y tiene que
sobrevivir a reinstalar o actualizar la aplicación. Si viviera dentro del
paquete, la siguiente versión la borraría con todas las mediciones. Por eso va
a la carpeta de datos del sistema operativo.

Con una excepción deliberada: **si ya existe una base junto al código, se sigue
usando esa**. Todo el desarrollo ha escrito en `karate_sistema.db` dentro del
repositorio, y mover ese archivo en silencio dejaría el historial huérfano sin
que nadie se enterara hasta abrir el programa y ver la lista de alumnos vacía.
Migrar es una decisión del usuario, no un efecto secundario de actualizar.
"""
import os
import sys
from pathlib import Path

NOMBRE_MODELO = "pose_landmarker_full.task"
NOMBRE_BASE = "karate_sistema.db"

# Nombre de la carpeta de datos, igual en los tres sistemas para que una copia
# de seguridad hecha en uno se reconozca en otro.
CARPETA_DATOS = "ShotokanAI"

# Variables de entorno de escape. Existen para tres casos reales: las pruebas,
# apuntar a una base compartida en el dojo, y poder mover los datos sin tocar
# el código. Tienen prioridad sobre todo lo demás.
VAR_MODELO = "SHOTOKAN_MODELO"
VAR_BASE = "SHOTOKAN_BD"


class ModeloNoEncontrado(FileNotFoundError):
    """El archivo del modelo de pose no está donde debería."""


def raiz_aplicacion():
    """
    La carpeta desde la que se distribuyen los archivos del programa.

    Con PyInstaller, `sys._MEIPASS` apunta a la carpeta temporal donde el
    ejecutable descomprimió sus datos, y cambia en cada arranque; sin él, la
    carpeta de este archivo. En ningún caso el directorio de trabajo, que es
    precisamente lo que no se puede suponer.
    """
    empaquetado = getattr(sys, "_MEIPASS", None)
    if empaquetado:
        return Path(empaquetado)
    return Path(__file__).resolve().parent


def carpeta_de_datos(entorno=None, inicio=None):
    """
    Dónde guarda sus datos el usuario, según el sistema operativo.

    macOS usa `~/Library/Application Support`, Windows `%APPDATA%` y el resto
    sigue la convención XDG. La carpeta se crea si no existe.
    """
    entorno = os.environ if entorno is None else entorno
    hogar = Path(inicio) if inicio else Path.home()

    if sys.platform == "darwin":
        base = hogar / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(entorno.get("APPDATA") or (hogar / "AppData" / "Roaming"))
    else:
        base = Path(entorno.get("XDG_DATA_HOME") or (hogar / ".local" / "share"))

    carpeta = base / CARPETA_DATOS
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def modelo(entorno=None, raiz=None):
    """
    Ruta absoluta del modelo de pose.

    Falla con un mensaje que dice qué falta y dónde se buscó, en vez de dejar
    que MediaPipe informe un error sobre un archivo que nadie nombró. Un modelo
    ausente es el fallo más probable de un empaquetado mal hecho, y es de los
    que se diagnostican en diez segundos si el mensaje lo dice.
    """
    entorno = os.environ if entorno is None else entorno
    declarado = entorno.get(VAR_MODELO)
    if declarado:
        ruta = Path(declarado)
    else:
        ruta = (Path(raiz) if raiz else raiz_aplicacion()) / NOMBRE_MODELO

    if not ruta.is_file():
        raise ModeloNoEncontrado(
            f"No se encontró el modelo de estimación de pose en {ruta}. "
            f"El archivo '{NOMBRE_MODELO}' (unos 32 MB) tiene que acompañar al "
            f"programa; si lo moviste, indica su ubicación en la variable "
            f"{VAR_MODELO}.")
    return str(ruta)


def base_de_datos(entorno=None, raiz=None, inicio=None):
    """
    Ruta absoluta de la base de datos, sin mover nunca una que ya exista.

    El orden es deliberado: lo que declare el usuario, luego la base heredada
    junto al código —para no dejar huérfano el historial del desarrollo— y solo
    entonces la carpeta de datos del sistema, que es donde deben nacer las
    nuevas.
    """
    entorno = os.environ if entorno is None else entorno
    declarada = entorno.get(VAR_BASE)
    if declarada:
        return str(Path(declarada))

    heredada = (Path(raiz) if raiz else raiz_aplicacion()) / NOMBRE_BASE
    if heredada.is_file():
        return str(heredada)

    return str(carpeta_de_datos(entorno, inicio) / NOMBRE_BASE)
