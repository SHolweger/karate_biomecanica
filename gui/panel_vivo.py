"""
Lógica de presentación del análisis en vivo, sin interfaz gráfica.

Vive separada de `live_screen.py` por la misma razón que `validacion_umbrales.py`
y `fuentes.py`: decidir qué correcciones mostrar y cómo redactar una medición son
reglas, no dibujo, y como reglas se pueden verificar en la integración continua,
donde no hay cámara ni entorno gráfico. Este módulo no importa CustomTkinter ni
OpenCV a propósito.

Lo que consume son los diccionarios de diagnóstico que emite `TechniqueAnalyzer`
— las mismas estructuras que el renderizador dibuja sobre el video.
"""

# Articulaciones que el sistema mide hoy, con el nombre que el sensei usa y el
# orden en que se leen. La clave es la `categoria` que trae cada diagnóstico.
#
# No están aquí la rotación de cadera, la velocidad del puño ni el balance: el
# sistema todavía no las calcula. Mostrarlas vacías insinuaría que el dato existe
# y no llegó, cuando la verdad es que aún no se mide. Entran cuando se
# implementen (ver backlog del capítulo 4).
ARTICULACIONES = [
    ("codo_izq",    "Codo izquierdo"),
    ("codo_der",    "Codo derecho"),
    ("rodilla_izq", "Rodilla izquierda"),
    ("rodilla_der", "Rodilla derecha"),
]

# Puntos donde irían los sensores inerciales (RF-02, RF-04). Se declaran para que
# la pantalla pueda mostrar el subsistema como pendiente en vez de omitirlo:
# omitirlo dejaría creer que el análisis ya los usa.
PUNTOS_IMU = [
    "Muñeca derecha",
    "Muñeca izquierda",
    "Tobillo derecho",
    "Tobillo izquierdo",
]

SIN_DATO = "—"

# Textos del selector de alumno de la pantalla en vivo cuando todavía no hay a
# quién medir.
ELIGE_ALUMNO = "Elige un alumno"
SIN_ALUMNOS = "Sin alumnos registrados"


def etiqueta_alumno(atleta, nombres):
    """
    Qué dice el selector de alumno según el estado de la medición.

    Antes, sin alumno elegido el desplegable mostraba el nombre del primero de
    la lista. Era engañoso: el sensei leía «Diego Morales» en el recuadro, creía
    que estaba midiendo a Diego y en realidad no había sesión abierta ni cámara
    encendida —solo el aviso de que faltaba elegir—. El desplegable debe pedir la
    elección, no fingir que ya se hizo.

    Elegir por él tampoco sirve: abriría una sesión a nombre de alguien que nadie
    seleccionó, y ese registro quedaría en el historial de ese alumno.
    """
    if atleta:
        return atleta["nombre"]
    return ELIGE_ALUMNO if nombres else SIN_ALUMNOS


def formatear_tiempo(timestamp_ms):
    """Milisegundos de sesión a `MM:SS`, como se leen en un cronómetro."""
    total_segundos = max(0, int(timestamp_ms)) // 1000
    return f"{total_segundos // 60:02d}:{total_segundos % 60:02d}"


def formatear_angulo(angulo):
    """
    Ángulo legible, o guion si la articulación no está visible.

    El guion no es un adorno: significa "no medido en este fotograma", que es
    distinto de cero grados — un cero sería una afirmación sobre la postura.
    """
    return SIN_DATO if angulo is None else f"{angulo:.0f}°"


def veredicto_legible(correcto):
    """
    Correcto / Incorrecto / guion.

    Reemplaza al puntaje numérico del prototipo. Un 0–100 exigiría una métrica
    de calidad continua que el sistema no calcula: las reglas emiten un veredicto
    binario contra un rango angular, y convertirlo en un número daría una
    precisión que el dato no tiene.
    """
    if correcto is None:
        return SIN_DATO
    return "Correcto" if correcto else "Incorrecto"


def metricas_articulares(diagnosticos):
    """
    Un renglón por articulación medible, en orden fijo.

    El orden es fijo —y no el de llegada— para que los valores no salten de
    posición entre fotogramas: un panel cuyas filas se reordenan solas es
    ilegible en movimiento.
    """
    por_categoria = {}
    for diagnostico in _aplanar(diagnosticos):
        categoria = diagnostico.get("categoria")
        if categoria is not None:
            por_categoria[categoria] = diagnostico

    filas = []
    for categoria, etiqueta in ARTICULACIONES:
        diagnostico = por_categoria.get(categoria, {})
        filas.append({
            "categoria": categoria,
            "etiqueta": etiqueta,
            "valor": formatear_angulo(diagnostico.get("angulo")),
            "correcto": diagnostico.get("correcto"),
        })
    return filas


class FeedCorrecciones:
    """
    Las últimas correcciones del sistema experto, en orden inverso.

    Es la retroalimentación que justifica el sistema: un porcentaje al final de
    la sesión no enseña nada, pero "rota más la cadera" en el momento sí. El
    análisis corre a ~30 fotogramas por segundo y el mismo diagnóstico se repite
    en decenas seguidos, así que el filtro central es no volver a anotar una
    corrección que ya está vigente: sin él la lista se llenaría de la misma línea
    y empujaría fuera de pantalla lo que cambió.

    Una corrección repetida SÍ vuelve a entrar si en medio hubo otra distinta —
    ahí el alumno recayó, y esa recaída es información.
    """

    def __init__(self, maximo=8):
        self.maximo = maximo
        self.entradas = []
        self._vigente_por_categoria = {}

    def registrar(self, diagnosticos, timestamp_ms):
        """
        Incorpora los diagnósticos de un fotograma. Devuelve cuántos se anotaron.
        """
        anotadas = 0
        for diagnostico in _aplanar(diagnosticos):
            if not self._es_anotable(diagnostico):
                continue
            categoria = diagnostico.get("categoria")
            mensaje = diagnostico["mensaje"]
            if self._vigente_por_categoria.get(categoria) == mensaje:
                continue

            self._vigente_por_categoria[categoria] = mensaje
            self.entradas.insert(0, {
                "tiempo": formatear_tiempo(timestamp_ms),
                "mensaje": mensaje,
                "correcto": diagnostico.get("correcto"),
                "categoria": categoria,
            })
            anotadas += 1

        del self.entradas[self.maximo:]
        return anotadas

    @staticmethod
    def _es_anotable(diagnostico):
        """
        Solo entran los veredictos cerrados y con texto.

        Un `correcto` nulo es un estado transitorio ("EN TRANSICION") o una
        articulación fuera de cuadro; anotarlo llenaría la lista de ruido de
        movimiento en vez de correcciones técnicas — el mismo criterio con el que
        la base de datos decide qué cuenta para la precisión.
        """
        return bool(diagnostico.get("mensaje")) and diagnostico.get("correcto") is not None


def _aplanar(diagnosticos):
    """
    Acepta un diagnóstico suelto o listas anidadas.

    `analyze_tsuki` devuelve una lista (un brazo cada uno) y `analyze_stance` un
    diccionario; quien llama no debería tener que recordar cuál es cuál.
    """
    if diagnosticos is None:
        return []
    if isinstance(diagnosticos, dict):
        return [diagnosticos]

    planos = []
    for elemento in diagnosticos:
        planos.extend(_aplanar(elemento))
    return planos
