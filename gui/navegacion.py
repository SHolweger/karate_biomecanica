"""
Mapa de navegación del sistema (RNF-04).

El RNF-04 exige que el ciclo de uso se complete en **no más de tres
pulsaciones**. Hasta ahora ese requisito estaba asociado a un caso de prueba que
verifica que se abre una sesión de análisis, no que se abra en tres clics: nadie
había contado las pulsaciones reales. Y la navegación cambió por completo al
aparecer la barra lateral, de modo que la cuenta anterior —si la hubo— dejó de
valer.

Aquí se declara, para cada tarea principal, la secuencia exacta de controles que
hay que pulsar partiendo del panel de inicio. Dos pruebas la vigilan desde
ángulos distintos:

  * `tests/unit/test_navegacion.py` comprueba el límite de tres pulsaciones.
    Vive en las unitarias porque este módulo no importa CustomTkinter, de modo
    que la cuenta se verifica también en integración continua, sin entorno
    gráfico.
  * `tests/e2e/test_navegacion_rnf04.py` recorre cada ruta pulsando los widgets
    reales de la aplicación. Es lo que impide que esta declaración envejezca:
    si alguien renombra un botón, intercala una pantalla o mueve una acción a
    otro menú, la ruta deja de ser transitable y la prueba falla.

Qué cuenta como pulsación: cada activación de un control con el ratón. Elegir un
valor en un desplegable cuenta como una, aunque materialmente sean dos gestos
(abrirlo y elegir). **Escribir no cuenta**: llenar el nombre de un alumno o la
dirección de una cámara IP es teclear, no navegar, y el requisito mide
profundidad de navegación.

La última pulsación de cada ruta es la que ejecuta la tarea —guardar, confirmar,
abrir la pantalla de destino—, no un paso intermedio: lo que se audita es el
costo de la tarea completa, no el de llegar a asomarse a ella.
"""
from collections import namedtuple

# Secciones de la barra lateral, en el orden en que se usan durante una clase:
# primero el estado del dojo, luego la medición, después el criterio y el
# seguimiento, y al final la configuración del equipo — que se toca una vez y
# casi nunca más.
#
# "perfiles" no está aquí. Elegir sensei no es una sección del sistema sino un
# cambio de quién lo opera, y vive en el pie de la barra junto a la identidad
# activa, que es donde el usuario espera encontrarlo.
#
# "Calibración" tampoco está: recalibrar un umbral es algo que se hace sobre una
# técnica concreta, y se llega desde la biblioteca de técnicas, donde el criterio
# vigente está a la vista. Como sección suelta invitaba a abrir una tabla de diez
# umbrales sin recordar cuál se quería tocar.
#
# Vive en este módulo y no en `barra_lateral.py` para que la suite pueda
# verificar la composición del menú sin CustomTkinter instalado.
SECCIONES = [
    ("inicio",    "Inicio"),
    ("vivo",      "Análisis en vivo"),
    ("historial", "Alumnos y progreso"),
    ("tecnicas",  "Técnicas"),
    ("camara",    "Cámara"),
]

# El límite del RNF-04.
MAXIMO_PULSACIONES = 3

# Punto de partida de todas las rutas: el panel que el sensei ve al entrar.
ORIGEN = "InicioScreen"

# Controles de la pantalla de inicio que llevan a otro lado. Se declaran para
# poder comprobar que ninguna ruta arranca de un control que no existe allí.
CONTROLES_DE_INICIO = ("Iniciar análisis en vivo", "Ver historial")

# Tipos de control que una ruta puede pulsar.
CONTROLES = ("boton", "opcion", "radio", "tarjeta")

# Etiquetas que dependen de los datos del dojo y no del código: el nombre de un
# alumno, el de un sensei, el índice de la cámara conectada. La ruta las declara
# con una marca y la prueba de interfaz las sustituye por el valor real.
ETIQUETAS_VARIABLES = ("{alumno}", "{sensei}", "{camara}", "{cambiar perfil}")

Paso = namedtuple("Paso", "control etiqueta")
Ruta = namedtuple("Ruta", "clave tarea destino pasos")


def etiqueta_cambiar_perfil(rol):
    """
    Texto del control con el que se cambia de sensei, en el pie de la barra.

    Vive aquí porque es a la vez parte de la barra lateral y el primer paso de
    una ruta declarada abajo; escribirlo dos veces habría dejado que uno de los
    dos se desactualizara en silencio.
    """
    return f"{(rol or 'sensei').title()} · cambiar perfil"


# Las tareas principales del sistema, con la secuencia de controles que cada una
# cuesta partiendo del panel de inicio.
RUTAS = (
    Ruta("medir", "Tomar una medición a un alumno", "LiveScreen",
         (Paso("boton", "Iniciar análisis en vivo"),
          Paso("opcion", "{alumno}"))),

    Ruta("inscribir", "Inscribir un alumno nuevo", "HistorialScreen",
         (Paso("boton", "Alumnos y progreso"),
          Paso("boton", "Registrar alumno"),
          Paso("boton", "Guardar alumno"))),

    Ruta("progreso", "Consultar el progreso de un alumno", "AlumnoScreen",
         (Paso("boton", "Alumnos y progreso"),
          Paso("boton", "Ver perfil"))),

    Ruta("reporte", "Abrir el reporte de una sesión", "ReporteScreen",
         (Paso("boton", "Alumnos y progreso"),
          Paso("boton", "Ver perfil"),
          Paso("boton", "Ver reporte"))),

    Ruta("grafica", "Generar la gráfica de evolución de un alumno", "AlumnoScreen",
         (Paso("boton", "Alumnos y progreso"),
          Paso("boton", "Ver perfil"),
          Paso("boton", "Generar reporte"))),

    Ruta("tecnicas", "Consultar qué evalúa el sistema y con qué criterio", "TecnicasScreen",
         (Paso("boton", "Técnicas"),)),

    Ruta("calibrar", "Recalibrar el umbral de una técnica", "UmbralesScreen",
         (Paso("boton", "Técnicas"),
          Paso("boton", "Calibrar umbrales"),
          Paso("boton", "Guardar cambios"))),

    Ruta("camara", "Cambiar la fuente de video", "CamaraScreen",
         (Paso("boton", "Cámara"),
          Paso("radio", "{camara}"),
          Paso("boton", "Usar esta cámara"))),

    Ruta("sensei", "Cambiar el sensei que opera el sistema", "InicioScreen",
         (Paso("boton", "{cambiar perfil}"),
          Paso("tarjeta", "{sensei}"),
          Paso("boton", "Entrar"))),
)


def etiquetas_de_seccion():
    """Los textos de los botones de la barra lateral."""
    return [etiqueta for _, etiqueta in SECCIONES]


def pulsaciones(ruta):
    """Cuántos clics cuesta la tarea."""
    return len(ruta.pasos)


def ruta(clave):
    """La ruta declarada con esa clave."""
    for candidata in RUTAS:
        if candidata.clave == clave:
            return candidata
    raise KeyError(f"no hay ninguna ruta declarada con la clave '{clave}'")


def exceden_el_limite(rutas=RUTAS, limite=MAXIMO_PULSACIONES):
    """
    Las rutas que incumplen el RNF-04, con su cuenta.

    Devuelve una lista de (tarea, pulsaciones) en vez de un booleano para que el
    fallo de la prueba diga qué tarea se alargó y cuánto, que es lo que hace
    falta para corregirla.
    """
    return [(r.tarea, pulsaciones(r)) for r in rutas if pulsaciones(r) > limite]
