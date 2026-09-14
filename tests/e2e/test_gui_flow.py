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
from gui.inicio_screen import InicioScreen
from gui.perfil_screen import PerfilScreen
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]

MODELO_POSE = "pose_landmarker_full.task"


# Las fixtures `app`, `entrenador_registrado` y el guardia de entorno gráfico
# viven en tests/e2e/conftest.py: las comparten todos los módulos de interfaz.


def test_el_primer_arranque_pide_crear_la_cuenta_inicial(app):
    """Base de datos vacía: la pantalla de acceso debe abrir en modo registro."""
    assert isinstance(app.pantalla_actual, LoginScreen)
    assert app.entrenador is None


def test_crear_la_primera_cuenta_lleva_al_panel_de_inicio(app):
    """Flujo de alta inicial completo, disparando el mismo manejador que el botón."""
    login = app.pantalla_actual
    login.nombre_var.set("Sebastian Holweger")
    login.usuario_var.set("sholweger")
    login.correo_var.set("sholweger@dojo.gt")
    login.password_var.set("clave123")

    login._crear_cuenta(rol="principal")

    assert app.entrenador["nombre"] == "Sebastian Holweger"
    assert isinstance(app.pantalla_actual, InicioScreen)


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

        assert isinstance(app.pantalla_actual, InicioScreen)
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


@ficha(
    id_caso="TC-AUTO-013",
    nombre="Al abrir el análisis en vivo con un alumno elegido queda registrada una sesión "
           "abierta a su nombre",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es el flujo principal de uso del sistema",
    componente="gui/ (App, LoginScreen, InicioScreen, LiveScreen)",
    requisitos=["RF-06", "RNF-04"],
    precondiciones="CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico "
                   "disponible; archivo `pose_landmarker_full.task` presente; entrenador "
                   "registrado en la base temporal",
    datos_entrada="Entrenador usuario=\"sensei\", password=\"clave123\"; atleta "
                  "\"Diego Morales\", grado \"5o kyu\"; cámara sustituida por "
                  "`CamaraSintetica` (frames 640×480 generados en memoria)",
    pasos=[
        Paso("Crear la aplicación `App(db)` con la ventana oculta (`withdraw()`)",
             "La pantalla inicial es `LoginScreen`"),
        Paso("Disparar `app.on_login_exitoso(entrenador)`",
             "assert isinstance(app.pantalla_actual, InicioScreen)"),
        Paso("Navegar a `LiveScreen` inyectando la cámara sintética",
             "assert isinstance(app.pantalla_actual, LiveScreen)"),
        Paso("Consultar la sesión creada en la base de datos",
             "assert fila[\"hora_fin\"] is None (sesión abierta mientras se entrena)"),
    ],
    resultado_esperado="PASSED. En entornos sin interfaz gráfica (CI headless) el caso se "
                       "marca SKIPPED de forma controlada, no FAILED",
    evidencia="Reporte de consola de pytest; captura de pantalla manual de la ventana en "
              "ejecución local para el expediente.",
)
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
    assert isinstance(app.pantalla_actual, InicioScreen)

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


@ficha(
    id_caso="TC-AUTO-014",
    nombre="Terminar la sesión cierra el registro en la base de datos, libera la cámara y "
           "regresa a la selección de perfiles",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="si la cámara no se libera, la siguiente sesión no puede abrirla",
    componente="gui/ (App.on_terminar_sesion, LiveScreen)",
    requisitos=["RF-06", "RF-07"],
    precondiciones="Las mismas de TC-AUTO-013, con una `LiveScreen` activa",
    datos_entrada="Instancia de `CamaraSintetica` con bandera `liberada`; atleta "
                  "\"Diego Morales\"",
    pasos=[
        Paso("Abrir `LiveScreen` con la cámara sintética y guardar el `id_sesion`",
             "Sesión abierta en la base de datos"),
        Paso("Disparar `app.on_terminar_sesion()` (el mismo manejador del botón "
             "\"Terminar sesión\")",
             "El método se ejecuta sin excepción"),
        Paso("Verificar el cierre del registro",
             "assert fila[\"hora_fin\"] is not None"),
        Paso("Verificar la liberación del hardware y la navegación",
             "assert camara.liberada is True y assert isinstance(app.pantalla_actual, "
             "InicioScreen)"),
    ],
    resultado_esperado="PASSED. En CI headless se marca SKIPPED de forma controlada",
    evidencia="Reporte de consola de pytest y captura de pantalla manual de la ejecución "
              "local.",
)
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
    assert isinstance(app.pantalla_actual, InicioScreen), "debe volver al panel de inicio"


# --------------------------------------------------------------------------
# Barra lateral: navegación permanente
# --------------------------------------------------------------------------

def test_el_acceso_no_muestra_barra_lateral(app):
    """Antes de autenticarse no hay nada que navegar: la barra estorbaría."""
    assert app.barra is None


def test_tras_autenticarse_aparece_la_barra_con_la_seccion_de_inicio_activa(
        app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)

    assert app.barra is not None
    assert app.barra.seccion_activa == "inicio"


@pytest.mark.parametrize("seccion, nombre_pantalla", [
    ("inicio", "InicioScreen"),
    ("vivo", "LiveScreen"),
    ("historial", "HistorialScreen"),
    ("tecnicas", "TecnicasScreen"),
    ("camara", "CamaraScreen"),
])
def test_cada_seccion_de_la_barra_abre_su_pantalla(app, entrenador_registrado,
                                                   seccion, nombre_pantalla):
    """
    Se dispara el mismo manejador que el botón de la barra, no el constructor
    de la pantalla: lo que se verifica es la navegación, no el widget.
    """
    app.on_login_exitoso(entrenador_registrado)

    app._navegar(seccion)

    assert type(app.pantalla_actual).__name__ == nombre_pantalla
    assert app.barra.seccion_activa == seccion


def test_la_calibracion_se_alcanza_desde_tecnicas_y_no_desde_la_barra(app, entrenador_registrado):
    """
    Recalibrar es algo que se hace SOBRE una técnica, así que se llega desde la
    biblioteca, donde el criterio vigente está a la vista. Como sección suelta
    invitaba a abrir una tabla de diez umbrales sin recordar cuál se quería
    tocar.
    """
    from gui.barra_lateral import SECCIONES

    assert "umbrales" not in [clave for clave, _ in SECCIONES]

    app.on_login_exitoso(entrenador_registrado)
    app._navegar("tecnicas")
    app.pantalla_actual._abrir_umbrales()

    assert type(app.pantalla_actual).__name__ == "UmbralesScreen"
    assert app.barra.seccion_activa == "tecnicas", \
        "la barra debe seguir señalando de dónde se vino"


def test_la_barra_sobrevive_al_cambiar_de_seccion(app, entrenador_registrado):
    """
    Reutilizar la barra en vez de reconstruirla es lo que evita el parpadeo al
    navegar. Si se recreara, cada cambio de sección la destruiría y volvería a
    armarla completa.
    """
    app.on_login_exitoso(entrenador_registrado)
    barra_inicial = app.barra

    app._navegar("tecnicas")
    app._navegar("historial")

    assert app.barra is barra_inicial


def test_el_detalle_de_un_alumno_conserva_marcada_la_seccion_de_historial(
        app, db, entrenador_registrado):
    """
    Bajar al detalle no debe hacer perder de vista dónde se está: alumnos, un
    alumno y una de sus sesiones son la misma sección del sistema.
    """
    atleta = db.crear_atleta("Diego Morales")
    app.on_login_exitoso(entrenador_registrado)

    app.on_abrir_alumno(atleta)

    assert app.barra.seccion_activa == "historial"


def test_cerrar_sesion_de_entrenador_retira_la_barra_y_vuelve_al_acceso(
        app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)

    app._navegar("salir")

    assert app.barra is None, "sin entrenador no debe quedar barra de navegación"
    assert app.entrenador is None
    assert isinstance(app.pantalla_actual, LoginScreen)


def test_un_usuario_repetido_se_explica_en_pantalla_en_vez_de_reventar(app, db):
    """
    Regresión de un fallo real: registrar un usuario ya existente lanzaba
    sqlite3.IntegrityError. La traza salía por la terminal, la ventana no
    mostraba nada y el botón parecía no responder.
    """
    db.crear_entrenador("Sensei Uno", "sensei", None, "clave123")
    login = app.pantalla_actual
    login.nombre_var.set("Sensei Dos")
    login.usuario_var.set("sensei")
    login.password_var.set("otra_clave")

    login._crear_cuenta(rol="sensei")

    assert "ya está registrado" in login.error_var.get()
    assert app.entrenador is None, "no debió avanzar con un usuario ocupado"
    assert isinstance(app.pantalla_actual, LoginScreen)
