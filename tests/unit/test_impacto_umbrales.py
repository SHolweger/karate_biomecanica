"""
Pruebas del resumen de impacto de una recalibración (RF-08).

Lo que se verifica es la traducción: el motor de re-evaluación devuelve listas
de filas, y el cuerpo técnico decide leyendo frases. Si la traducción miente
—por omisión o por exceso— la decisión se toma mal, y es una decisión sobre la
vara con que se mide a los alumnos.

El módulo no importa CustomTkinter, así que todo esto corre también en
integración continua.
"""
import pytest

from gui.impacto_umbrales import (COBERTURA_MINIMA, NO_SE_ESCRIBE, SIN_IMPACTO,
                                  SIN_MEDICIONES, agrupar_por_tecnica, aviso_de_cobertura,
                                  describir_grupo, resumen, titular)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


def cambio(tecnica="kokutsu_dachi", correcto_nuevo=False):
    return {"tecnica_clave": tecnica, "correcto": True, "correcto_nuevo": correcto_nuevo,
            "diagnostico_nuevo": "POSTURA: CORREGIR ALTURA"}


def informe(cambian=(), sostienen=(), no_juzgadas=()):
    return {"cambian": list(cambian), "sostienen": list(sostienen),
            "no_juzgadas": list(no_juzgadas),
            "total": len(cambian) + len(sostienen) + len(no_juzgadas)}


# ---------------- el titular ----------------

@ficha(
    id_caso="TC-AUTO-047",
    nombre="El impacto de una recalibración se expresa en veredictos que cambian, no en filas",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "recalibrar sin ver el efecto es cambiar la vara de medir a ciegas; el número de "
        "veredictos que se mueven es lo que le dice al cuerpo técnico si el ajuste describe "
        "mejor la postura o si se pasó de estricto"
    ),
    componente="gui/impacto_umbrales.py (titular)",
    requisitos="RF-08",
    precondiciones="Ninguna. El módulo no importa CustomTkinter",
    datos_entrada="Informe con 3 mediciones que cambian y 2 que sostienen su veredicto",
    pasos=[
        Paso("Invocar titular() con el informe", "Se cuentan cambios sobre juzgadas"),
        Paso("Leer la frase resultante",
             "assert dice «3 de 5 mediciones cambiarían de veredicto»"),
    ],
    resultado_esperado="Una frase que el cuerpo técnico puede usar para decidir",
)
def test_el_titular_cuenta_los_cambios_sobre_las_juzgadas():
    texto = titular(informe(cambian=[cambio()] * 3, sostienen=[{}] * 2))
    assert texto == "3 de 5 mediciones cambiarían de veredicto."


def test_una_sola_medicion_se_redacta_en_singular():
    """Un texto que dice «1 mediciones cambiarían» desacredita al resto del reporte."""
    assert titular(informe(cambian=[cambio()])) == "1 de 1 medición cambiaría de veredicto."


def test_sin_impacto_se_dice_explicitamente():
    assert titular(informe(sostienen=[{}] * 10)) == SIN_IMPACTO


def test_sin_mediciones_no_se_finge_un_resultado():
    """«Ninguna cambiaría» sobre cero mediciones sería una garantía falsa."""
    assert titular(informe()) == SIN_MEDICIONES


# ---------------- la dirección del cambio ----------------

def test_se_cuentan_por_separado_las_dos_direcciones():
    """
    Que doce pasen a incorrectas significa un criterio más exigente; que doce
    pasen a correctas, uno más permisivo. Sumarlas borraría ese dato.
    """
    grupos = agrupar_por_tecnica([
        cambio(correcto_nuevo=False), cambio(correcto_nuevo=False),
        cambio(correcto_nuevo=True),
    ])

    assert grupos["kokutsu_dachi"]["a_incorrecto"] == 2
    assert grupos["kokutsu_dachi"]["a_correcto"] == 1
    assert grupos["kokutsu_dachi"]["total"] == 3


def test_cada_tecnica_se_cuenta_aparte():
    grupos = agrupar_por_tecnica([cambio("kokutsu_dachi"), cambio("zenkutsu_dachi"),
                                  cambio("zenkutsu_dachi")])

    assert set(grupos) == {"kokutsu_dachi", "zenkutsu_dachi"}
    assert grupos["zenkutsu_dachi"]["total"] == 2


def test_la_linea_de_una_tecnica_nombra_las_direcciones_presentes():
    assert describir_grupo({"a_incorrecto": 8, "a_correcto": 0, "total": 8}) \
        == "8 dejan de ser correctas"
    assert describir_grupo({"a_incorrecto": 3, "a_correcto": 2, "total": 5}) \
        == "3 dejan de ser correctas · 2 pasan a ser correctas"


# ---------------- la cobertura ----------------

def test_cuando_parte_del_historial_queda_fuera_se_advierte():
    aviso = aviso_de_cobertura({"juzgadas": 200, "reevaluables": 150})

    assert "150 de 200" in aviso
    assert "50" in aviso
    assert "anteriores" in aviso


def test_con_cobertura_baja_se_avisa_que_el_resultado_describe_la_muestra():
    """
    «No cambia casi nada» deja de ser una conclusión sobre el historial cuando
    la mayor parte quedó fuera del recuento.
    """
    aviso = aviso_de_cobertura({"juzgadas": 200, "reevaluables": 20})
    assert "describe la muestra" in aviso


def test_con_cobertura_suficiente_no_se_repite_el_aviso():
    """Un aviso que aparece siempre deja de leerse."""
    justo_encima = int(200 * COBERTURA_MINIMA) + 1
    aviso = aviso_de_cobertura({"juzgadas": 200, "reevaluables": justo_encima})
    assert "describe la muestra" not in aviso


def test_con_el_historial_completo_no_hay_aviso():
    assert aviso_de_cobertura({"juzgadas": 200, "reevaluables": 200}) is None


def test_sin_historial_no_hay_aviso_de_cobertura():
    assert aviso_de_cobertura({"juzgadas": 0, "reevaluables": 0}) is None


# ---------------- el resumen completo ----------------

def test_el_resumen_siempre_aclara_que_no_escribe_nada():
    """
    Consultar el impacto no puede parecer que aplica el cambio: el veredicto
    registrado es la evidencia de qué criterio regía al medir.
    """
    salida = resumen(informe(cambian=[cambio()]), {"juzgadas": 1, "reevaluables": 1})
    assert salida["nota"] == NO_SE_ESCRIBE


def test_el_resumen_marca_si_hubo_cambios():
    con = resumen(informe(cambian=[cambio()]))
    sin = resumen(informe(sostienen=[{}]))

    assert con["hay_cambios"] is True
    assert sin["hay_cambios"] is False


def test_el_resumen_funciona_sin_datos_de_cobertura():
    salida = resumen(informe(cambian=[cambio()]))
    assert salida["cobertura"] is None
