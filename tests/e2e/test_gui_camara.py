"""
Pruebas de extremo a extremo de la pantalla de fuente de video (RF-01).

Cierran el riesgo de puesta en marcha más caro del proyecto: hasta ahora el
índice de cámara estaba escrito en el código y correspondía al equipo de
desarrollo. En cualquier otra máquina el sistema mostraba una ventana en negro
sin explicar la causa.

Las cámaras del sistema se sustituyen por dobles: el objetivo es verificar la
lógica de selección, verificación y persistencia, no el driver de OpenCV.
"""
import pytest

pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")

import numpy as np

from gui import camara_screen
from gui.camara_screen import CLAVE_FUENTE, CamaraScreen, fuente_configurada
from gui.perfil_screen import PerfilScreen
from vision.camera import CamaraNoDisponible
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]


class CamaraDoble:
    """Cámara que entrega un fotograma real de numpy, sin hardware."""

    def __init__(self, fuente, ancho=1280, alto=720):
        self.fuente = fuente
        self._frame = np.zeros((alto, ancho, 3), dtype=np.uint8)
        self.liberada = False

    def get_frame(self):
        return self._frame

    def release(self):
        self.liberada = True


@pytest.fixture
def camaras_simuladas(monkeypatch):
    """Dos cámaras detectadas por el sistema, sin tocar OpenCV."""
    monkeypatch.setattr(camara_screen, "listar_camaras", lambda *a, **k: [
        {"indice": 0, "ancho": 1280, "alto": 720},
        {"indice": 1, "ancho": 640, "alto": 480},
    ])
    monkeypatch.setattr(camara_screen, "Camera", CamaraDoble)


@pytest.fixture
def pantalla_camara(app, entrenador_registrado, camaras_simuladas):
    """Pantalla abierta por la misma vía que el usuario: login y botón de la barra."""
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_camara()
    return app.pantalla_actual


def test_lista_las_camaras_detectadas_en_el_equipo(pantalla_camara):
    assert isinstance(pantalla_camara, CamaraScreen)
    assert [c["indice"] for c in pantalla_camara.disponibles] == [0, 1]


@ficha(
    id_caso="TC-AUTO-022",
    nombre="La fuente de video elegida se verifica antes de guardarse y sobrevive al reinicio "
           "del sistema",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="con el índice de cámara escrito en el código, el sistema fallaba en "
                         "silencio en cualquier equipo distinto al de desarrollo: la ventana "
                         "quedaba en negro sin informar la causa, que es el peor escenario "
                         "posible durante una demostración en vivo",
    componente="gui/camara_screen.py (CamaraScreen) + persistence/database.py (guardar_config)",
    requisitos="RF-01",
    precondiciones="CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico "
                   "disponible; entrenador autenticado; dispositivos de captura sustituidos "
                   "por dobles de prueba",
    datos_entrada="Dos cámaras simuladas (índices 0 y 1); se selecciona el índice 1",
    pasos=[
        Paso("Autenticarse y abrir la pantalla con `_abrir_camara()` (el manejador del botón real)",
             "assert isinstance(app.pantalla_actual, CamaraScreen)"),
        Paso("Seleccionar la cámara de índice 1 y disparar `guardar_seleccion()`",
             "assert guardado is True (la fuente entregó un fotograma verificable)"),
        Paso("Consultar la preferencia almacenada en la base de datos",
             "assert db.leer_config('fuente_video') == '1'"),
        Paso("Resolver la fuente como lo hace la pantalla de análisis al abrirse",
             "assert fuente_configurada(db) == '1'"),
    ],
    resultado_esperado="PASSED. La fuente queda configurada solo después de comprobar que "
                       "entrega imagen, y la pantalla de análisis la reutiliza sin que el "
                       "entrenador vuelva a elegirla",
    evidencia="Reporte de consola de pytest; captura de la pantalla de cámara para el "
              "expediente.",
)
def test_la_fuente_elegida_se_verifica_y_persiste(pantalla_camara, db):
    pantalla_camara.seleccion.set("1")

    assert pantalla_camara.guardar_seleccion() is True
    assert pantalla_camara.error_var.get() == ""
    assert db.leer_config(CLAVE_FUENTE) == "1"
    assert fuente_configurada(db) == "1"


def test_una_camara_que_no_abre_no_se_guarda(pantalla_camara, db, monkeypatch):
    """
    Verificar antes de guardar es la diferencia entre descubrir el problema
    ahora o descubrirlo con el alumno enfrente y la sesión ya iniciada.
    """
    def no_abre(fuente):
        raise CamaraNoDisponible(f"No se pudo abrir la cámara {fuente}.")

    monkeypatch.setattr(camara_screen, "Camera", no_abre)
    pantalla_camara.seleccion.set("1")

    assert pantalla_camara.guardar_seleccion() is False
    assert "No se pudo abrir" in pantalla_camara.error_var.get()
    assert db.leer_config(CLAVE_FUENTE) is None, "no debió guardarse una fuente que falla"


def test_una_camara_que_abre_pero_no_entrega_imagen_se_rechaza(pantalla_camara, db, monkeypatch):
    """
    Caso real en macOS: el dispositivo se abre aunque otra aplicación lo tenga
    tomado, y solo al leer un fotograma se descubre que no entrega nada.
    """
    class CamaraMuda(CamaraDoble):
        def get_frame(self):
            return None

    monkeypatch.setattr(camara_screen, "Camera", CamaraMuda)
    pantalla_camara.seleccion.set("0")

    assert pantalla_camara.guardar_seleccion() is False
    assert "no entregó imagen" in pantalla_camara.error_var.get()
    assert db.leer_config(CLAVE_FUENTE) is None


def test_la_camara_ip_se_guarda_como_direccion_completa(pantalla_camara, db):
    """La vía para conectar un teléfono por la red local del dojo, sin cables."""
    pantalla_camara.seleccion.set("__ip__")
    pantalla_camara.url_var.set("http://192.168.1.50:8080/video")

    assert pantalla_camara.guardar_seleccion() is True
    assert db.leer_config(CLAVE_FUENTE) == "http://192.168.1.50:8080/video"


def test_elegir_camara_ip_sin_escribir_la_direccion_avisa(pantalla_camara, db):
    pantalla_camara.seleccion.set("__ip__")
    pantalla_camara.url_var.set("   ")

    assert pantalla_camara.guardar_seleccion() is False
    assert "dirección" in pantalla_camara.error_var.get()
    assert db.leer_config(CLAVE_FUENTE) is None


def test_avisa_cuando_la_camara_configurada_ya_no_esta_conectada(app, db, entrenador_registrado,
                                                                 camaras_simuladas):
    """
    El equipo del dojo cambia: se desconecta la cámara USB que estaba
    configurada. El sistema debe decirlo al abrir la pantalla, no al fallar.
    """
    db.guardar_config(CLAVE_FUENTE, "4")
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_camara()

    assert "no está disponible" in app.pantalla_actual.error_var.get()


def test_volver_regresa_a_la_seleccion_de_perfiles(app, pantalla_camara):
    pantalla_camara._volver()

    assert isinstance(app.pantalla_actual, PerfilScreen)
