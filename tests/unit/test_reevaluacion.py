"""
Pruebas de la re-evaluación de mediciones guardadas (RF-08).

Lo que está en juego: los rangos de Kokutsu Dachi que hoy gobiernan el
clasificador son provisionales, a confirmar con el cuerpo técnico. Si esa
confirmación corrige un número, la pregunta inmediata es cuánto del historial
ya registrado cambiaría de veredicto — y responderla sin volver al dojo es la
diferencia entre una recalibración y una sesión de medición repetida.

Estas pruebas fijan dos cosas: que un veredicto se puede recalcular con otros
umbrales, y que el sistema se niega a recalcular cuando la fila no alcanza. La
segunda importa tanto como la primera: un veredicto inventado sobre una técnica
que nadie midió completa es peor que no tener veredicto.
"""
import pytest

from expert_system.knowledge_base import KarateRules
from expert_system.reevaluacion import (MedicionNoReevaluable, comparar,
                                        es_reevaluable, reevaluar)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


def reglas_con(**umbrales):
    """
    Construye reglas con umbrales alterados, como lo haría una recalibración.

    Recibe (tecnica, articulacion) aplanados con doble guion bajo para poder
    escribirlos como argumentos nombrados: kokutsu_dachi__rodilla_trasera.
    """
    bd = {}
    for clave_plana, (v_min, v_max) in umbrales.items():
        tecnica, articulacion = clave_plana.split("__", 1)
        bd[(tecnica, articulacion)] = {
            "valor_min": v_min, "valor_max": v_max, "id_umbral": 99,
        }
    return KarateRules(umbrales_bd=bd)


def medicion(tecnica_clave, a1, a2=None, correcto=None):
    return {"tecnica_clave": tecnica_clave, "angulo_regla_1": a1,
            "angulo_regla_2": a2, "correcto": correcto}


# ---------------- el caso que originó el módulo ----------------

@ficha(
    id_caso="TC-AUTO-039",
    nombre="Una medición de Kokutsu Dachi se vuelve a juzgar cuando el sensei corrige el umbral",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "los rangos de Kokutsu Dachi vigentes son provisionales; sin re-evaluación, "
        "confirmarlos con el cuerpo técnico obligaría a repetir toda la toma de datos en el dojo"
    ),
    componente="expert_system/reevaluacion.py (reevaluar)",
    requisitos="RF-08",
    precondiciones="Ninguna. El módulo no depende de base de datos ni de cámara",
    datos_entrada=(
        "Kokutsu con rodilla frontal 160° y trasera 105°, juzgada correcta con el umbral "
        "vigente (trasera 90-120°); umbral corregido a 90-100°"
    ),
    pasos=[
        Paso("Construir reglas con el umbral corregido de la rodilla trasera",
             "KarateRules toma el rango nuevo"),
        Paso("Invocar reevaluar() con los dos ángulos guardados",
             "assert correcto is False: 105° queda fuera de 90-100°"),
    ],
    resultado_esperado="El veredicto recalculado es Incorrecto, sin haber vuelto a medir",
)
def test_corregir_el_umbral_trasero_cambia_el_veredicto_de_un_kokutsu_guardado():
    # Tal como se midió: con el umbral vigente (trasera 90-120°) esto es correcto.
    correcto_original, _ = reevaluar("kokutsu_dachi", 160.0, 105.0, KarateRules())
    assert correcto_original is True

    # El sensei ajusta el rango de la rodilla trasera. Los mismos 105° ya no pasan.
    correcto_nuevo, _ = reevaluar(
        "kokutsu_dachi", 160.0, 105.0,
        reglas_con(kokutsu_dachi__rodilla_trasera=(90.0, 100.0)),
    )
    assert correcto_nuevo is False


def test_reevaluar_no_toca_la_medicion_original():
    """El informe se calcula sobre la fila; la fila no se modifica."""
    fila = medicion("kokutsu_dachi", 160.0, 105.0, correcto=True)
    copia = dict(fila)

    comparar([fila], reglas_con(kokutsu_dachi__rodilla_trasera=(90.0, 100.0)))

    assert fila == copia, "el módulo no debe escribir sobre lo ya registrado"


# ---------------- técnicas de un solo ángulo ----------------

def test_un_tsuki_se_reevalua_con_su_unico_angulo():
    correcto, mensaje = reevaluar("tsuki", 168.0, None, KarateRules())
    assert correcto is True
    assert mensaje == "TSUKI: EXCELENTE"


def test_endurecer_el_umbral_del_tsuki_vuelve_hiperextendido_lo_que_era_excelente():
    correcto, mensaje = reevaluar(
        "tsuki", 168.0, None, reglas_con(tsuki__codo=(160.0, 165.0)))
    assert correcto is False
    assert "HIPEREXTENDIDO" in mensaje


# ---------------- lo que NO se puede re-juzgar ----------------

def test_el_mae_geri_no_es_reevaluable_porque_su_veredicto_usa_la_velocidad():
    """
    El Kime se juzga por ángulo Y por velocidad angular pico. La velocidad la
    observa la máquina de estados a lo largo de varios fotogramas y la fila no
    la guarda, así que recalcular daría un veredicto que nadie midió.
    """
    assert es_reevaluable("mae_geri", 175.0) is False

    with pytest.raises(MedicionNoReevaluable, match="velocidad angular"):
        reevaluar("mae_geri", 175.0, None, KarateRules())


def test_una_transicion_no_es_reevaluable_porque_no_se_juzgo_contra_ningun_umbral():
    assert es_reevaluable(None, 140.0) is False

    with pytest.raises(MedicionNoReevaluable, match="transición"):
        reevaluar(None, 140.0, None, KarateRules())


def test_una_postura_de_dos_articulaciones_con_un_solo_angulo_se_rechaza():
    """
    Este es exactamente el estado en que quedaron las mediciones anteriores a
    esta versión: la fila guardaba un ángulo aunque la regla juzgara dos.
    """
    assert es_reevaluable("kokutsu_dachi", 160.0, None) is False

    with pytest.raises(MedicionNoReevaluable, match="dos articulaciones"):
        reevaluar("kokutsu_dachi", 160.0, None, KarateRules())


# ---------------- el informe comparativo ----------------

def test_el_informe_separa_las_que_sostienen_de_las_que_cambian():
    mediciones = [
        medicion("kokutsu_dachi", 160.0, 105.0, correcto=True),   # 105 sale de 90-100 -> cambia
        medicion("kokutsu_dachi", 160.0,  95.0, correcto=True),   # 95 sigue dentro -> sostiene
        medicion("mae_geri", 175.0, None, correcto=True),         # no re-evaluable
    ]

    informe = comparar(mediciones, reglas_con(kokutsu_dachi__rodilla_trasera=(90.0, 100.0)))

    assert len(informe["cambian"]) == 1
    assert len(informe["sostienen"]) == 1
    assert len(informe["no_juzgadas"]) == 1
    assert informe["total"] == 3


def test_el_informe_dice_a_que_veredicto_cambia_cada_medicion():
    informe = comparar(
        [medicion("kokutsu_dachi", 160.0, 105.0, correcto=True)],
        reglas_con(kokutsu_dachi__rodilla_trasera=(90.0, 100.0)),
    )

    cambio = informe["cambian"][0]
    assert cambio["correcto"] is True          # lo que se registró
    assert cambio["correcto_nuevo"] is False   # lo que diría la regla de hoy
    assert cambio["diagnostico_nuevo"], "un cambio sin texto no le dice nada al sensei"


def test_las_no_juzgadas_explican_el_motivo():
    informe = comparar([medicion("mae_geri", 175.0, None, correcto=True)], KarateRules())

    assert "velocidad angular" in informe["no_juzgadas"][0]["motivo"]


def test_el_total_del_informe_cuenta_todas_las_mediciones_recibidas():
    """
    Sin esto se puede leer "solo cambian 3" ignorando que 200 quedaron fuera
    del recuento por no ser re-evaluables.
    """
    mediciones = [medicion("mae_geri", 175.0, None)] * 7 + [medicion("tsuki", 168.0, None, True)]

    informe = comparar(mediciones, KarateRules())

    assert informe["total"] == 8
    assert len(informe["no_juzgadas"]) == 7


def test_un_informe_sin_mediciones_no_revienta():
    informe = comparar([], KarateRules())
    assert informe["total"] == 0
    assert informe["cambian"] == []
