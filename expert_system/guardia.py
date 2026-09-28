"""
Qué pierna va adelante, y cuándo el sistema no puede saberlo.

Vive separado de `analyzer.py` por la misma razón que `panel_vivo.py` y
`validacion_umbrales.py`: es geometría pura sobre números, no depende de
MediaPipe ni de OpenCV, y como tal puede verificarse en integración continua.

---------------------------------------------------------------------------
POR QUÉ EXISTE ESTE MÓDULO (28-sep-2026)
---------------------------------------------------------------------------

Zenkutsu Dachi y Kokutsu Dachi son, para el clasificador, **la misma postura
con las piernas intercambiadas**: una rodilla flexionada y la otra extendida.
Lo único que las distingue es cuál de las dos está adelante.

Hasta hoy esa decisión se tomaba así:

    z_diff = tobillo_izq.z - tobillo_der.z
    if z_diff < 0: guardia = "IZQ ADELANTE"
    else:          guardia = "DER ADELANTE"

Dos defectos, y el segundo es el grave:

1. **Solo miraba el eje Z.** La profundidad es la magnitud menos fiable de
   MediaPipe. Pero además es innecesario mirarla sola: cuando la grabación es
   de perfil —que es justamente como hay que filmar estas dos posturas— la
   pierna adelantada se distingue en el eje X, que es la magnitud MÁS fiable
   del modelo. El sistema estaba usando el peor dato disponible.

2. **No existía la rama «no lo sé».** Un `z_diff` de 0,0001 —ruido puro—
   decidía la guardia con la misma firmeza que uno de 0,3. Y como Zenkutsu y
   Kokutsu son simétricos, equivocar la guardia no produce un «no reconocido»:
   produce **la otra postura, con veredicto positivo**. Medido sobre la misma
   geometría corporal, cambiando solo el signo de Z:

       Z correcta  ->  ZENKUTSU (IZQ ADELANTE): POSTURA: FIRME
       Z invertida ->  KOKUTSU  (DER ADELANTE): POSTURA: ESTABLE

   Esa fila entra a la base de datos con `correcto = True` y la técnica
   equivocada, y contamina el historial y la gráfica de evolución del alumno.
   Es el único defecto conocido que **corrompe datos** en vez de solo fallar.

La corrección tiene dos partes:

* Se proyecta la separación de los tobillos sobre el **eje sagital del
  cuerpo** —el eje adelante/atrás de la persona, deducido de la línea de
  caderas— en vez de mirar el eje Z de la cámara. Así la decisión usa
  automáticamente el eje que mejor la informa: X cuando la toma es de perfil,
  Z cuando es frontal, y la mezcla correspondiente en las tomas oblicuas.

* Cuando esa separación no alcanza un mínimo, **se devuelve None**: el
  sistema declara que no puede afirmar qué pierna va adelante, igual que el
  veredicto ya puede ser None. Es el mismo criterio que gobierna toda la
  presentación del proyecto — no mostrar lo que no se mide.

---------------------------------------------------------------------------
LO QUE ESTO **NO** ARREGLA
---------------------------------------------------------------------------

La zona muerta convierte el caso dudoso en una abstención, que es mucho mejor
que una respuesta segura y equivocada. Pero si la toma es frontal y MediaPipe
estima la profundidad con el signo cambiado de forma sostenida, la proyección
saldrá grande y con el sentido incorrecto, y el sistema volverá a acertar la
postura equivocada con confianza.

El remedio completo de ese caso no es numérico sino de protocolo: **Zenkutsu,
Kokutsu, Tsuki y Mae Geri ocurren en el plano sagital y hay que filmarlos de
perfil**. Con la toma correcta esta función decide sobre el eje X y el problema
desaparece. `orientacion_frente_a_camara()` existe precisamente para poder
avisarlo antes de medir en vez de descubrirlo después.
"""

IZQ_ADELANTE = "IZQ ADELANTE"
DER_ADELANTE = "DER ADELANTE"

# Cuánto tienen que estar separados los tobillos, a lo largo del eje sagital,
# para afirmar cuál va adelante. Se expresa en ANCHOS DE CADERA de la propia
# persona y no en unidades normalizadas de MediaPipe, para que no dependa de
# la resolución de la cámara ni de a qué distancia esté el ejecutante.
#
# El valor sale de la definición de las posturas, no de un ajuste empírico: un
# Zenkutsu o un Kokutsu son, por construcción, posturas con un pie claramente
# adelantado respecto del otro. Si los pies no llegan a separarse medio ancho
# de cadera en el eje adelante/atrás, todavía no es ninguna de las dos —es una
# postura simétrica o una transición—, y afirmar una guardia sería inventar.
#
# Conviene contrastarlo contra grabaciones reales antes de fijarlo en la tesis.
SEPARACION_MINIMA_EN_CADERAS = 0.5

# Por debajo de esta fracción, la línea de caderas se considera degenerada
# (las dos caderas prácticamente en el mismo punto) y no define ningún eje.
ANCHO_DE_CADERA_MINIMO = 1e-6


def eje_sagital(cadera_izq, cadera_der):
    """
    El eje adelante/atrás del cuerpo, en el plano horizontal (x, z).

    Se deduce de la línea de caderas: el eje sagital es perpendicular a ella.
    Devuelve `(vector_unitario, ancho_de_caderas)`, o `(None, 0.0)` si las dos
    caderas caen en el mismo punto y no hay línea que usar.

    De las dos perpendiculares posibles hay que elegir una, y cuál es no es
    cuestión de gusto: sale de la anatomía. Con el eje vertical de la imagen
    apuntando hacia abajo, el costado izquierdo de una persona cumple
    `izquierda = arriba × adelante`, y despejando queda

        adelante ∝ (-hz, hx)

    donde `h` es el vector de la cadera derecha anatómica (landmark 24) a la
    izquierda (23). Se comprueba en los dos casos límite: de frente, las
    caderas se separan solo en x con `hx < 0`, y el eje sale (0, -1), hacia la
    cámara; de perfil se separan en profundidad y el eje sale horizontal, en el
    sentido en que mira la persona.

    **Esto estaba al revés hasta el 29-sep-2026**, y el signo equivocado no lo
    delató ninguna prueba: se dedujo de `tests/helpers/fakes.py`, que coloca el
    landmark 24 en x=0,58 —la mitad derecha de la pantalla— mientras que
    MediaPipe lo pone en la izquierda. Medido sobre una grabación real: cadera
    24 en x=0,461 y cadera 23 en x=0,579. El doble y el código compartían el
    mismo supuesto falso, así que las pruebas confirmaban el error en lugar de
    encontrarlo. El coste fue que un Zenkutsu se reportara como Kokutsu: con la
    guardia invertida, la pierna estirada pasa por delantera y la flexionada
    por trasera, que es exactamente la firma de la postura contraria.

    Queda una limitación heredada: de espaldas a la cámara el eje se invierte,
    porque la línea de caderas no distingue el frente del dorso. Detectarlo
    exigiría mirar la cara, que no es lo que este módulo observa.
    """
    hx = cadera_izq[0] - cadera_der[0]
    hz = cadera_izq[1] - cadera_der[1]
    ancho = (hx * hx + hz * hz) ** 0.5
    if ancho < ANCHO_DE_CADERA_MINIMO:
        return None, 0.0

    return (-hz / ancho, hx / ancho), ancho


def separacion_sagital(cadera_izq, cadera_der, tobillo_izq, tobillo_der):
    """
    Cuánto se adelanta un tobillo respecto del otro, en anchos de cadera.

    Positivo = el tobillo izquierdo (visual) va adelante. Negativo = el
    derecho. Cero = no hay diferencia medible.

    Cada punto es un par `(x, z)`. Dividir entre el ancho de caderas es lo que
    hace la medida independiente de la resolución y de la distancia a la
    cámara: un mismo Zenkutsu grabado de cerca y de lejos da el mismo número.
    """
    eje, ancho = eje_sagital(cadera_izq, cadera_der)
    if eje is None:
        return 0.0

    ax = tobillo_izq[0] - tobillo_der[0]
    az = tobillo_izq[1] - tobillo_der[1]
    return (ax * eje[0] + az * eje[1]) / ancho


def pierna_adelantada(separacion, minimo=SEPARACION_MINIMA_EN_CADERAS):
    """
    IZQ_ADELANTE, DER_ADELANTE o **None** cuando no se puede afirmar.

    `None` no es un fallo: es el resultado correcto cuando los tobillos no se
    separan lo suficiente en el eje sagital. Quien llama debe tratarlo como
    trata un veredicto nulo — informar, no calificar.
    """
    if abs(separacion) < minimo:
        return None
    return IZQ_ADELANTE if separacion > 0 else DER_ADELANTE


def orientacion_frente_a_camara(cadera_izq, cadera_der):
    """
    Cuánto mira la persona a la cámara, de 0,0 (de perfil) a 1,0 (de frente).

    Es la fracción del ancho de caderas que se ve en el eje X de la imagen.
    De frente, las dos caderas se separan solo en X y el valor es 1; de perfil
    se separan sobre todo en profundidad y el valor tiende a 0.

    Sirve para avisar ANTES de medir que la toma no corresponde al plano de la
    técnica (ver el encabezado del módulo): las posturas simétricas —Heiko,
    Kiba— se evalúan en el plano frontal y quieren un valor alto, mientras que
    Zenkutsu, Kokutsu, Tsuki y Mae Geri ocurren en el plano sagital y quieren
    un valor bajo. Medir un tsuki de frente a la cámara hace que un codo
    extendido a 175° se proyecte como 90° y se informe como flexionado.

    Devuelve 1.0 si no hay línea de caderas utilizable: sin información, el
    supuesto conservador es la toma frontal, que es la que más avisa.
    """
    hx = cadera_izq[0] - cadera_der[0]
    hz = cadera_izq[1] - cadera_der[1]
    ancho = (hx * hx + hz * hz) ** 0.5
    if ancho < ANCHO_DE_CADERA_MINIMO:
        return 1.0
    return abs(hx) / ancho
