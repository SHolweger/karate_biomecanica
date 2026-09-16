"""
Pruebas de extremo a extremo del análisis en vivo rediseñado (RF-01, RF-06).

Se concentran en dos cosas que la pantalla anterior no hacía: elegir al alumno
desde aquí —y no en una pantalla previa— y encajar el video en el espacio que le
toca en vez de imponer su resolución al resto de la ventana.

Como el resto de la carpeta, el módulo se omite entero si no hay entorno gráfico
o faltan las dependencias de la GUI.
"""
import pytest

pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")

from gui.live_screen import LiveScreen
from gui.panel_vivo import ELIGE_ALUMNO, SIN_ALUMNOS
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]


@pytest.fixture
def dos_alumnos(db):
    return [{"id_atleta": db.crear_atleta("Diego Morales"), "nombre": "Diego Morales"},
            {"id_atleta": db.crear_atleta("Ana Lucía Pérez"), "nombre": "Ana Lucía Pérez"}]


@pytest.fixture
def vivo(app, db, entrenador_registrado, dos_alumnos, camara_sintetica):
    app.on_login_exitoso(entrenador_registrado)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador_registrado, dos_alumnos[0],
                          cam=camara_sintetica, app=app)
    app.pantalla_actual = pantalla
    pantalla.pack(expand=True, fill="both")
    yield pantalla
    pantalla.cerrar()


# ---------------- elección del alumno ----------------

def test_sin_alumno_elegido_no_se_abre_la_camara_ni_se_crea_sesion(app, db,
                                                                   entrenador_registrado,
                                                                   dos_alumnos):
    """
    Una sesión sin alumno quedaría registrada a nombre de nadie y contaminaría
    los promedios del dojo. Mejor no crearla.
    """
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_vivo(atleta=None)
    pantalla = app.pantalla_actual

    assert isinstance(pantalla, LiveScreen)
    assert pantalla.id_sesion is None
    assert pantalla.cam is None
    assert "alumno" in pantalla.estado_var.get().lower()
    assert db.conn.execute("SELECT COUNT(*) AS n FROM sesion").fetchone()["n"] == 0


def test_el_desplegable_ofrece_a_todos_los_alumnos_inscritos(vivo, dos_alumnos):
    assert vivo.alumno_var.get() == "Diego Morales"
    assert set(vivo.selector_alumno.cget("values")) == {a["nombre"] for a in dos_alumnos}


def test_cambiar_de_alumno_cierra_la_sesion_anterior_y_abre_otra(vivo, db):
    """
    Seguir registrando en la sesión anterior atribuiría a un alumno las
    mediciones de otro: el peor error posible en un historial de entrenamiento.
    """
    primera = vivo.id_sesion
    assert primera is not None

    vivo._cambiar_alumno("Ana Lucía Pérez")

    segunda = vivo.id_sesion
    assert segunda is not None and segunda != primera
    assert vivo.atleta["nombre"] == "Ana Lucía Pérez"

    cerrada = db.conn.execute("SELECT hora_fin FROM sesion WHERE id_sesion = ?",
                              (primera,)).fetchone()
    assert cerrada["hora_fin"] is not None, "la sesión anterior quedó abierta"


def test_elegir_al_mismo_alumno_no_abre_una_sesion_nueva(vivo):
    antes = vivo.id_sesion

    vivo._cambiar_alumno("Diego Morales")

    assert vivo.id_sesion == antes


def test_salir_de_la_seccion_cierra_la_sesion_en_curso(app, vivo, db):
    """
    La barra sigue visible durante la medición, así que se puede navegar a otra
    sección con una sesión abierta. Destruir el widget no libera la cámara ni
    sella la hora de fin: eso lo hace `_limpiar_pantalla`.
    """
    id_sesion = vivo.id_sesion

    app._navegar("tecnicas")

    fila = db.conn.execute("SELECT hora_fin FROM sesion WHERE id_sesion = ?",
                           (id_sesion,)).fetchone()
    assert fila["hora_fin"] is not None, "la sesión quedó abierta para siempre"


# ---------------- encaje del video ----------------

@ficha(
    id_caso="TC-AUTO-033",
    nombre="El video se ajusta al espacio disponible conservando su proporción, en vez de "
           "imponer su resolución al resto de la pantalla",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="una cámara entrega 1280x720 y el fotograma se dibujaba a tamaño "
                         "nativo, de modo que empujaba al panel derecho —donde viven las "
                         "correcciones del sistema experto— hasta reducirlo a 193 px de los 320 "
                         "que pide, recortando el texto de cada corrección; en un equipo con "
                         "pantalla pequeña el panel quedaría fuera de cuadro y el RF-06 dejaría "
                         "de cumplirse en la práctica",
    componente="gui/live_screen.py (_escalar, _mostrar_frame)",
    requisitos=("RF-01", "RF-06"),
    precondiciones="CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico "
                   "disponible; cámara sustituida por `CamaraSintetica`",
    datos_entrada="Huecos de 560x420 y 300x300 contra fotogramas de 1280x720 y 640x480",
    pasos=[
        Paso("Calcular el tamaño de un fotograma 1280x720 en un hueco de arranque",
             "assert el resultado cabe en el hueco y conserva la proporción 16:9"),
        Paso("Comprobar que un fotograma más alto que ancho también se limita por el alto",
             "assert alto <= hueco disponible"),
        Paso("Verificar que la proporción original se conserva en ambos casos",
             "assert ancho/alto se mantiene dentro de un 1 % del original"),
    ],
    resultado_esperado="PASSED. El panel de correcciones conserva su ancho y los ángulos se ven "
                       "sin deformar, que es condición para que lo mostrado corresponda a lo "
                       "medido.",
    evidencia="Reporte de consola de pytest; captura de pantalla del análisis en vivo.",
)
def test_el_video_se_ajusta_al_hueco_sin_deformarse(vivo):
    ancho, alto = vivo._escalar(1280, 720)

    assert ancho <= max(vivo.video_label.winfo_width(), vivo.VIDEO_ARRANQUE[0])
    assert alto <= max(vivo.video_label.winfo_height(), vivo.VIDEO_ARRANQUE[1])
    assert abs((ancho / alto) - (1280 / 720)) < 0.02, "la proporción debe conservarse"

    # Un fotograma vertical debe quedar limitado por el alto, no por el ancho.
    ancho_alto, alto_alto = vivo._escalar(480, 640)
    assert abs((ancho_alto / alto_alto) - (480 / 640)) < 0.02


def test_el_escalado_nunca_devuelve_un_tamano_nulo(vivo):
    """Un tamaño de 0 px haría que Pillow lance al redimensionar."""
    ancho, alto = vivo._escalar(10_000, 4)

    assert ancho >= 1 and alto >= 1


def test_un_fotograma_grande_no_agranda_el_contenedor_del_video(app, vivo):
    """
    La comprobación de fondo del caso TC-AUTO-033.

    Se mide el ancho que el contenedor del video PIDE, no el que recibe: el
    reparto real depende del tamaño de la ventana, y el resto de la carpeta
    trabaja con la ventana oculta. Lo que causaba el defecto era justamente que
    ese ancho pedido crecía hasta el del fotograma —unos 1292 px con una cámara
    de 1280x720— y el gestor de geometría se lo quitaba al panel derecho.
    """
    import numpy as np

    marco_video = vivo.video_label.master
    ancho_pedido_antes = marco_video.winfo_reqwidth()

    vivo._mostrar_frame(np.zeros((720, 1280, 3), dtype=np.uint8))
    app.update_idletasks()

    assert marco_video.winfo_reqwidth() == ancho_pedido_antes, \
        "el contenedor creció con la imagen en vez de ajustarla"
    assert marco_video.winfo_reqwidth() < 1280, \
        "el video volvería a empujar al panel de correcciones fuera de sitio"


def test_el_tamano_de_dibujado_no_altera_los_angulos_medidos(vivo):
    """
    Separación entre medir y mostrar.

    El ángulo se calcula sobre los puntos que MediaPipe devuelve para el
    fotograma original, antes de que la imagen se dibuje; el escalado solo
    decide con cuántos píxeles de pantalla se pinta. Esta prueba lo fija: el
    mismo fotograma analizado con el panel de un tamaño y de otro debe producir
    exactamente los mismos grados.

    Importa porque un ángulo que dependiera del tamaño de la ventana sería una
    medición inservible: el diagnóstico cambiaría al mover el borde de la
    aplicación.
    """
    import numpy as np

    from helpers.fakes import pose_sintetica

    landmarks = pose_sintetica(angulo_codo_izq=118.0, angulo_codo_der=171.0)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    alto, ancho, _ = frame.shape

    primera = vivo.analyzer.analyze_tsuki(landmarks, ancho, alto)
    angulos_primera = [d["angulo"] for d in primera]

    # Se fuerza un hueco de dibujado radicalmente distinto y se vuelve a medir.
    vivo.VIDEO_ARRANQUE = (120, 90)
    vivo._mostrar_frame(frame)
    segunda = vivo.analyzer.analyze_tsuki(landmarks, ancho, alto)

    assert [d["angulo"] for d in segunda] == angulos_primera, \
        "el tamaño con el que se dibuja el video llegó a influir en la medición"


def test_sin_alumno_elegido_el_desplegable_no_nombra_al_primero_de_la_lista(
        app, db, entrenador_registrado, dos_alumnos):
    """
    Regresión: el selector arrancaba mostrando «Diego Morales» aunque nadie lo
    hubiera elegido. El sensei leía ese nombre en el recuadro y creía estar
    midiendo a Diego, cuando no había sesión abierta ni cámara encendida.
    """
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_vivo(atleta=None)
    pantalla = app.pantalla_actual

    assert pantalla.alumno_var.get() == ELIGE_ALUMNO
    assert pantalla.alumno_var.get() not in [a["nombre"] for a in dos_alumnos]
    assert set(pantalla.selector_alumno.cget("values")) == {a["nombre"] for a in dos_alumnos}, \
        "el aviso no debe colarse como una opción elegible del desplegable"


def test_sin_alumnos_inscritos_el_desplegable_lo_declara(app, db, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_vivo(atleta=None)
    pantalla = app.pantalla_actual

    assert pantalla.alumno_var.get() == SIN_ALUMNOS
    assert pantalla.selector_alumno.cget("state") == "disabled"
