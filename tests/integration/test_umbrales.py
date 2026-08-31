"""
Pruebas de integración de los umbrales parametrizados (RF-08).

Verifican que los umbrales dejaron de ser constantes de código, que recalibrar
crea una versión nueva sin destruir la anterior, y que cada medición queda
ligada a la versión de umbral que la juzgó — que es lo que sostiene la
trazabilidad de los reportes de progreso frente a una recalibración.
"""
import pytest

from persistence.medicion_logger import MedicionLogger
from expert_system.knowledge_base import KarateRules, UMBRALES_LITERATURA
from expert_system.kick_state_machine import MaeGeriStateMachine


@pytest.fixture
def db_sembrada(db):
    """Base de datos temporal con los umbrales de literatura ya cargados."""
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    return db


@pytest.mark.integracion
def test_la_siembra_es_idempotente(db_sembrada):
    # El fixture ya sembró; una segunda siembra no debe insertar ni duplicar.
    nuevos = db_sembrada.sembrar_umbrales(UMBRALES_LITERATURA)
    assert nuevos == 0, f"la segunda siembra insertó {nuevos} filas"
    assert len(db_sembrada.cargar_umbrales_vigentes()) == len(UMBRALES_LITERATURA)


@pytest.mark.integracion
def test_las_reglas_usan_los_umbrales_de_la_base(db_sembrada):
    reglas = KarateRules(db_sembrada.cargar_umbrales_vigentes())
    assert reglas.evaluate_tsuki(165)[0], "165 es correcto con el umbral 160-175"

    # El entrenador endurece el criterio a 170-175.
    db_sembrada.actualizar_umbral("tsuki", "codo", 170, 175, id_entrenador=None)

    recalibradas = KarateRules(db_sembrada.cargar_umbrales_vigentes())
    correcto, mensaje, _ = recalibradas.evaluate_tsuki(165)
    assert not correcto, "165 ya no debe pasar con el umbral 170-175"
    assert "FLEXIONADO" in mensaje, mensaje


@pytest.mark.integracion
def test_recalibrar_crea_version_nueva_sin_borrar_la_anterior(db_sembrada):
    original = db_sembrada.cargar_umbrales_vigentes()[("kokutsu_dachi", "rodilla_frontal")]
    id_nuevo = db_sembrada.actualizar_umbral("kokutsu_dachi", "rodilla_frontal", 95, 125,
                                             id_entrenador=None, fuente="modelado_experto")
    assert id_nuevo != original["id_umbral"], "debe crear una fila nueva, no sobrescribir"

    historial = db_sembrada.historial_umbral("kokutsu_dachi", "rodilla_frontal")
    assert len(historial) == 2, f"deberían quedar 2 versiones, hay {len(historial)}"

    vigentes = [h for h in historial if h["vigente"]]
    assert len(vigentes) == 1, "solo una versión puede estar vigente"
    assert vigentes[0]["id_umbral"] == id_nuevo
    assert vigentes[0]["fuente"] == "modelado_experto"

    anterior = [h for h in historial if not h["vigente"]][0]
    assert anterior["valor_min"] == original["valor_min"]
    assert anterior["fuente"] == "literatura"


@pytest.mark.integracion
def test_la_medicion_conserva_el_umbral_que_la_juzgo(db_sembrada):
    id_entrenador = db_sembrada.crear_entrenador("Sensei", "sensei", None, "clave")
    id_atleta = db_sembrada.crear_atleta("Atleta de prueba")
    id_sesion = db_sembrada.iniciar_sesion(id_atleta, id_entrenador)

    reglas = KarateRules(db_sembrada.cargar_umbrales_vigentes())
    id_vigente = reglas.id_umbral_principal("tsuki")
    assert id_vigente is not None, "las reglas deben conocer el id del umbral cargado"

    MedicionLogger(db_sembrada, id_sesion).registrar(
        [{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE",
          "angulo": 168.0, "correcto": True, "id_umbral": id_vigente}], 1000)

    # Se recalibra DESPUÉS de haber medido.
    db_sembrada.actualizar_umbral("tsuki", "codo", 170, 175, id_entrenador=id_entrenador)

    historial = db_sembrada.consultar_historial(id_atleta)
    assert len(historial) == 1, historial
    assert historial[0]["id_umbral"] == id_vigente, \
        "la medición debe seguir apuntando al umbral con el que fue evaluada"

    version = [h for h in db_sembrada.historial_umbral("tsuki", "codo")
               if h["id_umbral"] == id_vigente][0]
    assert version["valor_min"] == 160.0, "la versión histórica no debe mutar"


@pytest.mark.integracion
def test_rechaza_un_maximo_menor_que_el_minimo(db_sembrada):
    with pytest.raises(ValueError):
        db_sembrada.actualizar_umbral("tsuki", "codo", 175, 160, id_entrenador=None)


@pytest.mark.integracion
def test_la_maquina_de_estados_hereda_el_umbral_de_kime(db_sembrada):
    # El umbral de extensión de la FSM y el criterio de Kime son el mismo
    # número: recalibrar uno debe mover el otro.
    maquina = MaeGeriStateMachine(5, KarateRules(db_sembrada.cargar_umbrales_vigentes()))
    assert maquina.umbral_extension == 160.0

    db_sembrada.actualizar_umbral("mae_geri", "rodilla_kime", 170, 180, id_entrenador=None)
    recalibrada = MaeGeriStateMachine(5, KarateRules(db_sembrada.cargar_umbrales_vigentes()))
    assert recalibrada.umbral_extension == 170.0


@pytest.mark.unitaria
def test_sin_base_de_datos_usa_los_valores_de_literatura():
    reglas = KarateRules()
    assert reglas.rango("tsuki", "codo") == (160.0, 175.0)
    assert reglas.id_umbral_principal("tsuki") is None, "sin base de datos no hay versión que anotar"
    assert reglas.evaluate_tsuki(168)[0]


@pytest.mark.unitaria
def test_un_umbral_sin_maximo_no_limita_por_arriba():
    # La velocidad angular del Mae Geri tiene mínimo pero no máximo.
    reglas = KarateRules()
    assert reglas.rango("mae_geri", "velocidad_angular") == (400.0, None)
    correcto, mensaje, _ = reglas.evaluate_mae_geri(170, 5000)
    assert correcto, mensaje
