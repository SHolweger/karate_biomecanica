"""
Validación del formulario de calibración de umbrales (RF-08).

Vive en un módulo aparte, sin importar CustomTkinter, por una razón concreta:
la regla que decide qué es un umbral admisible es lógica del dominio, no del
widget. Separada así, la suite automatizada la verifica incluso en un entorno
sin interfaz gráfica (CI headless), donde la pantalla misma no se puede
construir y sus pruebas quedan en SKIPPED.

La validación es previa a la base de datos, no sustituta: `actualizar_umbral`
sigue rechazando un máximo menor que el mínimo. Aquí se atrapa antes para poder
explicarle al entrenador qué campo está mal, en vez de dejar subir una
excepción.
"""

# Un ángulo articular interno, tal como lo calcula BiomechanicsMath, siempre
# cae entre 0° y 180°: un umbral fuera de ese intervalo sería inalcanzable y
# dejaría la técnica sin poder aprobarse nunca. Las magnitudes en otras
# unidades (velocidad angular, °/s) no tienen este techo.
LIMITE_ANGULAR = 180.0
UNIDAD_ANGULAR = "grados"

# Formas de escribir "este umbral no tiene límite superior". El Mae Geri es el
# caso real: exige al menos 400 °/s de velocidad angular, sin máximo.
SIN_LIMITE = ("", "-", "--", "—", "sin limite", "sin límite", "ninguno", "none", "n/a")


class ValorInvalido(ValueError):
    """Lo escrito en el formulario no describe un rango utilizable."""


def _a_numero(texto, campo):
    """
    Convierte el texto de un campo a float.

    Acepta la coma como separador decimal porque es la convención local de
    escritura y equivocarse en eso no es un error del entrenador, es una
    rigidez del formulario.
    """
    limpio = str(texto).strip().replace(",", ".")
    try:
        return float(limpio)
    except ValueError:
        raise ValorInvalido(f"el {campo} '{texto}' no es un número")


def interpretar_rango(texto_min, texto_max, unidad=UNIDAD_ANGULAR):
    """
    Convierte lo escrito en el formulario al par (valor_min, valor_max) que
    espera `Database.actualizar_umbral`.

    Un máximo vacío significa "sin límite superior" y se traduce a None, no a
    cero: son cosas distintas y confundirlas invertiría el criterio de la regla.

    Devuelve (float, float | None). Lanza ValorInvalido con un mensaje dirigido
    al entrenador —no al programador— cuando algo no cuadra.
    """
    # El mínimo no admite "sin límite": toda técnica necesita un piso contra el
    # cual juzgarse. Solo el techo es opcional.
    if not str(texto_min).strip():
        raise ValorInvalido("el valor mínimo es obligatorio")

    valor_min = _a_numero(texto_min, "valor mínimo")

    if str(texto_max).strip().lower() in SIN_LIMITE:
        valor_max = None
    else:
        valor_max = _a_numero(texto_max, "valor máximo")

    if valor_min < 0 or (valor_max is not None and valor_max < 0):
        raise ValorInvalido("un umbral no puede ser negativo")

    if valor_max is not None and valor_max < valor_min:
        raise ValorInvalido(
            f"el máximo ({formatear_valor(valor_max)}) no puede ser menor que el "
            f"mínimo ({formatear_valor(valor_min)})"
        )

    if unidad == UNIDAD_ANGULAR:
        for valor, campo in ((valor_min, "mínimo"), (valor_max, "máximo")):
            if valor is not None and valor > LIMITE_ANGULAR:
                raise ValorInvalido(
                    f"el {campo} ({formatear_valor(valor)}°) supera los "
                    f"{formatear_valor(LIMITE_ANGULAR)}° que puede medir una articulación"
                )

    return valor_min, valor_max


def formatear_valor(valor):
    """Muestra 160 en vez de 160.0, y 160.5 cuando el decimal sí importa."""
    if valor is None:
        return "sin límite"
    return f"{valor:g}"
