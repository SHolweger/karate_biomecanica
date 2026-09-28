"""
Pruebas de la herramienta que compara medir en 2D contra medir en 3D.

`comparar_2d_3d.py` replica el árbol de decisión de `analyze_stance` porque
tiene que alimentarlo con dos juegos de ángulos distintos sobre los mismos
landmarks, y el analizador calcula los suyos por dentro. Esa réplica es una
deuda: si el clasificador cambia y la copia no, la herramienta seguiría
respondiendo con criterios viejos y la comparación —de la que depende decidir
si el sistema pasa a 3D— saldría falseada sin avisar.

Estas pruebas atan las dos implementaciones. Corren en integración continua
porque nada de lo que se ejercita aquí importa MediaPipe ni OpenCV: el módulo
los carga dentro de `comparar()`, que es justo la función que no se prueba.
"""
import pytest

from comparar_2d_3d import _clasificar
from expert_system.analyzer import TechniqueAnalyzer
from expert_system.guardia import DER_ADELANTE, IZQ_ADELANTE
from helpers.fakes import pose_sintetica
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

ANCHO, ALTO = 1000, 1000

# Cada caso: ángulo de rodilla izquierda, derecha, profundidad de los tobillos
# y la postura que el sistema debe reconocer.
CASOS = [
    ("postura natural",     172, 172,  0.0,  0.0, "heiko_dachi"),
    ("postura de jinete",   140, 140,  0.0,  0.0, "kiba_dachi"),
    ("adelantada, izq",     100, 175, -0.3,  0.3, "zenkutsu_dachi"),
    ("adelantada, der",     175, 100,  0.3, -0.3, "zenkutsu_dachi"),
    ("atrasada, izq",       165, 105, -0.3,  0.3, "kokutsu_dachi"),
    ("atrasada, der",       105, 165,  0.3, -0.3, "kokutsu_dachi"),
    ("guardia ambigua",     100, 175, -0.01, 0.01, "guardia_indefinida"),
    ("entre posturas",      145, 175, -0.3,  0.3, "transicion"),
]


def _postura_segun_el_analizador(resultado):
    """Traduce el mensaje del analizador a la misma clave que usa la herramienta."""
    mensaje = resultado["mensaje"]
    if "POSTURA NATURAL" in mensaje:
        return "heiko_dachi"
    if "KIBA DACHI" in mensaje:
        return "kiba_dachi"
    if "ZENKUTSU" in mensaje:
        return "zenkutsu_dachi"
    if "KOKUTSU" in mensaje:
        return "kokutsu_dachi"
    if "GUARDIA INDEFINIDA" in mensaje:
        return "guardia_indefinida"
    return "transicion"


@ficha(
    id_caso="TC-AUTO-052",
    nombre="La herramienta de comparación 2D/3D clasifica igual que el analizador "
           "del sistema en todas las posturas del catálogo",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la herramienta replica el árbol de decisión de "
                         "`analyze_stance` para poder alimentarlo con dos juegos de "
                         "ángulos sobre los mismos landmarks. De esa comparación "
                         "depende decidir si los ángulos del sistema pasan a "
                         "calcularse en tres dimensiones, así que una réplica "
                         "desactualizada no daría un error visible: daría una "
                         "recomendación equivocada sobre una decisión de arquitectura",
    componente="comparar_2d_3d.py (_clasificar) contra expert_system/analyzer.py",
    requisitos="RF-03",
    precondiciones="Ninguna: ambas implementaciones operan sobre ángulos, sin cámara",
    datos_entrada="Ocho poses sintéticas que cubren las cuatro posturas del catálogo "
                  "con ambas guardias, más la guardia ambigua y una transición",
    pasos=[
        Paso("Analizar cada pose con TechniqueAnalyzer.analyze_stance",
             "Se obtiene el mensaje de diagnóstico de la categoría `postura`"),
        Paso("Clasificar los mismos ángulos con `_clasificar` de la herramienta",
             "Se obtiene una clave de postura"),
        Paso("Contrastar ambas respuestas caso por caso",
             "assert coinciden en los ocho casos"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
@pytest.mark.parametrize("nombre, izq, der, z_izq, z_der, esperada", CASOS)
def test_la_herramienta_clasifica_igual_que_el_sistema(nombre, izq, der, z_izq, z_der, esperada):
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)
    pose = pose_sintetica(angulo_rodilla_izq=izq, angulo_rodilla_der=der,
                          z_tobillo_izq=z_izq, z_tobillo_der=z_der)

    resultado = next(r for r in analizador.analyze_stance(pose, ANCHO, ALTO)
                     if r["categoria"] == "postura")
    del_sistema = _postura_segun_el_analizador(resultado)

    # La herramienta recibe los ángulos ya calculados y la guardia ya deducida,
    # que es exactamente lo que hace dentro de su bucle de comparación.
    guardia = (None if del_sistema == "guardia_indefinida"
               else (IZQ_ADELANTE if z_izq < z_der else DER_ADELANTE))
    de_la_herramienta = _clasificar(izq, der, guardia)

    assert del_sistema == esperada, f"{nombre}: el analizador reconoció {del_sistema}"
    assert de_la_herramienta == esperada, (
        f"{nombre}: la herramienta reconoció {de_la_herramienta} y el sistema "
        f"{del_sistema}; la réplica del clasificador quedó desactualizada")


def test_sin_guardia_no_se_elige_entre_zenkutsu_y_kokutsu():
    """
    La herramienta hereda la abstención del sistema: sin saber qué pierna va
    adelante, una postura asimétrica no se resuelve a ninguna de las dos.
    """
    assert _clasificar(100, 175, guardia=None) == "guardia_indefinida"
    assert _clasificar(165, 105, guardia=None) == "guardia_indefinida"
    assert _clasificar(100, 175, guardia=IZQ_ADELANTE) == "zenkutsu_dachi"


def test_las_posturas_simetricas_no_dependen_de_la_guardia():
    """Heiko y Kiba salen igual con guardia, sin ella y con la contraria."""
    for guardia in (None, IZQ_ADELANTE, DER_ADELANTE):
        assert _clasificar(172, 172, guardia) == "heiko_dachi"
        assert _clasificar(140, 140, guardia) == "kiba_dachi"
