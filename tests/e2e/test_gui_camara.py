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
from gui.inicio_screen import InicioScreen
from vision.camera import CamaraNoDisponible
from vision.grabacion import CLAVE_GRABAR, grabacion_activada
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
    app._navegar("camara")
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
    app._navegar("camara")

    assert "no está disponible" in app.pantalla_actual.error_var.get()


def test_volver_regresa_al_panel_de_inicio(app, pantalla_camara):
    pantalla_camara._volver()

    assert isinstance(app.pantalla_actual, InicioScreen)


# --------------------------------------------------------------------------
# Regresiones de la pantalla de cámara
# --------------------------------------------------------------------------

def test_abrir_la_pantalla_con_una_camara_ip_ya_configurada_no_inventa_un_error(
        app, db, entrenador_registrado, camaras_simuladas):
    """
    Regresión: con una cámara IP guardada, la pantalla mostraba
    "La cámara configurada (índice __ip__) no está disponible ahora."

    `__ip__` es el valor interno del selector, no un índice de dispositivo. La
    comprobación de "la cámara configurada ya no existe" lo leía después de que
    el bloque de cámara IP hubiera reemplazado la selección, y concluía que un
    dispositivo inexistente se había desconectado.
    """
    db.guardar_config(CLAVE_FUENTE, "http://192.168.1.50:8080/video")
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("camara")
    pantalla = app.pantalla_actual

    assert pantalla.error_var.get() == "", \
        f"se mostró un error inventado: {pantalla.error_var.get()}"
    assert pantalla.url_var.get() == "http://192.168.1.50:8080/video", \
        "la dirección guardada debe precargarse para poder corregirla"
    assert pantalla.fuente_elegida() == "http://192.168.1.50:8080/video"


# ---------------------------------------------------------------------------
# Analizar una grabación (RF-01)
#
# Es la contraparte de grabar la sesión: el video de una tarde en el dojo se
# vuelve a pasar por el mismo encadenamiento, con los umbrales que rijan ese
# día. Sin esta opción, la grabación solo serviría para mirarla.
# ---------------------------------------------------------------------------

@pytest.fixture
def grabacion(tmp_path):
    """Un archivo con extensión de video y contenido, que es lo que se valida."""
    ruta = tmp_path / "20261003_180542_ana_gomez_s14.mp4"
    ruta.write_bytes(b"\x00" * 128)
    return str(ruta)


@ficha(
    id_caso="TC-AUTO-045",
    nombre="Una sesión grabada se puede elegir como fuente y queda configurada para volver a "
           "analizarse",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "si la grabación no se puede volver a analizar desde la interfaz, el video de una "
        "sesión solo sirve para mirarlo, y corregir un umbral seguiría exigiendo repetir la "
        "medición en el dojo"
    ),
    componente="gui/camara_screen.py (CamaraScreen) + vision/fuentes.py (validar_grabacion)",
    requisitos="RF-01",
    precondiciones="CustomTkinter, OpenCV, MediaPipe y Pillow instalados; entorno gráfico; "
                   "un archivo de video existente",
    datos_entrada="Ruta de un .mp4 con contenido",
    pasos=[
        Paso("Elegir la opción de video grabado y escribir la ruta",
             "fuente_elegida() devuelve la ruta"),
        Paso("Pulsar «Usar esta cámara»", "La fuente se verifica y se guarda"),
        Paso("Consultar fuente_configurada()", "assert devuelve la ruta del video"),
    ],
    resultado_esperado="La grabación queda como fuente del próximo análisis",
)
def test_una_grabacion_se_elige_y_queda_configurada(pantalla_camara, db, grabacion):
    pantalla_camara.seleccion.set("__archivo__")
    pantalla_camara.archivo_var.set(grabacion)

    assert pantalla_camara.fuente_elegida() == grabacion
    assert pantalla_camara.guardar_seleccion() is True
    assert fuente_configurada(db) == grabacion


def test_la_grabacion_configurada_se_precarga_al_volver_a_la_pantalla(app, db,
                                                                      entrenador_registrado,
                                                                      camaras_simuladas,
                                                                      grabacion):
    """Configurar la fuente es una tarea de instalación, no algo que repetir cada sesión."""
    db.guardar_config(CLAVE_FUENTE, grabacion)

    app.on_login_exitoso(entrenador_registrado)
    app._navegar("camara")
    pantalla = app.pantalla_actual

    assert pantalla.seleccion.get() == "__archivo__"
    assert pantalla.archivo_var.get() == grabacion


def test_un_archivo_que_no_esta_se_rechaza_antes_de_intentar_abrirlo(pantalla_camara, tmp_path):
    """
    OpenCV responde lo mismo ante un archivo ausente que ante una cámara
    ocupada: "no se pudo abrir". Revisar el archivo primero permite decir cuál
    es el problema real.
    """
    pantalla_camara.seleccion.set("__archivo__")
    pantalla_camara.archivo_var.set(str(tmp_path / "se_borro.mp4"))

    assert pantalla_camara.guardar_seleccion() is False
    assert "se_borro.mp4" in pantalla_camara.error_var.get()
    assert "disco desconectado" in pantalla_camara.error_var.get()


def test_una_grabacion_a_medio_escribir_se_rechaza_nombrando_la_causa(pantalla_camara, tmp_path):
    vacio = tmp_path / "interrumpida.mp4"
    vacio.write_bytes(b"")

    pantalla_camara.seleccion.set("__archivo__")
    pantalla_camara.archivo_var.set(str(vacio))

    assert pantalla_camara.probar_seleccion() is False
    assert "vacío" in pantalla_camara.error_var.get()


def test_sin_archivo_escrito_el_aviso_menciona_las_tres_opciones(pantalla_camara):
    pantalla_camara.seleccion.set("__archivo__")
    pantalla_camara.archivo_var.set("")

    assert pantalla_camara.probar_seleccion() is False
    assert "video" in pantalla_camara.error_var.get()


def test_elegir_una_camara_del_sistema_sigue_funcionando(pantalla_camara, db):
    """La opción nueva no puede haber desplazado a la que ya existía."""
    pantalla_camara.seleccion.set("1")

    assert pantalla_camara.guardar_seleccion() is True
    assert fuente_configurada(db) == "1"


# ---------------------------------------------------------------------------
# Grabar o solo medir (RF-01)
#
# Dos motivos para poder apagarlo, los dos del usuario y no del sistema: el
# consentimiento —en un dojo se entrena con menores— y el disco, que es el
# equipo con el que el instructor da clase.
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-046",
    nombre="El instructor decide si las sesiones se graban, y la decisión persiste entre arranques",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "grabar sin que el usuario lo haya decidido llena su disco sin aviso y, con alumnos "
        "menores de edad, lo pone a filmar sin el consentimiento de sus encargados"
    ),
    componente="gui/camara_screen.py (CamaraScreen) + vision/grabacion.py (grabacion_activada)",
    requisitos="RF-01",
    precondiciones="CustomTkinter, OpenCV, MediaPipe y Pillow instalados; entorno gráfico",
    datos_entrada="El interruptor de grabación, apagado y vuelto a encender",
    pasos=[
        Paso("Apagar el interruptor", "Se guarda en la tabla de configuración al instante"),
        Paso("Volver a abrir la pantalla", "El interruptor sigue apagado"),
        Paso("Encenderlo de nuevo", "assert la configuración vuelve a activar la grabación"),
    ],
    resultado_esperado="La elección del instructor se respeta y sobrevive al reinicio",
)
def test_el_instructor_decide_si_se_graba_y_se_recuerda(app, db, entrenador_registrado,
                                                        camaras_simuladas):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("camara")
    pantalla = app.pantalla_actual

    assert pantalla.grabar_var.get() is True, "viene activada: es lo que hace repetible el análisis"

    pantalla.grabar_var.set(False)
    pantalla._cambiar_grabacion()
    assert grabacion_activada(db.leer_config(CLAVE_GRABAR)) is False

    # Se reabre la pantalla, como en un arranque posterior.
    app._navegar("camara")
    assert app.pantalla_actual.grabar_var.get() is False

    app.pantalla_actual.grabar_var.set(True)
    app.pantalla_actual._cambiar_grabacion()
    assert grabacion_activada(db.leer_config(CLAVE_GRABAR)) is True


def test_el_texto_explica_que_implica_el_estado_no_que_hace_el_boton(app, entrenador_registrado,
                                                                     camaras_simuladas):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("camara")
    pantalla = app.pantalla_actual

    encendido = pantalla.detalle_grabacion_var.get()
    assert "consentimiento" in encendido, "el motivo legal tiene que estar a la vista"
    assert "espacio en disco" in encendido

    pantalla.grabar_var.set(False)
    pantalla._cambiar_grabacion()
    apagado = pantalla.detalle_grabacion_var.get()
    assert "se miden y se registran igual" in apagado, "apagar no puede parecer que anula el análisis"


def test_apagar_la_grabacion_no_toca_la_fuente_de_video(app, db, entrenador_registrado,
                                                        camaras_simuladas):
    """Son dos ajustes independientes: de dónde viene el video y si se guarda."""
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("camara")
    pantalla = app.pantalla_actual
    pantalla.seleccion.set("1")
    pantalla.guardar_seleccion()

    pantalla.grabar_var.set(False)
    pantalla._cambiar_grabacion()

    assert fuente_configurada(db) == "1"
