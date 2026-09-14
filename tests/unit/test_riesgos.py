"""
Pruebas de las señales de riesgo de lesión (RF-05, RF-07).

Es la parte del reporte donde una afirmación de más tiene consecuencias reales:
decirle a un instructor que su alumno está en riesgo cuando no lo está le hace
cambiar un entrenamiento sin motivo, y no decírselo cuando sí lo está es peor.
Por eso casi todas las pruebas de este módulo comprueban cuándo el sistema debe
CALLARSE: pocas repeticiones, diferencias dentro de lo normal, un desliz suelto.
"""
import pytest

from expert_system.riesgos import (ATENCION, MINIMO_POR_LADO, PREVENCION, RIESGO,
                                   UMBRAL_ASIMETRIA, alcance, analizar, evaluar_asimetria,
                                   evaluar_hiperextension)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


def lado(evaluaciones, precision):
    aciertos = None if precision is None else round(evaluaciones * precision / 100)
    return {"evaluaciones": evaluaciones, "aciertos": aciertos, "precision": precision}


# ---------------- hiperextensión ----------------

def test_una_hiperextension_aislada_no_se_reporta():
    """Una repetición mal ejecutada es un desliz, no un hábito."""
    assert evaluar_hiperextension(veces=1, total=40) is None


def test_una_hiperextension_frecuente_se_reporta_como_riesgo():
    hallazgo = evaluar_hiperextension(veces=12, total=40)

    assert hallazgo is not None
    assert hallazgo["nivel"] == RIESGO
    assert "12 de 40" in hallazgo["detalle"]
    assert "ligamento" in hallazgo["detalle"]
    assert hallazgo["recomendacion"], "un riesgo sin qué hacer al respecto no sirve"


def test_una_proporcion_baja_se_reporta_como_atencion_y_no_como_riesgo():
    """Distinguir grados evita que todo se vea igual de urgente."""
    hallazgo = evaluar_hiperextension(veces=6, total=40)   # 15 %

    assert hallazgo["nivel"] == ATENCION


def test_la_proporcion_importa_mas_que_la_cuenta():
    """
    Dos hiperextensiones en cuatro repeticiones y dos en doscientas son
    situaciones opuestas. Sin el total, la cuenta suelta no dice nada.
    """
    assert evaluar_hiperextension(veces=2, total=4)["nivel"] == RIESGO
    assert evaluar_hiperextension(veces=2, total=200) is None


def test_sin_evaluaciones_no_se_afirma_nada():
    assert evaluar_hiperextension(veces=0, total=0) is None


# ---------------- asimetría ----------------

@ficha(
    id_caso="TC-AUTO-036",
    nombre="La asimetría entre lados solo se reporta cuando hay repeticiones suficientes en "
           "ambos, de modo que un fallo aislado no se presente como señal de lesión",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="con tres repeticiones por lado un solo fallo mueve el porcentaje 33 "
                         "puntos, de modo que casi cualquier sesión corta produciría una "
                         "«asimetría marcada»; un instructor que recibe esa alerta cambia el "
                         "entrenamiento de un alumno sano, y si la alerta salta siempre deja de "
                         "creerle también cuando es real",
    componente="expert_system/riesgos.py (evaluar_asimetria)",
    requisitos=("RF-05", "RF-07"),
    precondiciones="Ninguna; la función es pura y no consulta la base de datos",
    datos_entrada="Lado izquierdo con 3 evaluaciones al 33 % y derecho con 3 al 100 % (67 puntos "
                  "de diferencia, por debajo del mínimo de repeticiones); después los mismos "
                  "porcentajes con 12 evaluaciones por lado",
    pasos=[
        Paso("Evaluar la asimetría con 3 repeticiones por lado",
             "assert el resultado es None pese a los 67 puntos de diferencia"),
        Paso("Evaluar los mismos porcentajes con 12 repeticiones por lado",
             "assert se reporta un hallazgo de nivel 'riesgo'"),
        Paso("Comprobar que el hallazgo nombra el lado rezagado",
             "assert 'izquierdo' aparece en el título"),
    ],
    resultado_esperado="PASSED. El sistema se pronuncia sobre asimetría solo cuando la muestra "
                       "lo respalda, y nombra qué lado trabajar.",
    evidencia="Reporte de consola de pytest.",
)
def test_la_asimetria_exige_repeticiones_suficientes_en_ambos_lados():
    escasas = {"izquierdo": lado(3, 33.0), "derecho": lado(3, 100.0)}
    assert evaluar_asimetria(escasas) is None, "con tres repeticiones cualquier fallo distorsiona"

    suficientes = {"izquierdo": lado(12, 33.0), "derecho": lado(12, 100.0)}
    hallazgo = evaluar_asimetria(suficientes)

    assert hallazgo is not None
    assert hallazgo["nivel"] == RIESGO
    assert "izquierdo" in hallazgo["titulo"], "debe nombrar el lado rezagado"


def test_un_solo_lado_con_pocas_repeticiones_basta_para_callar():
    mezcla = {"izquierdo": lado(MINIMO_POR_LADO - 1, 40.0),
              "derecho": lado(30, 95.0)}

    assert evaluar_asimetria(mezcla) is None


def test_una_diferencia_dentro_de_lo_normal_no_se_reporta():
    """
    Una misma persona varía entre repeticiones. Por debajo del umbral, la
    diferencia entre lados cabe dentro de esa variación.
    """
    parejo = {"izquierdo": lado(20, 82.0), "derecho": lado(20, 82.0 + UMBRAL_ASIMETRIA - 1)}

    assert evaluar_asimetria(parejo) is None


def test_la_asimetria_se_detecta_en_cualquier_direccion():
    izquierdo_flojo = evaluar_asimetria({"izquierdo": lado(20, 50.0), "derecho": lado(20, 90.0)})
    derecho_flojo = evaluar_asimetria({"izquierdo": lado(20, 90.0), "derecho": lado(20, 50.0)})

    assert "izquierdo" in izquierdo_flojo["titulo"]
    assert "derecho" in derecho_flojo["titulo"]


def test_un_lado_sin_evaluaciones_cerradas_no_produce_comparacion():
    """
    Precisión None significa "no medido", no "cero". Compararla con un número
    afirmaría que ese lado falla todo.
    """
    sin_datos = {"izquierdo": lado(0, None), "derecho": lado(20, 90.0)}

    assert evaluar_asimetria(sin_datos) is None


def test_un_lado_ausente_no_revienta():
    assert evaluar_asimetria({}) is None
    assert evaluar_asimetria({"derecho": lado(20, 90.0)}) is None


# ---------------- análisis completo ----------------

def test_una_sesion_limpia_lo_declara_en_vez_de_devolver_una_lista_vacia():
    """
    Un bloque vacío se leería como que el análisis no corrió, que es distinto de
    que no encontró nada.
    """
    hallazgos = analizar({"veces": 0, "total": 30},
                         {"izquierdo": lado(15, 88.0), "derecho": lado(15, 91.0)})

    assert len(hallazgos) == 1
    assert hallazgos[0]["nivel"] == PREVENCION
    assert "Sin señales de riesgo" in hallazgos[0]["titulo"]


def test_los_hallazgos_se_ordenan_del_mas_urgente_al_informativo():
    hallazgos = analizar({"veces": 6, "total": 40},                      # atención
                         {"izquierdo": lado(20, 30.0), "derecho": lado(20, 95.0)})  # riesgo

    assert [h["nivel"] for h in hallazgos] == [RIESGO, ATENCION]


def test_el_analisis_declara_donde_termina_su_alcance():
    """
    Una sección de prevención que no dice qué no cubre invita a leerla como si
    cubriera todo.
    """
    texto = alcance()

    assert "valgo" in texto and "inerciales" in texto
