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


# ---------------- calibración del umbral de abstención de la guardia ----------------

from comparar_2d_3d import (UMBRALES_SEPARACION, _separacion_de,
                            analizar_separaciones, guardia_que_explica)
from expert_system.guardia import SEPARACION_MINIMA_EN_CADERAS, pierna_adelantada

IZQ, DER = IZQ_ADELANTE, DER_ADELANTE


@ficha(
    id_caso="TC-AUTO-071",
    nombre="El barrido del umbral de abstención de la guardia cuenta aciertos, "
           "guardias contrarias y abstenciones contra una referencia que no sale de los pies",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="SEPARACION_MINIMA_EN_CADERAS decide cuándo el sistema "
                         "se abstiene de afirmar qué pierna va adelante, y "
                         "equivocarse de guardia es el único defecto conocido que "
                         "corrompe datos: registra un Zenkutsu como Kokutsu con "
                         "veredicto positivo. El valor vigente salió de la "
                         "definición de las posturas y falta contrastarlo contra "
                         "grabaciones reales; esta es la herramienta que lo hace, y "
                         "una cuenta mal hecha fijaría en la tesis un umbral falso",
    componente="comparar_2d_3d.py (analizar_separaciones, guardia_que_explica)",
    requisitos="RF-03",
    precondiciones="Ninguna: opera sobre separaciones y ángulos, sin cámara",
    datos_entrada="Pares (separación con signo, guardia de referencia) escritos a mano "
                  "y las poses sintéticas del catálogo",
    pasos=[
        Paso("Barrer cuatro muestras conocidas con umbrales 0, 0,5 y 1",
             "assert las cuentas de acierta / contraria / abstiene son las calculadas a mano"),
        Paso("Comprobar que la fila vigente decide igual que pierna_adelantada",
             "assert acierta + contraria == fotogramas con guardia decidida"),
        Paso("Deducir la referencia de las rodillas en poses sintéticas",
             "assert coincide con la guardia que deduce el sistema de los pies"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_el_barrido_cuenta_aciertos_contrarias_y_abstenciones():
    muestras = [(0.9, IZQ), (0.3, IZQ), (-0.2, IZQ), (-0.8, DER)]
    filas = {f["umbral"]: f for f in
             analizar_separaciones(muestras, umbrales=(0.0, 0.5, 1.0))["filas"]}

    assert filas[0.0] == {"umbral": 0.0, "acierta": 3, "contraria": 1, "abstiene": 0}
    assert filas[0.5] == {"umbral": 0.5, "acierta": 2, "contraria": 0, "abstiene": 2}
    assert filas[1.0] == {"umbral": 1.0, "acierta": 0, "contraria": 0, "abstiene": 4}


def test_la_contraria_maxima_acota_el_umbral_por_abajo():
    """Por encima de la mayor separación equivocada, no pasa ningún error."""
    muestras = [(0.9, IZQ), (0.3, IZQ), (-0.2, IZQ), (-0.45, IZQ), (-0.8, DER)]
    resultado = analizar_separaciones(muestras, umbrales=(0.44, 0.46))

    assert resultado["contraria_maxima"] == pytest.approx(0.45)
    contrarias = {f["umbral"]: f["contraria"] for f in resultado["filas"]}
    assert contrarias[0.44] == 1
    assert contrarias[0.46] == 0


def test_sin_errores_no_hay_cota():
    resultado = analizar_separaciones([(0.9, IZQ), (-0.7, DER)])
    assert resultado["contraria_maxima"] is None
    assert resultado["correcta"]["mediana"] in (0.7, 0.9)


def test_la_fila_vigente_decide_igual_que_el_sistema():
    """
    El barrido incluye el umbral vigente, y en esa fila decide exactamente lo
    que decide `pierna_adelantada` con su valor por omisión. Si alguien cambia
    la constante, la fila marcada «vigente» la sigue.
    """
    assert SEPARACION_MINIMA_EN_CADERAS in UMBRALES_SEPARACION
    muestras = [(s / 20.0, IZQ if i % 3 else DER)
                for i, s in enumerate(range(-30, 31))]
    fila = next(f for f in analizar_separaciones(muestras)["filas"]
                if f["umbral"] == SEPARACION_MINIMA_EN_CADERAS)
    decididas = sum(1 for s, _ in muestras if pierna_adelantada(s) is not None)

    assert fila["acierta"] + fila["contraria"] == decididas
    assert fila["abstiene"] == len(muestras) - decididas


@pytest.mark.parametrize("nombre, izq, der, z_izq, z_der, esperada",
                         [c for c in CASOS if c[5] in ("zenkutsu_dachi", "kokutsu_dachi")])
def test_la_referencia_de_las_rodillas_coincide_con_la_guardia_del_sistema(
        nombre, izq, der, z_izq, z_der, esperada):
    """
    La referencia del barrido se deduce de las rodillas y la guardia del
    sistema de los pies. Sobre una pose limpia tienen que coincidir; si no, el
    barrido contaría como «contraria» cada fotograma correcto.
    """
    pose = pose_sintetica(angulo_rodilla_izq=izq, angulo_rodilla_der=der,
                          z_tobillo_izq=z_izq, z_tobillo_der=z_der)

    referencia = guardia_que_explica(izq, der, esperada)
    assert referencia is not None, nombre
    assert pierna_adelantada(_separacion_de(pose)) == referencia, nombre


@pytest.mark.parametrize("izq, der, esperado", [
    (172, 172, "zenkutsu_dachi"),   # de pie: no está en la postura
    (140, 140, "zenkutsu_dachi"),   # Kiba
    (145, 175, "zenkutsu_dachi"),   # transición
    (100, 175, "heiko_dachi"),      # postura simétrica: la guardia no importa
    (100, 175, None),
])
def test_fuera_de_la_postura_declarada_no_hay_referencia(izq, der, esperado):
    assert guardia_que_explica(izq, der, esperado) is None


def test_zenkutsu_y_kokutsu_dan_referencias_opuestas_para_la_misma_geometria():
    """
    Son la misma postura con las piernas intercambiadas: por eso la referencia
    exige saber cuál se ejecutó, y por eso la herramienta solo calibra con
    `--esperado`.
    """
    assert guardia_que_explica(100, 175, "zenkutsu_dachi") == IZQ
    assert guardia_que_explica(100, 175, "kokutsu_dachi") == DER
