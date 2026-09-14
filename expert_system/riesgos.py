"""
Señales de riesgo de lesión a partir de lo que el sistema efectivamente midió.

Es la parte del reporte que más fácil sería inventar, así que conviene dejar
claro de dónde sale cada afirmación. Este módulo NO estima cargas articulares ni
fuerzas: para eso harían falta los sensores inerciales (RF-02, RF-04), que
todavía no están montados. Lo que hace es leer los veredictos ya registrados y
señalar dos patrones que la literatura asocia con lesión y que la visión por
computadora sí puede sostener:

1. HIPEREXTENSIÓN ARTICULAR REPETIDA. Bloquear el codo al final del golpe
   transfiere el impacto al ligamento en lugar de a la musculatura. El sistema
   ya lo detecta como veredicto; aquí solo se cuenta con qué frecuencia ocurre,
   porque una vez es un desliz y veinte veces es un hábito.

2. ASIMETRÍA LATERAL SOSTENIDA. Una diferencia marcada entre el desempeño de un
   lado y el otro indica que el alumno compensa con el lado dominante. El
   promedio global la oculta: un 50 % parejo y un 80/20 dan el mismo número, y
   solo el segundo anticipa una lesión por sobreuso.

Deliberadamente NO se afirma nada sobre valgo de rodilla, velocidad de impacto
ni estabilidad de cadera. El valgo requiere que el alumno esté de frente a la
cámara y ese criterio todavía no está validado con el dojo; los otros dos
necesitan unidades reales que la cámara no entrega.

Como el resto de la lógica del sistema, no importa nada de la interfaz ni de la
base de datos: recibe cifras y devuelve hallazgos.
"""

# Diferencia en puntos porcentuales a partir de la cual la asimetría deja de ser
# variación normal. Por debajo de este valor, la diferencia entre lados cabe
# dentro de lo que varía una misma persona entre repeticiones.
UMBRAL_ASIMETRIA = 20.0

# Evaluaciones mínimas por lado para que la comparación signifique algo. Con
# tres repeticiones, un solo fallo mueve el porcentaje 33 puntos y cualquier
# diferencia parecería alarmante.
MINIMO_POR_LADO = 6

# Proporción de repeticiones hiperextendidas a partir de la cual se considera
# hábito y no desliz.
PROPORCION_HIPEREXTENSION = 0.10
MINIMO_HIPEREXTENSIONES = 2

# Fragmento del veredicto que emite la base de conocimientos para el bloqueo
# articular. Vive aquí, junto a la regla que lo interpreta.
VEREDICTO_HIPEREXTENSION = "HIPEREXTENDIDO"

# Niveles, del más urgente al informativo. Ordenan el bloque en pantalla.
RIESGO = "riesgo"
ATENCION = "atencion"
PREVENCION = "prevencion"
ORDEN_NIVELES = [RIESGO, ATENCION, PREVENCION]


def _hallazgo(nivel, titulo, detalle, recomendacion):
    return {"nivel": nivel, "titulo": titulo, "detalle": detalle,
            "recomendacion": recomendacion}


def evaluar_hiperextension(veces, total):
    """
    Señala el bloqueo articular repetido al final del golpe.

    Una sola hiperextensión no se reporta: puede ser una repetición suelta mal
    ejecutada. Lo que interesa es el patrón.
    """
    if total == 0 or veces < MINIMO_HIPEREXTENSIONES:
        return None

    proporcion = veces / total
    if proporcion < PROPORCION_HIPEREXTENSION:
        return None

    nivel = RIESGO if proporcion >= 0.25 else ATENCION
    return _hallazgo(
        nivel,
        "Hiperextensión del codo al impacto",
        f"{veces} de {total} evaluaciones cerradas superaron el rango de extensión "
        f"({proporcion * 100:.0f} %). Bloquear la articulación transfiere el impacto al "
        f"ligamento en vez de a la musculatura.",
        "Trabajar el Tsuki a velocidad media frente al espejo, deteniendo la extensión "
        "justo antes del bloqueo, hasta que el tope sea muscular y no articular.")


def evaluar_asimetria(por_lado):
    """
    Compara el desempeño de un lado contra el otro.

    Solo se pronuncia cuando ambos lados tienen suficientes repeticiones: con
    pocas, un fallo aislado produce diferencias enormes que no significan nada.
    """
    izquierdo = por_lado.get("izquierdo") or {}
    derecho = por_lado.get("derecho") or {}

    if (izquierdo.get("evaluaciones", 0) < MINIMO_POR_LADO
            or derecho.get("evaluaciones", 0) < MINIMO_POR_LADO):
        return None
    if izquierdo.get("precision") is None or derecho.get("precision") is None:
        return None

    diferencia = abs(izquierdo["precision"] - derecho["precision"])
    if diferencia < UMBRAL_ASIMETRIA:
        return None

    flojo = "izquierdo" if izquierdo["precision"] < derecho["precision"] else "derecho"
    solido = "derecho" if flojo == "izquierdo" else "izquierdo"

    nivel = RIESGO if diferencia >= 2 * UMBRAL_ASIMETRIA else ATENCION
    return _hallazgo(
        nivel,
        f"Asimetría lateral: el lado {flojo} viene rezagado",
        f"{diferencia:.0f} puntos de diferencia entre lados "
        f"({izquierdo['precision']:.0f} % izquierdo contra {derecho['precision']:.0f} % "
        f"derecho). Una diferencia sostenida indica que el alumno compensa con el lado "
        f"{solido}, lo que sobrecarga ese lado con el tiempo.",
        f"Dedicar series adicionales al lado {flojo} y ejecutar las repeticiones alternando "
        f"lados, para que el {solido} no marque el ritmo de ambos.")


def sin_hallazgos():
    """Mensaje cuando la sesión no muestra ninguna señal de riesgo."""
    return _hallazgo(
        PREVENCION,
        "Sin señales de riesgo en esta sesión",
        "No se detectó hiperextensión repetida ni asimetría marcada entre lados.",
        "Mantener el trabajo actual. Las señales se recalculan en cada sesión.")


def analizar(hiperextension, por_lado):
    """
    Hallazgos de una sesión, del más urgente al informativo.

    `hiperextension` es {'veces', 'total'} y `por_lado` el resultado de
    `desempeno_por_lado`. Ambos vienen de la base; aquí solo se interpretan.

    Devuelve siempre al menos un elemento: una sesión sin señales de riesgo debe
    decirlo explícitamente. Un bloque vacío se leería como que el análisis no
    corrió, que es distinto de que no encontró nada.
    """
    hallazgos = [h for h in (evaluar_hiperextension(hiperextension.get("veces", 0),
                                                    hiperextension.get("total", 0)),
                             evaluar_asimetria(por_lado))
                 if h is not None]

    if not hallazgos:
        return [sin_hallazgos()]
    return sorted(hallazgos, key=lambda h: ORDEN_NIVELES.index(h["nivel"]))


def alcance():
    """
    Qué NO cubre este análisis, para que el reporte pueda declararlo.

    Una sección de prevención de lesiones que no dice dónde termina invita a
    leerla como si cubriera todo. Decir qué falta es parte de ser honesto sobre
    lo que el sistema mide hoy.
    """
    return ("Análisis basado en visión por computadora. No evalúa valgo de rodilla, "
            "velocidad de impacto ni estabilidad de cadera: esas señales requieren los "
            "sensores inerciales, todavía no integrados.")
