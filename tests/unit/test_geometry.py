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
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

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


@ficha(
    id_caso="TC-AUTO-001",
    nombre="Reconstrucción exacta del ángulo interno de una articulación en todo el "
           "rango de movimiento humano",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="todo diagnóstico del sistema experto depende de este cálculo",
    componente="biomechanics/geometry.py (BiomechanicsMath)",
    requisitos="RF-05",
    precondiciones="Ninguna. `BiomechanicsMath` es una clase de utilidad sin estado ni "
                   "dependencias externas",
    datos_entrada="Nueve ángulos conocidos del rango articular: "
                  "[0, 15, 30, 45, 60, 90, 120, 150, 179], con puntos generados por "
                  "trigonometría a radio 100 px",
    pasos=[
        Paso("Construir los tres puntos A, B, C a partir de un ángulo conocido θ",
             "Coordenadas válidas en el plano de la imagen"),
        Paso("Invocar `BiomechanicsMath.calculate_angle(A, B, C)`",
             "Devuelve un valor de tipo `float`"),
        Paso("Comparar el resultado contra θ",
             "assert obtenido == pytest.approx(θ, abs=0.01)"),
        Paso("Repetir para los nueve ángulos del rango",
             "Los nueve casos parametrizados finalizan en PASSED"),
    ],
    resultado_esperado="PASSED sin excepciones ni tiempos de espera agotados",
)
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


@ficha(
    id_caso="TC-AUTO-002",
    nombre="El ángulo devuelto nunca excede 180° aunque los segmentos crucen la "
           "discontinuidad de atan2",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="un ángulo de 340° no entra en ningún umbral y el sistema "
                         "dejaría de evaluar la técnica",
    componente="biomechanics/geometry.py (BiomechanicsMath)",
    requisitos="RF-05",
    precondiciones="Ninguna",
    datos_entrada="Pares de orientaciones opuestas al corte ±180°: (170°, −170°), "
                  "(150°, −150°), (−179°, 179°)",
    pasos=[
        Paso("Colocar los segmentos proximal y distal a lados opuestos de ±180°",
             "Configuración geométrica que produce un ángulo reflejo interno"),
        Paso("Invocar `calculate_angle`",
             "Se ejecuta la rama de normalización `360 − ángulo`"),
        Paso("Verificar el ángulo interno equivalente",
             "assert obtenido == pytest.approx(esperado, abs=0.01)"),
        Paso("Verificar la invariante global de rango",
             "assert 0.0 <= ángulo <= 180.0"),
    ],
    resultado_esperado="PASSED en los tres casos parametrizados",
)
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


# --------------------------------------------------------------------------
# Ángulos en tres dimensiones
#
# La razón de ser de `calculate_angle_3d`: la proyección 2D deforma el ángulo
# cuando el plano de la técnica no es paralelo al sensor, y eso es lo que hace
# que un tsuki lanzado de frente se informe como flexionado.
# --------------------------------------------------------------------------

def _brazo_girado(angulo_real, giro_grados):
    """
    Hombro, codo y muñeca con un ángulo de codo real conocido, **con el brazo
    entero girado** `giro` grados sobre el eje vertical.

    El giro es del conjunto, no del antebrazo sobre el codo: girar solo el
    antebrazo cambiaría el ángulo real en vez de conservarlo, y entonces la
    prueba no estaría midiendo el error de proyección sino una postura
    distinta. (Una primera versión de este ayudante hacía justo eso.)

    Con giro=0 el plano del brazo es paralelo al sensor —la vista de perfil
    perfecta—; conforme crece, el plano se pone de canto.
    """
    a, g = math.radians(angulo_real), math.radians(giro_grados)
    codo = (0.0, 0.0, 0.0)
    hombro = (math.cos(g), 0.0, -math.sin(g))
    muneca = (math.cos(a) * math.cos(g), math.sin(a), -math.cos(a) * math.sin(g))
    return hombro, codo, muneca


def test_el_ayudante_conserva_el_angulo_real_al_girar():
    """
    Sin esto, las pruebas de abajo podrían estar midiendo el error de un
    ayudante mal construido en vez del error de proyección del sistema.
    """
    for giro in (0, 30, 60, 85):
        hombro, codo, muneca = _brazo_girado(175.0, giro)
        assert BiomechanicsMath.calculate_angle_3d(hombro, codo, muneca) == \
            pytest.approx(175.0, abs=0.01), f"el giro de {giro}° alteró el ángulo real"


def test_en_el_plano_del_sensor_las_dos_medidas_coinciden():
    """Sin giro no hay escorzo, así que 2D y 3D tienen que dar lo mismo."""
    hombro, codo, muneca = _brazo_girado(120.0, giro_grados=0)

    assert BiomechanicsMath.calculate_angle(
        hombro[:2], codo[:2], muneca[:2]) == pytest.approx(120.0, abs=0.1)
    assert BiomechanicsMath.calculate_angle_3d(
        hombro, codo, muneca) == pytest.approx(120.0, abs=0.1)


@pytest.mark.parametrize("angulo_real, giro, esperado_2d", [
    (175.0, 30, 174.2), (175.0, 60, 170.1), (175.0, 85, 134.9),
    (160.0, 30, 157.2), (160.0, 60, 143.9), (160.0, 85, 103.5),
    (120.0, 30, 116.6), (120.0, 60, 106.1), (120.0, 85,  92.9),
])
def test_el_error_de_proyeccion_crece_con_el_giro(angulo_real, giro, esperado_2d):
    """
    El hallazgo del 28-sep-2026, fijado en números para que no se cite de
    memoria en la tesis: la terna puede correr pytest.

    Dos lecturas de la tabla. La primera, que el error crece con el giro. La
    segunda, más incómoda: **la deformación empuja siempre hacia 90°**, así que
    un codo extendido se lee como flexionado y nunca al revés. Un tsuki
    correcto a 175° grabado casi de frente se mide en 134,9° y la regla lo
    corrige como FLEXIONADO, regañando a un alumno que lo hizo bien.

    En los tres casos la medida en tres dimensiones recupera el ángulo real.
    """
    hombro, codo, muneca = _brazo_girado(angulo_real, giro)

    assert BiomechanicsMath.calculate_angle(
        hombro[:2], codo[:2], muneca[:2]) == pytest.approx(esperado_2d, abs=0.1)
    assert BiomechanicsMath.calculate_angle_3d(
        hombro, codo, muneca) == pytest.approx(angulo_real, abs=0.1)


def test_de_canto_la_medida_2d_pierde_todo_el_angulo():
    """
    El límite. Con el plano del brazo exactamente de canto al sensor, el brazo
    se proyecta sobre una recta: hombro y codo caen en el mismo punto y el
    ángulo 2D deja de estar definido —el sistema informa 90°, que no es una
    medición sino el residuo de un cálculo degenerado—. La medida 3D sigue
    siendo exacta.

    No es un caso de laboratorio: es lo que ocurre al grabar de frente una
    técnica que avanza hacia la cámara.
    """
    hombro, codo, muneca = _brazo_girado(175.0, giro_grados=90)

    assert hombro[:2] == pytest.approx(codo[:2], abs=1e-12), \
        "de canto, el brazo proyectado colapsa a un punto"
    assert BiomechanicsMath.calculate_angle_3d(
        hombro, codo, muneca) == pytest.approx(175.0, abs=0.1)


def test_los_extremos_no_rompen_el_calculo():
    """
    0° y 180° son justo los ángulos del Kime, y son donde el redondeo de punto
    flotante puede sacar el coseno de [-1, 1] y hacer estallar `acos`.
    """
    recto = BiomechanicsMath.calculate_angle_3d((0, 0, 0), (1, 0, 0), (2, 0, 0))
    plegado = BiomechanicsMath.calculate_angle_3d((0, 0, 0), (1, 0, 0), (0, 0, 0))

    assert recto == pytest.approx(180.0)
    assert plegado == pytest.approx(0.0)


def test_una_articulacion_degenerada_no_inventa_un_angulo():
    """Dos puntos estimados en el mismo sitio no definen ninguna dirección."""
    assert BiomechanicsMath.calculate_angle_3d((1, 1, 1), (1, 1, 1), (2, 0, 0)) == 0.0
