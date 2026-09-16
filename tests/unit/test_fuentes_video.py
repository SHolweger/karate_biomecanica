"""
Pruebas unitarias de la resolución de la fuente de video (RF-01).

Verifican la lógica que decide si una fuente es un dispositivo local o una
cámara de red, y cómo se convierte a lo que espera OpenCV. No abren hardware:
`normalizar` y `es_url` son funciones puras, que es justamente la razón de
haberlas separado de la clase `Camera`.
"""
import pytest

from vision.fuentes import (CamaraNoDisponible, describir, es_archivo, es_url,
                            normalizar)
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


# ---------------- archivos de video grabados ----------------

@pytest.mark.parametrize("ruta", [
    "sesion.mp4", "grabaciones/kihon.MOV", "/Users/sebastian/tatami.avi",
    "prueba.mkv", "captura.webm", "video.m4v", "clip.mpeg",
])
def test_una_grabacion_se_reconoce_como_archivo(ruta):
    """
    Regresión del 16-sep-2026. Al extraer esta resolución de `camera.py` se
    perdió el soporte de rutas de archivo, y `test_rendimiento.py` —que mide la
    latencia real del sistema contra el RNF-01 y el RF-01— dejó de poder
    ejecutarse sobre una grabación. El fallo pasó inadvertido porque ese script
    no forma parte de la suite.
    """
    assert es_archivo(ruta) is True
    assert normalizar(ruta) == ruta.strip()


@pytest.mark.parametrize("fuente", ["0", "2", "camara", "", "sesion", "notas.txt",
                                    "carpeta.mp4/algo", None])
def test_lo_que_no_es_una_grabacion_no_se_confunde_con_una(fuente):
    """
    El reconocimiento es por extensión y estricto a propósito. Aceptar cualquier
    texto como ruta convertiría un error de escritura en la pantalla de cámara
    en un intento silencioso de abrir un archivo inexistente, con un mensaje que
    apunta al lugar equivocado.
    """
    assert es_archivo(fuente) is False


def test_una_transmision_de_red_con_extension_de_video_sigue_siendo_una_url():
    """
    `http://camara.local/stream.mp4` es una cámara IP, no un archivo. Tratarla
    como archivo produciría un diagnóstico que culpa al disco de un problema de
    red.
    """
    url = "http://camara.dojo.local/stream.mp4"

    assert es_url(url) is True
    assert es_archivo(url) is False
    assert "Cámara IP" in describir(url)


def test_la_descripcion_distingue_una_grabacion_de_una_camara():
    assert "Video grabado" in describir("sesion.mp4")
    assert "Cámara del sistema" in describir(0)


def test_el_mensaje_de_error_menciona_las_tres_formas_validas():
    """Quien se equivoca al escribir una fuente debe ver qué sí se acepta."""
    with pytest.raises(CamaraNoDisponible) as error:
        normalizar("camara del tatami")

    mensaje = str(error.value)
    assert "índice" in mensaje and "IP" in mensaje and "archivo de video" in mensaje
