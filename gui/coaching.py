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
    # Desde el 18-oct-2026 solo lo emite Kiba Dachi, que es simétrica: no hay
    # guardia que nombrar, así que el motivo ya no habla de ella.
    "POSTURA: CORREGIR ALTURA":
        ("Corrige la altura de la postura",
         "en el Kiba Dachi las dos rodillas se flexionan por igual, a media altura"),

    # Posturas asimétricas: el veredicto nombra la rodilla y el sentido. El
    # motivo es el mismo para Zenkutsu y Kokutsu —la tabla se indexa por
    # veredicto, no por técnica—, así que dice lo que vale para las dos.
    "POSTURA: FLEXIONA MAS LA RODILLA DELANTERA":
        ("Flexiona más la rodilla de adelante",
         "con la rodilla delantera tan recta la postura queda alta y rígida"),
    "POSTURA: EXTIENDE LA RODILLA DELANTERA":
        ("Abre un poco la rodilla de adelante",
         "está más doblada de lo que pide la postura y carga la articulación"),
    "POSTURA: FLEXIONA MAS LA RODILLA TRASERA":
        ("Flexiona más la rodilla de atrás",
         "en el Kokutsu el peso descansa sobre la pierna trasera"),
    "POSTURA: EXTIENDE LA RODILLA TRASERA":
        ("Estira la pierna de atrás",
         "la rodilla trasera está más doblada de lo que pide la postura"),
    "POSTURA: CORREGIR AMBAS RODILLAS":
        ("Corrige las dos rodillas",
         "ninguna de las dos está en su rango: empieza por la que sostiene el peso"),

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


def veredicto_conocido(mensaje):
    """
    El veredicto de la tabla que contiene el mensaje, o None si no hay ninguno.

    El analizador no entrega el veredicto pelado: a las posturas les antepone la
    que reconoció —«ZENKUTSU (IZQ ADELANTE): POSTURA: FIRME»,
    «POSTURA NATURAL: HEIKO DACHI: CORRECTO»—. Se prueba el mensaje entero y
    luego lo que queda tras cada «: », del más largo al más corto, de modo que
    gana la entrada más específica de la tabla.

    Hasta el 18-oct-2026 solo se buscaba el mensaje entero, así que **ninguna
    postura llegaba traducida al panel**: el sensei leía el texto técnico en
    Heiko, Kiba, Zenkutsu y Kokutsu, y solo el Tsuki —cuyo prefijo es el de
    lado— se traducía. La guarda de la tabla pasaba igual, porque comprobaba la
    tabla y no el mensaje que la pantalla recibe. Lo fija TC-AUTO-066.
    """
    resto = mensaje
    while True:
        if resto in CORRECCIONES:
            return resto
        if ": " not in resto:
            return None
        resto = resto.split(": ", 1)[1]


def traducir(mensaje):
    """
    Corrección legible a partir de un veredicto del motor.

    Devuelve (instrucción, motivo). Un veredicto sin entrada en la tabla se
    devuelve tal cual y sin motivo: es preferible mostrar el texto técnico que
    inventar un consejo que la regla no respalda — si mañana se agrega una regla
    nueva, el panel seguirá siendo correcto aunque suene menos natural.
    """
    sin_lado, lado = separar_lado(mensaje or "")
    veredicto = veredicto_conocido(sin_lado)
    if veredicto is None:
        return sin_lado, None

    instruccion, motivo = CORRECCIONES[veredicto]
    if lado is not None:
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
    # Los que la base de conocimientos construye en un método y no en un
    # `return` literal —el veredicto por rodilla de Zenkutsu y Kokutsu— los
    # declara ella misma. Una prueba recorre la regla y comprueba que la
    # declaración está completa.
    emitidos.update(knowledge_base.VEREDICTOS_DECLARADOS)
    return sorted(emitidos - set(CORRECCIONES))
