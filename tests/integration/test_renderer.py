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
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion

ANCHO, ALTO = 640, 480


@pytest.fixture
def renderer():
    return SkeletonRenderer()


@pytest.fixture
def frame_negro():
    """Lienzo en negro: cualquier píxel distinto de cero es algo que se dibujó."""
    return np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)


@ficha(
    id_caso="TC-AUTO-017",
    nombre="Sin persona detectada, el fotograma se devuelve intacto y no se dibuja ningún "
           "esqueleto",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="dibujar sobre un fotograma sin pose detectada mostraría un "
                         "esqueleto fantasma al alumno; una excepción aquí congela el "
                         "video en plena clase",
    componente="biomechanics/renderer.py (SkeletonRenderer.draw)",
    requisitos="RF-06",
    precondiciones="OpenCV y NumPy instalados; `SkeletonRenderer()` recién construido",
    datos_entrada="Lienzo negro de 640×480×3 (`np.zeros`, dtype uint8) y lista de poses "
                  "igual a `None`",
    pasos=[
        Paso("Construir el lienzo en negro",
             "Cualquier píxel distinto de cero será algo que se dibujó"),
        Paso("Invocar `renderer.draw(frame, None)`", "Retorna sin lanzar excepción"),
        Paso("Verificar que no se copió ni sustituyó el fotograma",
             "assert resultado is frame_negro"),
        Paso("Verificar que no se pintó nada", "assert resultado.sum() == 0"),
    ],
    resultado_esperado="PASSED. Caso complementario: "
                       "test_dibuja_el_esqueleto_cuando_hay_pose comprueba el camino "
                       "positivo",
)
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


@ficha(
    id_caso="TC-AUTO-086",
    nombre="En el análisis en vivo el video lleva el esqueleto y los grados, y los textos de "
           "veredicto quedan solo en el panel",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="el veredicto, la corrección y la técnica reconocida se escribían "
                         "encima del video y tapaban al deportista, cuando el panel de la "
                         "derecha ya los muestra. Quitarlos del todo dejaría a la consola, "
                         "que no tiene panel, sin ninguna retroalimentación",
    componente="biomechanics/renderer.py (draw_diagnostics); gui/live_screen.py",
    requisitos="RF-06",
    precondiciones="OpenCV instalado; el resto no necesita cámara ni pantalla",
    datos_entrada="Un diagnóstico con mensaje y ángulo sobre un fotograma negro",
    pasos=[
        Paso("Dibujar sin mensajes un diagnóstico con ángulo",
             "assert la franja del mensaje sigue negra y el número junto a la articulación sí aparece"),
        Paso("Dibujar sin mensajes un diagnóstico sin ángulo",
             "assert el fotograma queda intacto"),
        Paso("Leer la llamada de la pantalla en vivo",
             "assert pasa con_mensajes=False"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_sin_mensajes_quedan_los_grados_y_no_el_texto(renderer, frame_negro):
    diagnostico = [{"mensaje": "IZQ - TSUKI: EXCELENTE", "color": (0, 255, 0), "y_offset": 50,
                    "angulo": 170.0, "pos_angulo": (300, 300)}]

    renderer.draw_diagnostics(frame_negro, diagnostico, con_mensajes=False)

    assert frame_negro[30:60, :].sum() == 0, "el mensaje se dibujó sobre el video"
    assert frame_negro[270:310, 290:360].sum() > 0, "faltan los grados junto a la articulación"

    otro = np.zeros_like(frame_negro)
    renderer.draw_diagnostics(otro, [{"mensaje": "PIERNAS: OCULTAS/NO VISIBLES", "color": (0, 165, 255),
                                      "y_offset": 130, "angulo": None, "pos_angulo": None}],
                              con_mensajes=False)
    assert otro.sum() == 0


def test_la_pantalla_en_vivo_no_escribe_los_mensajes_sobre_el_video():
    """La costura: la pantalla tiene que pedirlo, o el cambio no llega a verse."""
    import ast
    from pathlib import Path

    fuente = Path(__file__).resolve().parents[2] / "gui" / "live_screen.py"
    llamadas = [nodo for nodo in ast.walk(ast.parse(fuente.read_text(encoding="utf-8")))
                if isinstance(nodo, ast.Call) and getattr(nodo.func, "attr", "") == "draw_diagnostics"]
    assert llamadas, "la pantalla en vivo ya no llama a draw_diagnostics: revisar esta prueba"
    for llamada in llamadas:
        argumentos = {k.arg: k.value for k in llamada.keywords}
        assert isinstance(argumentos.get("con_mensajes"), ast.Constant) \
            and argumentos["con_mensajes"].value is False
