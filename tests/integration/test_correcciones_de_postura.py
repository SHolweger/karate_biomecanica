"""
Pruebas de la costura entre el veredicto de postura y su corrección (RF-06).

Por qué existe este módulo
--------------------------
`gui/coaching.py` traduce el veredicto técnico del motor a la frase que el
sensei diría en el tatami. Su guarda, TC-AUTO-034, comprueba que cada veredicto
que la base de conocimientos puede emitir tenga su entrada en la tabla — y
pasaba. Pero **ninguna postura llegaba traducida al panel** (detectado el
18-oct-2026).

La razón es que el analizador no entrega el veredicto pelado: le antepone la
postura que reconoció,

    ZENKUTSU (IZQ ADELANTE): POSTURA: CORREGIR ALTURA

y `traducir` solo sabía quitar el prefijo de lado de los golpes («IZQ - »). La
búsqueda en la tabla fallaba, y por diseño un veredicto sin entrada se muestra
tal cual. El Tsuki se traducía; Heiko, Kiba, Zenkutsu y Kokutsu, nunca. Ni en
el panel en vivo ni en el reporte de sesión.

Es la misma lección que la del doble de MediaPipe: la guarda comprobaba la
TABLA, no lo que la pantalla recibe. Estas pruebas hacen el recorrido real
—geometría corporal, analizador, mensaje, traducción— y por eso son las que
fallan cuando la costura se rompe.
"""
import pytest

from expert_system.analyzer import TechniqueAnalyzer
from gui.coaching import traducir
from helpers.fakes import pose_sintetica
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion

ANCHO = ALTO = 1000

# Una geometría por postura y veredicto. Los ángulos salen de los rangos de
# literatura de `knowledge_base.UMBRALES_LITERATURA` y de los cortes del
# clasificador en `analyzer.py`; la guardia, de los tobillos (izquierda adelante).
IZQ_ADELANTE = dict(z_tobillo_izq=-0.3, z_tobillo_der=0.3)

POSTURAS = [
    ("heiko correcto",       dict(angulo_rodilla_izq=175, angulo_rodilla_der=175)),
    ("heiko flexionado",     dict(angulo_rodilla_izq=162, angulo_rodilla_der=162)),
    ("kiba correcto",        dict(angulo_rodilla_izq=140, angulo_rodilla_der=140)),
    ("kiba alto",            dict(angulo_rodilla_izq=158, angulo_rodilla_der=158)),
    ("zenkutsu correcto",    dict(angulo_rodilla_izq=100, angulo_rodilla_der=170, **IZQ_ADELANTE)),
    ("zenkutsu incorrecto",  dict(angulo_rodilla_izq=125, angulo_rodilla_der=170, **IZQ_ADELANTE)),
    ("kokutsu correcto",     dict(angulo_rodilla_izq=165, angulo_rodilla_der=105, **IZQ_ADELANTE)),
    ("kokutsu incorrecto",   dict(angulo_rodilla_izq=165, angulo_rodilla_der=128, **IZQ_ADELANTE)),
]


def _veredicto_de_postura(**geometria):
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)
    resultados = analizador.analyze_stance(pose_sintetica(**geometria), ANCHO, ALTO)
    return [d for d in resultados if d["categoria"] == "postura"][0]


@ficha(
    id_caso="TC-AUTO-066",
    nombre="Todo veredicto de postura que produce el analizador llega traducido al panel",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "el panel de correcciones es la forma en que el sistema cumple el RF-06. "
        "Hasta el 18-oct-2026 ninguna postura llegaba traducida —el sensei leía "
        "«ZENKUTSU (IZQ ADELANTE): POSTURA: CORREGIR ALTURA»— y la guarda de la "
        "tabla (TC-AUTO-034) pasaba, porque comprobaba la tabla y no el mensaje "
        "que la pantalla recibe"),
    componente="gui/coaching.py (traducir) + expert_system/analyzer.py (analyze_stance)",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna; el analizador corre sin cámara sobre poses sintéticas",
    datos_entrada=(
        "Ocho geometrías corporales: Heiko, Kiba, Zenkutsu y Kokutsu, cada una "
        "bien y mal ejecutada"),
    pasos=[
        Paso("Construir la pose y pasarla por analyze_stance",
             "assert el diagnóstico de categoría `postura` trae veredicto cerrado"),
        Paso("Traducir el mensaje completo, con el prefijo de postura incluido",
             "assert instruccion != mensaje"),
        Paso("Comprobar que la corrección trae su porqué",
             "assert motivo is not None"),
    ],
    resultado_esperado="PASSED en las ocho geometrías: ninguna llega al panel en lenguaje técnico",
)
@pytest.mark.parametrize("nombre, geometria", POSTURAS, ids=[n for n, _ in POSTURAS])
def test_el_veredicto_de_postura_llega_traducido(nombre, geometria):
    diagnostico = _veredicto_de_postura(**geometria)
    mensaje = diagnostico["mensaje"]
    assert diagnostico["correcto"] is not None, (
        f"{nombre}: la geometría no produjo un veredicto cerrado ({mensaje!r}); "
        f"la prueba no estaría probando nada")

    instruccion, motivo = traducir(mensaje)

    assert instruccion != mensaje, (
        f"{nombre}: el panel mostraría el texto técnico {mensaje!r}")
    assert motivo is not None, f"{nombre}: la corrección llegó sin su porqué"


def test_la_traduccion_no_se_queda_con_la_postura_equivocada():
    """
    Quitar el prefijo de postura no puede costar el sentido de la corrección:
    un Zenkutsu mal ejecutado no debe traducirse como si estuviera bien.
    """
    bien, _ = traducir(_veredicto_de_postura(**dict(POSTURAS)["zenkutsu correcto"])["mensaje"])
    mal, _ = traducir(_veredicto_de_postura(**dict(POSTURAS)["zenkutsu incorrecto"])["mensaje"])

    assert bien != mal


def test_el_lado_de_los_golpes_se_sigue_traduciendo():
    """Lo que ya funcionaba —el prefijo de lado del Tsuki— no se rompe."""
    instruccion, motivo = traducir("IZQ - TSUKI: FLEXIONADO")

    assert instruccion == "Extiende más el brazo (izquierdo)"
    assert motivo is not None


def test_un_veredicto_desconocido_con_prefijo_sigue_mostrandose_tal_cual():
    """
    La regla de `traducir` no cambia: si no hay entrada para el veredicto, se
    muestra el texto técnico entero —feo pero cierto— y no un consejo inventado.
    Quitar prefijos no debe convertir «algo desconocido» en «algo conocido».
    """
    mensaje = "TECNICA NUEVA (IZQ): ALGO QUE NADIE TRADUJO"

    assert traducir(mensaje) == (mensaje, None)
