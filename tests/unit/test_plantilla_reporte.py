"""
Pruebas unitarias de la plantilla de reportes (tests/reporte/plantilla.py).

La plantilla es la herramienta que decide si un caso de prueba está bien
documentado, así que ella misma tiene que estar probada: si aceptara una ficha
incompleta, el documento generado se vería impecable y estaría vacío por dentro.

Las fichas de este archivo se construyen a mano, sin el decorador, para no
contaminar el registro global de IDs del proyecto.
"""
import dataclasses

import pytest

from reporte.plantilla import (
    FichaCasoPrueba,
    FichaInvalida,
    Paso,
    Prioridad,
    TipoPrueba,
    ficha,
    verificar_correlativos,
)

pytestmark = pytest.mark.unitaria


CAMPOS_VALIDOS = dict(
    id_caso="TC-AUTO-900",
    nombre="Ficha de ejemplo usada solo por las pruebas de la plantilla",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="sin plantilla verificada, la documentación puede mentir",
    componente="tests/reporte/plantilla.py (FichaCasoPrueba)",
    requisitos="RF-05",
    precondiciones="Ninguna",
    datos_entrada="Los campos declarados en CAMPOS_VALIDOS",
    pasos=[
        Paso("Construir la ficha", "No se lanza excepción"),
        Paso("Comprobar el resultado", "assert ficha.id_caso == 'TC-AUTO-900'"),
    ],
    resultado_esperado="PASSED",
)


def ficha_con(**cambios):
    """Ficha válida con los campos indicados sustituidos."""
    return FichaCasoPrueba(**{**CAMPOS_VALIDOS, **cambios})


# ---------------------------------------------------------------------------
# Construcción y normalización
# ---------------------------------------------------------------------------
def test_una_ficha_completa_se_construye_sin_errores():
    f = ficha_con()

    assert f.id_caso == "TC-AUTO-900"
    assert f.numero == 900
    assert f.tipo is TipoPrueba.UNITARIA


def test_acepta_el_tipo_y_la_prioridad_escritos_como_texto():
    """Comodidad para quien escribe la ficha: no obliga a importar los Enum."""
    f = ficha_con(tipo="unitaria", prioridad="alta")

    assert f.tipo is TipoPrueba.UNITARIA
    assert f.prioridad is Prioridad.ALTA


def test_un_requisito_suelto_se_normaliza_a_tupla():
    assert ficha_con(requisitos="RNF-05").requisitos == ("RNF-05",)
    assert ficha_con(requisitos="RF-01, RF-05").requisitos == ("RF-01", "RF-05")
    assert ficha_con(requisitos=["RF-01", "RF-05"]).requisitos == ("RF-01", "RF-05")


def test_los_pasos_admiten_tuplas_ademas_de_objetos_paso():
    f = ficha_con(pasos=[("Hacer algo", "assert algo"), Paso("Y algo más", "assert más")])

    assert all(isinstance(p, Paso) for p in f.pasos)
    assert f.pasos[0].accion == "Hacer algo"


def test_la_ficha_es_inmutable():
    """Una ficha es evidencia declarada de antemano; no se edita en caliente."""
    f = ficha_con()

    with pytest.raises(dataclasses.FrozenInstanceError):
        f.id_caso = "TC-AUTO-999"


# ---------------------------------------------------------------------------
# Reglas del formato
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("id_malo", ["TC-001", "tc-auto-001", "TC-AUTO-1", "", "TC-AUTO-0001"])
def test_rechaza_un_identificador_fuera_del_patron(id_malo):
    with pytest.raises(FichaInvalida) as error:
        ficha_con(id_caso=id_malo)

    assert "id_caso" in str(error.value)


@pytest.mark.parametrize("campo", [
    "justificacion_riesgo", "componente", "precondiciones",
    "datos_entrada", "resultado_esperado",
])
def test_ningun_campo_obligatorio_puede_quedar_vacio(campo):
    with pytest.raises(FichaInvalida) as error:
        ficha_con(**{campo: "   "})

    assert campo in str(error.value)


def test_rechaza_un_nombre_demasiado_corto():
    with pytest.raises(FichaInvalida) as error:
        ficha_con(nombre="Prueba 1")

    assert "nombre" in str(error.value)


@pytest.mark.parametrize("requisito", ["RF-5", "REQ-01", "RF01", "RNF-123"])
def test_rechaza_un_requisito_mal_escrito(requisito):
    with pytest.raises(FichaInvalida) as error:
        ficha_con(requisitos=requisito)

    assert "requisitos" in str(error.value)


def test_exige_trazabilidad_a_algun_requisito():
    with pytest.raises(FichaInvalida) as error:
        ficha_con(requisitos=[])

    assert "requisito" in str(error.value)


def test_exige_un_minimo_de_pasos():
    with pytest.raises(FichaInvalida) as error:
        ficha_con(pasos=[Paso("Un solo paso", "assert algo")])

    assert "pasos" in str(error.value)


def test_exige_al_menos_una_asercion_explicita():
    """
    Regla de fondo: una ficha cuyos pasos solo describen acciones documenta una
    ejecución, no una prueba. Debe verse al menos un `assert`.
    """
    with pytest.raises(FichaInvalida) as error:
        ficha_con(pasos=[
            Paso("Abrir la aplicación", "La ventana aparece"),
            Paso("Mirar la pantalla", "Se ve bien"),
        ])

    assert "aserción" in str(error.value)


def test_un_tipo_de_prueba_inexistente_se_rechaza():
    with pytest.raises(FichaInvalida):
        ficha_con(tipo="carga")


@ficha(
    id_caso="TC-AUTO-019",
    nombre="Una ficha incompleta es rechazada y el error enumera todos los campos que "
           "incumplen el formato",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="si la plantilla aceptara fichas incompletas, el documento de "
                         "casos se vería impecable y estaría vacío por dentro",
    componente="tests/reporte/plantilla.py (FichaCasoPrueba)",
    requisitos="RF-08",
    precondiciones="Ninguna. La ficha se construye directamente, sin pasar por el "
                   "decorador ni por el registro global",
    datos_entrada="Ficha válida con tres campos corrompidos a la vez: id_caso=\"MALO\", "
                  "nombre=\"corto\", requisitos=\"X-1\"",
    pasos=[
        Paso("Construir la ficha con los tres campos inválidos",
             "Se lanza `FichaInvalida` en el momento de la construcción"),
        Paso("Inspeccionar la lista de problemas del error",
             "assert len(error.value.problemas) >= 3"),
        Paso("Verificar que el mensaje nombra cada campo incumplido",
             "El texto del error menciona id_caso, nombre y requisitos"),
    ],
    resultado_esperado="PASSED. La validación es acumulativa: quien escribe una ficha ve "
                       "de una sola vez todo lo que le falta",
)
def test_el_error_enumera_todos_los_problemas_de_una_vez():
    """
    Quien escribe una ficha nueva debe ver la lista completa de lo que le falta,
    no descubrirlo campo por campo en corridas sucesivas.
    """
    with pytest.raises(FichaInvalida) as error:
        ficha_con(id_caso="MALO", nombre="corto", requisitos="X-1")

    assert len(error.value.problemas) >= 3


# ---------------------------------------------------------------------------
# Renderizado
# ---------------------------------------------------------------------------
def test_el_markdown_contiene_todos_los_campos_del_formato():
    salida = ficha_con().a_markdown(nodeid="tests/unit/test_x.py::test_y",
                                    veredicto="PASSED")

    for encabezado in ("ID del Caso de Prueba", "Nombre de la Prueba", "Tipo de Prueba",
                       "Prioridad / Riesgo", "Precondiciones",
                       "Datos de Entrada (Test Data)", "Archivo / Clase del Script",
                       "Pasos de Ejecución Automatizada y Aserciones",
                       "Criterios de Salida y Manejo de Errores"):
        assert encabezado in salida, f"falta la sección '{encabezado}' en la ficha"

    assert "tests/unit/test_x.py::test_y" in salida
    assert "PASSED" in salida


def test_el_markdown_marca_la_casilla_del_tipo_seleccionado():
    salida = ficha_con(tipo=TipoPrueba.E2E).a_markdown()

    assert "**[X]** Interfaz (UI/E2E)" in salida
    assert "[ ] Unitaria" in salida


def test_el_markdown_declara_cuando_el_script_no_se_recolecto():
    """El reporte no inventa la ruta del script: si no la tiene, lo dice."""
    salida = ficha_con().a_markdown()

    assert "no recolectado" in salida


def test_los_pasos_se_numeran_solos_en_orden():
    salida = ficha_con(pasos=[
        Paso("Primero", "assert a"),
        Paso("Segundo", "assert b"),
        Paso("Tercero", "assert c"),
    ]).a_markdown()

    assert "| 1 | Primero |" in salida
    assert "| 3 | Tercero |" in salida


# ---------------------------------------------------------------------------
# Integridad de la serie de casos
# ---------------------------------------------------------------------------
def test_una_serie_correlativa_no_reporta_problemas():
    serie = [ficha_con(id_caso=f"TC-AUTO-{n:03d}") for n in (1, 2, 3)]

    assert verificar_correlativos(serie) == []


def test_detecta_un_hueco_en_la_numeracion():
    """Un hueco suele significar un caso borrado del código pero citado en el informe."""
    serie = [ficha_con(id_caso=f"TC-AUTO-{n:03d}") for n in (1, 2, 5)]

    problemas = verificar_correlativos(serie)

    assert len(problemas) == 1
    assert "TC-AUTO-003" in problemas[0] and "TC-AUTO-004" in problemas[0]


def test_detecta_identificadores_repetidos():
    serie = [ficha_con(id_caso="TC-AUTO-001"), ficha_con(id_caso="TC-AUTO-001")]

    assert any("repetido" in p for p in verificar_correlativos(serie))


def test_el_decorador_impide_que_dos_pruebas_reclamen_el_mismo_id():
    campos = {**CAMPOS_VALIDOS, "id_caso": "TC-AUTO-901"}

    @ficha(**campos)
    def prueba_falsa_uno():
        ...

    with pytest.raises(FichaInvalida) as error:
        @ficha(**campos)
        def prueba_falsa_dos():
            ...

    assert "duplicado" in str(error.value)


def test_el_decorador_cuelga_la_ficha_sin_envolver_la_funcion():
    """
    pytest debe seguir viendo la función original: si el decorador la envolviera,
    se perderían la firma y las fixtures que pytest inyecta por nombre.
    """
    @ficha(**{**CAMPOS_VALIDOS, "id_caso": "TC-AUTO-902"})
    def prueba_falsa(reglas, tmp_path):
        ...

    assert prueba_falsa.ficha_caso.id_caso == "TC-AUTO-902"
    assert prueba_falsa.__name__ == "prueba_falsa"
    assert prueba_falsa.__code__.co_varnames[:2] == ("reglas", "tmp_path")


# --------------------------------------------------------------------------
# Auditoría del formato: qué es incumplimiento y qué es limitación del entorno
# --------------------------------------------------------------------------

class _ConfigFalsa:
    """Config mínima: el auditor no la consulta, pero el constructor la exige."""

    def getoption(self, _nombre):
        return False


def _auditor(ids, modulos_omitidos=()):
    """Auditor cargado con las fichas indicadas y, opcionalmente, módulos omitidos."""
    from reporte.plugin import CasoDocumentado, ReporteFormal

    auditor = ReporteFormal(_ConfigFalsa())
    for numero in ids:
        ficha_caso = ficha_con(id_caso=f"TC-AUTO-{numero:03d}")
        auditor.casos[ficha_caso.id_caso] = CasoDocumentado(
            ficha=ficha_caso, nodeid=f"tests/unit/test_x.py::test_{numero}")
    auditor.modulos = {"tests/unit/test_x.py": {f"TC-AUTO-{n:03d}" for n in ids}}
    auditor.modulos_omitidos = list(modulos_omitidos)
    return auditor


@pytest.mark.unitaria
def test_un_hueco_real_es_incumplimiento_en_una_corrida_completa():
    """
    Sin módulos omitidos, un hueco significa que un caso documentado se borró
    del código: eso sí debe romper la corrida con --exigir-fichas.
    """
    problemas, avisos = _auditor([1, 2, 4])._auditar_formato()

    assert any("huecos" in p for p in problemas)
    assert avisos == []


@pytest.mark.unitaria
def test_un_hueco_por_modulos_omitidos_es_solo_un_aviso():
    """
    Regresión de una falla real de integración continua. El entorno de CI no
    tiene interfaz gráfica, así que omite las pruebas E2E en bloque; sus fichas
    se declaran al importar el módulo, de modo que nunca se registran y la serie
    aparece incompleta. Tratarlo como incumplimiento dejaba la suite en rojo de
    forma permanente, y una señal siempre roja deja de avisar cuando algo se
    rompe de verdad.
    """
    problemas, avisos = _auditor(
        [1, 2, 4], modulos_omitidos=["tests/e2e/test_gui_flow.py"])._auditar_formato()

    assert problemas == [], "un hueco explicado por el entorno no es un incumplimiento"
    assert any("huecos" in a for a in avisos), "pero debe informarse igual"
    assert any("omitido" in a for a in avisos), "y explicarse por qué"


@pytest.mark.unitaria
def test_un_modulo_sin_ficha_sigue_siendo_incumplimiento_aunque_haya_omitidos():
    """
    La tolerancia alcanza solo a los huecos de numeración. Un módulo de pruebas
    sin ningún caso documentado es un incumplimiento real en cualquier entorno.
    """
    auditor = _auditor([1, 2], modulos_omitidos=["tests/e2e/test_gui_flow.py"])
    auditor.modulos["tests/unit/test_sin_ficha.py"] = set()

    problemas, _ = auditor._auditar_formato()

    assert any("ningún caso documentado" in p for p in problemas)


# ---------------- estabilidad del catálogo versionado ----------------

@pytest.mark.unitaria
def test_el_catalogo_no_lleva_fecha_ni_totales_que_cambien_en_cada_corrida():
    """
    El catálogo está versionado en el repositorio. Una marca de tiempo lo
    reescribiría en cada `pytest`, y un total de pruebas recolectadas lo
    reescribiría además según el entorno, porque en integración continua se
    omiten los módulos que necesitan cámara.

    Ese churn tiene dos costos reales: ensucia cada comparación de versiones con
    un cambio que no corresponde a ninguna modificación del código, y deja el
    archivo modificado en la copia de trabajo, lo que impide aplicar parches
    hasta descartarlo a mano. (Ocurrió el 14-sep-2026 al intentar aplicar un
    lote sobre un repositorio donde la suite acababa de correr.)
    """
    documento = _auditor([1, 2, 3])._documento_casos()

    assert "**Generado:**" not in documento, "una fecha reescribe el archivo en cada corrida"
    assert "recolectadas" not in documento, "el total depende del entorno de ejecución"
    assert "**Casos documentados:** 3" in documento


@pytest.mark.unitaria
def test_dos_corridas_identicas_producen_exactamente_el_mismo_catalogo():
    """
    La comprobación de fondo: mismo contenido, byte por byte. Sin esto, la única
    forma de notar el churn es verlo aparecer en `git status`.
    """
    primero = _auditor([1, 2, 3])._documento_casos()
    segundo = _auditor([1, 2, 3])._documento_casos()

    assert primero == segundo
