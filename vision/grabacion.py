"""
Reglas de la grabación de una sesión (RF-01, RF-07).

Por qué existe
--------------
Hasta ahora una sesión dejaba mediciones pero no dejaba la ejecución. Eso basta
mientras el criterio de evaluación no se mueva, y deja de bastar en cuanto se
mueve: si un umbral se corrige, `expert_system/reevaluacion.py` puede volver a
juzgar los ángulos guardados, pero no puede recuperar un ángulo que nadie midió
—por ejemplo, si más adelante se agrega una articulación al análisis—. Con la
grabación, la ejecución se puede volver a analizar entera, no solo re-juzgar.

Para la toma de datos de campo la diferencia es práctica: juntar al grupo en el
dojo depende de agendas que el sistema no controla, y una ejecución perdida no
se recupera repitiéndola —sería otra ejecución, de otro día, con otro
cansancio—.

Qué se graba
------------
El fotograma CRUDO, antes de dibujarle el esqueleto y los diagnósticos.

Es una decisión y no un detalle: el video anotado se puede regenerar en
cualquier momento volviendo a pasar el crudo por el analizador, mientras que el
camino inverso no existe. Grabar el anotado dejaría las conclusiones de hoy
cocidas dentro de la evidencia, que es justamente lo que esta grabación intenta
evitar.

Este módulo no importa OpenCV
-----------------------------
Aquí viven solo las decisiones —cómo se llama el archivo, dónde va, a cuántos
fotogramas por segundo se escribe—, por el mismo motivo que `vision/fuentes.py`
vive separado de `camera.py`: así se verifican en integración continua, donde no
hay cámara ni códecs. Lo que necesita hardware está en `vision/grabador.py`.
"""
import os
import re
import unicodedata

# Carpeta por defecto. Fuera de `evidencias/`, que va versionada: un video de
# sesión pesa cientos de megabytes y no tiene nada que hacer en el repositorio.
DIRECTORIO_POR_DEFECTO = "grabaciones"

EXTENSION = ".mp4"

# Cuántos fotogramas se observan antes de decidir la velocidad de escritura.
#
# No se puede usar la velocidad que declara la cámara: el bucle de análisis no
# corre a esa velocidad sino a la que permite la estimación de pose, que es
# varias veces más lenta. Declarar 30 fps sobre un flujo real de 10 produciría
# un video que se reproduce al triple y que ya no coincide con los tiempos de
# las mediciones guardadas.
#
# Doce fotogramas son alrededor de un segundo de análisis real: suficiente para
# una media estable y lo bastante corto como para que el arranque no se note.
FRAMES_PARA_ESTIMAR = 12

# Límites de cordura de la estimación. Fuera de este rango el número no describe
# una grabación sino un tropiezo (el primer fotograma tarda más porque carga el
# modelo; una pausa del sistema operativo hunde la media).
FPS_MINIMO = 1.0
FPS_MAXIMO = 60.0
FPS_POR_DEFECTO = 10.0


def _sin_tildes(texto):
    """Quita diacríticos conservando la letra base: 'Ramírez' -> 'Ramirez'."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def parte_de_nombre(nombre, maximo=24):
    """
    Convierte el nombre de un alumno en un fragmento seguro para un archivo.

    El nombre se conserva —en el dojo, 'sesion_014.mp4' no le dice nada a nadie
    y obliga a abrir el sistema para saber de quién es el video— pero se limpia:
    los espacios, las tildes y los signos de un nombre real ('José Pérez Ah Sún')
    rompen rutas, scripts y copias entre sistemas de archivos distintos.
    """
    if not nombre:
        return "sin_alumno"

    limpio = _sin_tildes(nombre).lower()
    limpio = re.sub(r"[^a-z0-9]+", "_", limpio).strip("_")
    return (limpio[:maximo].rstrip("_") or "sin_alumno")


def nombre_de_archivo(id_sesion, nombre_alumno, cuando):
    """
    Nombre del archivo de una sesión: fecha, hora, alumno e id.

    `cuando` es un datetime. El orden no es estético: empezando por la fecha en
    formato ISO, el listado alfabético de la carpeta queda en orden cronológico,
    que es como se busca una sesión ("la del martes pasado") cuando hay cien.

    El id de sesión va al final porque es lo que ata el archivo a la base de
    datos sin ambigüedad: dos sesiones del mismo alumno el mismo minuto son
    improbables, pero el id las separa igual.
    """
    marca = cuando.strftime("%Y%m%d_%H%M%S")
    return f"{marca}_{parte_de_nombre(nombre_alumno)}_s{id_sesion}{EXTENSION}"


def ruta_de_sesion(id_sesion, nombre_alumno, cuando, directorio=DIRECTORIO_POR_DEFECTO):
    """Ruta completa del archivo de una sesión, sin crear nada."""
    return os.path.join(directorio, nombre_de_archivo(id_sesion, nombre_alumno, cuando))


def fps_estimado(marcas_ms):
    """
    Fotogramas por segundo reales, deducidos de las marcas de tiempo observadas.

    `marcas_ms` son los timestamps en milisegundos de los fotogramas analizados,
    en orden. Se mide el intervalo total entre el primero y el último y se divide
    entre el número de intervalos: eso ignora el costo del primer fotograma —que
    incluye la carga del modelo de pose y no representa al resto— porque el
    primero solo marca el inicio del conteo, no un intervalo.

    Devuelve `FPS_POR_DEFECTO` cuando no hay suficiente información o cuando el
    resultado cae fuera del rango de cordura. Un valor por defecto razonable
    produce un video ligeramente desincronizado; un valor absurdo produce uno
    que no se puede ver.
    """
    if not marcas_ms or len(marcas_ms) < 2:
        return FPS_POR_DEFECTO

    transcurrido_ms = marcas_ms[-1] - marcas_ms[0]
    if transcurrido_ms <= 0:
        return FPS_POR_DEFECTO

    intervalos = len(marcas_ms) - 1
    fps = intervalos * 1000.0 / transcurrido_ms

    if fps < FPS_MINIMO or fps > FPS_MAXIMO:
        return FPS_POR_DEFECTO
    return round(fps, 2)


def describir_resultado(ruta, frames, fps):
    """
    Frase que el sensei lee al terminar la sesión.

    Incluye la velocidad de escritura a propósito: es el dato que explica por
    qué el video dura lo que dura, y sin él una grabación de 10 fps parece
    entrecortada por un defecto en vez de por el costo real del análisis.
    """
    if not ruta or not frames:
        return "No se grabó video de esta sesión."

    segundos = frames / fps if fps else 0
    return (f"Video de la sesión: {os.path.basename(ruta)} "
            f"({frames} fotogramas, {segundos:.0f} s a {fps:g} fps)")


# ---------------------------------------------------------------------------
# Preferencias del equipo
#
# Viven en la tabla `configuracion`, junto a la fuente de video, por el mismo
# motivo: el sistema es local por diseño (RNF-02) y todo el estado del dojo debe
# caber en un solo archivo respaldable.
# ---------------------------------------------------------------------------
CLAVE_GRABAR = "grabar_sesiones"
CLAVE_DIRECTORIO = "directorio_grabaciones"


def grabacion_activada(valor_guardado):
    """
    ¿Se graba video en este equipo?

    Activada por defecto: la grabación es lo que hace repetible el análisis, y
    un sistema que silenciosamente no graba defrauda la expectativa de quien
    creyó estar registrando la clase.

    Poder apagarla no es un lujo. En un dojo se entrena con menores, y filmar a
    un menor requiere el consentimiento de quien lo tiene a cargo. Que el sensei
    pueda decidirlo por equipo —y no que el sistema lo imponga— es lo que
    permite cumplir ese requisito sin renunciar al resto del análisis: apagada,
    la sesión se mide igual y solo deja de quedar el video.

    Se interpreta el texto tal como lo guarda la tabla de configuración, donde
    todo valor es una cadena.
    """
    if valor_guardado is None or valor_guardado == "":
        return True
    return str(valor_guardado).strip().lower() not in ("0", "false", "no", "off")


def directorio_configurado(valor_guardado):
    """Carpeta donde escribir, o la de por defecto si no se configuró ninguna."""
    if valor_guardado is None or not str(valor_guardado).strip():
        return DIRECTORIO_POR_DEFECTO
    return str(valor_guardado).strip()


# Lo que se muestra en el reporte de una sesión cuando no quedó video. Se
# declara la ausencia en vez de omitir la línea: omitirla dejaría al sensei sin
# saber si la sesión no se grabó o si el reporte simplemente no lo menciona —y
# esa diferencia importa cuando va a buscar el archivo.
SIN_VIDEO = "Sin video"


def nombre_visible(ruta_guardada):
    """
    Cómo se nombra el video de una sesión en el reporte.

    Se muestra el nombre del archivo y no la ruta completa: la ruta de un disco
    externo del dojo ocupa media pantalla y no aporta nada que el nombre —que ya
    lleva fecha, alumno e id de sesión— no diga mejor.
    """
    if not ruta_guardada or not str(ruta_guardada).strip():
        return SIN_VIDEO
    return os.path.basename(str(ruta_guardada).strip())
