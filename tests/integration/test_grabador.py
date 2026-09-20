"""
Pruebas del grabador de sesión (RF-01, RF-07).

Estas sí necesitan OpenCV y códecs reales, así que viven en integración y se
omiten solas donde no hay. Lo que verifican, además de que el archivo se
escriba, es la propiedad que hace segura la toma de datos en el dojo: que
ningún fallo de grabación se lleve por delante las mediciones.
"""
import numpy as np
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

cv2 = pytest.importorskip("cv2", reason="el grabador necesita OpenCV y sus códecs")

from vision.grabacion import FRAMES_PARA_ESTIMAR          # noqa: E402
from vision.grabador import GrabadorSesion                 # noqa: E402

pytestmark = pytest.mark.integracion

ANCHO, ALTO = 320, 240


def _frame(valor=0):
    """Un fotograma sintético. El contenido no importa; el tamaño sí."""
    return np.full((ALTO, ANCHO, 3), valor % 256, dtype=np.uint8)


def _grabar(directorio, cuantos, intervalo_ms=100):
    grabador = GrabadorSesion(14, "Ana Gómez", directorio=str(directorio))
    for i in range(cuantos):
        grabador.escribir(_frame(i), timestamp_ms=i * intervalo_ms)
    return grabador


@ficha(
    id_caso="TC-AUTO-042",
    nombre="Una sesión analizada deja un archivo de video reproducible con todos sus fotogramas",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "sin la grabación, una ejecución medida en el dojo no se puede volver a analizar; "
        "repetirla no es equivalente porque sería otra ejecución, de otro día"
    ),
    componente="vision/grabador.py (GrabadorSesion)",
    requisitos="RF-01, RF-07",
    precondiciones="OpenCV disponible con al menos un códec de la lista CODECS",
    datos_entrada="30 fotogramas sintéticos de 320x240 separados 100 ms",
    pasos=[
        Paso("Escribir los 30 fotogramas con GrabadorSesion.escribir()",
             "Los primeros 12 se retienen para medir la velocidad real"),
        Paso("Cerrar la grabación", "El archivo queda en disco"),
        Paso("Reabrir el archivo con cv2.VideoCapture y contar los fotogramas",
             "assert se recuperan los 30, ninguno perdido en el tramo de estimación"),
    ],
    resultado_esperado="Un .mp4 legible con los 30 fotogramas y la velocidad medida",
)
def test_una_sesion_deja_un_video_reproducible_con_todos_sus_fotogramas(tmp_path):
    grabador = _grabar(tmp_path, cuantos=30)
    grabador.cerrar()

    ruta = grabador.ruta_si_existe
    assert ruta is not None, "la sesión debió dejar un archivo"

    captura = cv2.VideoCapture(ruta)
    try:
        assert captura.isOpened(), "el archivo escrito debe poder reabrirse"
        leidos = 0
        while True:
            hay, _ = captura.read()
            if not hay:
                break
            leidos += 1
    finally:
        captura.release()

    assert leidos == 30, "los retenidos para estimar la velocidad también deben quedar grabados"


def test_los_fotogramas_retenidos_para_estimar_no_se_pierden(tmp_path):
    """El tramo de estimación es parte de la sesión, no un descarte."""
    grabador = _grabar(tmp_path, cuantos=FRAMES_PARA_ESTIMAR)
    grabador.cerrar()

    assert grabador.frames_escritos == FRAMES_PARA_ESTIMAR


def test_una_sesion_mas_corta_que_el_tramo_de_estimacion_igual_deja_video(tmp_path):
    """
    Cinco fotogramas son poco video, pero un archivo ausente se lee como un
    fallo del sistema y no como una sesión corta.
    """
    grabador = _grabar(tmp_path, cuantos=5)
    grabador.cerrar()

    assert grabador.ruta_si_existe is not None
    assert grabador.frames_escritos == 5


def test_una_sesion_sin_un_solo_fotograma_no_inventa_un_archivo(tmp_path):
    grabador = GrabadorSesion(14, "Ana", directorio=str(tmp_path))
    resumen = grabador.cerrar()

    assert grabador.ruta_si_existe is None
    assert "No se grabó video" in resumen


def test_la_velocidad_escrita_es_la_medida_y_no_la_nominal_de_la_camara(tmp_path):
    """A 100 ms por fotograma el video debe declarar ~10 fps, no 30."""
    grabador = _grabar(tmp_path, cuantos=20, intervalo_ms=100)
    grabador.cerrar()

    captura = cv2.VideoCapture(grabador.ruta_si_existe)
    try:
        fps = captura.get(cv2.CAP_PROP_FPS)
    finally:
        captura.release()

    assert fps == pytest.approx(10.0, abs=0.5)


# ---------------- lo que hace segura la toma de datos ----------------

@ficha(
    id_caso="TC-AUTO-043",
    nombre="Un fallo al escribir el video no interrumpe la sesión de medición",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "se graba sobre el equipo de un dojo, no sobre un servidor vigilado: un disco lleno "
        "o un códec ausente no puede costar las mediciones de toda una tarde"
    ),
    componente="vision/grabador.py (GrabadorSesion.escribir)",
    requisitos="RF-01, RF-07",
    precondiciones="OpenCV disponible",
    datos_entrada="Un escritor que levanta excepción al escribir, tras 12 fotogramas normales",
    pasos=[
        Paso("Grabar hasta que el archivo se abra", "El escritor real queda creado"),
        Paso("Sustituirlo por uno que falla y seguir escribiendo 10 fotogramas",
             "escribir() no levanta"),
        Paso("Consultar el estado", "assert grabando is False y error explica el motivo"),
    ],
    resultado_esperado="La grabación se apaga con su motivo registrado; el bucle sigue corriendo",
)
def test_un_fallo_al_escribir_apaga_la_grabacion_pero_no_levanta(tmp_path):
    grabador = _grabar(tmp_path, cuantos=FRAMES_PARA_ESTIMAR)
    assert grabador.grabando, "precondición: la grabación debía estar activa"

    class EscritorRoto:
        def write(self, frame):
            raise OSError("no space left on device")

        def release(self):
            pass

    grabador._escritor = EscritorRoto()

    for i in range(10):
        grabador.escribir(_frame(i), timestamp_ms=2000 + i * 100)   # no debe levantar

    assert grabador.grabando is False
    assert "no space left" in grabador.error


def test_tras_un_fallo_el_resumen_explica_por_que_no_hay_video(tmp_path):
    """El sensei se entera al terminar la sesión, no cuando vaya a buscar el archivo."""
    grabador = GrabadorSesion(14, "Ana", directorio=str(tmp_path))
    grabador._renunciar("el disco está lleno")

    resumen = grabador.cerrar()

    assert "No se grabó video" in resumen
    assert "el disco está lleno" in resumen


def test_sin_codec_disponible_la_grabacion_se_apaga_con_su_motivo(tmp_path, monkeypatch):
    """No todo OpenCV trae los mismos códecs, y eso no se sabe hasta intentarlo."""
    class EscritorQueNoAbre:
        def isOpened(self):
            return False

        def release(self):
            pass

    monkeypatch.setattr("vision.grabador.cv2.VideoWriter",
                        lambda *a, **k: EscritorQueNoAbre())

    grabador = _grabar(tmp_path, cuantos=FRAMES_PARA_ESTIMAR)

    assert grabador.grabando is False
    assert "códec" in grabador.error
    assert grabador.ruta_si_existe is None


def test_escribir_none_no_rompe_nada(tmp_path):
    """La cámara devuelve None cuando deja de entregar; no es motivo para renunciar."""
    grabador = GrabadorSesion(14, "Ana", directorio=str(tmp_path))

    grabador.escribir(None, timestamp_ms=0)

    assert grabador.grabando is True
    assert grabador.frames_escritos == 0
