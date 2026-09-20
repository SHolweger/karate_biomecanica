"""
Qué le cuesta al historial adoptar una recalibración (RF-08).

El problema que resuelve
------------------------
`expert_system/reevaluacion.py` sabe volver a juzgar una medición con otros
umbrales, pero devuelve listas de filas. Un sensei no lee listas de filas: lee
«si adopto esto, doce ejecuciones que di por correctas dejan de serlo».

Este módulo traduce lo uno en lo otro. Es la pieza que convierte una capacidad
del motor en una decisión informada, y por eso importa dónde aparece: **antes**
de guardar, no después. Recalibrar sin ver el efecto es cambiar la vara de medir
a ciegas; el número de veredictos que se mueven es justamente lo que le dice al
cuerpo técnico si el ajuste describe mejor la postura o si se pasó de estricto.

Por qué es un módulo aparte y sin CustomTkinter
-----------------------------------------------
Lo mismo que `gui/validacion_umbrales.py` y `gui/coaching.py`: la regla de
presentación se verifica en integración continua, donde no hay entorno gráfico.
Aquí vive qué se dice; la pantalla solo lo dibuja.

Una nota sobre el tono de los mensajes
--------------------------------------
Ninguna frase de este módulo afirma que el criterio nuevo sea el correcto. El
sistema no está en posición de saberlo: los umbrales los fija el cuerpo técnico,
no el programa. Lo que el sistema sí puede afirmar —y es todo lo que afirma— es
cuántos veredictos se moverían.
"""

# Umbral a partir del cual la cobertura del informe se advierte explícitamente.
#
# Por debajo de esto, "no cambia casi nada" deja de ser una conclusión sobre el
# historial y pasa a ser una conclusión sobre la muestra. Que el sensei lo lea
# sin el aviso sería dejarlo creer que revisó algo que no revisó.
COBERTURA_MINIMA = 0.60

SIN_MEDICIONES = "Todavía no hay mediciones con las que contrastar este cambio."
SIN_IMPACTO = "Ninguna medición del historial cambiaría de veredicto."
NO_SE_ESCRIBE = "Consultar esto no modifica nada de lo ya registrado."


def agrupar_por_tecnica(cambian):
    """
    Los veredictos que se mueven, contados por técnica y por dirección.

    La dirección importa tanto como el número. Doce ejecuciones que pasan de
    correcto a incorrecto significan que el criterio nuevo es más exigente;
    doce en el sentido contrario, que es más permisivo. Sumarlas en un solo
    total borraría exactamente el dato que el cuerpo técnico necesita.
    """
    grupos = {}
    for fila in cambian:
        clave = fila.get("tecnica_clave")
        grupo = grupos.setdefault(clave, {"a_incorrecto": 0, "a_correcto": 0, "total": 0})
        if fila.get("correcto_nuevo"):
            grupo["a_correcto"] += 1
        else:
            grupo["a_incorrecto"] += 1
        grupo["total"] += 1
    return grupos


def titular(informe):
    """La frase que resume el efecto, en los términos en que se va a decidir."""
    total = informe.get("total", 0)
    if not total:
        return SIN_MEDICIONES

    cambian = len(informe.get("cambian", []))
    if not cambian:
        return SIN_IMPACTO

    juzgadas = cambian + len(informe.get("sostienen", []))
    sustantivo = "medición" if juzgadas == 1 else "mediciones"
    verbo = "cambiaría" if cambian == 1 else "cambiarían"
    return f"{cambian} de {juzgadas} {sustantivo} {verbo} de veredicto."


def aviso_de_cobertura(cobertura):
    """
    Cuánto del historial alcanzó el informe, y cuándo eso hay que advertirlo.

    Devuelve None cuando la cobertura es suficiente: un aviso que aparece
    siempre deja de leerse.
    """
    juzgadas = cobertura.get("juzgadas", 0)
    reevaluables = cobertura.get("reevaluables", 0)

    if not juzgadas:
        return None
    if reevaluables >= juzgadas:
        return None

    fuera = juzgadas - reevaluables
    aviso = (f"{reevaluables} de {juzgadas} mediciones del historial se pudieron volver a "
             f"juzgar. Las otras {fuera} no guardan con qué se juzgaron, porque son "
             f"anteriores a esa versión del sistema.")

    if reevaluables / juzgadas < COBERTURA_MINIMA:
        aviso += (" Al quedar fuera la mayor parte, este resultado describe la muestra "
                  "más que al historial completo.")
    return aviso


def resumen(informe, cobertura=None):
    """
    Todo lo que la pantalla necesita mostrar, ya resuelto.

    Se devuelve estructurado y no como un bloque de texto para que la pantalla
    decida el formato —una línea por técnica, con su color— sin que este módulo
    tenga que saber nada de widgets.
    """
    return {
        "titular": titular(informe),
        "hay_cambios": bool(informe.get("cambian")),
        "por_tecnica": agrupar_por_tecnica(informe.get("cambian", [])),
        "cobertura": aviso_de_cobertura(cobertura or {}),
        "nota": NO_SE_ESCRIBE,
    }


def describir_grupo(grupo):
    """
    Una técnica del informe, en una línea.

    Se nombran las dos direcciones por separado incluso cuando una es cero: leer
    «8 dejan de ser correctas» sin ver que ninguna va en sentido contrario no es
    lo mismo que leerlo sabiéndolo.
    """
    partes = []
    if grupo["a_incorrecto"]:
        partes.append(f"{grupo['a_incorrecto']} dejan de ser correctas")
    if grupo["a_correcto"]:
        partes.append(f"{grupo['a_correcto']} pasan a ser correctas")
    return " · ".join(partes) if partes else "sin cambios"
