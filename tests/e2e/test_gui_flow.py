"""
Pruebas de extremo a extremo (E2E) de la interfaz gráfica (CustomTkinter).

Recorren el flujo completo que hace el sensei: login -> selección de perfil ->
análisis en vivo -> cierre de sesión, disparando los mismos manejadores que
disparan los botones reales.

Dos dependencias externas se sustituyen para que la prueba sea determinista:
  * la cámara, por CamaraSintetica (no hay hardware en el servidor de CI);
  * la ventana, que se oculta con withdraw() para no interrumpir al ejecutar
    la suite desde la terminal.

Todo el módulo se omite si no hay entorno gráfico o si faltan las
dependencias de la GUI (es el caso de un contenedor de CI headless): las
pruebas unitarias y de integración sí deben correr siempre.
"""
import os

import pytest

ctk = pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")

from gui.app import App
from gui.live_screen import LiveScreen
from gui.login_screen import LoginScreen
from gui.perfil_screen import PerfilScreen

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]

MODELO_POSE = "pose_landmarker_full.task"


@pytest.fixture(autouse=True)
def requiere_entorno_grafico():
    """Sin servidor de ventanas (CI headless) Tkinter no puede crear la aplicación."""
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        pytest.skip("sin entorno gráfico disponible (DISPLAY no definido)")


@pytest.fixture
def app(db):
    """Aplicación real con la base de datos temporal, con la ventana oculta."""
    aplicacion = App(db=db)
    aplicacion.withdraw()
    yield aplicacion
    if isinstance(aplicacion.pantalla_actual, LiveScreen):
        aplicacion.pantalla_actual.cerrar()
    aplicacion.destroy()


@pytest.fixture
def entrenador_registrado(db):
    db.crear_entrenador("Sensei Ejemplo", "sensei", "sensei@dojo.gt", "clave123", rol="principal")
    return db.autenticar_entrenador("sensei", "clave123")


def test_el_primer_arranque_pide_crear_la_cuenta_inicial(app):
    """Base de datos vacía: la pantalla de acceso debe abrir en modo registro."""
    assert isinstance(app.pantalla_actual, LoginScreen)
    assert app.entrenador is None


def test_crear_la_primera_cuenta_lleva_a_la_seleccion_de_perfiles(app):
    """Flujo de alta inicial completo, disparando el mismo manejador que el botón."""
    login = app.pantalla_actual
    login.nombre_var.set("Sebastian Holweger")
    login.usuario_var.set("sholweger")
    login.correo_var.set("sholweger@dojo.gt")
    login.password_var.set("clave123")

    login._crear_cuenta(rol="principal")

    assert app.entrenador["nombre"] == "Sebastian Holweger"
    assert isinstance(app.pantalla_actual, PerfilScreen)


def test_no_permite_crear_una_cuenta_incompleta(app):
    """Validación de formulario: sin nombre/usuario/contraseña no se avanza."""
    login = app.pantalla_actual
    login.nombre_var.set("")
    login.usuario_var.set("sholweger")
    login.password_var.set("clave123")

    login._crear_cuenta(rol="principal")

    assert app.entrenador is None, "avanzó con el formulario incompleto"
    assert "obligatorios" in login.error_var.get()
    assert isinstance(app.pantalla_actual, LoginScreen)


def test_login_con_credenciales_correctas(db, entrenador_registrado):
    app = App(db=db)
    app.withdraw()
    try:
        login = app.pantalla_actual
        login.usuario_var.set("sensei")
        login.password_var.set("clave123")

        login._intentar_login()

        assert isinstance(app.pantalla_actual, PerfilScreen)
        assert app.entrenador["usuario"] == "sensei"
    finally:
        app.destroy()


def test_login_con_credenciales_incorrectas_muestra_error(db, entrenador_registrado):
    """El acceso denegado debe informarse en pantalla y NO avanzar."""
    app = App(db=db)
    app.withdraw()
    try:
        login = app.pantalla_actual
        login.usuario_var.set("sensei")
        login.password_var.set("clave_equivocada")

        login._intentar_login()

        assert isinstance(app.pantalla_actual, LoginScreen)
        assert app.entrenador is None
        assert "incorrect" in login.error_var.get().lower()
    finally:
        app.destroy()


@pytest.mark.skipif(not os.path.exists(MODELO_POSE),
                    reason=f"falta el modelo de pose {MODELO_POSE}")
def test_elegir_un_perfil_abre_la_sesion_de_analisis(app, db, entrenador_registrado, camara_sintetica):
    """
    Al entrar a la pantalla en vivo debe quedar abierta una sesión en la base
    de datos: es lo que después liga cada medición con el alumno.
    """
    atleta = {"id_atleta": db.crear_atleta("Diego Morales", grado_cinturon="5o kyu"),
              "nombre": "Diego Morales"}
    app.on_login_exitoso(entrenador_registrado)
    assert isinstance(app.pantalla_actual, PerfilScreen)

    app.atleta = atleta
    app._mostrar(LiveScreen(app, db, entrenador_registrado, atleta, cam=camara_sintetica))

    assert isinstance(app.pantalla_actual, LiveScreen)
    fila = db.conn.execute("SELECT * FROM sesion WHERE id_sesion = ?",
                           (app.pantalla_actual.id_sesion,)).fetchone()
    assert fila["hora_fin"] is None, "la sesión debe quedar abierta mientras se entrena"


@pytest.mark.skipif(not os.path.exists(MODELO_POSE),
                    reason=f"falta el modelo de pose {MODELO_POSE}")
def test_el_video_se_embebe_en_la_ventana(app, db, entrenador_registrado, camara_sintetica):
    """
    Pipeline visual completo con un frame sintético: cámara -> MediaPipe ->
    renderer -> imagen de CustomTkinter dentro de la ventana.
    """
    atleta = {"id_atleta": db.crear_atleta("Diego Morales"), "nombre": "Diego Morales"}
    live = LiveScreen(app, db, entrenador_registrado, atleta, cam=camara_sintetica)
    app._mostrar(live)

    live._actualizar_frame()  # un refresco manual, sin esperar el temporizador de Tkinter

    assert camara_sintetica.frames_entregados >= 1
    assert live.video_label.image is not None, "el frame no llegó a la ventana"


@pytest.mark.skipif(not os.path.exists(MODELO_POSE),
                    reason=f"falta el modelo de pose {MODELO_POSE}")
def test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara(app, db, entrenador_registrado,
                                                                  camara_sintetica):
    """
    Criterio de salida del caso de uso: al terminar, la sesión queda cerrada en
    la base de datos y el hardware liberado. Si la cámara no se libera, la
    siguiente sesión no puede abrirla.
    """
    atleta = {"id_atleta": db.crear_atleta("Diego Morales"), "nombre": "Diego Morales"}

    # Se recorre el inicio del flujo real: en la aplicación no se puede llegar a
    # LiveScreen sin autenticarse, y es on_login_exitoso quien deja registrado
    # al entrenador de la sesión. Construir la pantalla en vivo sin ese paso
    # dejaba a la App en un estado que el usuario nunca puede producir.
    app.on_login_exitoso(entrenador_registrado)

    live = LiveScreen(app, db, entrenador_registrado, atleta, cam=camara_sintetica)
    app._mostrar(live)
    id_sesion = live.id_sesion

    app.on_terminar_sesion()

    fila = db.conn.execute("SELECT hora_fin FROM sesion WHERE id_sesion = ?", (id_sesion,)).fetchone()
    assert fila["hora_fin"] is not None, "no se registró la hora de fin"
    assert camara_sintetica.liberada is True, "la cámara quedó ocupada"
    assert isinstance(app.pantalla_actual, PerfilScreen), "debe volver a la selección de perfiles"
