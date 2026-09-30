"""
Pruebas de extremo a extremo del análisis en vivo rediseñado (RF-01, RF-06).

Se concentran en dos cosas que la pantalla anterior no hacía: elegir al alumno
desde aquí —y no en una pantalla previa— y encajar el video en el espacio que le
toca en vez de imponer su resolución al resto de la ventana.

Como el resto de la carpeta, el módulo se omite entero si no hay entorno gráfico
o faltan las dependencias de la GUI.
"""
import os

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

    # Las marcas de tiempo avanzan porque el análisis es el de una secuencia,
    # no el de un fotograma suelto. Lo que la prueba fija es que los GRADOS no
    # dependen del tamaño de dibujado; que el veredicto dependa del instante es
    # justamente lo correcto desde que el Tsuki se juzga como transición.
    primera = vivo.analyzer.analyze_tsuki(landmarks, ancho, alto, 0)
    angulos_primera = [d["angulo"] for d in primera]

    # Se fuerza un hueco de dibujado radicalmente distinto y se vuelve a medir.
    vivo.VIDEO_ARRANQUE = (120, 90)
    vivo._mostrar_frame(frame)
    segunda = vivo.analyzer.analyze_tsuki(landmarks, ancho, alto, 33)

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


# ---------------------------------------------------------------------------
# Grabación de la sesión (RF-01, RF-07)
#
# El encadenamiento completo: la pantalla en vivo analiza, y al terminar deja un
# archivo de video atado a la sesión que lo produjo. Es lo que permite volver a
# analizar una ejecución del dojo cuando el criterio cambie, en vez de tener que
# repetirla —y repetirla no es equivalente: sería otra ejecución, de otro día.
# ---------------------------------------------------------------------------

@pytest.fixture
def vivo_grabando(app, db, entrenador_registrado, dos_alumnos, camara_sintetica, tmp_path):
    """
    Igual que `vivo`, pero escribiendo en una carpeta temporal.

    La carpeta se configura en la base, no se pasa por argumento: es la misma
    vía por la que el sensei apuntaría la grabación a un disco externo del dojo,
    así que la prueba ejercita el camino real y no uno de laboratorio.
    """
    db.guardar_config("directorio_grabaciones", str(tmp_path))
    app.on_login_exitoso(entrenador_registrado)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador_registrado, dos_alumnos[0],
                          cam=camara_sintetica, app=app)
    app.pantalla_actual = pantalla
    pantalla.pack(expand=True, fill="both")
    yield pantalla, tmp_path
    pantalla.cerrar()


@ficha(
    id_caso="TC-AUTO-044",
    nombre="Una sesión de análisis en vivo deja un video atado a la sesión en la base de datos",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "sin video, una toma de datos en el dojo es irrepetible: si el criterio de evaluación "
        "cambia, la ejecución medida ya no se puede volver a analizar"
    ),
    componente="gui/live_screen.py + vision/grabador.py + persistence/database.py",
    requisitos="RF-01, RF-07",
    precondiciones="Entorno gráfico, CustomTkinter, OpenCV y MediaPipe disponibles; "
                   "cámara sintética inyectada y carpeta de grabaciones temporal",
    datos_entrada="Veinte fotogramas de la cámara sintética",
    pasos=[
        Paso("Avanzar el ciclo de video 20 veces con _actualizar_frame()",
             "El grabador retiene, estima la velocidad y escribe"),
        Paso("Cerrar la pantalla", "Se cierra el archivo y se anota la ruta en la sesión"),
        Paso("Consultar la columna ruta_video de la sesión",
             "assert el archivo existe en disco y la fila lo apunta"),
    ],
    resultado_esperado="Un .mp4 en la carpeta configurada, referenciado por la sesión",
)
def test_una_sesion_en_vivo_deja_video_atado_a_la_sesion(vivo_grabando, db):
    pantalla, carpeta = vivo_grabando
    id_sesion = pantalla.id_sesion
    assert id_sesion is not None, "precondición: la sesión debía abrirse"

    for _ in range(20):
        pantalla._actualizar_frame()

    pantalla.cerrar()

    fila = db.conn.execute("SELECT ruta_video FROM sesion WHERE id_sesion = ?",
                           (id_sesion,)).fetchone()
    assert fila["ruta_video"], "la sesión debe apuntar al video que la registró"

    ruta = fila["ruta_video"]
    assert os.path.exists(ruta), f"el archivo anotado debe existir: {ruta}"
    assert os.path.getsize(ruta) > 0, "un archivo vacío no es una grabación"
    assert ruta.startswith(str(carpeta)), "debe escribir en la carpeta configurada"


def test_el_video_lleva_el_nombre_del_alumno_medido(vivo_grabando):
    """En el dojo, 'sesion_014.mp4' obliga a abrir el sistema para saber de quién es."""
    pantalla, _ = vivo_grabando
    for _ in range(20):
        pantalla._actualizar_frame()
    pantalla.cerrar()

    assert "diego_morales" in pantalla.resumen_grabacion


def test_el_video_grabado_se_puede_volver_a_abrir_como_fuente_de_analisis(vivo_grabando, db):
    """
    Es la razón de ser de la grabación: el archivo tiene que servir de entrada
    al mismo encadenamiento que lo produjo (ver vision/fuentes.py).
    """
    import cv2

    from vision.fuentes import es_archivo

    pantalla, _ = vivo_grabando
    id_sesion = pantalla.id_sesion
    for _ in range(20):
        pantalla._actualizar_frame()
    pantalla.cerrar()

    ruta = db.conn.execute("SELECT ruta_video FROM sesion WHERE id_sesion = ?",
                           (id_sesion,)).fetchone()["ruta_video"]

    assert es_archivo(ruta), "la resolución de fuentes debe reconocerlo como grabación"

    captura = cv2.VideoCapture(ruta)
    try:
        assert captura.isOpened()
        hay, frame = captura.read()
        assert hay and frame is not None, "debe entregar fotogramas al reabrirse"
    finally:
        captura.release()


def test_con_la_grabacion_apagada_la_sesion_se_mide_igual_y_lo_dice(app, db,
                                                                    entrenador_registrado,
                                                                    dos_alumnos,
                                                                    camara_sintetica, tmp_path):
    """
    En un dojo se entrena con menores. Apagar la grabación no puede costar el
    análisis, y el sistema debe declarar que está apagada en vez de callarlo.
    """
    db.guardar_config("directorio_grabaciones", str(tmp_path))
    db.guardar_config("grabar_sesiones", "0")
    app.on_login_exitoso(entrenador_registrado)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador_registrado, dos_alumnos[0],
                          cam=camara_sintetica, app=app)
    pantalla.pack(expand=True, fill="both")
    id_sesion = pantalla.id_sesion

    for _ in range(15):
        pantalla._actualizar_frame()

    assert pantalla.grabador is None
    assert "desactivada" in pantalla.resumen_grabacion

    pantalla.cerrar()

    fila = db.conn.execute("SELECT ruta_video FROM sesion WHERE id_sesion = ?",
                           (id_sesion,)).fetchone()
    assert fila["ruta_video"] is None
    assert not list(tmp_path.glob("*.mp4")), "no debió escribirse ningún video"

    # Que la sesión "se midió igual" se afirma por el ciclo de análisis, no por
    # el contenido de `tecnica_evaluada`: la cámara sintética entrega un
    # fotograma liso, MediaPipe no reconoce a nadie en él y no hay técnica que
    # registrar. Lo que esta prueba puede sostener —y es lo que importa— es que
    # apagar la grabación no interrumpió el ciclo: se consumieron los quince
    # fotogramas y la sesión llegó abierta hasta el cierre.
    # `>=` y no `==`: `_comenzar()` ya analiza un fotograma al montar la
    # pantalla, así que el total incluye ese. Fijar el número exacto ataría la
    # prueba a ese detalle del arranque sin ganar nada; lo que se afirma es que
    # los quince fotogramas que esta prueba impulsó se consumieron.
    assert camara_sintetica.frames_entregados >= 15
    assert id_sesion is not None


def test_la_pantalla_en_vivo_anuncia_si_esta_grabando(vivo_grabando):
    """Nadie debería descubrir que lo estaban filmando después."""
    pantalla, _ = vivo_grabando
    assert pantalla.grabacion_var.get() == "● Grabando"


def test_con_la_grabacion_apagada_la_pantalla_lo_dice_en_vez_de_callarlo(app, db,
                                                                         entrenador_registrado,
                                                                         dos_alumnos,
                                                                         camara_sintetica):
    """
    Una etiqueta ausente se lee como "no me fijé", no como "no se está
    grabando". El estado tiene que estar afirmado en los dos casos.
    """
    db.guardar_config("grabar_sesiones", "0")
    app.on_login_exitoso(entrenador_registrado)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador_registrado, dos_alumnos[0],
                          cam=camara_sintetica, app=app)
    try:
        assert pantalla.grabacion_var.get() == "○ Solo midiendo"
    finally:
        pantalla.cerrar()


# ---------------------------------------------------------------------------
# Analizar una grabación no la vuelve a grabar (RF-01, RF-07)
#
# La grabación existe para conservar la ejecución. Cuando la fuente YA es una
# grabación, la ejecución ya está conservada: volver a escribirla produciría un
# duplicado —diez minutos en Full HD no son poca cosa— y, peor, un segundo
# archivo que compite con el original como evidencia de la misma sesión.
# ---------------------------------------------------------------------------

@pytest.fixture
def grabacion_como_fuente(db, tmp_path, camara_sintetica):
    """
    Un archivo de video configurado como fuente del análisis.

    La cámara se inyecta igual, porque lo que se verifica aquí no es la lectura
    del archivo —eso lo cubre test_marca_de_tiempo.py— sino la decisión de no
    volver a grabarlo.
    """
    ruta = tmp_path / "sesion_del_dojo.mp4"
    ruta.write_bytes(b"\x00" * 256)
    db.guardar_config("fuente_video", str(ruta))
    db.guardar_config("directorio_grabaciones", str(tmp_path / "salida"))
    return str(ruta)


def _montar_vivo(app, db, entrenador, alumno, cam):
    app.on_login_exitoso(entrenador)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador, alumno, cam=cam, app=app)
    pantalla.pack(expand=True, fill="both")
    return pantalla


def test_analizar_una_grabacion_no_produce_un_duplicado(app, db, entrenador_registrado,
                                                        dos_alumnos, camara_sintetica,
                                                        grabacion_como_fuente, tmp_path):
    pantalla = _montar_vivo(app, db, entrenador_registrado, dos_alumnos[0], camara_sintetica)
    try:
        for _ in range(20):
            pantalla._actualizar_frame()
        assert pantalla.grabador is None, "no debe abrirse un grabador sobre una grabación"
    finally:
        pantalla.cerrar()

    assert not list((tmp_path / "salida").glob("*.mp4")) if (tmp_path / "salida").exists() \
        else True, "no debió escribirse ningún video nuevo"


def test_la_sesion_apunta_al_archivo_que_se_analizo(app, db, entrenador_registrado,
                                                    dos_alumnos, camara_sintetica,
                                                    grabacion_como_fuente):
    """
    El video de la sesión es el archivo analizado. Dejar la columna vacía haría
    que el reporte dijera «Sin video» sobre una sesión que nació de uno.
    """
    pantalla = _montar_vivo(app, db, entrenador_registrado, dos_alumnos[0], camara_sintetica)
    id_sesion = pantalla.id_sesion
    try:
        for _ in range(10):
            pantalla._actualizar_frame()
    finally:
        pantalla.cerrar()

    fila = db.conn.execute("SELECT ruta_video FROM sesion WHERE id_sesion = ?",
                           (id_sesion,)).fetchone()
    assert fila["ruta_video"] == grabacion_como_fuente


def test_la_pantalla_dice_que_esta_analizando_una_grabacion(app, db, entrenador_registrado,
                                                            dos_alumnos, camara_sintetica,
                                                            grabacion_como_fuente):
    """
    Ni «Grabando» ni «Solo midiendo» describen lo que ocurre: el estado tiene
    que decir la verdad o el aviso deja de ser informativo.
    """
    pantalla = _montar_vivo(app, db, entrenador_registrado, dos_alumnos[0], camara_sintetica)
    try:
        assert "grabación" in pantalla.grabacion_var.get().lower()
    finally:
        pantalla.cerrar()


def test_el_bucle_no_se_reentra_a_si_mismo(app, db, entrenador_registrado, dos_alumnos,
                                           camara_sintetica, monkeypatch):
    """
    Regresión del 28-sep-2026: RecursionError en la Mac al medir la interfaz.

    Desde que el refresco se reprograma descontando lo ya gastado, el
    temporizador del siguiente fotograma está vencido casi siempre —el trabajo
    de uno supera el intervalo—. CustomTkinter llama a `update_idletasks()` por
    su cuenta al dibujar widgets, y en macOS esa llamada atiende los
    temporizadores vencidos: dibujar una corrección reentraba en el bucle, que
    volvía a dibujar, hasta agotar la pila.

    Aquí se provoca la reentrada a propósito, en el punto donde macOS la
    provocaba: mientras se pinta el panel de correcciones. Sin la guardia esto
    recurre hasta el RecursionError; con ella, la llamada de dentro vuelve en
    el acto y el fotograma se procesa una sola vez.
    """
    app.on_login_exitoso(entrenador_registrado)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador_registrado, dos_alumnos[0],
                          cam=camara_sintetica, app=app)
    app.pantalla_actual = pantalla
    try:
        entradas = []
        original = pantalla._mostrar_frame

        def mostrar_y_reentrar(frame):
            entradas.append(1)
            resultado = original(frame)
            # Lo que macOS hace por su cuenta: `configure` sobre un widget de
            # CustomTkinter acaba en `update_idletasks()`, que allí atiende el
            # temporizador ya vencido del siguiente fotograma.
            pantalla._actualizar_frame()
            return resultado

        monkeypatch.setattr(pantalla, "_mostrar_frame", mostrar_y_reentrar)

        antes = camara_sintetica.frames_entregados
        pantalla._actualizar_frame()

        assert camara_sintetica.frames_entregados - antes == 1, \
            "la reentrada procesó un fotograma extra: la guardia no la detuvo"
        assert len(entradas) == 1, "el fotograma se dibujó más de una vez"
    finally:
        pantalla.cerrar()


# --------------------------------------------------------------------------
# El ritmo del bucle, que es una cuestión de estabilidad y no de rendimiento
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-055",
    nombre="El bucle de análisis reprograma siempre con el intervalo completo y "
           "nunca con una espera mínima",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="entre el 28 y el 30 de septiembre el ciclo descontaba el "
                         "tiempo ya gastado antes de reprogramarse, con la intención "
                         "de recuperar fotogramas por segundo. Como el trabajo de un "
                         "fotograma supera el intervalo, la resta daba siempre el "
                         "mínimo, y el temporizador siguiente quedaba vencido casi "
                         "siempre. En macOS eso produjo dos fallos: la aplicación se "
                         "cerró con RecursionError durante un análisis en vivo, y la "
                         "ventana dejó de responder a los clics porque Tk recibía "
                         "alrededor del 2 % del tiempo para atender al usuario. La "
                         "guardia de reentrada no basta: impide que el bucle se llame "
                         "a sí mismo, no que los ciclos de eventos anidados se "
                         "acumulen",
    componente="gui/live_screen.py (_procesar_fotograma)",
    requisitos="RF-01, RNF-01",
    precondiciones="Entorno gráfico disponible; cámara sustituida por `CamaraSintetica`",
    datos_entrada="Un fotograma procesado por la pantalla de análisis en vivo, con el "
                  "método `after` interceptado para registrar los plazos solicitados",
    pasos=[
        Paso("Interceptar `after` en la pantalla y procesar un fotograma",
             "Se registran los plazos con que el ciclo se reprograma"),
        Paso("Comprobar el plazo de la reprogramación del ciclo",
             "assert es igual a INTERVALO_MS: el ciclo cede a Tk una fracción fija "
             "del tiempo, independientemente de lo que haya costado el fotograma"),
    ],
    resultado_esperado="PASSED en el entorno con interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_el_ciclo_reprograma_con_el_intervalo_completo(vivo):
    pantalla = vivo
    plazos = []
    original = pantalla.after

    def espiar(ms, *args, **kwargs):
        if args and args[0] == pantalla._actualizar_frame:
            plazos.append(ms)
        return original(ms, *args, **kwargs)

    pantalla.after = espiar
    try:
        pantalla._procesar_fotograma()
    finally:
        pantalla.after = original

    assert plazos, "el ciclo no se reprogramó"
    assert plazos[-1] == pantalla.INTERVALO_MS, (
        f"el ciclo se reprogramó con {plazos[-1]} ms en vez de "
        f"{pantalla.INTERVALO_MS}. Descontar el trabajo ya hecho deja el "
        f"temporizador vencido y en macOS eso tumba la aplicación.")
