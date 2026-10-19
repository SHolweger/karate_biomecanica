"""
Lo medido en una sesión, contra el criterio que lo juzgó.

El prototipo `.dc.html` traía en el reporte una lista de «puntos de control»
—«Ángulo de rodilla delantera · ideal 115–125° · 118° ✓»— con cifras de
adorno, junto a otras que el sistema no puede medir (rotación de cadera en
grados, alineación hombro-puño en centímetros, balance). Esta es la versión con
datos: para cada articulación que una regla juzga, la mediana de lo que se midió
en la sesión, el rango que regía y cuántas evaluaciones quedaron dentro.

Sale de los argumentos con que se juzgó cada medición (`angulo_regla_1`,
`angulo_regla_2`), que se guardan desde el 19-sep-2026, y no del número que se
dibuja en pantalla: en un Kokutsu con la derecha adelante no son el mismo.

Tres cosas que este resumen **no** hace, a propósito:

- **No juzga de nuevo.** El ✓ dice si la mediana cae dentro del rango; cuántas
  evaluaciones cupieron lo dice la cifra de al lado. Una mediana dentro con la
  mitad de las repeticiones fuera no es una técnica dominada, y por eso se
  muestran las dos cosas.
- **No incluye la Mae Geri.** Su veredicto depende también de la velocidad
  angular pico, que no se guarda por medición. Resumirla solo por el ángulo
  diría algo que el criterio no dice — el mismo motivo por el que
  `expert_system/reevaluacion.py` la deja fuera.
- **No nombra el lado en Kiba Dachi.** Se analiza en modo espejo y se filma de
  frente: la «izquierda» de la pantalla es la pierna derecha del alumno. Las
  dos rodillas se resumen juntas, contra el mismo rango.

Las filas son las de una sesión, una por veredicto registrado —el registro
escribe cuando el diagnóstico cambia, no en cada fotograma—, así que la mediana
es la de las evaluaciones, no la de los fotogramas.

Módulo puro: no importa CustomTkinter ni toca la base, y corre en CI.
"""
from statistics import median

from gui.tecnica_ideal import NOMBRES, texto_rango

# Qué articulación juzga cada argumento de la regla, con el nombre que lee el
# sensei. El índice es la posición en `angulos_regla` (0 → angulo_regla_1).
ARGUMENTOS = {
    "heiko_dachi": (("rodilla", "Rodilla más flexionada", (0,)),),
    "kiba_dachi": (("rodilla", "Rodillas", (0, 1)),),
    "zenkutsu_dachi": (("rodilla_frontal", "Rodilla delantera", (0,)),
                       ("rodilla_trasera", "Rodilla trasera", (1,))),
    "kokutsu_dachi": (("rodilla_frontal", "Rodilla delantera", (0,)),
                      ("rodilla_trasera", "Rodilla trasera", (1,))),
    "tsuki": (("codo", "Codo en el Kime", (0,)),),
}

# Orden de lectura: el mismo de la biblioteca de técnicas.
ORDEN = tuple(t for t in NOMBRES if t in ARGUMENTOS)


def _dentro(valor, rango):
    minimo, maximo = rango
    return valor >= minimo and (maximo is None or valor <= maximo)


def puntos_de_control(mediciones, rango_de):
    """
    Un punto por articulación juzgada, en orden de enseñanza.

    `mediciones` son filas con `tecnica_clave`, `angulo_regla_1`,
    `angulo_regla_2` y `correcto`. Solo cuentan las de veredicto cerrado, como
    en todas las consultas agregadas del sistema. `rango_de(tecnica,
    articulacion)` devuelve el `(mínimo, máximo)` que regía, o None si no se
    conoce; sin rango, la articulación no se resume.
    """
    valores = {}
    for fila in mediciones:
        tecnica = fila.get("tecnica_clave")
        if tecnica not in ARGUMENTOS or fila.get("correcto") is None:
            continue
        argumentos = (fila.get("angulo_regla_1"), fila.get("angulo_regla_2"))
        for articulacion, _, indices in ARGUMENTOS[tecnica]:
            for i in indices:
                if argumentos[i] is not None:
                    valores.setdefault((tecnica, articulacion), []).append(argumentos[i])

    puntos = []
    for tecnica in ORDEN:
        for articulacion, etiqueta, _ in ARGUMENTOS[tecnica]:
            serie = valores.get((tecnica, articulacion))
            rango = rango_de(tecnica, articulacion) if serie else None
            if not serie or rango is None:
                continue
            mediana = median(serie)
            puntos.append({
                "tecnica": tecnica,
                "nombre": NOMBRES[tecnica],
                "etiqueta": etiqueta,
                "mediana": mediana,
                "rango": rango,
                "dentro": sum(1 for v in serie if _dentro(v, rango)),
                "total": len(serie),
                "cumple": _dentro(mediana, rango),
            })
    return puntos


def texto_punto(punto):
    """«mediana 108° · criterio 90–115° · 10 de 12 dentro»."""
    return (f"mediana {punto['mediana']:.0f}° · criterio {texto_rango(punto['rango'])} · "
            f"{punto['dentro']} de {punto['total']} dentro")
