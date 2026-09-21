"""
Pruebas de la marca de tiempo de la fuente de video (RF-01, RF-05).

Lo que está en juego es la velocidad angular, y con ella el veredicto del Kime
del Mae Geri. La máquina de estados deriva esa velocidad dividiendo el cambio
de ángulo entre el tiempo transcurrido, de modo que un tiempo equivocado no
produce un error visible sino un veredicto plausible y falso.

Con una cámara en vivo, el reloj de pared mide correctamente ese intervalo. Con
una grabación no: el análisis avanza a la velocidad de la estimación de pose
—alrededor de 100 ms por fotograma— mientras el archivo puede contener un
fotograma cada 33 ms. El resultado sería una patada correcta reportada como
falta de explosividad, de forma sistemática y en todas las patadas del video.
"""
import time

import numpy as np
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

cv2 = pytest.importorskip("cv2", reason="la fuente de video necesita OpenCV")

from vision.camera import Camera                          # noqa: E402

pytestmark = pytest.mark.integracion

ANCHO, ALTO, FPS = 320, 240, 30.0


@pytest.fixture
def grabacion(tmp_path):
    """Un video de 30 fotogramas a 30 fps: un segundo exacto de contenido."""
    ruta = str(tmp_path / "ejecucion.mp4")
    escritor = cv2.VideoWriter(ruta, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (ANCHO, ALTO))
    if not escritor.isOpened():
        pytest.skip("sin códec disponible para escribir la grabación de prueba")
    for i in range(30):
        escritor.write(np.full((ALTO, ANCHO, 3), i * 8 % 256, dtype=np.uint8))
    escritor.release()
    return ruta


@ficha(
    id_caso="TC-AUTO-049",
    nombre="El tiempo de una grabación lo dicta el video y no la velocidad a la que se analiza",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "la velocidad angular del Kime se deriva del intervalo entre fotogramas; medirlo con el "
        "reloj de pared sobre una grabación lo infla varias veces y reporta como falta de "
        "explosividad toda patada correcta del video, de forma sistemática"
    ),
    componente="vision/camera.py (Camera.marca_de_tiempo_ms) + vision/fuentes.py",
    requisitos="RF-01, RF-05",
    precondiciones="OpenCV disponible; una grabación de 30 fotogramas a 30 fps",
    datos_entrada="La misma grabación leída dos veces: de corrido y con una pausa de 50 ms "
                  "entre lecturas",
    pasos=[
        Paso("Leer la grabación completa registrando la marca de cada fotograma",
             "Las marcas avanzan a razón de 1000/30 ms"),
        Paso("Repetir la lectura intercalando una pausa artificial entre fotogramas",
             "El reloj de pared avanza mucho más que el video"),
        Paso("Comparar ambas secuencias de marcas",
             "assert son idénticas: la pausa no altera el tiempo del video"),
    ],
    resultado_esperado="Las marcas dependen del contenido y no de la velocidad del análisis",
)
def test_una_pausa_en_el_analisis_no_altera_el_tiempo_de_la_grabacion(grabacion):
    def leer(pausa_s):
        cam = Camera(grabacion)
        marcas = []
        try:
            while True:
                frame = cam.get_frame()
                if frame is None:
                    break
                marcas.append(cam.marca_de_tiempo_ms())
                if pausa_s:
                    time.sleep(pausa_s)
        finally:
            cam.release()
        return marcas

    de_corrido = leer(0)
    con_pausa = leer(0.05)      # 50 ms por fotograma: ~1.5 s de reloj extra

    assert len(de_corrido) > 5, "precondición: la grabación debe entregar fotogramas"
    assert con_pausa == de_corrido, (
        "las marcas de una grabación no pueden depender de cuánto tarda el análisis")


def test_las_marcas_avanzan_al_ritmo_declarado_por_el_video(grabacion):
    cam = Camera(grabacion)
    marcas = []
    try:
        while True:
            if cam.get_frame() is None:
                break
            marcas.append(cam.marca_de_tiempo_ms())
    finally:
        cam.release()

    intervalos = [b - a for a, b in zip(marcas, marcas[1:])]
    esperado = 1000.0 / FPS
    assert all(i == pytest.approx(esperado, abs=1.0) for i in intervalos), \
        f"intervalos observados: {intervalos[:5]}"


def test_la_grabacion_empieza_en_cero(grabacion):
    """El primer fotograma de un archivo es el instante cero de la ejecución."""
    cam = Camera(grabacion)
    try:
        cam.get_frame()
        assert cam.marca_de_tiempo_ms() == pytest.approx(0.0, abs=1.0)
    finally:
        cam.release()


def test_una_fuente_en_vivo_sigue_usando_el_reloj_de_pared():
    """
    Con una cámara real el reloj de pared SÍ mide el intervalo correcto, y es
    la única referencia disponible. El cambio no debe alterar ese caso.
    """
    class CapturaFalsa:
        def isOpened(self):
            return True

        def read(self):
            return True, np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)

        def get(self, prop):
            return 0.0

        def release(self):
            pass

    cam = Camera.__new__(Camera)
    cam.fuente = 0
    cam.espejo = False
    cam.cap = CapturaFalsa()
    cam._es_grabacion = False
    cam._inicio = time.monotonic()
    cam._marca_ms = None

    cam.get_frame()
    primera = cam.marca_de_tiempo_ms()
    time.sleep(0.05)
    cam.get_frame()
    segunda = cam.marca_de_tiempo_ms()

    assert segunda - primera >= 40, "en vivo, el reloj de pared es la referencia correcta"


# ---------------------------------------------------------------------------
# La marca debe crecer siempre (RF-01)
#
# MediaPipe rechaza una marca que no supere a la anterior: levanta
# «Input timestamp must be monotonically increasing» y aborta el análisis. Sobre
# una grabación larga eso no es una hipótesis: basta que el contenedor repita
# una posición —cosa que este backend hace— para que el proceso muera a mitad
# de camino, después de veinte minutos de cómputo.
# ---------------------------------------------------------------------------

class CapturaConPosicionRepetida:
    """
    Contenedor que informa la misma posición dos veces seguidas.

    Reproduce lo que hace el backend real cuando no puede resolver la marca de
    un fotograma: en vez de fallar, repite la última que conoce.
    """

    def __init__(self, posiciones, fps=30.0):
        self._posiciones = list(posiciones)
        self._fps = fps
        self._i = 0

    def isOpened(self):
        return True

    def read(self):
        if self._i >= len(self._posiciones):
            return False, None
        self._i += 1
        return True, np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)

    def get(self, prop):
        if prop == cv2.CAP_PROP_POS_MSEC:
            return self._posiciones[self._i - 1]
        if prop == cv2.CAP_PROP_POS_FRAMES:
            return float(self._i)
        if prop == cv2.CAP_PROP_FPS:
            return self._fps
        return 0.0


def _camara_sobre(captura):
    cam = Camera.__new__(Camera)
    cam.fuente = "grabacion.mp4"
    cam.espejo = False
    cam.cap = captura
    cam._es_grabacion = True
    cam._inicio = 0.0
    cam._marca_ms = None
    return cam


def test_una_posicion_repetida_no_detiene_la_marca(  ):
    """
    El contenedor informa 0, 33.3, 33.3, 66.7. La tercera marca no puede
    quedarse en 33.3: MediaPipe abortaría el análisis completo.
    """
    cam = _camara_sobre(CapturaConPosicionRepetida([0.0, 33.33, 33.33, 66.67]))

    marcas = []
    while cam.get_frame() is not None:
        marcas.append(cam.marca_de_tiempo_ms())

    assert len(marcas) == 4
    assert all(b > a for a, b in zip(marcas, marcas[1:])), \
        f"las marcas deben crecer siempre; se obtuvo {marcas}"


def test_una_posicion_que_retrocede_tampoco_detiene_la_marca():
    """Un contenedor dañado puede informar una posición anterior."""
    cam = _camara_sobre(CapturaConPosicionRepetida([0.0, 100.0, 50.0, 200.0]))

    marcas = []
    while cam.get_frame() is not None:
        marcas.append(cam.marca_de_tiempo_ms())

    assert all(b > a for a, b in zip(marcas, marcas[1:])), \
        f"las marcas deben crecer siempre; se obtuvo {marcas}"


def test_al_rellenar_se_avanza_un_intervalo_de_fotograma_y_no_un_epsilon():
    """
    Cuando la posición no avanza, el intervalo real ES un fotograma. Avanzar
    por un valor arbitrariamente pequeño cumpliría la exigencia de MediaPipe
    pero inflaría la velocidad angular de ese fotograma hasta un valor absurdo.
    """
    cam = _camara_sobre(CapturaConPosicionRepetida([0.0, 33.33, 33.33], fps=30.0))

    marcas = []
    while cam.get_frame() is not None:
        marcas.append(cam.marca_de_tiempo_ms())

    intervalo_rellenado = marcas[2] - marcas[1]
    assert intervalo_rellenado == pytest.approx(1000.0 / 30.0, abs=0.5)
