"""
Pruebas de extremo a extremo de la pantalla de calibración de umbrales (RF-08).

Cierran el requisito por el lado que faltaba. Las pruebas de integración
(`tests/integration/test_umbrales.py`) ya demostraban que la base de datos
versiona correctamente una recalibración hecha desde Python; lo que se verifica
aquí es que el entrenador puede provocar esa recalibración desde la interfaz,
sin tocar el código fuente, y que el sistema experto empieza a juzgar con el
criterio nuevo.

Como el resto de la carpeta, el módulo se omite entero si no hay entorno
gráfico o faltan las dependencias de la GUI.
"""
import pytest

pytest.importorskip("customtkinter", reason="CustomTkinter no está instalado")
pytest.importorskip("cv2", reason="OpenCV no está instalado")
pytest.importorskip("mediapipe", reason="MediaPipe no está instalado")
pytest.importorskip("PIL", reason="Pillow no está instalado")

from expert_system.knowledge_base import KarateRules, UMBRALES_LITERATURA
from gui.inicio_screen import InicioScreen
from gui.umbrales_screen import UmbralesScreen
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = [pytest.mark.e2e, pytest.mark.lenta]

TSUKI_CODO = ("tsuki", "codo")


@pytest.fixture
def pantalla_umbrales(app, entrenador_registrado):
    """
    Pantalla de calibración abierta por la misma vía que el usuario: login y
    luego el botón de la selección de perfiles. Construirla directamente
    dejaría a la App sin entrenador, un estado que en la aplicación real no se
    puede producir — y sin entrenador la pantalla es de solo lectura.
    """
    app.on_login_exitoso(entrenador_registrado)
    app._navegar("umbrales")
    return app.pantalla_actual


def test_la_pantalla_lista_todos_los_umbrales_vigentes(pantalla_umbrales):
    """La App siembra los umbrales al arrancar; la pantalla debe mostrarlos todos."""
    assert isinstance(pantalla_umbrales, UmbralesScreen)
    assert pantalla_umbrales.puede_editar is True
    assert len(pantalla_umbrales.campos) == len(UMBRALES_LITERATURA)

    campos_tsuki = pantalla_umbrales.campos[TSUKI_CODO]
    assert campos_tsuki["min"].get() == "160"
    assert campos_tsuki["max"].get() == "175"


@ficha(
    id_caso="TC-AUTO-021",
    nombre="Recalibrar un umbral desde la interfaz cambia el criterio con el que el sistema "
           "experto evalúa, sin modificar el código fuente",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es la única vía por la que un instructor puede ajustar el criterio "
                         "técnico del sistema; si la pantalla no escribe en la base de datos, "
                         "el RF-08 queda sostenido solo por código que nadie del dojo puede "
                         "ejecutar",
    componente="gui/umbrales_screen.py (UmbralesScreen) + persistence/database.py "
               "(actualizar_umbral)",
    requisitos="RF-08",
    precondiciones="CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico "
                   "disponible; entrenador autenticado; umbrales de literatura ya sembrados "
                   "por `App` al arrancar",
    datos_entrada="Umbral `tsuki` / `codo`, vigente en 160–175°, editado a 170–175° desde el "
                  "formulario; ángulo de prueba 165°, correcto con el criterio anterior",
    pasos=[
        Paso("Autenticarse y abrir la pantalla con `_abrir_umbrales()` (el manejador del "
             "botón real)",
             "assert isinstance(app.pantalla_actual, UmbralesScreen)"),
        Paso("Escribir 170 en el campo del mínimo y disparar `_guardar_cambios()`",
             "assert guardados == 1 (se escribe solo el umbral modificado)"),
        Paso("Releer los umbrales vigentes y construir `KarateRules` con ellos",
             "assert reglas.evaluate_tsuki(165)[0] is False (165° ya no aprueba)"),
        Paso("Consultar `historial_umbral('tsuki', 'codo')`",
             "assert len(historial) == 2 y la versión vigente quedó firmada por el "
             "entrenador que la guardó"),
    ],
    resultado_esperado="PASSED. El criterio nuevo rige la siguiente sesión de análisis y la "
                       "versión anterior permanece en el historial, de modo que las "
                       "mediciones ya registradas siguen siendo interpretables",
    evidencia="Reporte de consola de pytest; captura de pantalla de la pantalla de "
              "calibración para el expediente.",
)
def test_recalibrar_cambia_el_criterio_del_sistema_experto(pantalla_umbrales, db,
                                                           entrenador_registrado):
    reglas_antes = KarateRules(db.cargar_umbrales_vigentes())
    assert reglas_antes.evaluate_tsuki(165)[0], "165° debe aprobar con el umbral 160-175"

    pantalla_umbrales.campos[TSUKI_CODO]["min"].set("170")
    guardados = pantalla_umbrales._guardar_cambios()

    assert guardados == 1, "solo debe escribirse el umbral que cambió"
    assert pantalla_umbrales.error_var.get() == ""

    reglas_despues = KarateRules(db.cargar_umbrales_vigentes())
    correcto, mensaje, _ = reglas_despues.evaluate_tsuki(165)
    assert not correcto, "165° ya no debe aprobar con el umbral 170-175"
    assert "FLEXIONADO" in mensaje, mensaje

    historial = db.historial_umbral(*TSUKI_CODO)
    assert len(historial) == 2, f"debería haber 2 versiones, hay {len(historial)}"

    vigente = [v for v in historial if v["vigente"]][0]
    assert vigente["valor_min"] == 170.0
    assert vigente["fuente"] == "modelado_experto"
    assert vigente["id_entrenador"] == entrenador_registrado["id_entrenador"], \
        "cada recalibración debe quedar firmada por el entrenador que la hizo"


def test_un_campo_invalido_no_guarda_ninguno_de_los_cambios(pantalla_umbrales, db):
    """
    Guardado todo-o-nada. Un guardado parcial dejaría la mitad del criterio
    recalibrado y la otra mitad no, sin que nadie pueda saber cuál mitad.
    """
    pantalla_umbrales.campos[TSUKI_CODO]["min"].set("170")             # cambio válido
    pantalla_umbrales.campos[("age_uke", "codo")]["max"].set("ciento cuarenta")  # inválido

    guardados = pantalla_umbrales._guardar_cambios()

    assert guardados == 0
    assert "Age Uke" in pantalla_umbrales.error_var.get()
    assert "no es un número" in pantalla_umbrales.error_var.get()

    vigentes = db.cargar_umbrales_vigentes()
    assert vigentes[TSUKI_CODO]["valor_min"] == 160.0, "el cambio válido tampoco debió escribirse"
    assert len(db.historial_umbral(*TSUKI_CODO)) == 1


def test_guardar_sin_tocar_nada_no_crea_versiones_nuevas(pantalla_umbrales, db):
    """
    Cada guardado crea una versión; reescribir los diez umbrales sin cambios
    llenaría el historial de versiones idénticas y lo volvería ilegible.
    """
    guardados = pantalla_umbrales._guardar_cambios()

    assert guardados == 0
    assert "No hay cambios" in pantalla_umbrales.estado_var.get()
    for clave in db.cargar_umbrales_vigentes():
        assert len(db.historial_umbral(*clave)) == 1, f"se versionó {clave} sin haberlo tocado"


def test_descartar_devuelve_los_campos_al_valor_vigente(pantalla_umbrales, db):
    pantalla_umbrales.campos[TSUKI_CODO]["min"].set("120")

    pantalla_umbrales._recargar()

    assert pantalla_umbrales.campos[TSUKI_CODO]["min"].get() == "160"
    assert len(db.historial_umbral(*TSUKI_CODO)) == 1


def test_sin_entrenador_la_pantalla_queda_en_solo_lectura(app, db):
    """
    Restricción del RF-08. La navegación de la App no permite llegar aquí sin
    autenticarse; esta prueba fija el comportamiento del caso, para que una
    ruta futura hacia la pantalla no abra la edición por descuido.
    """
    pantalla = UmbralesScreen(app, db, entrenador=None)
    app._mostrar(pantalla)

    assert pantalla.puede_editar is False
    pantalla.campos[TSUKI_CODO]["min"].set("170")

    assert pantalla._guardar_cambios() == 0
    assert "entrenador" in pantalla.error_var.get()
    assert db.cargar_umbrales_vigentes()[TSUKI_CODO]["valor_min"] == 160.0


def test_el_historial_abre_una_sola_ventana_con_las_versiones_del_umbral(pantalla_umbrales, db):
    """
    El historial es lo que vuelve auditable una recalibración: sin él, el
    entrenador cambia un criterio y no queda forma de ver desde la aplicación
    con qué se evaluaba antes.
    """
    pantalla_umbrales.campos[TSUKI_CODO]["min"].set("170")
    pantalla_umbrales._guardar_cambios()

    pantalla_umbrales._abrir_historial(TSUKI_CODO)
    ventana = pantalla_umbrales.ventana_historial
    assert ventana is not None

    pantalla_umbrales._abrir_historial(TSUKI_CODO)
    assert pantalla_umbrales.ventana_historial is ventana, "no debe abrir una segunda ventana"

    pantalla_umbrales._cerrar_historial()
    assert pantalla_umbrales.ventana_historial is None


def test_una_base_sin_umbrales_lo_informa_en_vez_de_mostrar_una_tabla_vacia(pantalla_umbrales, db):
    """
    Caso de borde de una base creada a mano o migrada sin sembrar: la pantalla
    debe decirlo, no ofrecer un formulario de cero filas que aparenta que el
    sistema no tiene criterios configurables.
    """
    db.conn.execute("DELETE FROM umbral_referencia")
    db.conn.commit()

    pantalla_umbrales._recargar()

    assert pantalla_umbrales.campos == {}
    assert pantalla_umbrales._guardar_cambios() == 0


def test_volver_regresa_al_panel_de_inicio(app, pantalla_umbrales):
    pantalla_umbrales._volver()

    assert isinstance(app.pantalla_actual, InicioScreen)


# ---------------------------------------------------------------------------
# Ver el impacto antes de adoptar el cambio (RF-08)
#
# El escenario para el que se construyó: los rangos de Kokutsu Dachi vigentes
# son provisionales, deducidos del principio biomecánico. Cuando el cuerpo
# técnico los confirme y corrija un número, la pregunta inmediata es cuánto del
# historial cambia de veredicto — y hay que contestarla ANTES de adoptar el
# cambio, porque es lo que dice si el ajuste describe mejor la postura o si se
# pasó de estricto.
# ---------------------------------------------------------------------------

KOKUTSU_TRASERA = ("kokutsu_dachi", "rodilla_trasera")


@pytest.fixture
def kokutsu_medido(db, entrenador_registrado):
    """
    Cinco Kokutsu registrados con el umbral vigente (trasera 90–120°), los cinco
    dados por correctos. Tres tienen la rodilla trasera por encima de 100°.
    """
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, entrenador_registrado["id_entrenador"])
    reglas = KarateRules(db.cargar_umbrales_vigentes())

    for frontal, trasera in [(162, 118), (158, 105), (165, 96), (160, 112), (155, 92)]:
        correcto, mensaje, _ = reglas.evaluate_kokutsu_dachi(frontal, trasera)
        db.guardar_medicion(id_sesion, "Postura de piernas", frontal, mensaje, 0,
                            correcto=correcto,
                            id_umbral=reglas.id_umbral_principal("kokutsu_dachi"),
                            tecnica_clave="kokutsu_dachi",
                            angulo_regla_1=frontal, angulo_regla_2=trasera)
    db.cerrar_sesion(id_sesion)
    return id_sesion


def _escribir_rango(pantalla, clave, minimo, maximo):
    campos = pantalla.campos[clave]
    campos["min"].set(str(minimo))
    campos["max"].set(str(maximo))


@ficha(
    id_caso="TC-AUTO-048",
    nombre="Antes de adoptar una recalibración, el sistema informa cuántas mediciones del "
           "historial cambiarían de veredicto",
    tipo=TipoPrueba.E2E,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "recalibrar sin ver el efecto es cambiar a ciegas la vara con que se mide a los "
        "alumnos: el mismo historial puede pasar de 100 % a 40 % de precisión sin que nadie "
        "haya vuelto a medir"
    ),
    componente="gui/umbrales_screen.py + expert_system/reevaluacion.py + "
               "gui/impacto_umbrales.py",
    requisitos="RF-08",
    precondiciones="Entorno gráfico y dependencias de GUI; cinco Kokutsu registrados como "
                   "correctos con el umbral vigente de rodilla trasera (90–120°)",
    datos_entrada="Rodilla trasera de Kokutsu Dachi corregida de 90–120° a 90–100°",
    pasos=[
        Paso("Escribir el rango corregido en la fila de Kokutsu · rodilla trasera",
             "El formulario difiere del umbral vigente"),
        Paso("Pulsar «Ver impacto en el historial»",
             "Se vuelve a juzgar lo registrado con el criterio propuesto"),
        Paso("Leer el resumen",
             "assert reporta 3 de 5 mediciones que cambian de veredicto"),
    ],
    resultado_esperado="El resumen identifica las tres ejecuciones afectadas sin escribir nada",
)
def test_el_impacto_se_ve_antes_de_guardar(pantalla_umbrales, kokutsu_medido):
    _escribir_rango(pantalla_umbrales, KOKUTSU_TRASERA, 90, 100)

    resumen = pantalla_umbrales._ver_impacto()

    assert resumen is not None
    assert resumen["hay_cambios"] is True
    assert "3 de 5" in resumen["titular"]
    assert resumen["por_tecnica"]["kokutsu_dachi"]["a_incorrecto"] == 3
    pantalla_umbrales._cerrar_impacto()


def test_ver_el_impacto_no_guarda_el_umbral_ni_toca_las_mediciones(pantalla_umbrales, db,
                                                                   kokutsu_medido):
    """
    Consultar no puede aplicar. El veredicto registrado es la evidencia de qué
    criterio regía al medir, y el umbral vigente no debe moverse por mirarlo.
    """
    antes = db.cargar_umbrales_vigentes()[KOKUTSU_TRASERA]
    _escribir_rango(pantalla_umbrales, KOKUTSU_TRASERA, 90, 100)

    pantalla_umbrales._ver_impacto()
    pantalla_umbrales._cerrar_impacto()

    despues = db.cargar_umbrales_vigentes()[KOKUTSU_TRASERA]
    assert despues["valor_max"] == antes["valor_max"], "el umbral vigente no debió cambiar"

    veredictos = [f["correcto"] for f in db.mediciones_reevaluables()]
    assert veredictos == [1, 1, 1, 1, 1], "los veredictos registrados deben seguir intactos"


def test_un_ajuste_que_no_mueve_nada_tambien_se_informa(pantalla_umbrales, kokutsu_medido):
    """Que ninguna cambie es el resultado que permite adoptar el ajuste con confianza."""
    _escribir_rango(pantalla_umbrales, KOKUTSU_TRASERA, 85, 130)

    resumen = pantalla_umbrales._ver_impacto()

    assert resumen["hay_cambios"] is False
    assert "Ninguna" in resumen["titular"]
    pantalla_umbrales._cerrar_impacto()


def test_sin_cambios_escritos_no_se_abre_la_ventana(pantalla_umbrales, kokutsu_medido):
    assert pantalla_umbrales._ver_impacto() is None
    assert pantalla_umbrales.ventana_impacto is None
    assert "No hay cambios" in pantalla_umbrales.estado_var.get()


def test_un_valor_mal_escrito_se_avisa_en_vez_de_calcular_con_el(pantalla_umbrales,
                                                                 kokutsu_medido):
    _escribir_rango(pantalla_umbrales, KOKUTSU_TRASERA, "noventa", 100)

    assert pantalla_umbrales._ver_impacto() is None
    assert pantalla_umbrales.ventana_impacto is None
    assert pantalla_umbrales.error_var.get(), "debe decir qué fila corregir"


def test_el_impacto_contrasta_contra_el_criterio_completo_no_solo_el_campo_editado(
        pantalla_umbrales, kokutsu_medido):
    """
    Un Kokutsu se juzga por dos rodillas. Si el informe mirara solo el campo
    editado, endurecer la rodilla FRONTAL daría cero cambios aunque el criterio
    resultante rechace ejecuciones que antes pasaban.
    """
    # Las cinco ejecuciones tienen la frontal entre 155 y 165: exigir 160-175
    # deja fuera a las de 158 y 155.
    _escribir_rango(pantalla_umbrales, ("kokutsu_dachi", "rodilla_frontal"), 160, 175)

    resumen = pantalla_umbrales._ver_impacto()

    assert resumen["por_tecnica"]["kokutsu_dachi"]["a_incorrecto"] == 2
    pantalla_umbrales._cerrar_impacto()
