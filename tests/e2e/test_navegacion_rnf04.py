"""
Auditoría del RNF-04: el ciclo de uso en tres pulsaciones o menos.

`gui/navegacion.py` declara, para cada tarea principal, qué controles hay que
pulsar partiendo del panel de inicio. Las pruebas unitarias comprueban que
ninguna declaración pasa de tres pasos; lo que se comprueba aquí es que esa
declaración corresponde con la aplicación real.

La diferencia importa. Una prueba que llame a `app.on_abrir_reporte(id)` verifica
que la pantalla se construye, no que el sensei pueda llegar a ella: pasaría
igual si el botón no existiera. Aquí se recorre cada ruta **pulsando los widgets
que la ventana dibuja**, buscándolos por su etiqueta en el árbol de la
aplicación. Si alguien renombra un botón, intercala una pantalla intermedia o
mueve una acción a otro menú, el control deja de encontrarse donde la ruta lo
declara y la prueba falla señalando el paso exacto.

Lo que se sustituye por dobles es el hardware —la cámara y la enumeración de
dispositivos—, nunca la navegación: esa se ejerce tal cual.
"""
import os
import pathlib

import pytest

ctk = pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")
pytest.importorskip("matplotlib", reason="Matplotlib no está instalado")

import numpy as np

from gui import camara_screen, live_screen, navegacion
from gui.navegacion import MAXIMO_PULSACIONES, RUTAS
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]

MODELO_POSE = "pose_landmarker_full.task"


# --------------------------------------------------------------------------
# Pulsar controles reales
# --------------------------------------------------------------------------

def _descendientes(widget):
    """Todos los widgets bajo `widget`, en el orden en que se dibujaron."""
    for hijo in widget.winfo_children():
        yield hijo
        yield from _descendientes(hijo)


def _unico(candidatos, descripcion, raiz):
    """
    El primer control que coincide, o un fallo que dice qué había disponible.

    Se toma el primero y no se exige unicidad porque varias filas repiten la
    misma etiqueta —un «Ver perfil» por alumno— y quien usa el sistema pulsa
    uno cualquiera de ellos. Lo que la prueba verifica es que el control exista
    en ese punto del recorrido.
    """
    if candidatos:
        return candidatos[0]

    visibles = sorted({w.cget("text") for w in _descendientes(raiz)
                       if isinstance(w, ctk.CTkButton) and w.cget("text")})
    raise AssertionError(
        f"no se encontró {descripcion} en la pantalla actual. "
        f"Botones disponibles: {visibles}")


def _boton(raiz, etiqueta):
    return _unico([w for w in _descendientes(raiz)
                   if isinstance(w, ctk.CTkButton) and w.cget("text") == etiqueta],
                  f"el botón «{etiqueta}»", raiz)


def _desplegable(raiz, valor):
    return _unico([w for w in _descendientes(raiz)
                   if isinstance(w, ctk.CTkOptionMenu) and valor in w.cget("values")],
                  f"un desplegable con la opción «{valor}»", raiz)


def _radio(raiz, valor):
    return _unico([w for w in _descendientes(raiz)
                   if isinstance(w, ctk.CTkRadioButton) and str(w.cget("value")) == valor],
                  f"una casilla de selección con el valor «{valor}»", raiz)


def _tarjeta(raiz, etiqueta):
    """Un marco pulsable que contiene una etiqueta con ese texto."""
    def es_tarjeta(w):
        if not isinstance(w, ctk.CTkFrame):
            return False
        # CustomTkinter enruta `bind` al lienzo interno del widget (ver
        # CTkFrame.bind), así que es ahí donde queda registrada la respuesta al
        # clic y donde hay que preguntar si el marco es pulsable.
        if "<Button-1>" not in w._canvas.bind():
            return False
        return any(isinstance(h, ctk.CTkLabel) and h.cget("text") == etiqueta
                   for h in w.winfo_children())

    return _unico([w for w in _descendientes(raiz) if es_tarjeta(w)],
                  f"una tarjeta pulsable de «{etiqueta}»", raiz)


def _pulsar_tarjeta(tarjeta):
    """
    Clic sobre un marco que responde a `<Button-1>`.

    Tkinter descarta los eventos de ratón dirigidos a una ventana retirada, y la
    ventana de las pruebas lo está para no interrumpir a quien corre la suite.
    Se la devuelve al gestor de ventanas transparente y fuera de la pantalla el
    tiempo mínimo para que el evento se entregue: así el clic es real y sigue
    sin verse nada.

    `when="now"` entrega el evento al manejador en el acto, sin pasar por la
    cola. Es lo que permite no llamar nunca a `update()` — ver la advertencia
    de `_asentar`.
    """
    ventana = tarjeta.winfo_toplevel()
    oculta = ventana.state() == "withdrawn"
    if oculta:
        ventana.wm_attributes("-alpha", 0.0)
        ventana.geometry("+4000+4000")
        ventana.deiconify()
    try:
        _asentar(ventana)
        tarjeta._canvas.event_generate("<Button-1>", x=2, y=2, when="now")
    finally:
        if oculta:
            ventana.withdraw()
            ventana.wm_attributes("-alpha", 1.0)


def _asentar(widget):
    """
    Deja que Tk termine de colocar lo que se acaba de crear.

    **Nunca `update()`.** El análisis en vivo se refresca con `after(15 ms)` y
    cada fotograma cuesta unos 100 ms con MediaPipe real: cuando el manejador
    termina, el siguiente temporizador ya venció. `update()` procesa eventos
    hasta vaciar la cola, y esa cola no se vacía nunca —cada vuelta programa
    otra ya vencida—, de modo que el recorrido se cuelga en la ruta «medir».
    Ocurrió en la máquina de desarrollo el 18-sep-2026; en Linux la misma
    prueba pasaba, así que el fallo depende del sistema y no se puede confiar en
    haberlo visto pasar una vez.

    `update_idletasks` hace lo único que este recorrido necesita —geometría y
    redibujado— y no ejecuta temporizadores, así que el ciclo del video no
    avanza mientras se navega. Que no avance es correcto: lo que se audita es la
    navegación, no el video.
    """
    widget.update_idletasks()


def pulsar(app, paso, sustituciones):
    """Ejecuta un paso de una ruta sobre la aplicación viva."""
    etiqueta = sustituciones.get(paso.etiqueta, paso.etiqueta)

    if paso.control == "boton":
        _boton(app, etiqueta).invoke()
    elif paso.control == "opcion":
        # Es el mismo callback que dispara el desplegable de CustomTkinter al
        # elegir un valor: fija la opción y avisa a la pantalla.
        _desplegable(app, etiqueta)._dropdown_callback(etiqueta)
    elif paso.control == "radio":
        _radio(app, etiqueta).invoke()
    elif paso.control == "tarjeta":
        _pulsar_tarjeta(_tarjeta(app, etiqueta))
    else:  # pragma: no cover - lo impide la prueba unitaria del mapa
        raise AssertionError(f"tipo de control desconocido: {paso.control}")

    _asentar(app)
    return etiqueta


def recorrer(app, ruta, sustituciones, tecleos=None):
    """
    Recorre una ruta pulsando sus controles y devuelve cuántos se pulsaron.

    `tecleos` asocia el número de pulsaciones ya dadas con lo que el sensei
    escribe en ese momento —el nombre del alumno, su contraseña, un umbral—.
    Escribir no cuenta como pulsación: el RNF-04 mide profundidad de
    navegación, no cuántas teclas hay que tocar.
    """
    tecleos = tecleos or {}
    dados = 0
    for paso in ruta.pasos:
        pulsar(app, paso, sustituciones)
        dados += 1
        if dados in tecleos:
            tecleos[dados](app)
            _asentar(app)
    return dados


# --------------------------------------------------------------------------
# Andamiaje
# --------------------------------------------------------------------------

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


@pytest.fixture(autouse=True)
def taller(tmp_path, monkeypatch):
    """
    Carpeta de trabajo temporal.

    La ruta «Generar la gráfica de evolución» escribe un PNG en `evidencias/`;
    sin esto cada corrida dejaría archivos sueltos en el repositorio. El modelo
    de pose se enlaza dentro porque la pantalla en vivo lo abre por ruta
    relativa.
    """
    modelo = pathlib.Path(MODELO_POSE).resolve()
    if modelo.exists():
        (tmp_path / MODELO_POSE).symlink_to(modelo)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def hardware_simulado(monkeypatch):
    """Una cámara detectada por el sistema y una cámara que entrega imagen."""
    monkeypatch.setattr(camara_screen, "listar_camaras", lambda *a, **k: [
        {"indice": 0, "ancho": 1280, "alto": 720, "nombre": "FaceTime HD Camera"},
    ])
    monkeypatch.setattr(camara_screen, "Camera", CamaraDoble)
    monkeypatch.setattr(live_screen, "Camera", CamaraDoble)


@pytest.fixture
def dojo(db, entrenador_registrado):
    """Un alumno con una sesión cerrada: el estado mínimo para recorrerlo todo."""
    diego = db.crear_atleta("Diego Morales", grado_cinturon="5o kyu")
    sesion = db.iniciar_sesion(diego, entrenador_registrado["id_entrenador"])
    db.guardar_medicion(sesion, "tsuki", 168.0, "TSUKI: EXCELENTE", 1000, correcto=True)
    db.guardar_medicion(sesion, "tsuki", 179.0, "TSUKI: HIPEREXTENDIDO (Peligro)", 2000,
                        correcto=False)
    db.cerrar_sesion(sesion)
    return {"atleta": diego, "sesion": sesion, "nombre": "Diego Morales"}


@pytest.fixture
def sensei_en_el_sistema(app, entrenador_registrado, dojo, hardware_simulado):
    """
    Aplicación en el punto de partida del RNF-04: sensei autenticado, panel de
    inicio a la vista. Es desde aquí que se cuentan las pulsaciones.
    """
    app.on_login_exitoso(entrenador_registrado)
    assert type(app.pantalla_actual).__name__ == navegacion.ORIGEN
    return app


@pytest.fixture
def sustituciones(entrenador_registrado, dojo):
    """Las etiquetas que dependen de los datos del dojo, con su valor real."""
    return {
        "{alumno}": dojo["nombre"],
        "{sensei}": entrenador_registrado["nombre"],
        "{camara}": "0",
        "{cambiar perfil}": navegacion.etiqueta_cambiar_perfil(
            entrenador_registrado.get("rol")),
    }


def _escribir_nombre_del_alumno(app):
    app.pantalla_actual.campos["nombre"].set("Ana Lopez")


def _escribir_la_contrasena(app):
    app.pantalla_actual.password_var.set("clave123")


def _cambiar_un_umbral(app):
    """Baja un grado el mínimo vigente, para que haya algo que guardar."""
    campo = app.pantalla_actual.campos[("tsuki", "codo")]["min"]
    campo.set(str(float(campo.get().replace(",", ".")) - 1))


# Lo que el sensei escribe durante el recorrido, por ruta y por número de
# pulsaciones ya dadas.
TECLEOS = {
    "inscribir": {2: _escribir_nombre_del_alumno},
    "calibrar": {2: _cambiar_un_umbral},
    "sensei": {2: _escribir_la_contrasena},
}


# --------------------------------------------------------------------------
# La auditoría
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-038",
    nombre="Cada tarea principal se completa pulsando los controles reales de la interfaz, "
           "en no más de tres pulsaciones desde el panel de inicio",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="verifica el RNF-04 sobre la interfaz construida y no sobre una "
                         "declaración: una pantalla intermedia o un botón renombrado rompen "
                         "el recorrido y quedan a la vista",
    componente="gui/ (App, BarraLateral y las nueve pantallas), gui/navegacion.py",
    requisitos="RNF-04",
    precondiciones="CustomTkinter, OpenCV, MediaPipe, Pillow y Matplotlib instalados; entorno "
                   "gráfico disponible; sensei autenticado; un alumno con una sesión cerrada "
                   "en la base temporal",
    datos_entrada="Las nueve rutas de `gui.navegacion.RUTAS`; sensei \"Sensei Ejemplo\" "
                  "(clave123, rol principal); alumno \"Diego Morales\" con 2 evaluaciones "
                  "cerradas; cámara y enumeración de dispositivos sustituidas por dobles",
    pasos=[
        Paso("Situar la aplicación en el panel de inicio con el sensei autenticado",
             "assert la pantalla actual es `InicioScreen`"),
        Paso("Para cada ruta, buscar en el árbol de widgets el control que declara cada paso "
             "y activarlo (botón, desplegable, casilla o tarjeta)",
             "Cada control existe en ese punto del recorrido; si no, el fallo nombra el "
             "control buscado y lista los botones disponibles"),
        Paso("Contar las pulsaciones dadas",
             "assert pulsaciones <= 3"),
        Paso("Comprobar dónde terminó el recorrido",
             "assert la pantalla actual es la que la ruta declara como destino"),
    ],
    resultado_esperado="PASSED para las nueve rutas. En entornos sin interfaz gráfica (CI "
                       "headless) el caso se marca SKIPPED de forma controlada, no FAILED",
    evidencia="Reporte de consola de pytest, con una línea por tarea auditada.",
)
@pytest.mark.parametrize("ruta", RUTAS, ids=[r.clave for r in RUTAS])
def test_cada_tarea_principal_se_completa_en_tres_pulsaciones(sensei_en_el_sistema,
                                                              sustituciones, ruta):
    if ruta.clave == "medir" and not os.path.exists(MODELO_POSE):
        pytest.skip(f"falta el modelo de pose {MODELO_POSE}")

    app = sensei_en_el_sistema

    dadas = recorrer(app, ruta, sustituciones, TECLEOS.get(ruta.clave))

    assert dadas <= MAXIMO_PULSACIONES, \
        f"«{ruta.tarea}» cuesta {dadas} pulsaciones y el RNF-04 admite {MAXIMO_PULSACIONES}"
    assert type(app.pantalla_actual).__name__ == ruta.destino, \
        f"«{ruta.tarea}» terminó en {type(app.pantalla_actual).__name__} y no en {ruta.destino}"


# --------------------------------------------------------------------------
# Que cada recorrido haya hecho su trabajo, y no solo llegado
# --------------------------------------------------------------------------

def test_inscribir_un_alumno_lo_deja_registrado(sensei_en_el_sistema, sustituciones, db):
    """Tres pulsaciones y el alumno queda en la base, no solo el formulario abierto."""
    app = sensei_en_el_sistema

    recorrer(app, navegacion.ruta("inscribir"), sustituciones, TECLEOS["inscribir"])

    assert "Ana Lopez" in [a["nombre"] for a in db.listar_atletas()]


def test_recalibrar_deja_una_version_nueva_del_umbral(sensei_en_el_sistema, sustituciones, db):
    """
    El recorrido completo tiene que producir el efecto del RF-08: una versión
    nueva vigente, firmada por el sensei, sin borrar la anterior.
    """
    app = sensei_en_el_sistema
    antes = db.cargar_umbrales_vigentes()[("tsuki", "codo")]

    recorrer(app, navegacion.ruta("calibrar"), sustituciones, TECLEOS["calibrar"])

    despues = db.cargar_umbrales_vigentes()[("tsuki", "codo")]
    assert despues["valor_min"] == antes["valor_min"] - 1
    assert despues["id_umbral"] != antes["id_umbral"], "recalibrar debe versionar, no sobrescribir"


def test_medir_abre_una_sesion_a_nombre_del_alumno_elegido(sensei_en_el_sistema,
                                                           sustituciones, db, dojo):
    """Dos pulsaciones: iniciar el análisis y elegir a quién se mide."""
    if not os.path.exists(MODELO_POSE):
        pytest.skip(f"falta el modelo de pose {MODELO_POSE}")
    app = sensei_en_el_sistema

    recorrer(app, navegacion.ruta("medir"), sustituciones)

    fila = db.conn.execute("SELECT id_atleta, hora_fin FROM sesion WHERE id_sesion = ?",
                           (app.pantalla_actual.id_sesion,)).fetchone()
    assert fila["id_atleta"] == dojo["atleta"]
    assert fila["hora_fin"] is None, "la sesión debe quedar abierta mientras se entrena"


def test_cambiar_la_camara_la_deja_configurada(sensei_en_el_sistema, sustituciones, db):
    app = sensei_en_el_sistema

    recorrer(app, navegacion.ruta("camara"), sustituciones)

    assert db.leer_config(camara_screen.CLAVE_FUENTE) == "0"


def test_cambiar_de_sensei_exige_la_contrasena(sensei_en_el_sistema, sustituciones):
    """
    La tercera pulsación es «Entrar», no la tarjeta: elegir un perfil no da
    acceso. Sin contraseña el recorrido no llega al panel de inicio y se queda
    en la selección, que es exactamente lo que debe pasar.
    """
    app = sensei_en_el_sistema
    ruta = navegacion.ruta("sensei")

    recorrer(app, ruta, sustituciones)  # sin el tecleo de la contraseña

    assert type(app.pantalla_actual).__name__ == "PerfilScreen"
    assert "incorrect" in app.pantalla_actual.error_var.get().lower()


# --------------------------------------------------------------------------
# El recorrido detecta lo que debe detectar
# --------------------------------------------------------------------------

# Tope de vueltas del ciclo de video antes de darlo por desbocado. Basta con que
# sea mayor que 1 —la única vuelta legítima— y lo bastante pequeño para que la
# prueba falle en segundos en vez de quedarse colgada.
TOPE_VUELTAS = 5


def test_el_recorrido_no_deja_correr_el_ciclo_del_video(sensei_en_el_sistema, sustituciones,
                                                        monkeypatch):
    """
    Regresión del 18-sep-2026: la suite se quedaba colgada en la ruta «medir».

    El recorrido llamaba a `app.update()` tras cada pulsación. El análisis en
    vivo se refresca con `after(15 ms)` y cada fotograma cuesta unos 100 ms con
    MediaPipe real, así que al terminar un fotograma el siguiente temporizador ya
    había vencido: `update()` procesaba eventos hasta vaciar una cola que se
    rellenaba sola, y no volvía nunca.

    Aquí se cuentan las vueltas del ciclo durante el recorrido. La legítima es
    una —la que `_comenzar` dispara en el acto—; las demás solo pueden venir de
    que alguien haya vuelto a ejecutar temporizadores dentro del recorrido.

    El intervalo de refresco se pone en cero a propósito. Con el intervalo real
    el temporizador todavía no ha vencido cuando el recorrido sigue adelante, y
    si la máquina es lo bastante rápida el defecto no se manifiesta —que es
    justo por qué esta prueba pasaba en Linux mientras la suite se colgaba en la
    Mac—. En cero, el siguiente refresco está vencido siempre, en cualquier
    sistema: es la misma condición que produce un fotograma más lento que el
    intervalo, provocada a voluntad.

    El tope corta el ciclo en vez de dejar que la prueba se cuelgue: un fallo se
    lee, un cuelgue hay que diagnosticarlo.
    """
    if not os.path.exists(MODELO_POSE):
        pytest.skip(f"falta el modelo de pose {MODELO_POSE}")
    app = sensei_en_el_sistema
    monkeypatch.setattr(live_screen.LiveScreen, "INTERVALO_MS", 0)

    vueltas = []
    original = live_screen.LiveScreen._actualizar_frame

    def contada(self):
        vueltas.append(1)
        if len(vueltas) > TOPE_VUELTAS:
            self._activo = False   # corta el ciclo: la prueba debe fallar, no colgarse
            return
        original(self)

    monkeypatch.setattr(live_screen.LiveScreen, "_actualizar_frame", contada)

    recorrer(app, navegacion.ruta("medir"), sustituciones)

    assert len(vueltas) == 1, (
        f"el ciclo del video dio {len(vueltas)} vueltas durante el recorrido. "
        f"Alguien volvió a llamar a update() en vez de _asentar(): con fotogramas "
        f"más lentos que el intervalo de refresco, eso cuelga la suite.")


def test_un_control_que_no_existe_hace_fallar_el_recorrido(sensei_en_el_sistema):
    """
    Sin esto, un recorrido escrito con etiquetas inexistentes podría pasar en
    silencio y el RNF-04 quedaría verificado por una prueba que no pulsa nada.
    El mensaje debe nombrar el control buscado y listar los que sí están.
    """
    app = sensei_en_el_sistema
    inventado = navegacion.Paso("boton", "Botón que no existe")

    with pytest.raises(AssertionError) as fallo:
        pulsar(app, inventado, {})

    assert "Botón que no existe" in str(fallo.value)
    assert "Iniciar análisis en vivo" in str(fallo.value), \
        "el fallo debe listar los botones disponibles para poder corregir la ruta"
