"""
Pruebas unitarias de la resolución de la fuente de video (RF-01).

Verifican la lógica que decide si una fuente es un dispositivo local o una
cámara de red, y cómo se convierte a lo que espera OpenCV. No abren hardware:
`normalizar` y `es_url` son funciones puras, que es justamente la razón de
haberlas separado de la clase `Camera`.
"""
import pytest

from vision.fuentes import CamaraNoDisponible, describir, es_url, normalizar
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@pytest.mark.parametrize("fuente", [
    "http://192.168.1.50:8080/video",
    "https://camara.dojo.local/stream",
    "rtsp://192.168.0.10:554/live",
    "  http://10.0.0.4:4747/video  ",      # con espacios, como llega de un formulario
    "HTTP://192.168.1.50:8080/video",      # mayúsculas
])
def test_reconoce_una_camara_de_red(fuente):
    assert es_url(fuente) is True


@pytest.mark.parametrize("fuente", [0, 1, 2, "0", "2", "", "camara", None])
def test_no_confunde_un_dispositivo_local_con_una_direccion(fuente):
    assert es_url(fuente) is False


@ficha(
    id_caso="TC-AUTO-023",
    nombre="Un índice de cámara escrito como texto se convierte a entero antes de llegar a "
           "OpenCV",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="OpenCV distingue por tipo: con el entero 2 abre la tercera cámara "
                         "del equipo, pero con la cadena \"2\" busca un archivo de video "
                         "llamado \"2\". Como el valor llega desde un formulario de la "
                         "interfaz, siempre viene en texto, y sin la conversión el sistema "
                         "nunca abriría la cámara seleccionada",
    componente="vision/camera.py (normalizar)",
    requisitos="RF-01",
    precondiciones="Ninguna. `normalizar` es una función pura que no abre dispositivos",
    datos_entrada="Cuatro fuentes locales: los enteros 0 y 2, y las cadenas \"0\" y \"2\"",
    pasos=[
        Paso("Invocar `normalizar(entrada)` con cada una de las cuatro fuentes",
             "assert resultado == esperado en los cuatro casos"),
        Paso("Verificar el tipo del valor devuelto",
             "assert isinstance(resultado, int) — nunca una cadena"),
    ],
    resultado_esperado="PASSED. Las direcciones de cámara IP, en cambio, se conservan como "
                       "texto: es el tipo con el que OpenCV las interpreta como flujo de red",
)
@pytest.mark.parametrize("entrada, esperado", [
    (0, 0),
    (2, 2),
    ("0", 0),        # lo que devuelve un formulario de la interfaz
    ("2", 2),
])
def test_los_indices_se_convierten_a_entero(entrada, esperado):
    """
    OpenCV distingue por tipo: un entero abre un dispositivo del sistema y una
    cadena se interpreta como ruta o dirección. Pasarle "2" en vez de 2 haría
    que buscara un archivo llamado "2" en lugar de la tercera cámara.
    """
    resultado = normalizar(entrada)
    assert resultado == esperado
    assert isinstance(resultado, int)


def test_una_url_se_conserva_como_texto_y_sin_espacios():
    assert normalizar("  http://192.168.1.50:8080/video ") == "http://192.168.1.50:8080/video"


@pytest.mark.parametrize("basura", ["camara", "", None, "1.2.3", "índice dos"])
def test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util(basura):
    """
    El error nombra el valor recibido: si el entrenador escribió mal la
    dirección de la cámara IP, el mensaje debe dejarle ver qué se interpretó.
    """
    with pytest.raises(CamaraNoDisponible) as error:
        normalizar(basura)
    assert str(basura) in str(error.value)


def test_la_descripcion_distingue_red_de_dispositivo_local():
    assert "IP" in describir("http://192.168.1.50:8080/video")
    assert "índice 2" in describir(2)
