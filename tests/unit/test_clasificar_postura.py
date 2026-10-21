"""
El clasificador reconoce las ejecuciones con error, y solo desde la toma en que
se pueden medir (TC-AUTO-083).

Las cifras son las medianas de los tramos sostenidos de las tomas del protocolo
del 19-oct-2026, medidas el 21-oct con MediaPipe sobre los videos de Sebastián:
rodillas, orientación de la cadera respecto de la cámara (0 de perfil, 1 de
frente), separación de los pies sobre el eje sagital y apertura en x, las dos
en anchos de cadera. No son números elegidos para que la prueba pase: son lo
que el sistema vio.
"""
import itertools

import pytest

from expert_system import analyzer
from expert_system.analyzer import clasificar_postura
from expert_system.guardia import DER_ADELANTE, IZQ_ADELANTE
from expert_system.knowledge_base import (KIBA_EXTIENDE, KIBA_FLEXIONA, KIBA_REPARTE,
                                          KarateRules)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

# (rodilla izq, rodilla der, guardia, separación, orientación, apertura)
ZENKUTSU_ALTO = (174.7, 164.6, DER_ADELANTE, -0.55, 0.11, 0.4)
ZENKUTSU_TRASERA_DOBLADA = (139.2, 109.5, DER_ADELANTE, -0.76, 0.07, 0.4)
ZENKUTSU_DE_CLASE_133 = (133.4, 167.8, IZQ_ADELANTE, 0.47, 0.14, 0.4)
KIBA_ALTO = (157.8, 164.8, IZQ_ADELANTE, 3.80, 0.97, 2.70)
KIBA_MUY_BAJO = (111.6, 123.8, IZQ_ADELANTE, 0.41, 0.95, 3.04)
KIBA_CARGADO = (136.1, 160.4, IZQ_ADELANTE, 2.13, 0.81, 2.82)
KOKUTSU_DE_PERFIL = (176.4, 169.6, DER_ADELANTE, -1.57, 0.44, 0.5)
DE_PIE_CON_LOS_PIES_ABIERTOS = (177.0, 176.0, IZQ_ADELANTE, 0.6, 0.98, 2.30)


@ficha(
    id_caso="TC-AUTO-083",
    nombre="El clasificador reconoce las ejecuciones con error, y solo desde la toma "
           "en que se pueden medir",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="sobre las tomas con errores a propósito del 19-oct ninguna "
                         "recibió su corrección: el Zenkutsu alto salía Heiko y el sistema "
                         "decía «Estira las piernas», lo contrario de lo necesario; la "
                         "trasera doblada y los tres Kiba con error salían transición. Y "
                         "ampliar los cortes sin mirar la toma registraba un Kiba de peso "
                         "cargado, filmado de frente, como Zenkutsu con veredicto",
    componente="expert_system/analyzer.py (clasificar_postura, analyze_stance), "
               "expert_system/knowledge_base.py (evaluate_kiba_dachi)",
    requisitos="RF-03, RF-05",
    precondiciones="Ninguna: función pura y el doble de MediaPipe",
    datos_entrada="Medianas de los tramos sostenidos de err_zen_alto, err_zen_trasera, "
                  "zen_izq_desde_der, tec_kiba y kokutsu_der_desde_izq",
    pasos=[
        Paso("Clasificar los errores a propósito con la orientación y la apertura medidas",
             "assert Zenkutsu alto, Zenkutsu con la trasera doblada y los tres Kiba se reconocen"),
        Paso("Clasificar el Kiba cargado (de frente) y el Kokutsu de perfil",
             "assert ninguno sale Zenkutsu"),
        Paso("Clasificar sin orientación una rejilla de ángulos y guardias",
             "assert el resultado es el del árbol anterior al 21-oct"),
        Paso("Juzgar los tres Kiba con error",
             "assert «Baja más», «Sube un poco» y «Reparte el peso», cada uno el suyo"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest. Contraste sobre los videos con "
              "`revisar_correcciones.py` antes y después del cambio.",
)
@pytest.mark.parametrize("caso, esperada", [
    (ZENKUTSU_ALTO, "zenkutsu_dachi"),
    (ZENKUTSU_TRASERA_DOBLADA, "zenkutsu_dachi"),
    (ZENKUTSU_DE_CLASE_133, "zenkutsu_dachi"),
    (KIBA_ALTO, "kiba_dachi"),
    (KIBA_MUY_BAJO, "kiba_dachi"),
    (KIBA_CARGADO, "kiba_dachi"),
])
def test_los_errores_a_proposito_se_reconocen(caso, esperada):
    assert clasificar_postura(*caso) == esperada


def test_hasta_el_21_oct_ninguno_se_reconocia():
    """
    Sin orientación ni apertura, los mismos ángulos dan lo que daban antes: el
    Zenkutsu alto, un Heiko —de ahí el «Estira las piernas»—, y el resto,
    transición. Es el estado que la prueba de arriba corrige.
    """
    assert clasificar_postura(*ZENKUTSU_ALTO[:3]) == "heiko_dachi"
    assert clasificar_postura(*ZENKUTSU_TRASERA_DOBLADA[:3]) == "transicion"
    assert clasificar_postura(*KIBA_MUY_BAJO[:3]) == "transicion"
    assert clasificar_postura(*KIBA_CARGADO[:3]) == "transicion"


def test_la_toma_equivocada_no_inventa_un_zenkutsu():
    """
    De frente, qué pierna va adelante lo decide la profundidad, que es ruido: el
    Kiba cargado tenía «guardia» en el 82 % de los fotogramas. Y de perfil, el
    Kokutsu da las rodillas de un Zenkutsu alto —la trasera se dobla hacia la
    cámara y se ve recta—; lo separa la cadera de medio lado.
    """
    assert clasificar_postura(*KIBA_CARGADO) != "zenkutsu_dachi"
    assert clasificar_postura(*KOKUTSU_DE_PERFIL) == "transicion", (
        "ni Zenkutsu ni Heiko: de perfil el Kokutsu no se puede medir")
    assert clasificar_postura(*DE_PIE_CON_LOS_PIES_ABIERTOS) == "heiko_dachi"
    de_pie_algo_flexionado = (158.0, 163.0, IZQ_ADELANTE, 0.3, 0.98, 1.5)
    assert clasificar_postura(*de_pie_algo_flexionado) == "transicion", (
        "con los pies juntos, unas rodillas algo dobladas no son un Kiba alto")


def _arbol_anterior(izq, der, guardia):
    """El clasificador tal como estaba hasta el 21-oct-2026, copiado para compararlo."""
    if izq > 160 and der > 160:
        return "heiko_dachi"
    if 130 <= izq <= 160 and 130 <= der <= 160:
        return "kiba_dachi"
    if guardia is not None:
        frontal, trasero = (izq, der) if guardia == IZQ_ADELANTE else (der, izq)
        if frontal < 130 and trasero > 150:
            return "zenkutsu_dachi"
        if frontal >= 140 and trasero <= 135:
            return "kokutsu_dachi"
    elif min(izq, der) <= 135 and max(izq, der) >= 140:
        return "guardia_indefinida"
    return "transicion"


def test_sin_orientacion_el_clasificador_es_el_de_antes():
    """Lo que funcionaba se sigue reconociendo igual: las ampliaciones exigen la toma."""
    angulos = range(60, 181, 5)
    for izq, der, guardia in itertools.product(angulos, angulos,
                                                (None, IZQ_ADELANTE, DER_ADELANTE)):
        assert clasificar_postura(izq, der, guardia) == _arbol_anterior(izq, der, guardia)


def test_lo_que_ya_se_reconocia_se_reconoce_desde_cualquier_toma():
    angulos = range(60, 181, 5)
    for izq, der, guardia in itertools.product(angulos, angulos,
                                                (None, IZQ_ADELANTE, DER_ADELANTE)):
        antes = _arbol_anterior(izq, der, guardia)
        if antes in ("heiko_dachi", "kiba_dachi", "zenkutsu_dachi", "kokutsu_dachi"):
            for vista in (0.05, 0.4, 0.7, 1.0):
                assert clasificar_postura(izq, der, guardia, 0.3, vista, 1.5) == antes


@pytest.mark.parametrize("izq, der, esperado", [
    (KIBA_ALTO[0], KIBA_ALTO[1], KIBA_FLEXIONA),
    (KIBA_MUY_BAJO[0], KIBA_MUY_BAJO[1], KIBA_EXTIENDE),
    (KIBA_CARGADO[0], KIBA_CARGADO[1], KIBA_REPARTE),
])
def test_cada_kiba_con_error_recibe_su_correccion(izq, der, esperado):
    correcto, mensaje, _ = KarateRules().evaluate_kiba_dachi(izq, der)
    assert correcto is False and mensaje == esperado


def test_el_analizador_le_pasa_la_toma_al_clasificador(monkeypatch):
    """La costura: la orientación y la apertura salen de las caderas y los tobillos."""
    from helpers.fakes import pose_sintetica

    vistos = []

    def espia(*argumentos):
        vistos.append(argumentos)
        return "transicion"

    monkeypatch.setattr(analyzer, "clasificar_postura", espia)
    pose = pose_sintetica(angulo_rodilla_izq=140, angulo_rodilla_der=140)
    analyzer.TechniqueAnalyzer(ventana_filtro=1).analyze_stance(pose, 1000, 1000)

    (_, _, _, _, vista, apertura), = vistos
    caderas = abs(pose[24].x - pose[23].x)
    assert vista == pytest.approx(1.0), "el doble está de frente: caderas separadas solo en x"
    assert apertura == pytest.approx(abs(pose[28].x - pose[27].x) / caderas)
