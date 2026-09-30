"""
Cuándo hay un Tsuki que juzgar, y cuándo el brazo solo está ahí.

Módulo puro: recibe un ángulo de codo ya calculado y una marca de tiempo, y
decide si en este instante hay un golpe que evaluar. No conoce MediaPipe, ni
píxeles, ni la base de datos, así que la integración continua puede verificarlo
entero.

---------------------------------------------------------------------------
QUÉ DEFECTO CORRIGE
---------------------------------------------------------------------------

`analyze_tsuki` juzgaba el codo en CADA fotograma en que el brazo se viera, sin
preguntar antes si se estaba ejecutando un golpe. Como el rango de evaluación
del Tsuki es 160–175° y un brazo colgando al costado mide entre 160 y 180°, el
sistema emitía veredictos de Tsuki sobre alguien que estaba de pie sin hacer
nada:

    codo a 164°  ->  "TSUKI: EXCELENTE"                correcto=True
    codo a 179°  ->  "TSUKI: HIPEREXTENDIDO (Peligro)" correcto=False

Ninguno de los dos es un Tsuki. Quedó a la vista en la prueba en vivo del
30-sep-2026: de pie y con los brazos abajo, la pantalla informaba «IZQ - TSUKI:
EXCELENTE / DER - TSUKI: EXCELENTE», y al moverse a una postura, «IZQ - TSUKI:
HIPEREXTENDIDO (peligro)» con el veredicto de sesión en «Incorrecto».

Es el mismo tipo de fallo que el de la guardia (28-sep) y por eso importa más
que un mensaje feo en pantalla: **no falla, inventa**. Esas filas entran a la
base con `tecnica="tsuki"` y un veredicto cerrado, así que contaminan la
precisión del alumno, su gráfica de evolución y el conteo de errores
frecuentes. Y `expert_system/riesgos.py` cuenta las hiperextensiones para
advertir de lesión: bastaba estar de pie con los brazos estirados para que el
reporte recomendara corregir el bloqueo del codo al impacto.

El Mae Geri nunca tuvo este problema porque se evalúa con una máquina de
estados que solo emite veredicto al cerrar el Kime, y la postura aprendió a
abstenerse el 28-sep. El Tsuki era la única técnica que juzgaba un ESTADO en
vez de una TRANSICIÓN.

---------------------------------------------------------------------------
CÓMO SE DECIDE QUE HUBO UN GOLPE
---------------------------------------------------------------------------

Un Tsuki no es un ángulo: es una extensión del codo que termina deteniéndose
—el Kime es justamente el instante en que la extensión se detiene—. Así que el
criterio es un RECORRIDO, no un umbral:

1. Se mira cuánto ha subido el ángulo respecto del MÍNIMO de la ventana de
   tiempo reciente. Si sube `RECORRIDO_MINIMO`, el brazo se está extendiendo.
2. Se sigue el máximo. El veredicto se emite cuando el ángulo empieza a caer
   —el brazo vuelve, el golpe terminó— y se juzga con el máximo alcanzado, que
   es el ángulo del Kime.

Un brazo quieto no recorre nada: la ventana lo acompaña y la diferencia se
queda en el ruido del filtro. Por eso el criterio separa limpiamente sin
depender de calibrar un umbral fino, igual que la separación en anchos de
cadera de `guardia.py`.

**El par (recorrido, ventana) ES un umbral de velocidad**, y conviene decirlo
así: 35° en 500 ms equivale a exigir **70°/s**. Una extensión más lenta que eso
no se reconoce como golpe.

Esa consecuencia se comprobó en vivo el 30-sep-2026: **un Tsuki ejecutado
despacio no se detecta**. No es un fallo, es lo que el umbral decide — pero
estuvo mal descrito, porque este comentario llegó a afirmar que «una ejecución
lenta frente al espejo sigue siendo un Tsuki». Con este criterio, no.

Y ahí hay una tensión real que **no está resuelta**: `expert_system/riesgos.py`
recomienda literalmente «trabajar el Tsuki a velocidad media frente al espejo,
deteniendo la extensión justo antes del bloqueo». Un sistema que recomienda
practicar despacio y luego no mide cuando se practica despacio se contradice.
Bajar el umbral, en cambio, reabre la puerta a los falsos positivos que este
módulo existe para cerrar.

La decisión pide datos y no criterio, y por eso los dos umbrales son
**parámetros del constructor** y no constantes leídas directamente:
`revisar_tsuki.py` barre combinaciones sobre una grabación real y contrasta
los golpes reconocidos contra los ejecutados. Mientras tanto rigen los valores
del módulo.

`RECORRIDO_MINIMO` sale de la definición de la técnica —el Hikite parte del
puño en la cadera, con el codo muy flexionado, y hasta un Kizami Tsuki desde
kamae recorre bastante más de 35°— pero **conviene contrastarlo contra
grabaciones reales antes de fijarlo en la tesis**, igual que
`SEPARACION_MINIMA_EN_CADERAS`.

---------------------------------------------------------------------------
QUÉ CAMBIA EN LA BASE DE DATOS
---------------------------------------------------------------------------

Antes, un minuto de pie generaba filas de Tsuki cada vez que el ángulo cruzaba
el límite de 175° por el temblor natural del brazo. Ahora se registra **un
veredicto cerrado por golpe**, que es lo que «evaluaciones» debería haber
significado siempre. Los estados intermedios se registran con `correcto=None`,
así que quedan fuera de la precisión y del panel de correcciones sin perderse
del historial.
"""
from collections import deque

from expert_system.knowledge_base import KarateRules

# Estados de la máquina.
REPOSO = "REPOSO"
EXTENDIENDO = "EXTENDIENDO"
RECOGIENDO = "RECOGIENDO"

# Cuánto tiene que abrirse el codo, en grados, sobre el mínimo reciente para
# aceptar que el brazo está golpeando y no simplemente moviéndose. Ver arriba:
# provisional, a contrastar contra grabaciones del dojo.
RECORRIDO_MINIMO = 35.0

# Ventana de tiempo sobre la que se mide ese recorrido. En milisegundos y no en
# fotogramas a propósito: el bucle corre a la velocidad de MediaPipe, no a la
# de la cámara, así que contar fotogramas haría que el criterio dependiera de
# la máquina que analiza. Es el mismo motivo por el que `analyze_mae_geri`
# recibe `timestamp_ms`.
#
# Junto con RECORRIDO_MINIMO fija implícitamente una velocidad mínima de 70°/s,
# y ese es el número que conviene discutir: un Tsuki real extiende el codo unos
# 125° en 150-250 ms, o sea entre 500 y 800°/s, así que pasa con holgura de un
# orden de magnitud; levantar el brazo sin intención de golpear ronda los 60°/s
# y no pasa. Medio segundo cubre además la extensión entera, de modo que el
# mínimo de la ventana sigue siendo el Hikite y no un punto intermedio del
# propio golpe.
VENTANA_RECORRIDO_MS = 500

# Cuánto tiene que retroceder el ángulo desde su máximo para dar por terminada
# la extensión. Por encima del temblor que deja el filtro de media móvil, para
# no cerrar el golpe en un rebote de medición.
MARGEN_PICO = 6.0

# Si el brazo se queda extendido, el golpe se juzga igual con el máximo
# alcanzado. A diferencia del Mae Geri —donde sostener la pierna en el aire
# descarta el intento— aquí el golpe YA ocurrió: no recogerlo es una
# observación sobre el Hikite, no motivo para no evaluar el Kime.
TIEMPO_MAXIMO_EXTENSION_MS = 1500

SIN_GOLPE = "SIN TSUKI: BRAZO EN REPOSO"
EN_EXTENSION = "TSUKI: EXTENDIENDO..."

NARANJA = (0, 165, 255)
GRIS = (150, 150, 150)


class TsukiStateMachine:
    """
    Decide si hay un Tsuki que juzgar y lo evalúa una sola vez por golpe.

    Una instancia por brazo. Recibe el ángulo del codo YA filtrado —el filtro
    vive en el analizador, junto al resto de articulaciones— y devuelve siempre
    un diccionario, porque el codo se sigue midiendo aunque no haya técnica: lo
    que falta en los estados intermedios es el veredicto, no el dato.
    """

    def __init__(self, reglas=None, recorrido_minimo=RECORRIDO_MINIMO,
                 ventana_ms=VENTANA_RECORRIDO_MS):
        # Sin reglas explícitas se instancian las de literatura, para poder
        # probar la máquina sin base de datos.
        self.reglas = reglas or KarateRules()
        # Los dos umbrales son parámetros y no constantes leídas directamente
        # porque están declarados provisionales: hace falta poder barrerlos
        # contra grabaciones reales para elegirlos con datos. Lo hace
        # `revisar_tsuki.py`. El sistema usa los valores del módulo.
        self.recorrido_minimo = recorrido_minimo
        self.ventana_ms = ventana_ms
        self.reset()

    def reset(self):
        """
        Vuelve a empezar. La usa el analizador cuando el brazo desaparece de
        cuadro: un golpe interrumpido a media extensión se descarta en vez de
        juzgarse con el trozo que se alcanzó a ver.
        """
        self._ventana = deque()
        self.estado = REPOSO
        self.pico = None
        self.t_inicio_extension_ms = None
        self.ultimo_veredicto = None

    # -----------------------------------------------------------------
    # La ventana deslizante
    # -----------------------------------------------------------------

    def _recorrido(self, angulo, t_ms):
        """
        Cuánto se ha abierto el codo sobre el mínimo de la ventana reciente, y
        si en este instante se está abriendo o ya viene de vuelta.

        El recorrido vale 0 en el primer fotograma: sin historia no se puede
        afirmar que haya habido recorrido, y arrancar suponiendo que sí
        produciría un golpe fantasma cada vez que el alumno entra en cuadro con
        el brazo extendido.

        Hacen falta LAS DOS cifras. Con el recorrido a secas, el brazo seguía
        estando muy por encima del mínimo de la ventana MIENTRAS VOLVÍA del
        golpe, así que la máquina detectaba un segundo golpe en la propia
        recogida del primero y lo calificaba de «FLEXIONADO» a mitad del
        regreso. Que el ángulo esté en el máximo de la ventana es lo que
        distingue abrirse de estar abierto.
        """
        self._ventana.append((t_ms, angulo))
        while len(self._ventana) > 1 and t_ms - self._ventana[0][0] > self.ventana_ms:
            self._ventana.popleft()

        angulos = [a for _, a in self._ventana]
        return angulo - min(angulos), angulo >= max(angulos) - MARGEN_PICO

    # -----------------------------------------------------------------
    # El ciclo
    # -----------------------------------------------------------------

    def update(self, angulo, t_ms):
        """
        Procesa un fotograma y devuelve el diagnóstico del brazo.

        El veredicto cerrado (`correcto` True/False) aparece UNA vez por golpe,
        en el fotograma en que se cierra el Kime. El resto del tiempo `correcto`
        es None: el ángulo está medido, pero no hay técnica que calificar.
        """
        recorrido, abriendose = self._recorrido(angulo, t_ms)

        if self.estado == REPOSO:
            if recorrido >= self.recorrido_minimo and abriendose:
                self.estado = EXTENDIENDO
                self.pico = angulo
                self.t_inicio_extension_ms = t_ms
                return self._transitorio(angulo, EN_EXTENSION, NARANJA)
            return self._transitorio(angulo, SIN_GOLPE, GRIS)

        if self.estado == EXTENDIENDO:
            self.pico = max(self.pico, angulo)
            sostenido = t_ms - self.t_inicio_extension_ms > TIEMPO_MAXIMO_EXTENSION_MS

            if angulo <= self.pico - MARGEN_PICO or sostenido:
                self.estado = RECOGIENDO
                return self._juzgar(angulo)

            return self._transitorio(angulo, EN_EXTENSION, NARANJA)

        # RECOGIENDO: se sostiene el veredicto del golpe mientras el brazo
        # vuelve, igual que la máquina del Mae Geri sostiene el suyo mientras la
        # pierna se asienta. Se sale por cualquiera de dos caminos:
        #
        # - el brazo ya recogió lo bastante como para poder golpear otra vez.
        #   Hace falta mirarlo explícitamente por el Renzuki: en golpes
        #   encadenados el puño no vuelve al Hikite, y esperar a que la ventana
        #   se vacíe perdería el segundo golpe;
        # - o la ventana dejó de ver recorrido, que es lo que ocurre cuando el
        #   brazo se queda extendido donde terminó.
        if angulo <= self.pico - self.recorrido_minimo or recorrido < self.recorrido_minimo:
            self.estado = REPOSO
            self.pico = None
        return dict(self.ultimo_veredicto, angulo=angulo)

    # -----------------------------------------------------------------

    def _transitorio(self, angulo, mensaje, color):
        """
        Hay ángulo pero no hay veredicto.

        `tecnica` va en None a propósito, y no en "tsuki": la fila no es una
        medición de Tsuki, así que tampoco debe entrar en el informe de
        recalibración de `expert_system/reevaluacion.py`.
        """
        return {"angulo": angulo, "mensaje": mensaje, "color": color,
                "correcto": None, "tecnica": None, "angulos_regla": None}

    def _juzgar(self, angulo):
        """
        El veredicto del golpe, con el ángulo del Kime.

        Se evalúa `self.pico` —el máximo que alcanzó la extensión— y no el
        ángulo del fotograma actual, que ya viene de vuelta. Es el mismo
        criterio con el que la máquina del Mae Geri juzga el Kime con
        `angulo_maximo_extension`.
        """
        es_correcto, mensaje, color = self.reglas.evaluate_tsuki(self.pico)
        self.ultimo_veredicto = {
            "angulo": self.pico, "mensaje": mensaje, "color": color,
            "correcto": es_correcto,
            "id_umbral": self.reglas.id_umbral_principal("tsuki"),
            # Con qué ángulo se juzgó, para poder volver a juzgarlo si el
            # umbral cambia (RF-08). Es el del Kime, no el de pantalla.
            "tecnica": "tsuki", "angulos_regla": (self.pico,),
        }
        return dict(self.ultimo_veredicto, angulo=angulo)
