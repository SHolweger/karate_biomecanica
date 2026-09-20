"""
Re-evaluación de mediciones ya guardadas contra un umbral distinto (RF-08).

El problema que resuelve
------------------------
Cada medición se guarda junto al `id_umbral` que la juzgó, de modo que el
historial nunca queda sin criterio verificable. Pero eso responde "¿con qué
regla se juzgó esto?", no "¿qué diría la regla de hoy sobre lo que medí ayer?".

La segunda pregunta aparece apenas un umbral cambia. El caso concreto que
originó este módulo: los rangos de Kokutsu Dachi que hoy gobiernan el
clasificador se dedujeron del principio biomecánico y están pendientes de
confirmación del sensei. Si esa confirmación corrige un número, todo lo medido
antes queda juzgado con un criterio que ya no es el vigente — y sin forma de
saber cuánto habría cambiado, porque la fila guardaba un solo ángulo promedio y
ni siquiera decía qué postura se había detectado.

Para contestar hace falta guardar, junto a la medición, los MISMOS argumentos
con los que la regla la juzgó: la clave de la técnica y los ángulos que consumió
(uno o dos, según la articulación). Con eso, volver a juzgar es volver a llamar
a la misma función con otros umbrales.

Lo que este módulo NO hace
--------------------------
No escribe. Ni una sola fila.

Re-juzgar en el lugar borraría el veredicto original, que es justamente la
evidencia de qué criterio regía en ese momento — el mismo motivo por el que
recalibrar no reescribe el umbral sino que inserta una versión nueva. Así que
la salida es un INFORME comparativo: cuántas mediciones sostendrían su
veredicto, cuántas cambiarían y cuáles. Qué hacer con esa información es una
decisión del sensei, no un efecto secundario de consultarla.

Vive en un módulo sin dependencias de base de datos ni de visión, por la misma
razón que `gui/validacion_umbrales.py`: así la regla se verifica en integración
continua, donde no hay cámara ni SQLite con datos reales.
"""

# Qué método de KarateRules juzga cada técnica, y cuántos ángulos consume.
#
# El número de ángulos no es decorativo: es lo que distingue una técnica que se
# puede volver a juzgar desde una fila guardada de una que no. Una postura de
# dos articulaciones (Zenkutsu, Kokutsu, Kiba) necesita sus dos ángulos; con uno
# solo, la mitad del criterio faltaría y el veredicto recalculado sería una
# invención.
EVALUADORES = {
    "tsuki":           ("evaluate_tsuki", 1),
    "age_uke":         ("evaluate_age_uke", 1),
    "heiko_dachi":     ("evaluate_heiko_dachi", 1),
    "kiba_dachi":      ("evaluate_kiba_dachi", 2),
    "zenkutsu_dachi":  ("evaluate_zenkutsu_dachi", 2),
    "kokutsu_dachi":   ("evaluate_kokutsu_dachi", 2),
}

# El Mae Geri queda deliberadamente fuera.
#
# Su veredicto no depende solo del ángulo de Kime: `evaluate_mae_geri` consume
# también la velocidad angular pico, que es una magnitud que la máquina de
# estados observa a lo largo de varios fotogramas y que la fila no guarda.
# Recalcularlo con un solo ángulo produciría un "FALTA EXPLOSIVIDAD" o un "KIME
# EXCELENTE" que nadie midió. Es preferible declarar la medición como no
# re-evaluable a devolver un veredicto inventado — el mismo criterio por el que
# la interfaz no muestra lo que el sistema no mide.
NO_REEVALUABLES = {"mae_geri"}


class MedicionNoReevaluable(Exception):
    """La fila no trae lo necesario para volver a juzgarla. El mensaje dice qué falta."""


def es_reevaluable(tecnica_clave, angulo_1=None, angulo_2=None):
    """
    ¿Se puede volver a juzgar esta medición con otros umbrales?

    Falso cuando la técnica no se juzga por ángulos guardados (Mae Geri), cuando
    la fila no declara qué técnica era (una transición no se juzga contra ningún
    umbral, y se guarda con la clave vacía) o cuando falta alguno de los ángulos
    que la regla consume.
    """
    if not tecnica_clave or tecnica_clave in NO_REEVALUABLES:
        return False
    if tecnica_clave not in EVALUADORES:
        return False

    _, cuantos_angulos = EVALUADORES[tecnica_clave]
    if angulo_1 is None:
        return False
    if cuantos_angulos == 2 and angulo_2 is None:
        return False
    return True


def reevaluar(tecnica_clave, angulo_1, angulo_2, reglas):
    """
    Vuelve a juzgar una medición con los umbrales de `reglas`.

    Devuelve `(correcto, mensaje)` — el mismo par que devolvió la regla el día
    que se midió, pero calculado con el criterio que `reglas` tenga hoy.

    Levanta `MedicionNoReevaluable` si la fila no alcanza. Es un error y no un
    `None` silencioso a propósito: quien pregunta por un veredicto recalculado
    necesita distinguir "lo volví a juzgar y da incorrecto" de "no lo pude
    juzgar", y un `None` confundiría ambos casos.
    """
    if not es_reevaluable(tecnica_clave, angulo_1, angulo_2):
        raise MedicionNoReevaluable(
            f"No se puede volver a juzgar '{tecnica_clave}' con los ángulos "
            f"({angulo_1}, {angulo_2}): " + _por_que_no(tecnica_clave, angulo_1, angulo_2)
        )

    nombre_metodo, cuantos_angulos = EVALUADORES[tecnica_clave]
    evaluador = getattr(reglas, nombre_metodo)
    argumentos = (angulo_1,) if cuantos_angulos == 1 else (angulo_1, angulo_2)

    correcto, mensaje, _color = evaluador(*argumentos)
    return correcto, mensaje


def _por_que_no(tecnica_clave, angulo_1, angulo_2):
    """Explica el rechazo en los términos del dominio, no en los de la estructura de datos."""
    if not tecnica_clave:
        return "la medición no registró qué técnica se detectó (fue una transición)"
    if tecnica_clave in NO_REEVALUABLES:
        return ("su veredicto depende de la velocidad angular, que la medición no guarda")
    if tecnica_clave not in EVALUADORES:
        return "no hay una regla registrada para esa técnica"
    _, cuantos = EVALUADORES[tecnica_clave]
    if cuantos == 2 and angulo_1 is not None and angulo_2 is None:
        return "la regla juzga dos articulaciones y la medición solo guarda una"
    return "falta el ángulo que la regla consume"


def comparar(mediciones, reglas):
    """
    Informe de qué cambiaría si los umbrales de `reglas` hubieran regido siempre.

    `mediciones` es una secuencia de mapas con, al menos, las claves
    `tecnica_clave`, `angulo_regla_1`, `angulo_regla_2` y `correcto` — que es
    exactamente lo que devuelve `Database.mediciones_reevaluables()`.

    El informe separa tres grupos, y los tres importan:

      * `sostienen`   — el veredicto no cambia. Es la evidencia de que el ajuste
                        del umbral no desordenó el historial.
      * `cambian`     — el veredicto sí cambia. Cada entrada dice de qué a qué,
                        para que el sensei vea el costo del ajuste antes de
                        adoptarlo.
      * `no_juzgadas` — no se pudieron volver a juzgar, con el motivo. Contarlas
                        evita el error de leer "solo cambian 3" cuando en
                        realidad 200 quedaron fuera del recuento.
    """
    sostienen, cambian, no_juzgadas = [], [], []

    for fila in mediciones:
        clave = fila.get("tecnica_clave")
        a1 = fila.get("angulo_regla_1")
        a2 = fila.get("angulo_regla_2")
        try:
            correcto_nuevo, mensaje_nuevo = reevaluar(clave, a1, a2, reglas)
        except MedicionNoReevaluable as e:
            no_juzgadas.append({**fila, "motivo": str(e)})
            continue

        correcto_antes = fila.get("correcto")
        if correcto_antes is not None:
            correcto_antes = bool(correcto_antes)

        if correcto_antes == correcto_nuevo:
            sostienen.append(fila)
        else:
            cambian.append({
                **fila,
                "correcto_nuevo": correcto_nuevo,
                "diagnostico_nuevo": mensaje_nuevo,
            })

    return {
        "sostienen": sostienen,
        "cambian": cambian,
        "no_juzgadas": no_juzgadas,
        "total": len(sostienen) + len(cambian) + len(no_juzgadas),
    }
