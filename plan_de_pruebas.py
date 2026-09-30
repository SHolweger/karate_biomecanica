"""
El plan de pruebas, extraído del código que las ejecuta.

Genera dos archivos a partir de las fichas `@ficha(...)` declaradas junto a
cada prueba: una tabla `.csv` que abre en Excel o Project —con las columnas de
planificación vacías, para llenar— y un `.md` legible con el comando exacto de
cada caso y su criterio de aceptación.

---------------------------------------------------------------------------
POR QUÉ SE LEE EL CÓDIGO Y NO SE EJECUTA
---------------------------------------------------------------------------

Las fichas se evalúan al importar el módulo de pruebas, así que la forma obvia
de recogerlas sería importarlos todos. No sirve: los diez módulos de
`tests/e2e/` se omiten solos con `pytest.importorskip` cuando no hay entorno
gráfico, de modo que **un plan generado en el contenedor de integración
continua saldría sin los casos de interfaz**, que son justo los que hay que
ejecutar a mano delante de alguien.

Aquí se lee el **árbol sintáctico**. No se importa nada, no se ejecuta nada, y
el plan sale completo en cualquier máquina. Es la misma técnica con la que
`tests/unit/test_firmas_del_analizador.py` alcanza esos mismos módulos.

---------------------------------------------------------------------------
QUÉ SE PUEDE AFIRMAR DEL PLAN Y QUÉ NO
---------------------------------------------------------------------------

El plan cubre los **casos formales** —los que llevan ficha—, no las pruebas
totales. Son cosas distintas y conviene no confundirlas al presentarlo:

- Una ficha documenta un caso de prueba con su riesgo, sus datos y su criterio.
- Una prueba es una función de pytest. Un caso puede ejecutarse con varias
  (parametrizadas), y hay pruebas de apoyo que no necesitan ficha propia.

El resumen imprime las dos cifras por separado, y la columna «Pruebas que lo
ejecutan» dice cuántas funciones respaldan cada caso.
"""
import argparse
import ast
import csv
import re
import sys
from collections import namedtuple
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CARPETA_PRUEBAS = RAIZ / "tests"

# Columnas que el plan deja VACÍAS a propósito: son las que se llenan al
# planificar y al ejecutar. Ponerles un valor inventado convertiría el plan en
# un registro falso de pruebas que nadie corrió.
# El mismo patron que valida `tests/reporte/plantilla.py`. Hace falta filtrar
# porque el modulo que prueba la PLANTILLA declara fichas de mentira para
# ejercitarla, y esas no son casos del sistema: colarlas en el plan seria
# presentar como prueba del producto algo que solo prueba el formato.
PATRON_ID = re.compile(r"^TC-AUTO-\d{3}$")

COLUMNAS_A_LLENAR = ["Fecha planificada", "Fecha de ejecución", "Responsable",
                     "Resultado obtenido", "Defecto asociado", "Observaciones"]

Caso = namedtuple("Caso", "id nombre tipo prioridad componente requisitos "
                          "riesgo precondiciones datos pasos esperado "
                          "archivo funcion")


# ---------------------------------------------------------------------------
# Lectura de las fichas
# ---------------------------------------------------------------------------

def _valor(nodo):
    """El literal de un argumento de la ficha, sea texto, enum o lista de pasos."""
    if isinstance(nodo, ast.Constant):
        return nodo.value
    if isinstance(nodo, ast.Attribute):
        # TipoPrueba.UNITARIA -> "UNITARIA"; Prioridad.ALTA -> "ALTA"
        return nodo.attr
    if isinstance(nodo, ast.JoinedStr):
        # f-strings: se reconstruye lo que se puede y se marca lo que no.
        return "".join(p.value if isinstance(p, ast.Constant) else "…"
                       for p in nodo.values)
    if isinstance(nodo, ast.List):
        return [_valor(e) for e in nodo.elts]
    if isinstance(nodo, ast.Call):
        # Paso("acción", "resultado esperado")
        return tuple(_valor(a) for a in nodo.args)
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
        izq, der = _valor(nodo.left), _valor(nodo.right)
        if isinstance(izq, str) and isinstance(der, str):
            return izq + der
    return ""


def _es_ficha(decorador):
    return (isinstance(decorador, ast.Call)
            and isinstance(decorador.func, ast.Name)
            and decorador.func.id == "ficha")


def leer_casos(carpeta=CARPETA_PRUEBAS):
    """Todos los casos con ficha, ordenados por su ID."""
    casos = []
    for archivo in sorted(carpeta.rglob("test_*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.FunctionDef):
                continue
            for decorador in nodo.decorator_list:
                if not _es_ficha(decorador):
                    continue
                campos = {k.arg: _valor(k.value) for k in decorador.keywords}
                if not PATRON_ID.match(str(campos.get("id_caso", ""))):
                    continue
                casos.append(Caso(
                    id=campos.get("id_caso", ""),
                    nombre=campos.get("nombre", ""),
                    tipo=campos.get("tipo", ""),
                    prioridad=campos.get("prioridad", ""),
                    componente=campos.get("componente", ""),
                    requisitos=campos.get("requisitos", ""),
                    riesgo=campos.get("justificacion_riesgo", ""),
                    precondiciones=campos.get("precondiciones", ""),
                    datos=campos.get("datos_entrada", ""),
                    pasos=campos.get("pasos", []),
                    esperado=campos.get("resultado_esperado", ""),
                    archivo=str(archivo.relative_to(RAIZ)),
                    funcion=nodo.name))
    return sorted(casos, key=lambda c: c.id)


def comando(caso):
    """Lo que hay que escribir en la terminal para ejecutar ESE caso."""
    return f'python3 -m pytest "{caso.archivo}::{caso.funcion}" -v'


def necesita_pantalla(caso):
    """
    Los casos de `tests/e2e/` requieren entorno gráfico y cámara.

    Importa para planificar: no se pueden ejecutar en un servidor de
    integración continua, así que su fecha de ejecución es necesariamente una
    sesión delante de un equipo con pantalla.
    """
    return caso.archivo.startswith("tests/e2e/")


# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------

def escribir_csv(casos, destino):
    cabecera = ["ID", "Nombre del caso", "Tipo", "Prioridad", "Componente",
                "Requisito", "Entorno", "Comando de ejecución",
                "Resultado esperado", "Riesgo que cubre"] + COLUMNAS_A_LLENAR
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f)
        escritor.writerow(cabecera)
        for c in casos:
            escritor.writerow([
                c.id, c.nombre, c.tipo.capitalize(), c.prioridad.capitalize(),
                c.componente, c.requisitos,
                "Con pantalla y cámara" if necesita_pantalla(c) else "Cualquiera",
                comando(c), c.esperado, c.riesgo,
            ] + [""] * len(COLUMNAS_A_LLENAR))
    return destino


def escribir_md(casos, destino):
    lineas = [
        "# Plan de pruebas — Shotokan AI",
        "",
        "Sistema experto de análisis biomecánico del Karate-Do Shotokan.",
        "",
        "> **Documento generado.** Lo produce `plan_de_pruebas.py` leyendo las fichas",
        "> `@ficha(...)` declaradas junto a cada prueba. No editar a mano: para cambiar",
        "> un caso hay que editar su prueba, que es lo que garantiza que el plan y lo",
        "> que se ejecuta no se separen.",
        "",
        "## Cómo se ejecuta todo",
        "",
        "```bash",
        "python3 -m pytest -q                              # la suite completa",
        "python3 -m pytest --exigir-fichas --reporte-formal   # lo que corre CI",
        "```",
        "",
        "La suite completa **solo corre entera en un equipo con pantalla y cámara**.",
        "Sin entorno gráfico, los diez módulos de `tests/e2e/` se omiten solos: sus",
        "casos aparecen aquí marcados como «Con pantalla y cámara» y hay que",
        "planificarlos como sesión presencial.",
        "",
        "## Resumen",
        "",
    ]

    por_tipo, por_prioridad, con_pantalla = {}, {}, 0
    for c in casos:
        por_tipo[c.tipo] = por_tipo.get(c.tipo, 0) + 1
        por_prioridad[c.prioridad] = por_prioridad.get(c.prioridad, 0) + 1
        con_pantalla += 1 if necesita_pantalla(c) else 0

    lineas += [f"**Casos formales documentados:** {len(casos)}", ""]
    lineas += ["| Tipo | Casos |", "|---|---|"]
    lineas += [f"| {t.capitalize()} | {n} |" for t, n in sorted(por_tipo.items())]
    lineas += ["", "| Prioridad | Casos |", "|---|---|"]
    lineas += [f"| {p.capitalize()} | {n} |" for p, n in sorted(por_prioridad.items())]
    lineas += ["", f"**Requieren pantalla y cámara:** {con_pantalla} de {len(casos)}", ""]
    lineas += ["---", "", "## Catálogo", ""]

    for c in casos:
        lineas += [
            f"### {c.id} — {c.nombre}",
            "",
            f"| | |", "|---|---|",
            f"| **Tipo** | {c.tipo.capitalize()} |",
            f"| **Prioridad** | {c.prioridad.capitalize()} |",
            f"| **Componente** | `{c.componente}` |",
            f"| **Requisito** | {c.requisitos} |",
            f"| **Entorno** | {'Con pantalla y cámara' if necesita_pantalla(c) else 'Cualquiera'} |",
            f"| **Precondiciones** | {c.precondiciones} |",
            f"| **Datos de entrada** | {c.datos} |",
            "",
            "**Por qué existe este caso:** " + c.riesgo + ".",
            "",
            "**Comando**",
            "",
            "```bash",
            comando(c),
            "```",
            "",
            "**Pasos y aserciones**",
            "",
            "| # | Acción | Resultado esperado |",
            "|---|---|---|",
        ]
        for i, paso in enumerate(c.pasos, start=1):
            accion, esperado = (paso + ("", ""))[:2] if isinstance(paso, tuple) else (paso, "")
            lineas.append(f"| {i} | {accion} | {esperado} |")
        lineas += ["", f"**Criterio de aceptación:** {c.esperado}", "", "---", ""]

    Path(destino).write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return destino


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera el plan de pruebas (.csv para Excel y .md legible) a "
                    "partir de las fichas declaradas en el codigo.")
    parser.add_argument("--csv", default="docs/plan_de_pruebas.csv")
    parser.add_argument("--md", default="docs/plan_de_pruebas.md")
    args = parser.parse_args(argv)

    casos = leer_casos()
    if not casos:
        print("No se encontro ninguna ficha. ¿Se movio la carpeta tests/?", file=sys.stderr)
        return 1

    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    escribir_csv(casos, args.csv)
    escribir_md(casos, args.md)

    con_pantalla = sum(1 for c in casos if necesita_pantalla(c))
    print(f"{len(casos)} casos formales.")
    print(f"  {con_pantalla} requieren pantalla y camara; el resto corre en cualquier equipo.")
    print(f"  {args.csv}")
    print(f"  {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
