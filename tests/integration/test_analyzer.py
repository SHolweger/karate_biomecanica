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


def _tsuki_hasta(kime):
    """
    Los ángulos de codo de un Tsuki completo que cierra el Kime en `kime`.

    Desde el 30-sep-2026 hace falta ejecutar el golpe para obtener un veredicto:
    un fotograma suelto con el brazo extendido ya no basta, porque un brazo
    quieto no ejecuta ningún Tsuki (ver expert_system/tsuki.py). Sale del
    Hikite, extiende y empieza a recoger, que es cuando se cierra el Kime.
    """
    return [50, 50 + (kime - 50) * 0.25, 50 + (kime - 50) * 0.5,
            50 + (kime - 50) * 0.75, kime, kime - 20]


def _ejecutar_tsuki(analizador, izq, der, t0=0):
    """Pasa una secuencia de ángulos por brazo y devuelve el ÚLTIMO diagnóstico."""
    for fotograma, (angulo_izq, angulo_der) in enumerate(zip(izq, der)):
        resultados = analizador.analyze_tsuki(
            pose_sintetica(angulo_codo_izq=angulo_izq, angulo_codo_der=angulo_der),
            ANCHO, ALTO, t0 + fotograma * 33)
    return resultados


# --------------------------------------------------------------------------
# Tsuki — análisis de ambos brazos
# --------------------------------------------------------------------------

def test_evalua_los_dos_brazos_de_forma_independiente(analizador):
    """
    El karateka golpea con los dos brazos: el derecho llega y el izquierdo se
    queda corto. El sistema debe premiar uno y corregir el otro en el mismo
    frame, no promediarlos.

    Hasta el 30-sep-2026 esta prueba dejaba el brazo izquierdo quieto en hikite
    y esperaba que se calificara «FLEXIONADO». Ahí estaba escrito el defecto:
    un brazo retraído no ejecuta ningún golpe, así que ya no recibe veredicto
    —de eso se ocupa test_estar_de_pie_no_produce_veredicto_de_tsuki—. Lo que
    la prueba quería comprobar, que los dos brazos se juzgan por separado,
    sigue igual de vigente; lo que cambia es que ahora los dos golpean.
    """
    resultados = _ejecutar_tsuki(analizador, _tsuki_hasta(90), _tsuki_hasta(170))

    izquierdo = _por_categoria(resultados, "codo_izq")
    derecho = _por_categoria(resultados, "codo_der")
    assert izquierdo["correcto"] is False and "FLEXIONADO" in izquierdo["mensaje"]
    assert derecho["correcto"] is True and "EXCELENTE" in derecho["mensaje"]


def test_el_angulo_medido_coincide_con_la_pose_ejecutada(analizador):
    """Precisión de extremo a extremo: landmarks -> píxeles -> ángulo, con 1 grado de tolerancia."""
    landmarks = pose_sintetica(angulo_codo_izq=132)

    resultados = analizador.analyze_tsuki(landmarks, ANCHO, ALTO, 0)

    assert _por_categoria(resultados, "codo_izq")["angulo"] == pytest.approx(132, abs=1.0)


def test_brazo_no_visible_se_informa_en_vez_de_inventar_diagnostico(analizador):
    """
    Con visibilidad por debajo del umbral el sistema NO debe calificar: avisa
    que no puede ver el brazo. Un diagnóstico inventado sobre datos poco
    confiables es peor que no dar diagnóstico.
    """
    landmarks = pose_sintetica(angulo_codo_izq=170, visibilidad_brazos=0.3)

    resultados = analizador.analyze_tsuki(landmarks, ANCHO, ALTO, 0)

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
    for fotograma in range(5):
        suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=40), ANCHO, ALTO, fotograma * 33)

    suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=40, visibilidad_brazos=0.2), ANCHO, ALTO, 165)
    resultados = suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=170), ANCHO, ALTO, 198)

    assert _por_categoria(resultados, "codo_izq")["angulo"] == pytest.approx(170, abs=1.0), \
        "el angulo tras reaparecer no debe arrastrar el promedio de la postura previa"


def test_el_suavizado_amortigua_un_salto_de_jitter(analizador):
    """
    Con ventana 5, un frame atípico (ruido de MediaPipe) no debe arrastrar el
    diagnóstico: el ángulo reportado se mantiene cerca de la postura sostenida.
    """
    suavizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=5)
    for fotograma in range(5):
        suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=170), ANCHO, ALTO, fotograma * 33)

    resultados = suavizador.analyze_tsuki(pose_sintetica(angulo_codo_izq=100), ANCHO, ALTO, 165)

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
    analizador.filtros["guardia"].reset()
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

    argumentos = (landmarks, ANCHO, ALTO, 0) if metodo == "analyze_tsuki" \
        else (landmarks, ANCHO, ALTO)

    for diagnostico in getattr(analizador, metodo)(*argumentos):
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

    alturas = [d["y_offset"] for d in analizador.analyze_tsuki(landmarks, ANCHO, ALTO, 0)]

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


# ---------------------------------------------------------------------------
# Lo que la medición debe llevarse para poder volver a juzgarse (RF-08)
#
# Hasta esta versión el diagnóstico de piernas viajaba con un solo ángulo —el de
# la rodilla izquierda— y sin decir qué postura se había reconocido. Guardado
# así, un Kokutsu y un Zenkutsu quedaban indistinguibles en la base, y corregir
# un umbral no se podía aplicar a lo ya medido: faltaba la mitad del criterio.
# Estas pruebas fijan que el analizador emita los MISMOS argumentos con los que
# consultó la regla.
# ---------------------------------------------------------------------------

def test_la_postura_declara_con_que_tecnica_se_juzgo(analizador):
    """Sin la clave, la fila guardada no dice si fue Zenkutsu, Kokutsu o Kiba."""
    pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=170,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

    assert resultado["tecnica"] == "zenkutsu_dachi"


def test_la_postura_lleva_los_dos_angulos_con_que_la_regla_la_juzgo(analizador):
    """
    Kokutsu se juzga contra rodilla frontal Y trasera. La medición debe cargar
    ambos, en el mismo orden en que la regla los consume, o recalcular el
    veredicto con otro umbral sería imposible.
    """
    pose = pose_sintetica(angulo_rodilla_izq=160, angulo_rodilla_der=105,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

    assert resultado["tecnica"] == "kokutsu_dachi"
    frontal, trasera = resultado["angulos_regla"]
    assert frontal == pytest.approx(160, abs=1.5)
    assert trasera == pytest.approx(105, abs=1.5)


def test_los_angulos_de_la_regla_siguen_a_la_guardia_no_al_lado_de_la_pantalla(analizador):
    """
    Con la pierna DERECHA adelante, el primer argumento debe ser la rodilla
    derecha. Guardar siempre la izquierda —como se hacía— mezclaba la rodilla
    frontal de unas ejecuciones con la trasera de otras.
    """
    pose = pose_sintetica(angulo_rodilla_izq=105, angulo_rodilla_der=160,
                          z_tobillo_izq=0.3, z_tobillo_der=-0.3)
    resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

    assert resultado["tecnica"] == "kokutsu_dachi"
    frontal, _trasera = resultado["angulos_regla"]
    assert frontal == pytest.approx(160, abs=1.5), "la frontal es la derecha en esta guardia"


def test_una_transicion_no_declara_tecnica_ni_angulos_de_regla(analizador):
    """No se juzgó contra ningún umbral, así que no hay nada que re-juzgar."""
    pose = pose_sintetica(angulo_rodilla_izq=145, angulo_rodilla_der=175,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

    assert "TRANSICION" in resultado["mensaje"]
    assert resultado["tecnica"] is None
    assert resultado["angulos_regla"] is None


def test_un_tsuki_declara_su_tecnica_y_su_unico_angulo(analizador):
    """
    El ángulo declarado es el del Kime —el máximo que alcanzó la extensión— y
    no el del fotograma en que se emite el veredicto, que ya viene de vuelta.
    Es lo que permite volver a juzgar la medición si el umbral cambia (RF-08):
    guardar el de la recogida dejaría el historial imposible de re-evaluar.
    """
    resultado = _por_categoria(
        _ejecutar_tsuki(analizador, _tsuki_hasta(168), _tsuki_hasta(168)), "codo_izq")

    assert resultado["tecnica"] == "tsuki"
    assert resultado["angulos_regla"][0] == pytest.approx(168, abs=1.5)


# --------------------------------------------------------------------------
# La guardia: cuándo el sistema puede afirmar qué pierna va adelante
#
# Zenkutsu y Kokutsu son la misma postura con las piernas intercambiadas. Que
# el clasificador acierte una u otra depende ENTERAMENTE de la guardia, así
# que equivocarla no produce un "no reconocido" sino la otra postura con
# veredicto positivo. Ver expert_system/guardia.py.
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-051",
    nombre="Con los tobillos casi a la misma profundidad, el analizador no reporta "
           "Zenkutsu ni Kokutsu en lugar de elegir uno de los dos",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es la comprobación de extremo a extremo del defecto que "
                         "corrompía el historial: el analizador decidía la guardia por "
                         "el signo de una resta de profundidades, sin zona muerta, de "
                         "modo que el ruido de la estimación bastaba para que un "
                         "Zenkutsu correcto se guardara como un Kokutsu correcto. La "
                         "prueba unitaria TC-AUTO-050 verifica la geometría; esta "
                         "verifica que el analizador efectivamente se abstiene y no "
                         "persiste técnica ni ángulos de regla",
    componente="expert_system/analyzer.py (analyze_stance) sobre expert_system/guardia.py",
    requisitos="RF-03, RF-08",
    precondiciones="Analizador con ventana de filtro 1 y pose sintética de piernas visibles",
    datos_entrada="Pose con rodilla izquierda a 100° y derecha a 175° (la firma de una "
                  "postura adelantada) y los dos tobillos separados 0,02 en profundidad, "
                  "muy por debajo del medio ancho de cadera exigido",
    pasos=[
        Paso("Analizar la postura con la separación ambigua",
             "El diagnóstico de categoría `postura` sale con correcto=None"),
        Paso("Leer el mensaje emitido",
             "assert 'GUARDIA INDEFINIDA' in mensaje: se nombra la causa, no se "
             "confunde con una transición entre posturas"),
        Paso("Comprobar qué se persistiría",
             "assert tecnica is None y angulos_regla is None: no entra al historial "
             "con una técnica que el sistema no pudo determinar"),
        Paso("Repetir con la misma geometría y la profundidad invertida",
             "assert vuelve a abstenerse: la ambigüedad no se resuelve por el lado "
             "hacia el que apunte el ruido"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_una_guardia_ambigua_no_se_inventa(analizador):
    """
    El cuerpo dibuja una postura asimétrica —una rodilla flexionada y la otra
    extendida— pero los tobillos están casi a la misma profundidad.

    Antes, el signo de esa diferencia minúscula bastaba para reportar
    "ZENKUTSU: POSTURA FIRME" con correcto=True. Invirtiéndolo, la MISMA
    geometría corporal salía "KOKUTSU: POSTURA ESTABLE", también correcta. Una
    de las dos filas era siempre falsa, y ninguna se podía distinguir después
    en el historial.
    """
    for z_izq, z_der in ((-0.01, 0.01), (0.01, -0.01)):
        analizador.filtros["guardia"].reset()
        pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=175,
                              z_tobillo_izq=z_izq, z_tobillo_der=z_der)

        resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

        assert resultado["correcto"] is None, (
            f"con z={z_izq}/{z_der} el sistema emitió un veredicto sobre una guardia "
            f"que no puede distinguir: {resultado['mensaje']}")
        assert "GUARDIA INDEFINIDA" in resultado["mensaje"]
        assert resultado["tecnica"] is None
        assert resultado["angulos_regla"] is None


def test_con_separacion_real_la_guardia_si_se_decide(analizador):
    """
    Sin esta prueba la anterior podría pasar por un analizador que nunca
    reconoce una postura adelantada, y la abstención sería vacua.
    """
    pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=175,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    resultado = _por_categoria(analizador.analyze_stance(pose, ANCHO, ALTO), "postura")

    assert "ZENKUTSU (IZQ ADELANTE)" in resultado["mensaje"]
    assert resultado["correcto"] is True


def test_una_postura_simetrica_no_necesita_guardia(analizador):
    """
    Heiko y Kiba se evalúan por los dos ángulos de rodilla y no por cuál pierna
    va adelante, así que la abstención de la guardia no debe impedirlas. Es
    justo lo que Sebastián observó en el dojo: esas dos salían perfectas
    mientras Zenkutsu fallaba.
    """
    kiba = pose_sintetica(angulo_rodilla_izq=140, angulo_rodilla_der=140,
                          z_tobillo_izq=0.0, z_tobillo_der=0.0)
    resultado = _por_categoria(analizador.analyze_stance(kiba, ANCHO, ALTO), "postura")
    assert "KIBA DACHI" in resultado["mensaje"]
    assert resultado["correcto"] is True

    analizador.filtros["guardia"].reset()
    heiko = pose_sintetica(angulo_rodilla_izq=172, angulo_rodilla_der=172,
                           z_tobillo_izq=0.0, z_tobillo_der=0.0)
    resultado = _por_categoria(analizador.analyze_stance(heiko, ANCHO, ALTO), "postura")
    assert "POSTURA NATURAL" in resultado["mensaje"]
    assert resultado["correcto"] is True


# --------------------------------------------------------------------------
# Una fila por rodilla para el panel en vivo
# --------------------------------------------------------------------------

def test_cada_rodilla_se_informa_por_separado(analizador):
    """
    El panel declaraba "Rodilla izquierda" y "Rodilla derecha" desde siempre,
    pero los diagnósticos de postura viajaban bajo la categoría `postura`, que
    nunca coincide con esas dos: las filas mostraban un guion aunque los
    ángulos se midieran y se usaran para clasificar.
    """
    pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=175,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    resultados = analizador.analyze_stance(pose, ANCHO, ALTO)

    assert _por_categoria(resultados, "rodilla_izq")["angulo"] == pytest.approx(100, abs=1.5)
    assert _por_categoria(resultados, "rodilla_der")["angulo"] == pytest.approx(175, abs=1.5)


def test_el_veredicto_de_cada_rodilla_usa_el_rango_que_le_toca(analizador):
    """
    En un Zenkutsu la frontal y la trasera se juzgan contra rangos distintos
    (90–115° y 165–180°). Un único veredicto para las dos escondería cuál hay
    que corregir, que es precisamente lo que el sensei necesita saber.

    Aquí la frontal está bien (100°) y la trasera corta (160°): la postura
    entera es incorrecta, pero solo una de las dos piernas lo es.
    """
    pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=160,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    resultados = analizador.analyze_stance(pose, ANCHO, ALTO)

    assert _por_categoria(resultados, "postura")["correcto"] is False
    assert _por_categoria(resultados, "rodilla_izq")["correcto"] is True, \
        "la rodilla frontal a 100° está dentro de su rango"
    assert _por_categoria(resultados, "rodilla_der")["correcto"] is False, \
        "la trasera a 160° se queda corta del 165–180 que le exige el Zenkutsu"


def test_las_filas_por_rodilla_no_se_persisten_dos_veces(analizador):
    """
    Llevan `mensaje` vacío a propósito: el registro de la postura ya lo lleva
    la entrada `postura`, y `MedicionLogger` ignora los diagnósticos sin
    mensaje. Duplicarlos llenaría la base y el panel de correcciones con la
    misma medición repetida.
    """
    pose = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=175,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)

    resultados = analizador.analyze_stance(pose, ANCHO, ALTO)

    for categoria in ("rodilla_izq", "rodilla_der"):
        assert _por_categoria(resultados, categoria)["mensaje"] == ""


# ---------------------------------------------------------------------------
# El Tsuki solo se juzga cuando hay golpe (30-sep-2026)
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-057",
    nombre="El analizador no emite veredicto de Tsuki mientras el brazo no golpea",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="la maquina de estados del Tsuki puede ser correcta y aun asi "
                         "no proteger nada si el analizador sigue llamando a la regla "
                         "por su cuenta, que es exactamente lo que hacia hasta el "
                         "30-sep-2026. Esta prueba recorre la costura completa "
                         "-landmarks, pixeles, angulo, filtro, maquina, diagnostico- "
                         "porque es en esa costura donde vivia el defecto: la regla "
                         "siempre estuvo bien, lo que estaba mal era cuando se "
                         "consultaba",
    componente="expert_system/analyzer.py (analyze_tsuki) sobre expert_system/tsuki.py",
    requisitos="RF-03, RF-07",
    precondiciones="Analizador con ventana de filtro 1, sin base de datos: usa los "
                   "umbrales de literatura",
    datos_entrada="Pose sintetica de una persona de pie con los brazos casi extendidos "
                  "(172 grados, la cifra medida en la prueba en vivo del 30-sep), "
                  "repetida durante dos segundos de marcas de tiempo",
    pasos=[
        Paso("Analizar sesenta fotogramas de esa pose inmovil",
             "assert ningun diagnostico de codo lleva veredicto cerrado, ni de un "
             "brazo ni del otro"),
        Paso("Comprobar que el angulo si se informa",
             "assert los grados del codo aparecen en el diagnostico: el codo esta "
             "medido, lo que falta es la tecnica"),
        Paso("Comprobar que la fila no se marca como medicion de Tsuki",
             "assert `tecnica` es None, para que no entre en el informe de "
             "recalibracion retroactiva"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz grafica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_estar_de_pie_no_produce_veredicto_de_tsuki(analizador):
    """
    La regresión del defecto que encontró la prueba en vivo del 30-sep-2026.

    De pie y con los brazos abajo, la pantalla informaba «IZQ - TSUKI:
    EXCELENTE / DER - TSUKI: EXCELENTE», y esas filas entraban a la base con
    `tecnica="tsuki"` y veredicto cerrado. Sesenta fotogramas de brazo quieto
    producían sesenta mediciones de una técnica que nadie ejecutó.
    """
    pose = pose_sintetica(angulo_codo_izq=172, angulo_codo_der=172)

    for fotograma in range(60):
        resultados = analizador.analyze_tsuki(pose, ANCHO, ALTO, fotograma * 33)

        for categoria in ("codo_izq", "codo_der"):
            diagnostico = _por_categoria(resultados, categoria)
            assert diagnostico["correcto"] is None, \
                "un brazo inmóvil no ejecuta ningún Tsuki y no puede calificarse"
            assert diagnostico["tecnica"] is None, \
                "tampoco puede entrar al historial como medición de Tsuki"
            assert diagnostico["angulo"] == pytest.approx(172, abs=1), \
                "el codo sí está medido: lo que falta es la técnica, no el dato"


def test_un_golpe_si_produce_veredicto(analizador):
    """
    El contrapeso obligatorio: si la abstención se tragara también los golpes
    reales, la prueba anterior pasaría con un analizador que no sirve para
    nada. Se ejecuta un Tsuki con el brazo izquierdo mientras el derecho sigue
    quieto, y solo el izquierdo recibe veredicto.
    """
    veredictos = []
    for fotograma, angulo in enumerate([50] * 5 + [75, 100, 125, 150, 172]):
        pose = pose_sintetica(angulo_codo_izq=angulo, angulo_codo_der=172)
        veredictos.append(analizador.analyze_tsuki(pose, ANCHO, ALTO, fotograma * 33))

    # El golpe se cierra cuando el brazo empieza a volver.
    pose = pose_sintetica(angulo_codo_izq=150, angulo_codo_der=172)
    ultimo = analizador.analyze_tsuki(pose, ANCHO, ALTO, 10 * 33)

    assert _por_categoria(ultimo, "codo_izq")["correcto"] is True, \
        "un Tsuki que llega a 172° está dentro del rango y se juzga correcto"
    assert _por_categoria(ultimo, "codo_izq")["tecnica"] == "tsuki"
    assert _por_categoria(ultimo, "codo_der")["correcto"] is None, \
        "el brazo que no golpeó no recibe veredicto, aunque esté extendido"
