"""
Pruebas unitarias de biomechanics/geometry.py (BiomechanicsMath).

Es la función más crítica del sistema: TODO diagnóstico del sistema experto
depende de que este ángulo esté bien calculado. Un error aquí no rompe la
aplicación (no lanza excepción), solo hace que el sistema le diga al karateka
que su técnica está bien cuando está mal — el peor tipo de defecto para un
sistema de evaluación.
"""
import math

import pytest

from biomechanics.geometry import BiomechanicsMath

pytestmark = pytest.mark.unitaria

TOLERANCIA = 0.01  # grados


@pytest.mark.parametrize("nombre, a, b, c, esperado", [
    ("angulo recto",            (0, 100), (0, 0), (100, 0),    90.0),
    ("extension total",         (-100, 0), (0, 0), (100, 0),  180.0),
    ("brazo plegado",           (100, 0), (0, 0), (100, 0),     0.0),
    ("tsuki en rango correcto", (-100, 0), (0, 0), (100, 17),  170.3),
    ("angulo agudo de 45",      (100, 0), (0, 0), (100, 100),  45.0),
])
def test_calcula_el_angulo_interno_conocido(nombre, a, b, c, esperado):
    """Casos con respuesta geométrica conocida de antemano."""
    obtenido = BiomechanicsMath.calculate_angle(a, b, c)
    assert obtenido == pytest.approx(esperado, abs=0.1), \
        f"{nombre}: esperaba {esperado}, obtuve {obtenido}"


@pytest.mark.parametrize("grados_reales", [0, 15, 30, 45, 60, 90, 120, 150, 179])
def test_reconstruye_cualquier_angulo_del_rango_articular(grados_reales):
    """
    Barrido del rango de movimiento articular humano: se construyen los puntos
    a partir de un ángulo conocido y la función debe devolver ese mismo ángulo.
    """
    radio = 100
    vertice = (0, 0)
    a = (radio, 0)
    c = (radio * math.cos(math.radians(grados_reales)),
         radio * math.sin(math.radians(grados_reales)))

    assert BiomechanicsMath.calculate_angle(a, vertice, c) == pytest.approx(grados_reales, abs=TOLERANCIA)


@pytest.mark.parametrize("orientacion_a, orientacion_c, esperado", [
    (170, -170, 20),    # los dos segmentos caen a lados opuestos del corte de -180/180
    (150, -150, 60),
    (-179, 179, 2),
])
def test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular(orientacion_a, orientacion_c, esperado):
    """
    Caso límite del cálculo con atan2: si los dos segmentos quedan a lados
    opuestos de la discontinuidad de +-180 grados, la resta da un ángulo
    reflejo (>180) que debe convertirse a su equivalente interno. Sin esta
    corrección, una extremidad orientada hacia arriba podría reportar 340
    grados y ningún umbral del sistema experto la reconocería.
    """
    radio = 100
    a = (radio * math.cos(math.radians(orientacion_a)), radio * math.sin(math.radians(orientacion_a)))
    c = (radio * math.cos(math.radians(orientacion_c)), radio * math.sin(math.radians(orientacion_c)))

    assert BiomechanicsMath.calculate_angle(a, (0, 0), c) == pytest.approx(esperado, abs=TOLERANCIA)


@pytest.mark.parametrize("grados_reflejos, esperado", [(190, 170), (270, 90), (350, 10)])
def test_normaliza_angulos_reflejos_al_rango_articular(grados_reflejos, esperado):
    """
    Una articulación humana no puede medir más de 180 grados: si el cálculo
    vectorial cae del lado reflejo, debe devolverse el ángulo interno
    equivalente. Sin esta normalización un codo extendido podría reportarse
    como 190 y jamás entraría en el rango 160-175 de un Tsuki correcto.
    """
    radio = 100
    a = (radio, 0)
    c = (radio * math.cos(math.radians(grados_reflejos)),
         radio * math.sin(math.radians(grados_reflejos)))

    assert BiomechanicsMath.calculate_angle(a, (0, 0), c) == pytest.approx(esperado, abs=TOLERANCIA)


@pytest.mark.parametrize("grados", [0, 37, 90, 143, 180])
def test_el_resultado_nunca_sale_del_rango_0_180(grados):
    """Propiedad invariante: el ángulo interno siempre vive en [0, 180]."""
    radio = 100
    for signo in (1, -1):
        c = (radio * math.cos(math.radians(signo * grados)),
             radio * math.sin(math.radians(signo * grados)))
        angulo = BiomechanicsMath.calculate_angle((radio, 0), (0, 0), c)
        assert 0.0 <= angulo <= 180.0, f"angulo fuera de rango: {angulo}"


def test_es_simetrico_respecto_al_orden_de_los_extremos():
    """
    El ángulo del codo debe ser el mismo se mida hombro->muñeca o
    muñeca->hombro. Si no lo fuera, el diagnóstico dependería del orden en
    que el analizador pasa los landmarks.
    """
    hombro, codo, muneca = (100, 250), (140, 400), (260, 380)

    directo = BiomechanicsMath.calculate_angle(hombro, codo, muneca)
    invertido = BiomechanicsMath.calculate_angle(muneca, codo, hombro)

    assert directo == pytest.approx(invertido, abs=TOLERANCIA)


@pytest.mark.parametrize("factor", [0.5, 2, 10])
def test_es_invariante_a_la_distancia_a_la_camara(factor):
    """
    Escalar toda la pose (acercarse o alejarse de la cámara) no debe cambiar
    el ángulo: es lo que permite evaluar al karateka sin exigirle una
    distancia fija al lente.
    """
    hombro, codo, muneca = (100, 250), (140, 400), (260, 380)
    escala = lambda p: (p[0] * factor, p[1] * factor)

    original = BiomechanicsMath.calculate_angle(hombro, codo, muneca)
    escalado = BiomechanicsMath.calculate_angle(escala(hombro), escala(codo), escala(muneca))

    assert original == pytest.approx(escalado, abs=TOLERANCIA)


def test_puntos_superpuestos_no_lanzan_excepcion():
    """
    Caso límite: MediaPipe puede colapsar dos landmarks en el mismo píxel
    cuando la extremidad apunta hacia la cámara. La función debe devolver un
    número, no reventar el bucle de video con una excepción.
    """
    resultado = BiomechanicsMath.calculate_angle((50, 50), (50, 50), (80, 90))

    assert isinstance(resultado, float)
    assert 0.0 <= resultado <= 180.0
