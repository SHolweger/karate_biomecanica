"""
La articulación que falla, marcada en rojo sobre el video (TC-AUTO-073).

Desde el 18-oct-2026 el veredicto de postura dice qué rodilla corregir. El
prototipo lo enseñaba además sobre el esqueleto, con la articulación en rojo, y
eso es lo que estas pruebas fijan: que se marca la articulación juzgada mal —y
solo esa—, en el sitio donde el analizador la midió.

El riesgo no es estético. Una marca en la rodilla equivocada le diría al alumno
que corrija la pierna que está bien, y una marca sobre un veredicto nulo
inventaría un fallo que nadie midió.
"""
import pytest

from expert_system.analyzer import TechniqueAnalyzer
from gui.panel_vivo import ARTICULACIONES_MARCABLES, articulaciones_con_error
from helpers.fakes import pose_sintetica
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

ANCHO, ALTO = 1000, 1000


def _analizador():
    return TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)


def _de(resultados, categoria):
    return next(r for r in resultados if r["categoria"] == categoria)


@ficha(
    id_caso="TC-AUTO-073",
    nombre="Sobre el video se marca en rojo la articulación juzgada mal, y solo esa",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la marca le dice al alumno qué articulación corregir. En "
                         "la rodilla equivocada le haría corregir la pierna que está "
                         "bien, y sobre un veredicto nulo inventaría un fallo que el "
                         "sistema no midió",
    componente="gui/panel_vivo.py (articulaciones_con_error), "
               "expert_system/analyzer.py (pos_articulacion), "
               "biomechanics/renderer.py (draw_alertas)",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna: pose sintética, sin cámara ni interfaz",
    datos_entrada="Un Zenkutsu con la rodilla delantera fuera de rango y la trasera "
                  "dentro; un Tsuki que se queda corto; un fotograma negro",
    pasos=[
        Paso("Analizar el Zenkutsu y pedir las articulaciones con error",
             "assert solo aparece la rodilla delantera, en el píxel donde se midió"),
        Paso("Ejecutar un Tsuki que cierra el Kime flexionado",
             "assert se marca el codo de ese brazo y no el del otro"),
        Paso("Pasar veredictos nulos y correctos",
             "assert no se marca ninguna articulación"),
        Paso("Dibujar la marca sobre un fotograma negro",
             "assert el anillo queda en rojo alrededor de la articulación"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_en_un_zenkutsu_se_marca_solo_la_rodilla_que_falla():
    # Delantera a 125°: el clasificador la reconoce (< 130) pero su rango es
    # 90–115, así que falla. La trasera, a 175°, está dentro de 165–180.
    resultados = _analizador().analyze_stance(
        pose_sintetica(angulo_rodilla_izq=125, angulo_rodilla_der=175,
                       z_tobillo_izq=-0.3, z_tobillo_der=0.3), ANCHO, ALTO)
    postura = _de(resultados, "postura")
    assert "ZENKUTSU" in postura["mensaje"] and postura["correcto"] is False

    marcadas = articulaciones_con_error([resultados])

    # El número de la rodilla izquierda se escribe 20 px a su derecha: quitado
    # ese desplazamiento, es el píxel donde el analizador midió la rodilla.
    x, y = postura["pos_angulo"]
    assert marcadas == [(x - 20, y)]
    assert _de(resultados, "rodilla_der")["correcto"] is True


def test_en_un_tsuki_corto_se_marca_el_codo_de_ese_brazo():
    analizador = _analizador()
    izq = [50, 75, 100, 125, 150, 130]     # se queda en 150°: FLEXIONADO
    der = [50] * len(izq)                  # en Hikite: sin golpe
    for fotograma, (a_izq, a_der) in enumerate(zip(izq, der)):
        resultados = analizador.analyze_tsuki(
            pose_sintetica(angulo_codo_izq=a_izq, angulo_codo_der=a_der),
            ANCHO, ALTO, fotograma * 33)

    codo = _de(resultados, "codo_izq")
    assert codo["correcto"] is False, codo["mensaje"]
    assert _de(resultados, "codo_der")["correcto"] is None
    x, y = codo["pos_angulo"]
    assert articulaciones_con_error([resultados]) == [(x - 20, y)]


@pytest.mark.parametrize("correcto", [True, None])
def test_lo_correcto_y_lo_no_juzgado_no_se_marcan(correcto):
    diagnosticos = [{"categoria": c, "correcto": correcto, "pos_articulacion": (10, 10)}
                    for c in ARTICULACIONES_MARCABLES]
    assert articulaciones_con_error(diagnosticos) == []


def test_el_veredicto_de_la_postura_entera_no_tine_las_dos_rodillas():
    """
    La entrada `postura` lleva el veredicto de la postura completa. Si con él
    se marcaran las dos rodillas, se escondería cuál de las dos falla.
    """
    postura = {"categoria": "postura", "correcto": False, "pos_articulacion": (5, 5)}
    assert articulaciones_con_error([postura]) == []


def test_una_articulacion_oculta_no_se_marca():
    oculta = {"categoria": "mae_geri_izq", "correcto": False, "pos_articulacion": None}
    assert articulaciones_con_error([oculta]) == []


def test_la_patada_juzgada_mal_marca_la_rodilla():
    patada = {"categoria": "mae_geri_der", "correcto": False, "pos_articulacion": (300, 400)}
    assert articulaciones_con_error([[], [], [patada]]) == [(300, 400)]


def test_el_anillo_se_dibuja_en_rojo_alrededor_de_la_articulacion():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2", reason="OpenCV no está instalado")
    from biomechanics.renderer import SkeletonRenderer

    renderer = SkeletonRenderer()
    fotograma = np.zeros((480, 640, 3), dtype=np.uint8)
    renderer.draw_alertas(fotograma, [(320, 240)])

    radio = max(12, 480 // 40)
    azul, verde, rojo = (int(c) for c in fotograma[240, 320 + radio])
    assert (azul, verde, rojo) == renderer.ROJO_ALERTA
    assert rojo > 200 and verde < 100
    # Lejos de la articulación el fotograma queda intacto.
    assert fotograma[20, 20].tolist() == [0, 0, 0]


def test_sin_errores_el_fotograma_no_se_toca():
    np = pytest.importorskip("numpy")
    pytest.importorskip("cv2", reason="OpenCV no está instalado")
    from biomechanics.renderer import SkeletonRenderer

    fotograma = np.zeros((48, 64, 3), dtype=np.uint8)
    SkeletonRenderer().draw_alertas(fotograma, [])
    assert not fotograma.any()
