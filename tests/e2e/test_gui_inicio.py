"""
Pruebas de extremo a extremo del panel de inicio, la selección de sensei y la
inscripción de alumnos (RF-07, RF-08).

Cubren el rediseño del 14-sep-2026, que corrigió una confusión de fondo: hasta
entonces la selección de perfiles listaba ALUMNOS y su botón «+» los inscribía,
de modo que un sensei que intentaba registrar a otro instructor terminaba
creando un alumno. El perfil identifica a quién opera el sistema; el alumno es a
quién se mide, y se inscribe desde su propia sección.

Como el resto de la carpeta, el módulo se omite entero si no hay entorno gráfico
o faltan las dependencias de la GUI.
"""
import pytest

pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")

from gui.inicio_screen import InicioScreen, TEXTO_SIN_SENSORES
from gui.historial_screen import HistorialScreen
from gui.perfil_screen import PerfilScreen
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]


@pytest.fixture
def inicio(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    return app.pantalla_actual


@pytest.fixture
def alumnos(app, db, entrenador_registrado):
    """Dos alumnos: uno con mediciones y otro recién inscrito, sin entrenar."""
    diego = db.crear_atleta("Diego Morales", color_cinta="Café", grado_cinturon="1er kyu")
    db.crear_atleta("Marta Similox", color_cinta="Blanca")

    id_sesion = db.iniciar_sesion(diego, entrenador_registrado["id_entrenador"])
    for i in range(3):
        db.guardar_medicion(id_sesion, "tsuki", 170.0, "TSUKI: EXCELENTE", i * 500, correcto=True)
    db.guardar_medicion(id_sesion, "tsuki", 120.0, "TSUKI: FLEXIONADO", 2_000, correcto=False)
    db.cerrar_sesion(id_sesion)
    return diego


# ---------------- panel de inicio ----------------

def test_tras_autenticarse_se_abre_el_panel_de_inicio(app, inicio):
    assert isinstance(inicio, InicioScreen)
    assert app.barra.seccion_activa == "inicio"


def test_un_dojo_sin_actividad_lo_dice_en_vez_de_mostrar_cifras_en_cero(inicio):
    assert inicio.metricas["sesiones"] == 0
    assert inicio.metricas["precision"] is None, "sin mediciones no hay porcentaje que mostrar"
    assert inicio.recientes == []
    assert inicio.practicadas == []


def test_el_panel_refleja_la_actividad_real_del_dojo(app, db, alumnos, inicio):
    inicio.recargar()

    assert inicio.metricas["sesiones"] == 1
    assert inicio.metricas["alumnos_activos"] == 1
    assert inicio.metricas["alumnos_inscritos"] == 2, "Marta cuenta como inscrita sin entrenar"
    assert inicio.metricas["precision"] == 75.0
    assert [s["atleta"] for s in inicio.recientes] == ["Diego Morales"]
    assert [t["nombre_tecnica"] for t in inicio.practicadas] == ["tsuki"]


def test_el_panel_declara_que_no_hay_sensores_inerciales(inicio):
    """
    RF-02 y RF-04 siguen pendientes de hardware. Mostrar un contador en «0» se
    leería como "hay sensores y ninguno responde", que es un diagnóstico
    distinto y falso; el panel declara la ausencia del subsistema.
    """
    assert TEXTO_SIN_SENSORES == "Sin sensores IMU"


def test_desde_el_inicio_se_llega_al_analisis_en_vivo_y_al_historial(app, inicio):
    inicio._abrir_historial()
    assert isinstance(app.pantalla_actual, HistorialScreen)

    app.on_abrir_inicio()
    app.pantalla_actual._abrir_vivo()
    assert type(app.pantalla_actual).__name__ == "LiveScreen"


# ---------------- selección de sensei ----------------

@ficha(
    id_caso="TC-AUTO-032",
    nombre="Elegir un perfil de sensei exige su contraseña y no da acceso con un solo clic",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="la pantalla se parece a un selector de perfiles al estilo Netflix, "
                         "donde elegir una tarjeta entra sin más; si aquí se comportara igual, "
                         "sería una puerta trasera al inicio de sesión —cualquiera operaría como "
                         "el sensei principal con un clic— y dejaría sin valor el hash SHA-256 "
                         "del RNF-05, además de falsear la firma que queda en cada umbral "
                         "recalibrado y en cada sesión registrada",
    componente="gui/perfil_screen.py (PerfilScreen) + persistence/database.py "
               "(autenticar_entrenador)",
    requisitos=("RF-08", "RNF-05"),
    precondiciones="CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico "
                   "disponible; un sensei registrado con usuario «sensei» y contraseña "
                   "«clave123»",
    datos_entrada="Tarjeta del sensei registrado; primero una contraseña equivocada "
                  "(«incorrecta»), después la correcta («clave123»)",
    pasos=[
        Paso("Abrir la selección de perfiles con `on_cambiar_perfil()`",
             "assert isinstance(app.pantalla_actual, PerfilScreen) y app.barra is None"),
        Paso("Pulsar la tarjeta del sensei sin escribir contraseña y disparar `_entrar()`",
             "assert la aplicación sigue en PerfilScreen"),
        Paso("Escribir una contraseña equivocada y disparar `_entrar()`",
             "assert 'Contraseña incorrecta' en el mensaje de error y no se entró"),
        Paso("Escribir la contraseña correcta y disparar `_entrar()`",
             "assert isinstance(app.pantalla_actual, InicioScreen) y app.entrenador quedó fijado"),
    ],
    resultado_esperado="PASSED. Cambiar de perfil pasa siempre por la verificación de "
                       "credenciales, de modo que la firma de cada medición corresponde a quien "
                       "realmente la tomó.",
    evidencia="Reporte de consola de pytest; captura de pantalla de la selección de perfiles.",
)
def test_cambiar_de_perfil_pide_la_contrasena_del_sensei(app, db, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.on_cambiar_perfil()

    pantalla = app.pantalla_actual
    assert isinstance(pantalla, PerfilScreen)
    assert app.barra is None, "la barra no debe verse mientras se elige quién opera el sistema"

    sensei = db.listar_entrenadores()[0]
    pantalla._pedir_clave(sensei)

    assert pantalla._entrar() == 0, "sin contraseña no se entra"
    assert isinstance(app.pantalla_actual, PerfilScreen)

    pantalla.password_var.set("incorrecta")
    assert pantalla._entrar() == 0
    assert "incorrecta" in pantalla.error_var.get().lower()
    assert isinstance(app.pantalla_actual, PerfilScreen)

    pantalla.password_var.set("clave123")
    assert pantalla._entrar() == 1
    assert isinstance(app.pantalla_actual, InicioScreen)
    assert app.entrenador["usuario"] == sensei["usuario"]


def test_la_seleccion_lista_senseis_y_no_alumnos(app, db, entrenador_registrado, alumnos):
    """
    El error que motivó el rediseño: aquí aparecían los alumnos, de modo que
    registrar a un instructor nuevo lo convertía en atleta.
    """
    app.on_login_exitoso(entrenador_registrado)
    app.on_cambiar_perfil()

    nombres = {s["nombre"] for s in db.listar_entrenadores()}
    assert entrenador_registrado["nombre"] in nombres
    assert "Diego Morales" not in nombres, "un alumno no es un perfil de operación"
    assert len(app.pantalla_actual.tarjetas) == len(nombres)


def test_la_lista_de_senseis_nunca_expone_el_hash_de_la_contrasena(db, entrenador_registrado):
    """
    La pantalla no necesita el hash para nada. No sacarlo de la capa de datos
    evita que termine, por descuido, en un widget o en un registro de depuración.
    """
    for sensei in db.listar_entrenadores():
        assert "password_hash" not in sensei


# ---------------- inscripción de alumnos ----------------

def test_los_alumnos_se_inscriben_desde_su_propia_seccion(app, entrenador_registrado, db):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("historial")
    pantalla = app.pantalla_actual

    pantalla.abrir_registro()
    pantalla.campos["nombre"].set("Ana Lucía Pérez")
    pantalla.campos["edad"].set("21")
    pantalla.campos["peso"].set("58,5")
    pantalla.campos["color_cinta"].set("Negra")
    pantalla.campos["grado"].set("1º dan")
    pantalla.campos["tiempo_entrenando"].set("6 años")
    pantalla.campos["notas"].set("Prepara examen de 2º dan.")

    id_atleta = pantalla.guardar_alumno()

    assert id_atleta is not None
    ficha_alumna = db.obtener_atleta(id_atleta)
    assert ficha_alumna["nombre"] == "Ana Lucía Pérez"
    assert ficha_alumna["edad"] == 21
    assert ficha_alumna["peso_kg"] == 58.5, "la coma decimal debe aceptarse"
    assert ficha_alumna["color_cinta"] == "Negra"
    assert ficha_alumna["grado_cinturon"] == "1º dan"
    assert "2º dan" in ficha_alumna["notas"]
    assert pantalla.ventana_registro is None, "la ventana se cierra al guardar"


def test_el_campo_de_grado_solo_aparece_para_cinta_cafe_o_negra(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("historial")
    pantalla = app.pantalla_actual
    pantalla.abrir_registro()

    pantalla._al_cambiar_cinta("Café")
    assert pantalla.caja_grado.winfo_children(), "el café abarca varios kyu: el grado sí informa"
    assert pantalla.campos["grado"].get() == "3er kyu"

    pantalla._al_cambiar_cinta("Blanca")
    assert pantalla.caja_grado.winfo_children() == []
    assert pantalla.campos["grado"].get() == "", "el grado remanente se limpia al ocultarse"


def test_un_formulario_invalido_no_inscribe_a_nadie(app, entrenador_registrado, db):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("historial")
    pantalla = app.pantalla_actual
    pantalla.abrir_registro()

    pantalla.campos["nombre"].set("Diego Morales")
    pantalla.campos["edad"].set("dieciséis")

    assert pantalla.guardar_alumno() is None
    assert "edad" in pantalla.error_registro.get().lower()
    assert db.listar_atletas() == [], "no debe quedar a medio inscribir"
    assert pantalla.ventana_registro is not None, "la ventana sigue abierta para corregir"


def test_abrir_el_registro_dos_veces_no_duplica_la_ventana(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("historial")
    pantalla = app.pantalla_actual

    primera = pantalla.abrir_registro()
    assert pantalla.abrir_registro() is primera

    pantalla.cerrar_registro()
    assert pantalla.ventana_registro is None
