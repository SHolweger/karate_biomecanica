"""
Complemento de pytest que emite los reportes con formato normalizado.

Qué hace, en orden:

1. Durante la recolección, recoge la ficha (`FichaCasoPrueba`) que cada prueba
   documentada declaró con el decorador `@ficha(...)` y anota a qué módulo y a
   qué nivel (unitaria / integración / e2e) pertenece cada prueba.
2. Mientras la suite corre, registra el resultado real de cada prueba.
3. Al terminar, cruza lo declarado con lo observado y escribe dos documentos:
   la evidencia de ejecución y el documento de casos de prueba.

La regla que sostiene todo esto: el reporte nunca inventa un dato. El nombre
del script sale del `nodeid` que pytest recolectó, el veredicto sale del
resultado observado y la ficha sale del código fuente. Si algo no se pudo
determinar, el documento lo dice en vez de omitirlo.

Opciones de línea de comandos:

    pytest --reporte-formal          genera los dos documentos
    pytest --exigir-fichas           falla si el formato documental no se cumple
    pytest --dir-evidencias=RUTA     carpeta de la evidencia (por defecto evidencias/)
    pytest --doc-casos=RUTA          archivo del documento de casos
"""
from __future__ import annotations

import platform
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from reporte.plantilla import FichaCasoPrueba, TipoPrueba, verificar_correlativos

RUTA_EVIDENCIA_POR_DEFECTO = "evidencias"
RUTA_CASOS_POR_DEFECTO = "docs/casos_prueba_automatizados.generado.md"

NOMBRE_PROYECTO = "Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan"


def _ruta_legible(ruta, raiz):
    """
    Ruta relativa al proyecto cuando el archivo cae dentro de él, y absoluta
    cuando no. `--dir-evidencias` acepta cualquier carpeta, incluida una fuera
    del repositorio: asumir que siempre está adentro rompía la corrida al
    imprimir el resumen, después de haber escrito los documentos.
    """
    try:
        return ruta.relative_to(raiz)
    except ValueError:
        return ruta

# Marca de pytest -> nivel de la pirámide de pruebas, para el resumen por nivel.
NIVELES = {
    "unitaria": "Unitaria",
    "integracion": "Integración",
    "e2e": "Interfaz (UI/E2E)",
}

AVISO_GENERADO = (
    "> **Documento generado automáticamente.** Lo produce el complemento "
    "`tests/reporte/plugin.py` a partir de las fichas declaradas en el código "
    "con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. "
    "No editar a mano: cualquier cambio se pierde en la siguiente corrida. "
    "Para modificar una ficha hay que editar la prueba correspondiente."
)


# ---------------------------------------------------------------------------
# Opciones
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    grupo = parser.getgroup("reporte formal", "Reportes de pruebas con formato normalizado")
    grupo.addoption(
        "--reporte-formal", action="store_true", default=False,
        help="Genera la evidencia de ejecución y el documento de casos de prueba.",
    )
    grupo.addoption(
        "--exigir-fichas", action="store_true", default=False,
        help="Falla la corrida si algún módulo de pruebas no tiene ningún caso "
             "documentado con la plantilla, o si la serie de IDs tiene huecos o repetidos.",
    )
    grupo.addoption(
        "--dir-evidencias", action="store", default=RUTA_EVIDENCIA_POR_DEFECTO,
        metavar="RUTA", help="Carpeta donde se escribe la evidencia de ejecución.",
    )
    grupo.addoption(
        "--doc-casos", action="store", default=RUTA_CASOS_POR_DEFECTO,
        metavar="RUTA", help="Archivo donde se escribe el documento de casos de prueba.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "ficha(id_caso): caso documentado con la plantilla formal "
        "(lo agrega el decorador @ficha, no se escribe a mano)",
    )
    config._reporte_formal = ReporteFormal(config)
    config.pluginmanager.register(config._reporte_formal, "reporte-formal")


def pytest_unconfigure(config):
    plugin = getattr(config, "_reporte_formal", None)
    if plugin is not None:
        config.pluginmanager.unregister(plugin)
        del config._reporte_formal


# ---------------------------------------------------------------------------
# Estado recolectado
# ---------------------------------------------------------------------------
@dataclass
class ResultadoPrueba:
    """Lo observado para una prueba concreta (una fila del detalle de ejecución)."""

    nodeid: str
    modulo: str
    marcas: tuple[str, ...]
    estado: str = "no ejecutado"
    duracion: float = 0.0

    @property
    def nivel(self) -> str:
        for marca in self.marcas:
            if marca in NIVELES:
                return NIVELES[marca]
        return "Sin nivel declarado"


@dataclass
class CasoDocumentado:
    """Une la ficha declarada con las pruebas que efectivamente la ejecutan."""

    ficha: FichaCasoPrueba
    nodeid: str
    pruebas: list[ResultadoPrueba] = field(default_factory=list)

    @property
    def veredicto(self) -> str:
        """
        Un caso puede estar parametrizado en varias pruebas. El veredicto del
        caso es el peor de sus resultados: basta que una variante falle para
        que el caso no esté demostrado.
        """
        estados = {p.estado for p in self.pruebas}
        if not estados or estados == {"no ejecutado"}:
            return "NO EJECUTADO"
        if "failed" in estados or "error" in estados:
            return "FAILED"
        if estados <= {"skipped", "no ejecutado"}:
            return "SKIPPED"
        return "PASSED"

    @property
    def resumen_ejecucion(self) -> str:
        conteo = Counter(p.estado for p in self.pruebas)
        partes = [f"{n} {ESTADOS_LEGIBLES.get(e, e)}" for e, n in sorted(conteo.items())]
        return ", ".join(partes) if partes else "—"


ESTADOS_LEGIBLES = {
    "passed": "PASSED",
    "failed": "FAILED",
    "skipped": "SKIPPED",
    "error": "ERROR",
    "no ejecutado": "no ejecutado",
}


class ReporteFormal:
    """Recolecta, valida y emite. Se registra como complemento en pytest_configure."""

    def __init__(self, config):
        self.config = config
        self.inicio = datetime.now()
        self.resultados: dict[str, ResultadoPrueba] = {}
        self.casos: dict[str, CasoDocumentado] = {}
        self.modulos: dict[str, set[str]] = {}
        self.problemas_formato: list[str] = []
        self.avisos_formato: list[str] = []
        self.modulos_omitidos: list[str] = []

    # -- recolección --------------------------------------------------------
    def pytest_collectreport(self, report):
        """
        Anota los módulos que ni siquiera llegaron a importarse.

        Ocurre con las pruebas de interfaz en un entorno sin CustomTkinter ni
        servidor de ventanas: `pytest.importorskip` las omite en bloque. Sus
        fichas se declaran con un decorador que se ejecuta AL IMPORTAR, así que
        un módulo omitido no registra ninguna, y la serie de identificadores
        aparece incompleta aunque el repositorio esté correcto.
        """
        if report.outcome == "skipped":
            nombre = getattr(report, "nodeid", "") or str(report)
            if nombre:
                self.modulos_omitidos.append(nombre)
    def pytest_collection_modifyitems(self, session, config, items):
        for item in items:
            modulo = item.location[0]
            resultado = ResultadoPrueba(
                nodeid=item.nodeid,
                modulo=modulo,
                marcas=tuple(m.name for m in item.iter_markers()),
            )
            self.resultados[item.nodeid] = resultado
            self.modulos.setdefault(modulo, set())

            ficha = getattr(getattr(item, "function", None), "ficha_caso", None)
            if ficha is None:
                continue

            caso = self.casos.get(ficha.id_caso)
            if caso is None:
                # El nodeid sin la parte "[...]" identifica a la función, no a
                # una variante parametrizada: es lo que hay que citar como script.
                caso = CasoDocumentado(ficha=ficha, nodeid=item.nodeid.split("[")[0])
                self.casos[ficha.id_caso] = caso
            caso.pruebas.append(resultado)
            self.modulos[modulo].add(ficha.id_caso)

        self.problemas_formato, self.avisos_formato = self._auditar_formato()
        if self.problemas_formato and config.getoption("--exigir-fichas"):
            detalle = "\n".join(f"  - {p}" for p in self.problemas_formato)
            raise pytest.UsageError(
                "El formato documental de la suite no se cumple "
                f"({len(self.problemas_formato)} problema(s)):\n{detalle}\n"
                "Documentá los casos faltantes con @ficha(...) o quitá --exigir-fichas."
            )

    def _auditar_formato(self) -> tuple[list[str], list[str]]:
        """
        Separa los incumplimientos reales de los avisos que dependen del entorno.

        La distinción no es cosmética: `--exigir-fichas` hace fallar la corrida
        ante un problema, y la integración continua usa esa bandera. Tratar como
        defecto algo que solo refleja una limitación del entorno vuelve la señal
        inservible — una suite en rojo de forma permanente deja de avisar cuando
        algo se rompe de verdad.

        Un hueco en la serie de identificadores solo es evidencia de un caso
        borrado cuando la corrida fue COMPLETA. Si hubo módulos omitidos —el
        entorno de integración continua no tiene interfaz gráfica y omite las
        pruebas E2E en bloque— sus fichas nunca se registran y el hueco es
        esperado, no un error. Se informa igual, como aviso.

        Devuelve (problemas, avisos).
        """
        huecos = verificar_correlativos(c.ficha for c in self.casos.values())
        problemas, avisos = [], []

        if self.modulos_omitidos and huecos:
            avisos.extend(huecos)
            avisos.append(
                f"los huecos anteriores se explican por {len(self.modulos_omitidos)} "
                f"módulo(s) omitido(s) en este entorno; no se cuentan como incumplimiento"
            )
        else:
            problemas.extend(huecos)

        for modulo, ids in sorted(self.modulos.items()):
            if not ids:
                problemas.append(
                    f"{modulo}: ningún caso documentado con la plantilla "
                    "(se espera al menos uno por módulo de pruebas)"
                )
        return problemas, avisos

    # -- ejecución ----------------------------------------------------------
    def pytest_runtest_logreport(self, report):
        resultado = self.resultados.get(report.nodeid)
        if resultado is None:
            return

        resultado.duracion += report.duration
        if report.when == "setup":
            if report.failed:
                resultado.estado = "error"
            elif report.skipped:
                resultado.estado = "skipped"
        elif report.when == "call":
            resultado.estado = report.outcome
        elif report.when == "teardown" and report.failed:
            resultado.estado = "error"

    # -- emisión ------------------------------------------------------------
    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        # trylast: pytest-cov calcula el porcentaje total en su propio
        # pytest_terminal_summary, así que hay que correr después de él.
        if self.problemas_formato or self.avisos_formato:
            terminalreporter.write_sep("-", "formato documental", yellow=True)
            for problema in self.problemas_formato:
                terminalreporter.write_line(f"  incumplimiento: {problema}")
            for aviso in self.avisos_formato:
                terminalreporter.write_line(f"  aviso: {aviso}")

        if not config.getoption("--reporte-formal"):
            return

        raiz = config.rootpath
        marca_tiempo = self.inicio.strftime("%Y%m%d_%H%M%S")

        ruta_evidencia = raiz / config.getoption("--dir-evidencias") / \
            f"evidencia_ejecucion_{marca_tiempo}.md"
        ruta_casos = raiz / config.getoption("--doc-casos")

        for ruta, contenido in (
            (ruta_evidencia, self._documento_evidencia(exitstatus)),
            (ruta_casos, self._documento_casos()),
        ):
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(contenido, encoding="utf-8")

        terminalreporter.write_sep("-", "reportes con formato normalizado")
        for ruta in (ruta_evidencia, ruta_casos):
            terminalreporter.write_line(f"  {_ruta_legible(ruta, raiz)}")

    # -- contenido de los documentos ---------------------------------------
    def _documento_evidencia(self, exitstatus) -> str:
        fin = datetime.now()
        conteo = Counter(r.estado for r in self.resultados.values())
        total = len(self.resultados)
        veredicto = "APROBADA" if exitstatus == 0 else f"NO APROBADA (código de salida {exitstatus})"

        lineas = [
            "# Evidencia de ejecución — Suite de pruebas automatizadas",
            "",
            AVISO_GENERADO,
            "",
            "## 1. Identificación de la corrida",
            "",
            "| Campo | Valor |",
            "|---|---|",
            f"| **Sistema bajo prueba** | {NOMBRE_PROYECTO} |",
            f"| **Framework de automatización** | pytest {pytest.__version__} |",
            f"| **Comando ejecutado** | `{self._comando()}` |",
            f"| **Fecha y hora de inicio** | {self.inicio:%Y-%m-%d %H:%M:%S} |",
            f"| **Duración total** | {(fin - self.inicio).total_seconds():.2f} s |",
            f"| **Entorno de ejecución** | {platform.system()} {platform.release()} "
            f"({platform.machine()}) |",
            f"| **Intérprete** | Python {platform.python_version()} |",
            f"| **Rama / commit** | {self._git()} |",
            f"| **Pruebas recolectadas** | {total} |",
            f"| **Veredicto global** | **{veredicto}** |",
            "",
            "## 2. Resumen de resultados por nivel",
            "",
            "| Nivel | Pruebas | PASSED | FAILED | SKIPPED | Tiempo (s) |",
            "|---|---|---|---|---|---|",
        ]

        por_nivel: dict[str, list[ResultadoPrueba]] = {}
        for resultado in self.resultados.values():
            por_nivel.setdefault(resultado.nivel, []).append(resultado)

        orden = list(NIVELES.values()) + ["Sin nivel declarado"]
        for nivel in sorted(por_nivel, key=lambda n: orden.index(n) if n in orden else 99):
            grupo = por_nivel[nivel]
            c = Counter(r.estado for r in grupo)
            lineas.append(
                f"| {nivel} | {len(grupo)} | {c['passed']} | {c['failed'] + c['error']} "
                f"| {c['skipped']} | {sum(r.duracion for r in grupo):.2f} |"
            )
        lineas.append(
            f"| **Total** | **{total}** | **{conteo['passed']}** "
            f"| **{conteo['failed'] + conteo['error']}** | **{conteo['skipped']}** "
            f"| **{sum(r.duracion for r in self.resultados.values()):.2f}** |"
        )

        lineas += [
            "",
            "## 3. Casos de prueba documentados",
            "",
            "Cada fila corresponde a una ficha declarada con la plantilla formal. "
            "El veredicto es el peor resultado entre las variantes parametrizadas del caso.",
            "",
            "| ID | Caso | Requisito | Script | Ejecuciones | Veredicto |",
            "|---|---|---|---|---|---|",
        ]
        for caso in self._casos_ordenados():
            f = caso.ficha
            lineas.append(
                f"| {f.id_caso} | {_celda(f.nombre)} | {', '.join(f.requisitos)} "
                f"| `{caso.nodeid}` | {caso.resumen_ejecucion} | **{caso.veredicto}** |"
            )

        cobertura = self._cobertura()
        if cobertura is not None:
            lineas += [
                "",
                "## 4. Cobertura de código",
                "",
                f"Cobertura total de sentencias y ramas: **{cobertura:.2f} %** "
                "(medida con pytest-cov sobre los paquetes declarados en `.coveragerc`).",
            ]

        lineas += ["", "## 5. Detalle de ejecución", ""]
        for modulo in sorted(self.modulos):
            pruebas = [r for r in self.resultados.values() if r.modulo == modulo]
            if not pruebas:
                continue
            lineas += [
                f"### `{modulo}`",
                "",
                "| Prueba | Estado | Tiempo (ms) |",
                "|---|---|---|",
            ]
            for prueba in pruebas:
                nombre = prueba.nodeid.split("::", 1)[-1]
                lineas.append(
                    f"| `{_celda(nombre)}` | {ESTADOS_LEGIBLES.get(prueba.estado, prueba.estado)} "
                    f"| {prueba.duracion * 1000:.1f} |"
                )
            lineas.append("")

        if self.problemas_formato or self.avisos_formato:
            lineas += ["## 6. Observaciones sobre el formato documental", ""]
            lineas += [f"- **Incumplimiento:** {p}" for p in self.problemas_formato]
            lineas += [f"- Aviso: {a}" for a in self.avisos_formato]
            lineas.append("")

        return "\n".join(lineas).rstrip() + "\n"

    def _documento_casos(self) -> str:
        casos = self._casos_ordenados()
        lineas = [
            "# Casos de prueba automatizados",
            "",
            f"**Sistema:** {NOMBRE_PROYECTO}",
            f"**Generado:** {self.inicio:%Y-%m-%d %H:%M:%S}",
            f"**Casos documentados:** {len(casos)} de {len(self.resultados)} pruebas recolectadas",
            "",
            AVISO_GENERADO,
            "",
            "---",
            "",
            "## Resumen",
            "",
            "| Nivel | Casos documentados | Pruebas que los ejecutan |",
            "|---|---|---|",
        ]
        for tipo in TipoPrueba:
            del_tipo = [c for c in casos if c.ficha.tipo is tipo]
            if del_tipo:
                lineas.append(
                    f"| {tipo.value} | {len(del_tipo)} "
                    f"| {sum(len(c.pruebas) for c in del_tipo)} |"
                )
        lineas += ["", "---", ""]

        for caso in casos:
            lineas += [caso.ficha.a_markdown(caso.nodeid, caso.veredicto), "", "---", ""]

        lineas += [
            "## Trazabilidad: casos de prueba contra requisitos y componentes",
            "",
            "| Caso | Componente bajo prueba | Requisito asociado | Tipo |",
            "|---|---|---|---|",
        ]
        for caso in casos:
            f = caso.ficha
            lineas.append(
                f"| {f.id_caso} | `{_celda(f.componente)}` | {', '.join(f.requisitos)} "
                f"| {f.tipo.value} |"
            )

        return "\n".join(lineas).rstrip() + "\n"

    # -- utilidades ---------------------------------------------------------
    def _casos_ordenados(self) -> list[CasoDocumentado]:
        return sorted(self.casos.values(), key=lambda c: c.ficha.numero)

    def _comando(self) -> str:
        return " ".join(["pytest", *self.config.invocation_params.args])

    def _git(self) -> str:
        """Rama y commit, si el reporte se genera dentro de una copia de trabajo de git."""
        def correr(*args):
            try:
                salida = subprocess.run(
                    ["git", *args], cwd=str(self.config.rootpath),
                    capture_output=True, text=True, timeout=5, check=True,
                )
                return salida.stdout.strip()
            except (OSError, subprocess.SubprocessError):
                return ""

        rama = correr("rev-parse", "--abbrev-ref", "HEAD")
        commit = correr("rev-parse", "--short", "HEAD")
        if not commit:
            return "no disponible (fuera de un repositorio git)"
        sucio = " (con cambios sin confirmar)" if correr("status", "--porcelain") else ""
        return f"`{rama}` @ `{commit}`{sucio}"

    def _cobertura(self) -> float | None:
        """Porcentaje total que pytest-cov ya calculó, si se corrió con --cov."""
        plugin = self.config.pluginmanager.get_plugin("_cov")
        total = getattr(plugin, "cov_total", None)
        return float(total) if isinstance(total, (int, float)) else None


def _celda(texto: str) -> str:
    """Escapa lo que rompería una celda de tabla en Markdown."""
    return str(texto).replace("|", "\\|").replace("\n", " ")


# `sys` se usa solo para diagnosticar la ruta del intérprete cuando alguien
# ejecuta el complemento desde un entorno virtual distinto al esperado.
def pytest_report_header(config):
    if config.getoption("--reporte-formal"):
        return f"reporte formal: activo (intérprete {sys.executable})"
    return None
