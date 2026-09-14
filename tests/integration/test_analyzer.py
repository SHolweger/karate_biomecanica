"""
Pruebas de integración de expert_system/analyzer.py (TechniqueAnalyzer).

El analizador es la costura del sistema: recibe landmarks de MediaPipe,
los convierte a píxeles, calcula ángulos, los suaviza, decide QUÉ postura
está viendo y consulta la regla correspondiente. Se ejercita con poses
sintéticas (helpers/fakes.py) que reproducen ángulos articulares exactos,
sin cámara ni modelo de visión cargado.
"""
import pytest

from expert_system.analyzer import TechniqueAnalyzer
from helpers.fakes import pose_sintetica
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion

ANCHO, ALTO = 1000, 1000
NARANJA = (0, 165, 255)


@pytest.fixture
def analizador():
    """Ventana de filtro 1: un solo frame basta para obtener el diagnóstico, sin retardo."""
    return TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)


def _por_categoria(resultados, categoria):
    return next(r for r in resultados if r["categoria"] == categoria)


# --------------------------------------------------------------------------
# Tsuki — análisis de ambos brazos
# --------------------------------------------------------------------------

def test_evalua_los_dos_brazos_de_forma_independiente(analizador):
    """
    El karateka golpea con el brazo derecho mientras el izquierdo se mantiene
    en hikite (retraído). El sistema debe premiar uno y corregir el otro en el
    mismo frame, no promediarlos.
    """
    landmarks = pose_sintetica(angulo_codo_izq=90, angulo_codo_der=170)

    resultados = analizador.analyze_tsuki(landmarks, ANCHO, ALTO)

    izquierdo = _por_categoria(resultados, "codo_izq")
    derecho = _por_categoria(resultados, "codo_der")
    assert izquierdo["correcto"] is False and "FLEXIONADO" in izquierdo["mensaje"]
    assert derecho["correcto"] is True and "EXCELENTE" in derecho["mensaje"]


def test_el_angulo_medido_coincide_con_la_pose_ejecutada(analizador):
    """Precisión de extremo a extremo: landmarks -> píxeles -> ángulo, con 1 grado de tolerancia."""
    landmarks = pose_sintetica(angulo_codo_izq=132)

    resultados = analizador.analyze_tsuki(landmarks, ANCHO, ALTO)

    assert _por_categoria(resultados, "codo_izq")["angulo"] == pytest.approx(132, abs=1.0)


def test_brazo_no_visible_se_informa_en_vez_de_inventar_diagnostico(analizador):
    """
    Con visibilidad por debajo del umbral el sistema NO debe calificar: avisa
    que no puede ver el brazo. Un diagnóstico inventado sobre datos poco
    confiables es peor que no dar diagnóstico.
    """
    landmarks = pose_sintetica(angulo_codo_izq=170, visibilidad_brazos=0.3)

    resultados = analizador.analyze_tsuki(landmarks, ANCHO, ALTO)

    for categoria in ("codo_izq", "codo_der"):
        diagnostico = _por_categoria(resultados, categoria)
        assert diagnostico["correcto"] is None
        assert "OCULTO" in diagnostico["mensaje"]
        assert diagnostico["angulo"] is None
        assert diagnostico["color"] == NARANJA


def test_el_filtro_se_reinicia_cuando_el_brazo_desaparece(analizador):
    """
    Regresión del anti-jitter: al ocultarse una articulación su historial debe
    vaciarse, para que al reaparecer el primer ángulo no se promedie con la
    postura anterior.
    """
    suavizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=5)
    for _ in range(5):
        suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=40), ANCHO, ALTO)

    suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=40, visibilidad_brazos=0.2), ANCHO, ALTO)
    resultados = suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=170), ANCHO, ALTO)

    assert _por_categoria(resultados, "codo_izq")["angulo"] == pytest.approx(170, abs=1.0), \
        "el angulo tras reaparecer no debe arrastrar el promedio de la postura previa"


def test_el_suavizado_amortigua_un_salto_de_jitter(analizador):
    """
    Con ventana 5, un frame atípico (ruido de MediaPipe) no debe arrastrar el
    diagnóstico: el ángulo reportado se mantiene cerca de la postura sostenida.
    """
    suavizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=5)
    for _ in range(5):
        suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=170), ANCHO, ALTO)

    resultados = suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=100), ANCHO, ALTO)

    angulo = _por_categoria(resultados, "codo_izq")["angulo"]
    assert 150 < angulo < 170, f"un solo frame ruidoso movio el diagnostico a {angulo}"


# --------------------------------------------------------------------------
# Clasificador de posturas
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-006",
    nombre="El analizador identifica la postura ejecutada antes de evaluarla, a partir "
           "de los ángulos de ambas rodillas",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="si clasifica mal la postura, aplica la regla equivocada y todo "
                         "el diagnóstico es inválido",
    componente="expert_system/analyzer.py (TechniqueAnalyzer)",
    requisitos=["RF-01", "RF-05"],
    precondiciones="Instancia de `TechniqueAnalyzer(umbral_visibilidad=0.65, "
                   "ventana_filtro=1)`; pose sintética de 33 landmarks con visibilidad 1.0",
    datos_entrada="(izq=175, der=175) → Postura natural; (140, 140) → Kiba Dachi; "
                  "(100, 170) → Zenkutsu (peso adelante); (165, 105) → Kokutsu (peso "
                  "atrás). Profundidad z_tobillo_izq=−0.2, z_tobillo_der=0.2",
    pasos=[
        Paso("Generar la pose sintética con `pose_sintetica(...)`",
             "33 landmarks con los ángulos de rodilla solicitados (±0.1°)"),
        Paso("Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)`",
             "Lista de diagnósticos con la categoría `postura`"),
        Paso("Extraer el diagnóstico de la categoría `postura`",
             "El diccionario contiene la clave `mensaje`"),
        Paso("Validar la postura detectada",
             "assert \"KIBA DACHI\" in mensaje (y análogos por cada postura)"),
    ],
    resultado_esperado="PASSED en las cuatro posturas parametrizadas",
)
@pytest.mark.parametrize("nombre, izq, der, postura_esperada", [
    ("posicion natural",   175, 175, "POSTURA NATURAL"),
    ("postura de jinete",  140, 140, "KIBA DACHI"),
    ("postura adelantada", 100, 170, "ZENKUTSU"),
    ("postura atrasada",   165, 105, "KOKUTSU"),
])
def test_identifica_la_postura_antes_de_evaluarla(analizador, nombre, izq, der, postura_esperada):
    """
    El sistema no le pregunta al usuario qué postura hace: la deduce de los dos
    ángulos de rodilla y recién entonces aplica la regla que corresponde.
    """
    landmarks = pose_sintetica(angulo_rodilla_izq=izq, angulo_rodilla_der=der,
                               z_tobillo_izq=-0.2, z_tobillo_der=0.2)

    resultados = analizador.analyze_stance(landmarks, ANCHO, ALTO)

    assert postura_esperada in _por_categoria(resultados, "postura")["mensaje"], nombre


def test_la_guardia_se_deduce_de_la_profundidad_de_los_tobillos(analizador):
    """
    En Zenkutsu importa cuál pierna va adelante: se decide con el eje Z de
    MediaPipe (menor Z = más cerca de la cámara).
    """
    izq_adelante = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=170,
                                  z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    der_adelante = pose_sintetica(angulo_rodilla_izq=170, angulo_rodilla_der=100,
                                  z_tobillo_izq=0.3, z_tobillo_der=-0.3)

    mensaje_izq = _por_categoria(analizador.analyze_stance(izq_adelante, ANCHO, ALTO), "postura")["mensaje"]
    analizador.filtros["guardia_z"].reset()
    mensaje_der = _por_categoria(analizador.analyze_stance(der_adelante, ANCHO, ALTO), "postura")["mensaje"]

    assert "IZQ ADELANTE" in mensaje_izq
    assert "DER ADELANTE" in mensaje_der


def test_una_transicion_no_se_califica_como_error(analizador):
    """
    Mientras el atleta se desplaza entre posturas no hay nada que calificar:
    el sistema lo marca como transición con correcto=None, para que no
    contamine el porcentaje de aciertos de su historial.
    """
    landmarks = pose_sintetica(angulo_rodilla_izq=135, angulo_rodilla_der=170,
                               z_tobillo_izq=-0.1, z_tobillo_der=0.1)

    diagnostico = _por_categoria(analizador.analyze_stance(landmarks, ANCHO, ALTO), "postura")

    assert diagnostico["correcto"] is None
    assert "TRANSICION" in diagnostico["mensaje"]
    assert diagnostico["color"] == NARANJA


def test_kiba_dachi_mal_ejecutado_se_detecta_pero_se_corrige(analizador):
    """
    Se reconoce la intención (postura de jinete) aunque la altura esté mal:
    detectar la postura y evaluarla son decisiones separadas.
    """
    landmarks = pose_sintetica(angulo_rodilla_izq=158, angulo_rodilla_der=158)

    diagnostico = _por_categoria(analizador.analyze_stance(landmarks, ANCHO, ALTO), "postura")

    assert "KIBA DACHI" in diagnostico["mensaje"]
    assert diagnostico["correcto"] is False
    assert "CORREGIR ALTURA" in diagnostico["mensaje"]


def test_piernas_no_visibles_se_informan_sin_calificar(analizador):
    landmarks = pose_sintetica(visibilidad_piernas=0.4)

    diagnostico = _por_categoria(analizador.analyze_stance(landmarks, ANCHO, ALTO), "postura")

    assert diagnostico["correcto"] is None
    assert "OCULTAS" in diagnostico["mensaje"]


# --------------------------------------------------------------------------
# Mae Geri a través del analizador (integración analyzer + FSM)
# --------------------------------------------------------------------------

def test_una_patada_completa_atraviesa_el_analizador(analizador):
    """
    Prueba de integración larga: la misma patada que verifica la máquina de
    estados, pero entrando como landmarks. Confirma que el analizador extrae
    bien el ángulo de rodilla y la altura del tobillo que la FSM necesita.
    """
    def frame(angulo_rodilla, y_tobillo):
        """Un cuadro de video: ángulo de rodilla y altura del pie de la pierna que patea."""
        return pose_sintetica(angulo_rodilla_izq=angulo_rodilla, y_tobillo_izq=y_tobillo)

    analizador.analyze_mae_geri(frame(175, 0.90), ANCHO, ALTO, timestamp_ms=0)
    analizador.analyze_mae_geri(frame(50, 0.90), ANCHO, ALTO, timestamp_ms=33)
    analizador.analyze_mae_geri(frame(170, 0.50), ANCHO, ALTO, timestamp_ms=66)
    resultados = analizador.analyze_mae_geri(frame(50, 0.50), ANCHO, ALTO, timestamp_ms=100)

    patada = _por_categoria(resultados, "mae_geri_izq")
    assert patada["correcto"] is True
    assert "KIME EXCELENTE" in patada["mensaje"]
    assert patada["mensaje"].startswith("IZQ")


def test_cada_pierna_tiene_su_propia_maquina_de_estados(analizador):
    """
    Cualquiera de las dos piernas puede patear: el estado de una no debe
    contaminar el de la otra.
    """
    assert analizador.maquinas_patada["izq"] is not analizador.maquinas_patada["der"]

    landmarks = pose_sintetica(angulo_rodilla_izq=50, angulo_rodilla_der=175)
    analizador.analyze_mae_geri(pose_sintetica(angulo_rodilla_izq=175, angulo_rodilla_der=175),
                                ANCHO, ALTO, timestamp_ms=0)
    analizador.analyze_mae_geri(landmarks, ANCHO, ALTO, timestamp_ms=33)

    assert analizador.maquinas_patada["izq"].estado == "CARGA"
    assert analizador.maquinas_patada["der"].estado == "REPOSO"


# --------------------------------------------------------------------------
# Contrato de salida hacia el renderer y la base de datos
# --------------------------------------------------------------------------

@pytest.mark.parametrize("metodo", ["analyze_tsuki", "analyze_stance"])
def test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual(analizador, metodo):
    """
    SkeletonRenderer accede a mensaje/color/y_offset/angulo y MedicionLogger a
    categoria/correcto sin verificar existencia: si falta una clave, la
    aplicación falla en pleno entrenamiento.
    """
    landmarks = pose_sintetica(angulo_codo_izq=170, angulo_rodilla_izq=100, angulo_rodilla_der=170)

    for diagnostico in getattr(analizador, metodo)(landmarks, ANCHO, ALTO):
        assert set(diagnostico) >= {"angulo", "pos_angulo", "mensaje", "color", "y_offset",
                                    "categoria", "correcto"}, f"claves faltantes: {diagnostico}"
        assert isinstance(diagnostico["y_offset"], int)
        assert len(diagnostico["color"]) == 3
        assert diagnostico["correcto"] in (True, False, None)


def test_las_lineas_de_texto_no_se_encimam_en_pantalla(analizador):
    """
    Requisito de usabilidad: cada categoría se dibuja en una altura distinta.
    Dos diagnósticos con el mismo y_offset se superpondrían e impedirían al
    sensei leer la corrección.
    """
    landmarks = pose_sintetica(angulo_codo_izq=170, angulo_codo_der=100)

    alturas = [d["y_offset"] for d in analizador.analyze_tsuki(landmarks, ANCHO, ALTO)]

    assert len(set(alturas)) == len(alturas), f"diagnosticos superpuestos en {alturas}"


@ficha(
    id_caso="TC-AUTO-025",
    nombre="Un Kokutsu Dachi correctamente ejecutado se reconoce como tal y no como una "
           "transición entre posturas",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es una prueba de regresión de un defecto real: el clasificador "
                         "exigía la rodilla frontal flexionada para reconocer un Kokutsu, "
                         "cuando en esa postura el peso va atrás y la frontal queda casi "
                         "extendida. Toda ejecución correcta caía en la rama por defecto y se "
                         "reportaba como \"EN TRANSICION\", de modo que una de las posturas "
                         "del alcance no se evaluaba nunca y nada lo delataba",
    componente="expert_system/analyzer.py (clasificador de posturas)",
    requisitos=["RF-01", "RF-05"],
    precondiciones="Instancia de `TechniqueAnalyzer(ventana_filtro=1)`; poses sintéticas de "
                   "33 landmarks con visibilidad 1.0",
    datos_entrada="Cinco ejecuciones con la pierna frontal extendida y la trasera flexionada: "
                  "(170, 100), (165, 105), (160, 110), (155, 115) y (150, 120)",
    pasos=[
        Paso("Generar la pose sintética con la pierna izquierda adelante "
             "(z_tobillo_izq < z_tobillo_der)",
             "33 landmarks con los ángulos de rodilla solicitados"),
        Paso("Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)`",
             "assert \"KOKUTSU\" in mensaje en las cinco ejecuciones"),
        Paso("Comprobar que no se reportó como movimiento",
             "assert \"TRANSICION\" not in mensaje y assert \"MOVIENDOSE\" not in mensaje"),
    ],
    resultado_esperado="PASSED. Con el clasificador anterior las cinco ejecuciones fallaban, "
                       "por lo que esta prueba impide que la corrección se revierta",
)
@pytest.mark.parametrize("frontal, trasera", [
    (170, 100),
    (165, 105),
    (160, 110),
    (155, 115),
    (150, 120),
])
@pytest.mark.integracion
def test_un_kokutsu_real_no_se_confunde_con_una_transicion(analizador, frontal, trasera):
    """
    Prueba de regresión del defecto corregido el 14-sep-2026.

    En el Kokutsu Dachi el 70 % del peso descansa sobre la pierna trasera: esa
    rodilla se flexiona profundamente y la delantera permanece casi extendida.
    El clasificador anterior pedía justo lo contrario, de modo que ninguna de
    estas cinco ejecuciones —todas Kokutsu válidos— coincidía con alguna rama.
    """
    landmarks = pose_sintetica(angulo_rodilla_izq=frontal, angulo_rodilla_der=trasera,
                               z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    diagnostico = [d for d in analizador.analyze_stance(landmarks, ANCHO, ALTO)
                   if d["categoria"] == "postura"][0]
    mensaje = diagnostico["mensaje"]

    assert "KOKUTSU" in mensaje, f"frontal={frontal}, trasera={trasera} -> {mensaje}"
    assert "TRANSICION" not in mensaje and "MOVIENDOSE" not in mensaje, mensaje


@pytest.mark.integracion
def test_zenkutsu_y_kokutsu_no_se_confunden_entre_si(analizador):
    """
    Las dos posturas se distinguen por dónde va el peso, no por cuánto se
    flexiona: son imágenes espejo una de la otra en los ángulos de rodilla.
    """
    adelante = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=170,
                              z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    atras = pose_sintetica(angulo_rodilla_izq=165, angulo_rodilla_der=105,
                           z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    def postura(landmarks):
        return [d for d in analizador.analyze_stance(landmarks, ANCHO, ALTO)
                if d["categoria"] == "postura"][0]["mensaje"]

    assert "ZENKUTSU" in postura(adelante)
    assert "KOKUTSU" in postura(atras)
