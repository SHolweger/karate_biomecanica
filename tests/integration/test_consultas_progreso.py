"""
Pruebas de integración de las consultas agregadas del historial (RF-07).

Son la fuente de todo lo que muestran las pantallas de alumnos, perfil y
reporte de sesión. Se verifican aquí, contra una base real, y no a través de la
interfaz: si el porcentaje que ve el instructor está mal calculado, el problema
está en estas consultas, no en cómo se dibujan.

El criterio que atraviesa todas: solo cuentan las evaluaciones CERRADAS. Un
diagnóstico con `correcto` nulo es un estado transitorio o una articulación no
visible, y contarlo hundiría la precisión de un alumno por el solo hecho de
haberse movido frente a la cámara.
"""
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion


def _medir(db, id_sesion, tecnica, diagnostico, correcto, angulo=None, ts=1000):
    db.guardar_medicion(id_sesion, tecnica, angulo, diagnostico, ts, correcto=correcto)


@pytest.fixture
def dojo(db):
    """
    Un dojo con dos alumnos y una historia deliberadamente asimétrica.

    Diego: dos sesiones. En la primera 2 de 3 tsukis correctos; en la segunda
    mejora a 2 de 2, y falla ambas posturas. Ana: inscrita, sin entrenar.
    """
    id_entrenador = db.crear_entrenador("Sensei Ejemplo", "sensei", None, "clave")
    diego = db.crear_atleta("Diego Morales", grado_cinturon="5o kyu")
    ana = db.crear_atleta("Ana Lopez", grado_cinturon="3er kyu")

    s1 = db.iniciar_sesion(diego, id_entrenador)
    _medir(db, s1, "tsuki", "TSUKI: EXCELENTE", True, 168.0)
    _medir(db, s1, "tsuki", "TSUKI: EXCELENTE", True, 170.0)
    _medir(db, s1, "tsuki", "TSUKI: HIPEREXTENDIDO (Peligro)", False, 179.0)
    _medir(db, s1, "tsuki", "EN TRANSICION...", None)          # no debe contar
    db.cerrar_sesion(s1)

    s2 = db.iniciar_sesion(diego, id_entrenador)
    _medir(db, s2, "tsuki", "TSUKI: EXCELENTE", True, 169.0)
    _medir(db, s2, "tsuki", "TSUKI: EXCELENTE", True, 167.0)
    _medir(db, s2, "kokutsu_dachi", "POSTURA: CORREGIR ALTURA", False, 128.0)
    _medir(db, s2, "kokutsu_dachi", "POSTURA: CORREGIR ALTURA", False, 130.0)

    return {"db": db, "diego": diego, "ana": ana, "s1": s1, "s2": s2,
            "entrenador": id_entrenador}


# --------------------------------------------------------------------------
# Resumen de alumnos
# --------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-026",
    nombre="La precisión de un alumno se calcula solo sobre evaluaciones cerradas, ignorando "
           "los estados transitorios",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="durante una sesión el sistema emite muchos diagnósticos sin "
                         "veredicto (\"EN TRANSICION\", \"MAE GERI: CARGA\", articulación no "
                         "visible). Contarlos como fallos hundiría el porcentaje de cualquier "
                         "alumno por el solo hecho de haberse movido frente a la cámara, y el "
                         "instructor tomaría decisiones de entrenamiento sobre una cifra falsa",
    componente="persistence/database.py (resumen_atletas)",
    requisitos="RF-07",
    precondiciones="Base temporal con un atleta que acumula 4 evaluaciones correctas, "
                   "3 incorrectas y 1 estado transitorio sin veredicto",
    datos_entrada="Sesión 1: dos tsukis correctos, uno hiperextendido y un \"EN TRANSICION\". "
                  "Sesión 2: dos tsukis correctos y dos posturas incorrectas",
    pasos=[
        Paso("Invocar `resumen_atletas()`",
             "assert el atleta aparece con sesiones == 2"),
        Paso("Verificar el denominador del porcentaje",
             "assert evaluaciones == 7, no 8: el estado transitorio queda fuera"),
        Paso("Verificar el porcentaje calculado",
             "assert precision == pytest.approx(4 / 7 * 100)"),
    ],
    resultado_esperado="PASSED. Un alumno sin mediciones aparece con precisión None y no con "
                       "0 %, porque \"sin datos\" y \"falla todo\" son afirmaciones distintas",
)
def test_la_precision_ignora_los_estados_transitorios(dojo):
    resumen = {a["nombre"]: a for a in dojo["db"].resumen_atletas()}
    diego = resumen["Diego Morales"]

    assert diego["sesiones"] == 2
    assert diego["evaluaciones"] == 7, "el diagnóstico sin veredicto no debe contar"
    assert diego["aciertos"] == 4
    assert diego["precision"] == pytest.approx(4 / 7 * 100)


def test_un_alumno_sin_mediciones_aparece_con_precision_desconocida(dojo):
    """
    'Sin datos' y '0 %' son afirmaciones distintas. Mostrar cero diría que el
    alumno falla todo cuando en realidad nunca fue medido.
    """
    resumen = {a["nombre"]: a for a in dojo["db"].resumen_atletas()}
    ana = resumen["Ana Lopez"]

    assert ana["sesiones"] == 0
    assert ana["evaluaciones"] == 0
    assert ana["precision"] is None


def test_todos_los_alumnos_aparecen_aunque_no_hayan_entrenado(dojo):
    nombres = [a["nombre"] for a in dojo["db"].resumen_atletas()]
    assert nombres == ["Ana Lopez", "Diego Morales"], "orden alfabético y sin omitir a nadie"


# --------------------------------------------------------------------------
# Sesiones
# --------------------------------------------------------------------------

def test_las_sesiones_se_listan_de_la_mas_reciente_a_la_mas_antigua(dojo):
    sesiones = dojo["db"].listar_sesiones(dojo["diego"])

    assert [s["id_sesion"] for s in sesiones] == [dojo["s2"], dojo["s1"]]


def test_cada_sesion_trae_su_propia_precision(dojo):
    por_id = {s["id_sesion"]: s for s in dojo["db"].listar_sesiones(dojo["diego"])}

    assert por_id[dojo["s1"]]["precision"] == pytest.approx(2 / 3 * 100)
    assert por_id[dojo["s2"]]["precision"] == pytest.approx(50.0)


def test_una_sesion_abierta_se_distingue_de_una_cerrada(dojo):
    por_id = {s["id_sesion"]: s for s in dojo["db"].listar_sesiones(dojo["diego"])}

    assert por_id[dojo["s1"]]["hora_fin"] is not None
    assert por_id[dojo["s2"]]["hora_fin"] is None, "la segunda sesión quedó abierta"


def test_un_alumno_sin_sesiones_devuelve_lista_vacia(dojo):
    assert dojo["db"].listar_sesiones(dojo["ana"]) == []


# --------------------------------------------------------------------------
# Desempeño por técnica
# --------------------------------------------------------------------------

def test_las_tecnicas_se_ordenan_de_la_mas_floja_a_la_mas_solida(dojo):
    """
    Lo primero que el instructor lee debe ser lo que hay que corregir, no lo
    que ya sale bien.
    """
    tecnicas = dojo["db"].resumen_por_tecnica(dojo["diego"])

    assert [t["nombre_tecnica"] for t in tecnicas] == ["kokutsu_dachi", "tsuki"]
    assert tecnicas[0]["precision"] == 0.0
    assert tecnicas[1]["precision"] == pytest.approx(4 / 5 * 100)


def test_el_desempeno_puede_acotarse_a_una_sola_sesion(dojo):
    solo_s1 = dojo["db"].resumen_por_tecnica(dojo["diego"], id_sesion=dojo["s1"])

    assert [t["nombre_tecnica"] for t in solo_s1] == ["tsuki"], \
        "en la primera sesión no se evaluaron posturas"
    assert solo_s1[0]["evaluaciones"] == 3


def test_el_angulo_medio_se_promedia_por_tecnica(dojo):
    tsuki = [t for t in dojo["db"].resumen_por_tecnica(dojo["diego"])
             if t["nombre_tecnica"] == "tsuki"][0]

    assert tsuki["angulo_medio"] == pytest.approx((168 + 170 + 179 + 169 + 167) / 5)


# --------------------------------------------------------------------------
# Detalle de una sesión y errores frecuentes
# --------------------------------------------------------------------------

def test_el_detalle_de_sesion_identifica_al_alumno_y_al_entrenador(dojo):
    detalle = dojo["db"].detalle_sesion(dojo["s1"])

    assert detalle["atleta"] == "Diego Morales"
    assert detalle["entrenador"] == "Sensei Ejemplo"
    assert detalle["precision"] == pytest.approx(2 / 3 * 100)


def test_una_sesion_inexistente_devuelve_none(dojo):
    assert dojo["db"].detalle_sesion(99999) is None


def test_los_errores_se_agrupan_y_ordenan_por_frecuencia(dojo):
    """
    Es lo que convierte un porcentaje en una corrección accionable: no basta
    saber que falló, hay que saber en qué falló y cuántas veces.
    """
    errores = dojo["db"].errores_frecuentes(dojo["s2"])

    assert len(errores) == 1, "las dos posturas fallidas comparten diagnóstico"
    assert errores[0]["veces"] == 2
    assert errores[0]["nombre_tecnica"] == "kokutsu_dachi"
    assert "CORREGIR ALTURA" in errores[0]["diagnostico"]


def test_una_sesion_sin_errores_no_reporta_correcciones(db, dojo):
    """Si todo salió bien, no se inventan recomendaciones."""
    limpia = db.iniciar_sesion(dojo["diego"], dojo["entrenador"])
    _medir(db, limpia, "tsuki", "TSUKI: EXCELENTE", True, 170.0)

    assert db.errores_frecuentes(limpia) == []
