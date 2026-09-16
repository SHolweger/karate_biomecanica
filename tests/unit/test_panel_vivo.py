"""
Pruebas de la lógica de presentación del análisis en vivo (RF-06).

El requisito pide retroalimentación visual durante la ejecución. Lo que se
verifica aquí es la parte de ese requisito que se puede comprobar sin cámara ni
pantalla: qué se muestra, en qué orden, y sobre todo qué NO se muestra — porque
un panel que repite la misma corrección treinta veces por segundo, o que escribe
0° donde no midió nada, cumple el requisito de forma y lo incumple de fondo.
"""
import pytest

from gui.panel_vivo import (ARTICULACIONES, ELIGE_ALUMNO, FeedCorrecciones, PUNTOS_IMU,
                            SIN_ALUMNOS, SIN_DATO, etiqueta_alumno, formatear_angulo,
                            formatear_tiempo, metricas_articulares, veredicto_legible)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


def diagnostico(categoria, angulo=170.0, mensaje="IZQ - TSUKI: EXCELENTE", correcto=True):
    """Un diagnóstico con la forma que emite TechniqueAnalyzer."""
    return {"angulo": angulo, "mensaje": mensaje, "correcto": correcto,
            "categoria": categoria, "color": (0, 255, 0), "y_offset": 50}


# ---------------- formato ----------------

@pytest.mark.parametrize("milisegundos, esperado", [
    (0, "00:00"),
    (999, "00:00"),
    (1000, "00:01"),
    (24_000, "00:24"),
    (59_999, "00:59"),
    (60_000, "01:00"),
    (605_000, "10:05"),
    (-500, "00:00"),
])
def test_el_tiempo_se_lee_como_un_cronometro(milisegundos, esperado):
    assert formatear_tiempo(milisegundos) == esperado


@pytest.mark.parametrize("angulo, esperado", [
    (170.0, "170°"),
    (170.4, "170°"),
    (169.6, "170°"),
    (0.0, "0°"),
])
def test_el_angulo_se_redondea_a_grados_enteros(angulo, esperado):
    """Las décimas de grado no le dicen nada al sensei y hacen saltar el número."""
    assert formatear_angulo(angulo) == esperado


def test_una_articulacion_no_visible_se_marca_con_guion_y_no_con_cero():
    """
    Cero grados es una afirmación sobre la postura —el brazo completamente
    plegado—; "no visible" es la ausencia de una medición. Escribir 0° donde no
    se midió le diría al instructor que el alumno hizo algo que nunca hizo.
    """
    assert formatear_angulo(None) == SIN_DATO


@pytest.mark.parametrize("correcto, esperado", [
    (True, "Correcto"),
    (False, "Incorrecto"),
    (None, SIN_DATO),
])
def test_el_veredicto_es_binario_y_no_un_puntaje(correcto, esperado):
    """
    Sustituye al puntaje 0–100 del prototipo. Las reglas evalúan contra un rango
    angular y devuelven un veredicto; convertirlo en un número sugeriría una
    métrica de calidad continua que el sistema no calcula.
    """
    assert veredicto_legible(correcto) == esperado


# ---------------- métricas articulares ----------------

def test_las_articulaciones_se_muestran_siempre_en_el_mismo_orden():
    """
    Un panel cuyas filas se reordenan según qué se detectó primero es ilegible
    en movimiento: el sensei busca la rodilla derecha y la encuentra en otro
    sitio cada fotograma.
    """
    desordenados = [diagnostico("rodilla_der"), diagnostico("codo_izq")]

    filas = metricas_articulares(desordenados)

    assert [f["categoria"] for f in filas] == [c for c, _ in ARTICULACIONES]


def test_una_articulacion_sin_diagnostico_aparece_vacia_y_no_desaparece():
    filas = metricas_articulares([diagnostico("codo_izq", angulo=165.0)])

    por_categoria = {f["categoria"]: f for f in filas}
    assert por_categoria["codo_izq"]["valor"] == "165°"
    assert por_categoria["rodilla_der"]["valor"] == SIN_DATO
    assert por_categoria["rodilla_der"]["correcto"] is None


def test_acepta_listas_anidadas_como_las_que_devuelve_el_analizador():
    """
    `analyze_tsuki` devuelve una lista (un brazo cada uno) y `analyze_stance` un
    diccionario. Quien llama no debería tener que recordar cuál es cuál.
    """
    filas = metricas_articulares([
        [diagnostico("codo_izq", angulo=170.0), diagnostico("codo_der", angulo=90.0)],
        diagnostico("rodilla_izq", angulo=140.0),
    ])

    valores = {f["categoria"]: f["valor"] for f in filas}
    assert valores == {"codo_izq": "170°", "codo_der": "90°",
                       "rodilla_izq": "140°", "rodilla_der": SIN_DATO}


def test_sin_ningun_diagnostico_la_tabla_existe_pero_viene_vacia():
    filas = metricas_articulares([])

    assert len(filas) == len(ARTICULACIONES)
    assert all(f["valor"] == SIN_DATO for f in filas)


# ---------------- feed de correcciones ----------------

@ficha(
    id_caso="TC-AUTO-030",
    nombre="El panel de correcciones no repite una corrección que sigue vigente, de modo que "
           "la retroalimentación en pantalla conserve solo lo que cambió",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="el análisis corre a unos 30 fotogramas por segundo y el mismo "
                         "diagnóstico se repite en decenas consecutivos; sin el filtro, un solo "
                         "error sostenido durante un segundo llena la lista con treinta copias "
                         "idénticas y empuja fuera de pantalla las demás correcciones, "
                         "incumpliendo de fondo el RF-06 aunque el panel se dibuje",
    componente="gui/panel_vivo.py (FeedCorrecciones)",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Feed recién creado, sin correcciones previas",
    datos_entrada="Treinta fotogramas con el mismo diagnóstico incorrecto de codo; luego un "
                  "diagnóstico distinto; luego el primero otra vez",
    pasos=[
        Paso("Registrar el mismo diagnóstico incorrecto en 30 fotogramas seguidos",
             "assert len(feed.entradas) == 1"),
        Paso("Registrar un diagnóstico distinto de la misma articulación",
             "assert len(feed.entradas) == 2 y el más reciente queda primero"),
        Paso("Volver a registrar el diagnóstico original",
             "assert len(feed.entradas) == 3 (la recaída sí es información nueva)"),
        Paso("Registrar 20 correcciones distintas con un tope de 8",
             "assert len(feed.entradas) == 8 y conserva las más recientes"),
    ],
    resultado_esperado="PASSED. El panel muestra la secuencia de correcciones reales del alumno "
                       "y no la frecuencia de muestreo de la cámara.",
    evidencia="Reporte de consola de pytest.",
)
def test_una_correccion_vigente_no_se_vuelve_a_anotar():
    feed = FeedCorrecciones()
    hiperextendido = diagnostico("codo_der", angulo=178.0,
                                 mensaje="DER - TSUKI: HIPEREXTENDIDO (Peligro)", correcto=False)

    for fotograma in range(30):
        feed.registrar(hiperextendido, fotograma * 33)

    assert len(feed.entradas) == 1, "treinta fotogramas del mismo error son un solo aviso"
    assert feed.entradas[0]["tiempo"] == "00:00"

    flexionado = diagnostico("codo_der", angulo=120.0,
                             mensaje="DER - TSUKI: FLEXIONADO", correcto=False)
    feed.registrar(flexionado, 2_000)
    assert len(feed.entradas) == 2
    assert feed.entradas[0]["mensaje"] == "DER - TSUKI: FLEXIONADO", "lo nuevo va primero"

    feed.registrar(hiperextendido, 5_000)
    assert len(feed.entradas) == 3, "recaer en el error anterior sí es información nueva"
    assert feed.entradas[0]["tiempo"] == "00:05"


def test_dos_articulaciones_se_siguen_por_separado():
    """
    Un codo mal y una rodilla mal son dos correcciones, no una. Si el filtro
    fuera global, la segunda quedaría silenciada por la primera.
    """
    feed = FeedCorrecciones()

    feed.registrar([diagnostico("codo_izq", mensaje="IZQ - TSUKI: FLEXIONADO", correcto=False),
                    diagnostico("rodilla_izq", mensaje="POSTURA: CORREGIR ALTURA",
                                correcto=False)], 1_000)

    assert len(feed.entradas) == 2


def test_los_estados_transitorios_no_ensucian_la_lista():
    """
    Mismo criterio que usa la base de datos para la precisión: moverse frente a
    la cámara no es una corrección técnica.
    """
    feed = FeedCorrecciones()

    feed.registrar({"mensaje": "EN TRANSICION...", "correcto": None,
                    "categoria": "postura", "angulo": None}, 500)
    feed.registrar({"mensaje": "", "correcto": True, "categoria": "codo_izq", "angulo": 170.0}, 600)

    assert feed.entradas == []


def test_la_lista_conserva_solo_las_mas_recientes():
    feed = FeedCorrecciones(maximo=8)

    for i in range(20):
        feed.registrar(diagnostico("codo_der", mensaje=f"CORRECCION {i}", correcto=False),
                       i * 1_000)

    assert len(feed.entradas) == 8
    assert feed.entradas[0]["mensaje"] == "CORRECCION 19"
    assert feed.entradas[-1]["mensaje"] == "CORRECCION 12"


def test_registrar_informa_cuantas_correcciones_anoto():
    feed = FeedCorrecciones()

    assert feed.registrar([diagnostico("codo_izq", mensaje="A", correcto=False),
                           diagnostico("codo_der", mensaje="B", correcto=False)], 0) == 2
    assert feed.registrar(diagnostico("codo_izq", mensaje="A", correcto=False), 100) == 0


def test_un_fotograma_sin_persona_no_rompe_el_feed():
    feed = FeedCorrecciones()

    assert feed.registrar(None, 0) == 0
    assert feed.registrar([], 0) == 0
    assert feed.entradas == []


# ---------------- subsistema inercial ----------------

def test_los_puntos_imu_estan_declarados_aunque_no_haya_hardware():
    """
    El sistema declara el subsistema inercial como pendiente en vez de omitirlo.
    Omitirlo dejaría creer que el análisis ya lo usa; declararlo vacío dice la
    verdad: los puntos están definidos y el hardware todavía no.
    """
    assert len(PUNTOS_IMU) == 4
    assert all(isinstance(punto, str) and punto for punto in PUNTOS_IMU)


# ---------------- selector de alumno ----------------

def test_sin_alumno_elegido_el_selector_pide_elegir():
    """
    Mostrar el nombre del primero de la lista hacía creer que ya se estaba
    midiendo a esa persona, cuando no había sesión abierta ni cámara encendida.
    """
    assert etiqueta_alumno(None, ["Diego Morales", "Ana Lucía Pérez"]) == ELIGE_ALUMNO


def test_con_alumno_elegido_el_selector_lo_nombra():
    assert etiqueta_alumno({"nombre": "Diego Morales"}, ["Diego Morales"]) == "Diego Morales"


def test_sin_alumnos_inscritos_el_selector_lo_declara():
    """
    Un desplegable en blanco parecería un fallo de carga. Decir que no hay
    alumnos inscritos señala qué falta hacer: inscribir a alguien.
    """
    assert etiqueta_alumno(None, []) == SIN_ALUMNOS


def test_el_texto_del_selector_no_se_confunde_con_el_nombre_de_un_alumno():
    """
    Los dos avisos deben distinguirse de cualquier nombre propio: si alguno
    coincidiera con una opción real del desplegable, elegirlo abriría una sesión.
    """
    assert ELIGE_ALUMNO != SIN_ALUMNOS
    assert etiqueta_alumno(None, [ELIGE_ALUMNO]) == ELIGE_ALUMNO
