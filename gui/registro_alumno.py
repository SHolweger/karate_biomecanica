"""
Validación del formulario de inscripción de alumnos, sin interfaz gráfica.

Separada de la ventana por la misma razón que el resto de la lógica pura del
proyecto: decidir qué es una edad válida o cuándo procede pedir el grado son
reglas, y como reglas se verifican en la integración continua, donde no hay
entorno gráfico.
"""

# Cinturones del sistema kyu/dan de Shotokan, del principiante al avanzado.
COLORES_CINTA = ["Blanca", "Amarilla", "Naranja", "Verde", "Azul", "Morada", "Café", "Negra"]

# El grado numérico solo se pide a partir del cinturón café.
#
# En los colores anteriores el color YA determina el kyu, de modo que pedir el
# número por separado abre la puerta a que la ficha se contradiga (una cinta
# amarilla registrada como 2º kyu). Del café en adelante el mismo color abarca
# varios grados —café es 3º, 2º y 1º kyu; negra va de 1º dan en adelante— y ahí
# el número sí agrega información que el color no tiene.
CINTAS_CON_GRADO = {"Café", "Negra"}

GRADOS_CAFE = ["3er kyu", "2do kyu", "1er kyu"]
GRADOS_NEGRA = [f"{n}º dan" for n in range(1, 11)]

EDAD_MINIMA = 3
EDAD_MAXIMA = 99
PESO_MINIMO = 10.0
PESO_MAXIMO = 250.0


class DatosInvalidos(ValueError):
    """Un campo del formulario no se puede interpretar. El mensaje es para el sensei."""


def pide_grado(color_cinta):
    """¿Corresponde pedir el grado numérico para este color de cinta?"""
    return color_cinta in CINTAS_CON_GRADO


def grados_de(color_cinta):
    """Grados disponibles para un color. Vacío si el color ya determina el kyu."""
    if color_cinta == "Café":
        return list(GRADOS_CAFE)
    if color_cinta == "Negra":
        return list(GRADOS_NEGRA)
    return []


def interpretar_edad(texto):
    """Edad en años, o None si se dejó vacía."""
    return _entero_en_rango(texto, "La edad", EDAD_MINIMA, EDAD_MAXIMA)


def interpretar_peso(texto):
    """
    Peso en kilogramos, o None si se dejó vacío.

    Acepta coma decimal: en Guatemala se escribe 62,5 tan a menudo como 62.5, y
    rechazarlo sería corregir al usuario por una convención tipográfica.
    """
    limpio = (texto or "").strip().replace(",", ".")
    if not limpio:
        return None
    try:
        peso = float(limpio)
    except ValueError:
        raise DatosInvalidos(f"El peso «{texto.strip()}» no es un número.")
    if not PESO_MINIMO <= peso <= PESO_MAXIMO:
        raise DatosInvalidos(f"El peso debe estar entre {PESO_MINIMO:g} y {PESO_MAXIMO:g} kg.")
    return peso


def _entero_en_rango(texto, etiqueta, minimo, maximo):
    limpio = (texto or "").strip()
    if not limpio:
        return None
    try:
        valor = int(limpio)
    except ValueError:
        raise DatosInvalidos(f"{etiqueta} «{limpio}» no es un número entero.")
    if not minimo <= valor <= maximo:
        raise DatosInvalidos(f"{etiqueta} debe estar entre {minimo} y {maximo} años.")
    return valor


def interpretar_formulario(nombre, edad="", peso="", color_cinta="", grado="",
                           tiempo_entrenando="", notas=""):
    """
    Convierte lo escrito en el formulario en los argumentos de `crear_atleta`.

    Solo el nombre es obligatorio. Todo lo demás se completa después: en el dojo
    un alumno se apunta el primer día y la ficha se llena con el tiempo.

    Lanza `DatosInvalidos` con un mensaje dirigido al sensei —y no un error
    técnico— para que la ventana pueda mostrarlo tal cual.
    """
    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        raise DatosInvalidos("El nombre del alumno es obligatorio.")

    color = (color_cinta or "").strip() or None
    if color is not None and color not in COLORES_CINTA:
        raise DatosInvalidos(f"«{color}» no es un color de cinta reconocido.")

    # Un grado escrito bajo un color que no lo admite se descarta en vez de
    # guardarse: es el residuo de haber cambiado el color después de elegirlo, y
    # conservarlo dejaría una ficha que se contradice a sí misma.
    grado_limpio = (grado or "").strip() or None
    if not pide_grado(color):
        grado_limpio = None

    return {
        "nombre": nombre_limpio,
        "edad": interpretar_edad(edad),
        "peso_kg": interpretar_peso(peso),
        "color_cinta": color,
        "grado_cinturon": grado_limpio,
        "tiempo_entrenando": (tiempo_entrenando or "").strip() or None,
        "notas": (notas or "").strip() or None,
    }
