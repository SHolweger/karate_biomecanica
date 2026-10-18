"""
Pruebas de lo que hace entregable un artefacto generado (TC-AUTO-065).

Por qué existe este módulo
--------------------------
El 1-oct-2026 la entrega del aviso de señal perdida —un cambio que no toca el
plan de pruebas por ningún lado— quedó bloqueada dos días con este error:

    error: patch failed: docs/plan_de_pruebas.csv:1
    error: docs/plan_de_pruebas.csv: patch does not apply

La causa costó tres diagnósticos equivocados. No era el BOM, ni bastaba con
cambiar el generador: **`git am` aplica `--no-keep-cr` por omisión**, de modo
que borra el CR del final de cada línea del parche. Un archivo versionado con
CRLF deja entonces de coincidir con su propio blob, y el parche no aplica
aunque el archivo esté perfectamente bien. El que lo rompía era el transporte.

De ahí salen las dos decisiones que estas pruebas vigilan:

1. **El generador escribe LF**, aunque el valor por omisión de `csv` sea CRLF.
2. **El plan generado no se versiona**, ni el CSV ni el Markdown. No por su
   formato sino por su naturaleza: su fuente de verdad —los decoradores
   `@ficha(...)`— ya está versionada, así que los dos archivos son
   derivaciones, y versionar una derivación obliga a que dos máquinas la
   tengan byte a byte idéntica. Se obtienen con `python3 plan_de_pruebas.py`.

`docs/casos_prueba_automatizados.generado.md` **sí** se versiona, y la
diferencia no es arbitraria: registra qué pruebas pasaron en una corrida
—evidencia de un hecho, material de la tesis— y solo se reescribe en corridas
completas. Uno es un registro; el otro, una vista.

Se comprueba **la salida del generador**, no lo que haya en el disco: el disco
puede estar en cualquier estado —el plan se regenera a mano cuando hace falta—
y con la decisión de no versionarlo ya no importa.
"""
import csv
import subprocess
from pathlib import Path

import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

import plan_de_pruebas

pytestmark = pytest.mark.unitaria

RAIZ = Path(__file__).resolve().parents[2]
PLAN_CSV = "docs/plan_de_pruebas.csv"
PLAN_MD = "docs/plan_de_pruebas.md"
REGISTRO = "docs/casos_prueba_automatizados.generado.md"


@pytest.fixture
def plan_generado(tmp_path):
    """El plan recién generado en una carpeta temporal, no el del repositorio."""
    casos = plan_de_pruebas.leer_casos()
    assert casos, "el generador no encontró ninguna ficha; la prueba no probaría nada"
    csv_destino = tmp_path / "plan.csv"
    md_destino = tmp_path / "plan.md"
    plan_de_pruebas.escribir_csv(casos, csv_destino)
    plan_de_pruebas.escribir_md(casos, md_destino)
    return csv_destino, md_destino


# ---------------- el formato que sobrevive al transporte ----------------

@ficha(
    id_caso="TC-AUTO-065",
    nombre="Los artefactos generados salen en un formato que un parche puede transportar",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo=(
        "`git am` aplica --no-keep-cr por omisión y borra el CR de cada línea "
        "del parche: un archivo con CRLF deja de coincidir con su blob y "
        "bloquea la entrega de cambios que no tienen nada que ver con él. Ya "
        "costó dos días y tres diagnósticos equivocados"),
    componente="plan_de_pruebas.py (escribir_csv, escribir_md)",
    requisitos="RNF-06",
    precondiciones="Ninguna. El generador lee el árbol sintáctico de tests/ y no importa los módulos",
    datos_entrada="Las fichas declaradas en el repositorio, escritas a una carpeta temporal",
    pasos=[
        Paso("Generar el CSV y el Markdown en tmp_path",
             "assert csv_destino.exists() and md_destino.exists()"),
        Paso("Leer el CSV en binario y buscar retornos de carro",
             "assert b'\\r' not in csv_destino.read_bytes()"),
        Paso("Comprobar el BOM que Excel necesita",
             "assert csv_destino.read_bytes().startswith(b'\\xef\\xbb\\xbf')"),
        Paso("Comprobar que ninguno termina en línea en blanco",
             "assert not texto.endswith('\\n\\n')"),
    ],
    resultado_esperado="PASSED: LF, con BOM en el CSV y sin línea en blanco final",
)
def test_el_csv_generado_no_lleva_retornos_de_carro(plan_generado):
    csv_destino, _ = plan_generado
    crudo = csv_destino.read_bytes()
    assert b"\r" not in crudo, (
        "el CSV salió con CRLF. `git am` los borra al aplicar el parche y el "
        "archivo deja de coincidir con su blob")


def test_el_csv_generado_lleva_el_BOM_que_excel_necesita(plan_generado):
    """Sin BOM, Excel reparte las tildes por su cuenta y el plan llega ilegible."""
    csv_destino, _ = plan_generado
    assert csv_destino.read_bytes().startswith(b"\xef\xbb\xbf")


def test_el_markdown_generado_no_lleva_retornos_de_carro(plan_generado):
    _, md_destino = plan_generado
    assert b"\r" not in md_destino.read_bytes()


@pytest.mark.parametrize("cual", [0, 1])
def test_ninguno_termina_con_una_linea_en_blanco(plan_generado, cual):
    """
    Una línea en blanco al final es invisible al leer y aparece como una
    diferencia en cada regeneración.
    """
    texto = plan_generado[cual].read_text(encoding="utf-8-sig")
    assert texto.endswith("\n")
    assert not texto.endswith("\n\n")


def test_el_csv_generado_se_puede_volver_a_leer(plan_generado):
    """Un archivo que no se relee no es un archivo, es una cadena con suerte."""
    csv_destino, _ = plan_generado
    with open(csv_destino, newline="", encoding="utf-8-sig") as f:
        filas = list(csv.reader(f))
    assert len(filas) > 1
    assert filas[0][0] == "ID"


# ---------------- la decisión de qué se versiona ----------------

def _versionado(ruta):
    resultado = subprocess.run(["git", "ls-files", "--error-unmatch", ruta],
                               cwd=RAIZ, capture_output=True, text=True)
    return resultado.returncode == 0


@pytest.mark.parametrize("ruta", [PLAN_CSV, PLAN_MD])
def test_el_plan_generado_no_esta_versionado(ruta):
    """
    El plan es una DERIVACIÓN de las fichas, que sí están versionadas.
    Versionar una derivación obliga a que dos máquinas la tengan byte a byte
    idéntica, y en cuanto divergen ningún parche que la toque puede aplicar en
    las dos. Fue exactamente lo que pasó el 1-oct-2026.
    """
    assert not _versionado(ruta), (
        f"{ruta} volvió al índice. Se saca con:\n"
        f"    git rm --cached {ruta}\n"
        f"y se regenera cuando haga falta con `python3 plan_de_pruebas.py`.")


@pytest.mark.parametrize("ruta", [PLAN_CSV, PLAN_MD])
def test_el_plan_generado_esta_ignorado(ruta):
    """
    Que no esté versionado HOY no impide que vuelva mañana: al regenerarlo, los
    dos archivos aparecen como «sin seguimiento» y un `git add .` los mete otra
    vez. Ignorarlos cierra esa puerta. Hace falta comprobarlo y no darlo por
    hecho, porque `.gitignore` des-ignora `docs/*.md` y gana la última regla
    que coincide: puesta antes, la entrada del plan no tendría efecto.
    """
    resultado = subprocess.run(["git", "check-ignore", "-q", ruta],
                               cwd=RAIZ, capture_output=True, text=True)
    assert resultado.returncode == 0, (
        f"{ruta} no está ignorado: un `git add .` lo volvería a versionar")


def test_lo_demas_de_docs_no_queda_ignorado_de_rebote():
    """La regla del plan no puede tragarse la documentación que sí se versiona."""
    resultado = subprocess.run(["git", "check-ignore", "-q", REGISTRO],
                               cwd=RAIZ, capture_output=True, text=True)
    assert resultado.returncode == 1, f"{REGISTRO} quedó ignorado"


def test_el_registro_de_la_corrida_si_esta_versionado():
    """
    La otra mitad de la decisión, para que no se lea como «lo generado no se
    versiona nunca». Este archivo registra qué pruebas PASARON en una corrida
    —evidencia de un hecho, material de la tesis— y solo se reescribe en
    corridas completas. Uno es un registro; el otro, una vista.
    """
    assert _versionado(REGISTRO), (
        f"{REGISTRO} salió del índice. Es evidencia de la tesis, no una vista "
        f"regenerable: sin él no queda constancia de qué corrió y cuándo.")


def test_la_comprobacion_de_versionado_distingue_de_verdad():
    """
    Guarda de sí misma. Una comprobación que devolviera siempre lo mismo
    pasaría estas pruebas sin mirar nada — es el mismo error que la prueba que
    recorre archivos y no encuentra ninguno.
    """
    assert _versionado("plan_de_pruebas.py")
    assert not _versionado("docs/un_archivo_que_no_existe_jamas.csv")
