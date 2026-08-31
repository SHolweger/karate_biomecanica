"""
Pruebas de integración de biomechanics/renderer.py (SkeletonRenderer).

Dibujar sobre el video es difícil de verificar "a ojo" de forma automática,
así que se comprueba lo que sí es objetivo: que el frame se modifique cuando
debe, que NO se modifique cuando no hay nada que dibujar, y que el renderer
tolere los diagnósticos sin ángulo (articulación oculta) sin lanzar excepción
— un fallo aquí congela el video en plena clase.

Requiere OpenCV; si no está instalado, el módulo se omite.
"""
import pytest

np = pytest.importorskip("numpy", reason="NumPy no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")

from biomechanics.renderer import SkeletonRenderer
from helpers.fakes import pose_sintetica

pytestmark = pytest.mark.integracion

ANCHO, ALTO = 640, 480


@pytest.fixture
def renderer():
    return SkeletonRenderer()


@pytest.fixture
def frame_negro():
    """Lienzo en negro: cualquier píxel distinto de cero es algo que se dibujó."""
    return np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)


def test_sin_persona_detectada_el_video_se_devuelve_intacto(renderer, frame_negro):
    """Si MediaPipe no ve a nadie, no debe pintarse ningún esqueleto."""
    resultado = renderer.draw(frame_negro, None)

    assert resultado is frame_negro
    assert resultado.sum() == 0, "se dibujó algo sin haber pose detectada"


def test_dibuja_el_esqueleto_cuando_hay_pose(renderer, frame_negro):
    renderer.draw(frame_negro, [pose_sintetica()])

    assert frame_negro.sum() > 0, "el esqueleto no se dibujó sobre el frame"


def test_el_mapa_anatomico_no_referencia_puntos_inexistentes(renderer):
    """
    Cada conexión debe apuntar a landmarks válidos de MediaPipe (0-32). Un
    índice fuera de rango solo se manifestaría como IndexError en pleno
    entrenamiento, con el alumno frente a la cámara.
    """
    for inicio, fin in renderer.POSE_CONNECTIONS:
        assert 0 <= inicio <= 32 and 0 <= fin <= 32, f"conexión inválida: ({inicio}, {fin})"
        assert inicio != fin, f"conexión de un punto consigo mismo: ({inicio}, {fin})"


def test_dibuja_el_texto_del_diagnostico(renderer, frame_negro):
    diagnostico = [{"mensaje": "TSUKI: EXCELENTE", "color": (0, 255, 0), "y_offset": 50,
                    "angulo": 170.0, "pos_angulo": (300, 200)}]

    renderer.draw_diagnostics(frame_negro, diagnostico)

    assert frame_negro.sum() > 0


def test_un_diagnostico_sin_angulo_no_rompe_el_dibujado(renderer, frame_negro):
    """
    Caso de articulación oculta: llega mensaje pero angulo=None y
    pos_angulo=None. El renderer debe omitir el número, no fallar.
    """
    diagnostico = [{"mensaje": "BRAZO IZQ: OCULTO/NO VISIBLE", "color": (0, 165, 255),
                    "y_offset": 50, "angulo": None, "pos_angulo": None}]

    renderer.draw_diagnostics(frame_negro, diagnostico)  # no debe lanzar excepción

    assert frame_negro.sum() > 0


def test_una_lista_vacia_de_diagnosticos_deja_el_frame_igual(renderer, frame_negro):
    resultado = renderer.draw_diagnostics(frame_negro, [])

    assert resultado.sum() == 0


def test_el_color_del_diagnostico_llega_al_frame(renderer, frame_negro):
    """
    El color es el canal de comunicación con el karateka (verde correcto, rojo
    peligro): debe respetarse el que decidió la regla, no uno fijo.
    """
    renderer.draw_diagnostics(frame_negro, [{"mensaje": "TSUKI: EXCELENTE", "color": (0, 255, 0),
                                             "y_offset": 50, "angulo": None, "pos_angulo": None}])

    azul, verde, rojo = frame_negro[..., 0].sum(), frame_negro[..., 1].sum(), frame_negro[..., 2].sum()
    assert verde > 0 and azul == 0 and rojo == 0, "el texto no se dibujó en el color indicado"
