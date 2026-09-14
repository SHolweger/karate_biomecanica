"""
Pruebas de la validación del formulario de inscripción de alumnos (RF-07).

Lo que se fija aquí es el criterio con el que el sistema acepta o rechaza una
ficha: qué es obligatorio, qué se puede dejar en blanco y —el caso menos obvio—
cuándo el grado numérico procede y cuándo guardarlo produciría una ficha que se
contradice a sí misma.
"""
import pytest

from gui.registro_alumno import (CINTAS_CON_GRADO, COLORES_CINTA, DatosInvalidos,
                                 grados_de, interpretar_edad, interpretar_formulario,
                                 interpretar_peso, pide_grado)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


# ---------------- grado según el color de la cinta ----------------

@pytest.mark.parametrize("color", sorted(CINTAS_CON_GRADO))
def test_el_grado_se_pide_desde_la_cinta_cafe(color):
    assert pide_grado(color) is True
    assert grados_de(color), f"{color} debe ofrecer grados concretos"


@pytest.mark.parametrize("color", ["Blanca", "Amarilla", "Naranja", "Verde", "Azul", "Morada"])
def test_en_los_colores_iniciales_el_color_ya_determina_el_kyu(color):
    """
    Pedir el número por separado abriría la puerta a una ficha contradictoria:
    una cinta amarilla registrada como 2º kyu. El color ya lo dice.
    """
    assert pide_grado(color) is False
    assert grados_de(color) == []


def test_los_grados_ofrecidos_corresponden_al_color():
    assert grados_de("Café") == ["3er kyu", "2do kyu", "1er kyu"]
    assert grados_de("Negra")[0] == "1º dan"
    assert len(grados_de("Negra")) == 10


@ficha(
    id_caso="TC-AUTO-031",
    nombre="Un grado numérico escrito bajo un color de cinta que no lo admite se descarta al "
           "guardar, en vez de producir una ficha que se contradice",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="el campo de grado aparece y desaparece según el color elegido, de modo "
                         "que un sensei que escribe «1er kyu» y después corrige la cinta a "
                         "«Blanca» deja un valor huérfano en el formulario; guardarlo "
                         "registraría a un principiante como alumno avanzado y ese dato "
                         "alimenta después las estadísticas por grado",
    componente="gui/registro_alumno.py (interpretar_formulario)",
    requisitos="RF-07",
    precondiciones="Ninguna; la función es pura y no toca la base de datos",
    datos_entrada="Formulario con nombre «Marta Similox», color de cinta «Blanca» y grado "
                  "«1er kyu» remanente de una selección anterior",
    pasos=[
        Paso("Interpretar el formulario con cinta Café y grado «1er kyu»",
             "assert datos['grado_cinturon'] == '1er kyu' (el café sí admite grado)"),
        Paso("Interpretar el mismo formulario cambiando la cinta a «Blanca»",
             "assert datos['grado_cinturon'] is None (el grado se descarta)"),
        Paso("Comprobar que el resto de la ficha se conserva intacto",
             "assert datos['nombre'] == 'Marta Similox' y datos['color_cinta'] == 'Blanca'"),
    ],
    resultado_esperado="PASSED. La ficha guardada nunca afirma un grado que su color de cinta "
                       "contradice.",
    evidencia="Reporte de consola de pytest.",
)
def test_un_grado_huerfano_no_se_guarda():
    con_cafe = interpretar_formulario("Marta Similox", color_cinta="Café", grado="1er kyu")
    assert con_cafe["grado_cinturon"] == "1er kyu"

    con_blanca = interpretar_formulario("Marta Similox", color_cinta="Blanca", grado="1er kyu")
    assert con_blanca["grado_cinturon"] is None, "una cinta blanca no puede ser 1er kyu"
    assert con_blanca["nombre"] == "Marta Similox"
    assert con_blanca["color_cinta"] == "Blanca"


# ---------------- campos obligatorios y opcionales ----------------

@pytest.mark.parametrize("nombre", ["", "   ", None])
def test_el_nombre_es_el_unico_campo_obligatorio(nombre):
    with pytest.raises(DatosInvalidos, match="nombre"):
        interpretar_formulario(nombre)


def test_un_alumno_puede_inscribirse_solo_con_el_nombre():
    """
    Exigir peso o grado pondría un trámite delante del entrenamiento. El alumno
    se apunta el primer día y la ficha se completa después.
    """
    datos = interpretar_formulario("  Luis Garcia  ")

    assert datos["nombre"] == "Luis Garcia", "el nombre se recorta"
    assert all(datos[c] is None for c in
               ("edad", "peso_kg", "color_cinta", "grado_cinturon",
                "tiempo_entrenando", "notas"))


def test_la_ficha_completa_se_traduce_a_los_argumentos_de_crear_atleta():
    datos = interpretar_formulario(
        "Diego Morales", edad="16", peso="62.5", color_cinta="Café", grado="1er kyu",
        tiempo_entrenando="2 años", notas="  Lesión previa de rodilla derecha.  ")

    assert datos == {
        "nombre": "Diego Morales",
        "edad": 16,
        "peso_kg": 62.5,
        "color_cinta": "Café",
        "grado_cinturon": "1er kyu",
        "tiempo_entrenando": "2 años",
        "notas": "Lesión previa de rodilla derecha.",
    }


def test_un_color_de_cinta_inventado_se_rechaza():
    with pytest.raises(DatosInvalidos, match="color de cinta"):
        interpretar_formulario("Diego Morales", color_cinta="Turquesa")


def test_todos_los_colores_declarados_son_aceptados():
    for color in COLORES_CINTA:
        datos = interpretar_formulario("Diego Morales", color_cinta=color)
        assert datos["color_cinta"] == color


# ---------------- edad ----------------

@pytest.mark.parametrize("texto, esperado", [("16", 16), ("  8 ", 8), ("", None), ("   ", None)])
def test_la_edad_se_interpreta_o_queda_vacia(texto, esperado):
    assert interpretar_edad(texto) == esperado


@pytest.mark.parametrize("texto, fragmento", [
    ("dieciséis", "no es un número"),
    ("16.5", "no es un número"),
    ("2", "entre 3 y 99"),
    ("150", "entre 3 y 99"),
    ("-4", "entre 3 y 99"),
])
def test_una_edad_imposible_se_explica_en_lugar_de_guardarse(texto, fragmento):
    with pytest.raises(DatosInvalidos, match=fragmento):
        interpretar_edad(texto)


# ---------------- peso ----------------

@pytest.mark.parametrize("texto, esperado", [
    ("62.5", 62.5),
    ("62,5", 62.5),     # coma decimal, como se escribe en Guatemala
    (" 70 ", 70.0),
    ("", None),
])
def test_el_peso_admite_coma_decimal(texto, esperado):
    assert interpretar_peso(texto) == esperado


@pytest.mark.parametrize("texto, fragmento", [
    ("sesenta", "no es un número"),
    ("5", "entre 10 y 250"),
    ("400", "entre 10 y 250"),
])
def test_un_peso_imposible_se_explica(texto, fragmento):
    with pytest.raises(DatosInvalidos, match=fragmento):
        interpretar_peso(texto)


def test_el_error_nombra_el_campo_para_que_el_sensei_sepa_cual_corregir():
    """
    Un mensaje técnico («invalid literal for int()») deja al usuario sin saber
    qué arreglar. El texto va dirigido a quien llena la ficha.
    """
    with pytest.raises(DatosInvalidos) as error:
        interpretar_formulario("Diego Morales", edad="dieciséis")

    assert "edad" in str(error.value).lower()
    assert "dieciséis" in str(error.value)
