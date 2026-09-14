"""
Traducción de un diagnóstico técnico a una corrección que el alumno pueda usar.

El motor emite veredictos en el lenguaje del sistema —«TSUKI: HIPEREXTENDIDO
(Peligro)»— porque ese texto es también la clave con la que la base de datos
agrupa los errores frecuentes de una sesión. Cambiarlo rompería la continuidad
del historial: los registros viejos y los nuevos dejarían de agruparse juntos.

Así que el veredicto se conserva tal cual como RECORD, y aquí se le añade la
frase que el sensei diría en el tatami. Lo que corrige un alumno no es saber que
su codo está a 178°, sino oír «no bloquees el codo al impacto».

Es una tabla de traducción y nada más: no decide si algo está bien o mal, eso ya
viene resuelto por `KarateRules`.
"""

# Frase de entrenamiento por veredicto. La clave es el texto que emite la base de
# conocimientos, sin el prefijo de lado ("IZQ - " / "DER - ").
#
# Cada entrada dice QUÉ corregir y POR QUÉ, en ese orden. El porqué no es
# relleno: un alumno que entiende que la hiperextensión daña el codo la corrige
# aunque nadie lo esté mirando.
CORRECCIONES = {
    "TSUKI: EXCELENTE":
        ("Kime correcto", "el brazo llega extendido sin bloquear la articulación"),
    "TSUKI: HIPEREXTENDIDO (Peligro)":
        ("No bloquees el codo al impacto", "la hiperextensión carga el ligamento y lesiona"),
    "TSUKI: FLEXIONADO":
        ("Extiende más el brazo", "sin llegar al final no hay Kime y el golpe pierde fuerza"),

    "HEIKO DACHI: CORRECTO":
        ("Postura natural correcta", "peso repartido y piernas sin flexión marcada"),
    "HEIKO DACHI: DEMASIADO FLEXIONADO":
        ("Estira las piernas", "el Heiko Dachi es una postura natural, no una guardia baja"),

    "POSTURA: FIRME":
        ("Postura firme", "la altura y el reparto de peso son los correctos"),
    "POSTURA: ESTABLE":
        ("Postura estable", "el peso está donde corresponde a esta guardia"),
    "POSTURA: CORREGIR ALTURA":
        ("Corrige la altura de la postura",
         "la flexión de rodilla no corresponde a la guardia que estás marcando"),

    "MAE GERI: KIME EXCELENTE":
        ("Patada con Kime", "extensión completa y con velocidad"),
    "MAE GERI: KIME INCOMPLETO":
        ("Extiende del todo la pierna", "la patada se queda corta y no transmite impacto"),
    "MAE GERI: FALTA EXPLOSIVIDAD":
        ("Más velocidad en la extensión", "la potencia del Mae Geri nace de lo rápido que sale"),

    "HIKIASHI: CORRECTO":
        ("Buen Hikiashi", "recogiste la pierna antes de bajarla"),
    "HIKIASHI: PIERNA CAYO SIN RECOGER":
        ("Recoge la pierna antes de bajarla",
         "si el pie cae solo, quedas desequilibrado y expuesto"),

    "AGE UKE: EFECTIVO":
        ("Bloqueo efectivo", "el antebrazo desvía con el ángulo correcto"),
    "AGE UKE: DEMASIADO FLEXIONADO":
        ("Abre un poco el codo", "tan cerrado, el bloqueo no llega a desviar el ataque"),
    "AGE UKE: DEMASIADO EXTENDIDO":
        ("Cierra un poco el codo", "con el brazo estirado el bloqueo deja pasar el golpe"),
}

# Prefijos de lado que el analizador antepone al veredicto.
LADOS = {"IZQ - ": "izquierdo", "DER - ": "derecho"}


def separar_lado(mensaje):
    """Devuelve (veredicto sin prefijo, lado legible o None)."""
    for prefijo, lado in LADOS.items():
        if mensaje.startswith(prefijo):
            return mensaje[len(prefijo):], lado
    return mensaje, None


def traducir(mensaje):
    """
    Corrección legible a partir de un veredicto del motor.

    Devuelve (instrucción, motivo). Un veredicto sin entrada en la tabla se
    devuelve tal cual y sin motivo: es preferible mostrar el texto técnico que
    inventar un consejo que la regla no respalda — si mañana se agrega una regla
    nueva, el panel seguirá siendo correcto aunque suene menos natural.
    """
    veredicto, lado = separar_lado(mensaje or "")
    instruccion, motivo = CORRECCIONES.get(veredicto, (veredicto, None))

    if lado is not None and veredicto in CORRECCIONES:
        instruccion = f"{instruccion} ({lado})"
    return instruccion, motivo


def sin_traduccion():
    """
    Veredictos que la base de conocimientos emite y esta tabla no cubre.

    La usa la suite para avisar cuando se agrega una regla y se olvida su
    corrección: el panel seguiría funcionando, pero mostrando lenguaje de máquina
    en la pantalla donde el alumno espera una instrucción.
    """
    from expert_system import knowledge_base

    emitidos = set()
    for linea in open(knowledge_base.__file__, encoding="utf-8"):
        marca = 'return True, "' if 'return True, "' in linea else (
            'return False, "' if 'return False, "' in linea else None)
        if marca:
            emitidos.add(linea.split(marca, 1)[1].split('"', 1)[0])
    return sorted(emitidos - set(CORRECCIONES))
