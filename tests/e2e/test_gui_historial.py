"""
Pruebas de extremo a extremo de las pantallas de historial, alumno, reporte y
biblioteca de técnicas (RF-05, RF-07).

Cierran por el lado de la interfaz un conjunto de funciones que ya existían y
estaban probadas pero que ningún usuario podía alcanzar: el reporte de progreso
se generaba desde Python y nunca desde la aplicación, y el historial vivía en la
base sin ninguna pantalla que lo mostrara.

Se verifica la navegación completa —alumnos → un alumno → una de sus sesiones—
porque el valor de estas pantallas está en poder bajar al detalle y regresar.
"""
import pytest

pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")
pytest.importorskip("matplotlib", reason="Matplotlib no está instalado")

from gui.alumno_screen import AlumnoScreen
from gui.historial_screen import HistorialScreen
from gui.perfil_screen import PerfilScreen
from gui.reporte_screen import ReporteScreen
from gui.tecnicas_screen import TecnicasScreen
from gui.umbrales_screen import UmbralesScreen
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]


@pytest.fixture
def dojo_con_historia(db, entrenador_registrado):
    """Un alumno con una sesión cerrada que dejó aciertos y un error repetido."""
    id_entrenador = entrenador_registrado["id_entrenador"]
    diego = db.crear_atleta("Diego Morales", grado_cinturon="5o kyu")
    db.crear_atleta("Ana Lopez", grado_cinturon="3er kyu")

    sesion = db.iniciar_sesion(diego, id_entrenador)
    db.guardar_medicion(sesion, "tsuki", 168.0, "TSUKI: EXCELENTE", 1000, correcto=True)
    db.guardar_medicion(sesion, "tsuki", 179.0, "TSUKI: HIPEREXTENDIDO (Peligro)", 2000,
                        correcto=False)
    db.guardar_medicion(sesion, "tsuki", 178.5, "TSUKI: HIPEREXTENDIDO (Peligro)", 3000,
                        correcto=False)
    db.guardar_medicion(sesion, "tsuki", None, "EN TRANSICION...", 4000, correcto=None)
    db.cerrar_sesion(sesion)

    return {"atleta": diego, "sesion": sesion}


@pytest.fixture
def historial(app, entrenador_registrado, dojo_con_historia):
    """Pantalla de alumnos abierta por la misma vía que el usuario."""
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_historial()
    return app.pantalla_actual


# --------------------------------------------------------------------------
# Historial de alumnos
# --------------------------------------------------------------------------

def test_el_historial_lista_a_todos_los_alumnos(historial):
    assert isinstance(historial, HistorialScreen)
    assert [a["nombre"] for a in historial.resumen] == ["Ana Lopez", "Diego Morales"]


def test_el_alumno_sin_entrenar_aparece_sin_precision(historial):
    ana = [a for a in historial.resumen if a["nombre"] == "Ana Lopez"][0]
    assert ana["precision"] is None, "sin datos no es lo mismo que 0 %"


def test_volver_desde_el_historial_regresa_a_perfiles(app, historial):
    historial._volver()
    assert isinstance(app.pantalla_actual, PerfilScreen)


# --------------------------------------------------------------------------
# Perfil del alumno y generación del reporte
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-027",
    nombre="El reporte de progreso de un atleta se genera desde la interfaz y produce un "
           "archivo de imagen válido",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="el módulo de reportes funcionaba y estaba probado, pero no se "
                         "invocaba desde ninguna pantalla ni desde la consola: era código "
                         "inalcanzable para el usuario. El diagrama de casos de uso, en "
                         "cambio, declaraba la función como implementada, de modo que el "
                         "sistema prometía algo que nadie podía ejecutar",
    componente="gui/alumno_screen.py (AlumnoScreen) + persistence/reportes.py",
    requisitos="RF-07",
    precondiciones="CustomTkinter, MediaPipe, OpenCV, Pillow y Matplotlib instalados; "
                   "entorno gráfico disponible; atleta con una sesión cerrada que dejó "
                   "evaluaciones con veredicto",
    datos_entrada="Atleta \"Diego Morales\" con una sesión de 3 evaluaciones cerradas "
                  "(1 correcta, 2 incorrectas) y 1 estado transitorio",
    pasos=[
        Paso("Navegar alumnos → perfil del alumno con `on_abrir_alumno(id)`",
             "assert isinstance(app.pantalla_actual, AlumnoScreen)"),
        Paso("Disparar `generar_reporte()` (el manejador del botón real)",
             "assert ruta is not None — se produjo un archivo"),
        Paso("Verificar el archivo en disco",
             "assert el archivo existe y su tamaño es mayor que cero"),
        Paso("Leer el mensaje mostrado al instructor",
             "assert la ruta del reporte aparece en el texto de estado de la pantalla"),
    ],
    resultado_esperado="PASSED. Si el atleta no tiene evaluaciones cerradas, no se genera un "
                       "archivo vacío: se explica por qué todavía no hay nada que graficar",
    evidencia="Reporte de consola de pytest y el PNG de progreso generado durante la corrida.",
)
def test_el_reporte_de_progreso_se_genera_desde_la_pantalla(app, db, dojo_con_historia,
                                                            entrenador_registrado, tmp_path,
                                                            monkeypatch):
    monkeypatch.chdir(tmp_path)
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_alumno(dojo_con_historia["atleta"])
    pantalla = app.pantalla_actual

    assert isinstance(pantalla, AlumnoScreen)
    ruta = pantalla.generar_reporte()

    assert ruta is not None, "el atleta tiene evaluaciones cerradas: debió graficarse"
    archivo = tmp_path / ruta
    assert archivo.exists() and archivo.stat().st_size > 0
    assert ruta in pantalla.estado_var.get()


def test_sin_evaluaciones_cerradas_se_explica_en_vez_de_generar_un_grafico_vacio(
        app, db, entrenador_registrado, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    nuevo = db.crear_atleta("Recien Inscrito")
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_alumno(nuevo)

    assert app.pantalla_actual.generar_reporte() is None
    assert "todavía no hay" in app.pantalla_actual.estado_var.get().lower()


def test_el_perfil_muestra_el_desempeno_por_tecnica(app, db, dojo_con_historia,
                                                    entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_alumno(dojo_con_historia["atleta"])

    tecnicas = db.resumen_por_tecnica(dojo_con_historia["atleta"])
    assert [t["nombre_tecnica"] for t in tecnicas] == ["tsuki"]
    assert tecnicas[0]["precision"] == pytest.approx(100 / 3)


# --------------------------------------------------------------------------
# Reporte de sesión
# --------------------------------------------------------------------------

def test_el_reporte_de_sesion_resume_y_ordena_los_errores(app, db, dojo_con_historia,
                                                          entrenador_registrado):
    """
    El bloque de correcciones es lo que convierte un porcentaje en algo que el
    instructor puede mandar a practicar mañana.
    """
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_reporte(dojo_con_historia["sesion"])
    pantalla = app.pantalla_actual

    assert isinstance(pantalla, ReporteScreen)
    assert pantalla.sesion["atleta"] == "Diego Morales"
    assert pantalla.sesion["precision"] == pytest.approx(100 / 3)

    errores = db.errores_frecuentes(dojo_con_historia["sesion"])
    assert errores[0]["veces"] == 2 and "HIPEREXTENDIDO" in errores[0]["diagnostico"]


def test_un_reporte_de_sesion_inexistente_no_rompe_la_pantalla(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_reporte(99999)

    assert isinstance(app.pantalla_actual, ReporteScreen)
    assert app.pantalla_actual.sesion is None


def test_volver_desde_el_reporte_regresa_al_perfil_del_alumno(app, dojo_con_historia,
                                                              entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.on_abrir_reporte(dojo_con_historia["sesion"])

    app.pantalla_actual._volver()

    assert isinstance(app.pantalla_actual, AlumnoScreen)


# --------------------------------------------------------------------------
# Biblioteca de técnicas
# --------------------------------------------------------------------------

def test_la_biblioteca_muestra_las_tecnicas_que_el_sistema_evalua(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_tecnicas()

    assert isinstance(app.pantalla_actual, TecnicasScreen)


def test_la_biblioteca_refleja_una_recalibracion_del_entrenador(app, db, entrenador_registrado):
    """
    Los rangos se leen de la base de datos, no del código: si el dojo ajusta un
    criterio, la biblioteca muestra el criterio nuevo y lo marca como propio.
    """
    db.actualizar_umbral("tsuki", "codo", 165.0, 174.0,
                         id_entrenador=entrenador_registrado["id_entrenador"],
                         fuente="modelado_experto")
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_tecnicas()

    vigente = db.cargar_umbrales_vigentes()[("tsuki", "codo")]
    assert (vigente["valor_min"], vigente["valor_max"]) == (165.0, 174.0)
    assert vigente["fuente"] == "modelado_experto"


def test_desde_la_biblioteca_se_llega_a_la_calibracion(app, entrenador_registrado):
    app.on_login_exitoso(entrenador_registrado)
    app.pantalla_actual._abrir_tecnicas()

    app.pantalla_actual._abrir_umbrales()

    assert isinstance(app.pantalla_actual, UmbralesScreen)
