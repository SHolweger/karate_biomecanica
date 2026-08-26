"""
test_umbrales.py — Umbrales biomecánicos como datos parametrizados (RF-08).

Verifica que los umbrales dejaron de ser constantes de código, que recalibrar
crea una versión nueva sin destruir la anterior, y que cada medición queda
ligada a la versión de umbral que la juzgó.

No requiere cámara: usa una base de datos temporal y valores sintéticos.

Uso:
    ./venv/bin/python test_umbrales.py
"""
import os
import tempfile

from persistence.database import Database
from persistence.medicion_logger import MedicionLogger
from expert_system.knowledge_base import KarateRules, UMBRALES_LITERATURA
from expert_system.kick_state_machine import MaeGeriStateMachine


def _base_temporal():
    path = tempfile.mktemp(suffix=".db")
    db = Database(db_path=path)
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    return db, path


def _cerrar(db, path):
    db.close()
    if os.path.exists(path):
        os.remove(path)


def test_siembra_es_idempotente():
    db, path = _base_temporal()
    try:
        # La primera siembra ocurrio en _base_temporal(); la segunda no debe
        # insertar nada ni duplicar filas.
        nuevos = db.sembrar_umbrales(UMBRALES_LITERATURA)
        assert nuevos == 0, f"la segunda siembra inserto {nuevos} filas"
        vigentes = db.cargar_umbrales_vigentes()
        assert len(vigentes) == len(UMBRALES_LITERATURA), vigentes.keys()
    finally:
        _cerrar(db, path)


def test_las_reglas_usan_los_umbrales_de_la_base():
    db, path = _base_temporal()
    try:
        reglas = KarateRules(db.cargar_umbrales_vigentes())
        correcto, _, _ = reglas.evaluate_tsuki(165)
        assert correcto, "165 deberia ser un Tsuki correcto con el umbral 160-175"

        # El entrenador endurece el criterio: ahora exige 170-175.
        db.actualizar_umbral("tsuki", "codo", 170, 175, id_entrenador=None)
        reglas_nuevas = KarateRules(db.cargar_umbrales_vigentes())
        correcto, mensaje, _ = reglas_nuevas.evaluate_tsuki(165)
        assert not correcto, "165 ya no deberia pasar con el umbral 170-175"
        assert "FLEXIONADO" in mensaje, mensaje
    finally:
        _cerrar(db, path)


def test_recalibrar_crea_version_nueva_sin_borrar_la_anterior():
    db, path = _base_temporal()
    try:
        original = db.cargar_umbrales_vigentes()[("kokutsu_dachi", "rodilla_frontal")]
        id_nuevo = db.actualizar_umbral("kokutsu_dachi", "rodilla_frontal", 95, 125,
                                        id_entrenador=None, fuente="modelado_experto")

        assert id_nuevo != original["id_umbral"], "deberia crear una fila nueva, no sobrescribir"

        historial = db.historial_umbral("kokutsu_dachi", "rodilla_frontal")
        assert len(historial) == 2, f"deberian quedar 2 versiones, hay {len(historial)}"

        vigentes = [h for h in historial if h["vigente"]]
        assert len(vigentes) == 1, "solo una version puede estar vigente"
        assert vigentes[0]["id_umbral"] == id_nuevo
        assert vigentes[0]["fuente"] == "modelado_experto"

        # La version anterior sigue existiendo con sus valores intactos.
        anterior = [h for h in historial if not h["vigente"]][0]
        assert anterior["valor_min"] == original["valor_min"]
        assert anterior["fuente"] == "literatura"
    finally:
        _cerrar(db, path)


def test_la_medicion_registra_el_umbral_que_la_juzgo():
    db, path = _base_temporal()
    try:
        id_entrenador = db.crear_entrenador("Sensei", "sensei", None, "clave")
        id_atleta = db.crear_atleta("Atleta de prueba")
        id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

        reglas = KarateRules(db.cargar_umbrales_vigentes())
        id_vigente = reglas.id_umbral_principal("tsuki")
        assert id_vigente is not None, "las reglas deben conocer el id del umbral cargado"

        logger = MedicionLogger(db, id_sesion)
        logger.registrar([{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE",
                           "angulo": 168.0, "correcto": True, "id_umbral": id_vigente}], 1000)

        # Se recalibra DESPUES de haber medido.
        db.actualizar_umbral("tsuki", "codo", 170, 175, id_entrenador=id_entrenador)

        historial = db.consultar_historial(id_atleta)
        assert len(historial) == 1, historial
        assert historial[0]["id_umbral"] == id_vigente, \
            "la medicion debe seguir apuntando al umbral con el que fue evaluada"

        # Y ese umbral conserva los valores originales, no los recalibrados.
        version = [h for h in db.historial_umbral("tsuki", "codo")
                   if h["id_umbral"] == id_vigente][0]
        assert version["valor_min"] == 160.0, version
    finally:
        _cerrar(db, path)


def test_rechaza_un_maximo_menor_que_el_minimo():
    db, path = _base_temporal()
    try:
        try:
            db.actualizar_umbral("tsuki", "codo", 175, 160, id_entrenador=None)
        except ValueError:
            return
        raise AssertionError("deberia rechazar un rango invertido")
    finally:
        _cerrar(db, path)


def test_sin_base_de_datos_usa_los_valores_de_literatura():
    reglas = KarateRules()
    assert reglas.rango("tsuki", "codo") == (160.0, 175.0)
    assert reglas.id_umbral_principal("tsuki") is None, \
        "sin base de datos no hay version que anotar"
    correcto, _, _ = reglas.evaluate_tsuki(168)
    assert correcto


def test_la_maquina_de_estados_hereda_el_umbral_de_kime():
    # El umbral de extension de la FSM y el criterio de Kime son el mismo
    # numero: recalibrar uno debe mover el otro.
    db, path = _base_temporal()
    try:
        maquina = MaeGeriStateMachine(5, KarateRules(db.cargar_umbrales_vigentes()))
        assert maquina.umbral_extension == 160.0, maquina.umbral_extension

        db.actualizar_umbral("mae_geri", "rodilla_kime", 170, 180, id_entrenador=None)
        recalibrada = MaeGeriStateMachine(5, KarateRules(db.cargar_umbrales_vigentes()))
        assert recalibrada.umbral_extension == 170.0, recalibrada.umbral_extension
    finally:
        _cerrar(db, path)


def test_umbral_sin_maximo_no_limita_por_arriba():
    # La velocidad angular del Mae Geri tiene minimo pero no maximo.
    reglas = KarateRules()
    assert reglas.rango("mae_geri", "velocidad_angular") == (400.0, None)
    correcto, mensaje, _ = reglas.evaluate_mae_geri(170, 5000)
    assert correcto, mensaje


if __name__ == "__main__":
    pruebas = [
        test_siembra_es_idempotente,
        test_las_reglas_usan_los_umbrales_de_la_base,
        test_recalibrar_crea_version_nueva_sin_borrar_la_anterior,
        test_la_medicion_registra_el_umbral_que_la_juzgo,
        test_rechaza_un_maximo_menor_que_el_minimo,
        test_sin_base_de_datos_usa_los_valores_de_literatura,
        test_la_maquina_de_estados_hereda_el_umbral_de_kime,
        test_umbral_sin_maximo_no_limita_por_arriba,
    ]

    ok, fallidas = 0, 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"PASS - {prueba.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"FAIL - {prueba.__name__}: {e}")
            fallidas += 1

    print(f"\n{ok}/{len(pruebas)} pruebas pasaron.")
    if fallidas:
        raise SystemExit(1)
