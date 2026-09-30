"""
Que todas las llamadas al analizador pasen los argumentos que su firma pide.

Esta prueba existe por un fallo de proceso, no de diseño, y es de los que se
repiten: el contenedor de integración continua **omite los diez módulos de
`tests/e2e/`** porque no tiene entorno gráfico. Una llamada que quede desfasada
ahí pasa la suite completa del contenedor y revienta en la Mac de Sebastián.

Ocurrió el 30-sep-2026 al añadir `timestamp_ms` a `analyze_tsuki`: se
actualizaron los cuatro puntos de llamada del código y los doce de las pruebas
de integración, y quedaron dos en `tests/e2e/test_gui_vivo.py`. Aquí pasaron
652; en su equipo, `TypeError: missing 1 required positional argument`.

La comprobación es estática —se lee el árbol sintáctico, no se ejecuta nada—
así que alcanza a los módulos que este entorno no puede importar. Es la única
forma de verificarlos desde aquí.

Solo cuenta argumentos posicionales. No pretende sustituir a un verificador de
tipos: pretende que un cambio de firma no se escape por la puerta que la
integración continua tiene cerrada.
"""
import ast
import inspect
from pathlib import Path

import pytest

from expert_system.analyzer import TechniqueAnalyzer
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

RAIZ = Path(__file__).resolve().parents[2]

# Los métodos que la interfaz, el modo consola y las pruebas llaman por su
# nombre. Son la costura entre el motor y todo lo demás.
METODOS = ("analyze_tsuki", "analyze_stance", "analyze_mae_geri")

CARPETAS_IGNORADAS = {".git", "__pycache__", ".venv", "venv", "node_modules"}


def _archivos_de_python():
    for archivo in RAIZ.rglob("*.py"):
        if CARPETAS_IGNORADAS.isdisjoint(archivo.parts):
            yield archivo


def _argumentos_que_pide(nombre):
    """Cuántos posicionales pide el método, sin contar `self`."""
    return len(inspect.signature(getattr(TechniqueAnalyzer, nombre)).parameters) - 1


def _llamadas_a_los_metodos(archivo):
    """
    Cada llamada `algo.analyze_*(...)` del archivo, con su línea.

    Se omiten las que desempaquetan una tupla (`*argumentos`): ahí el número de
    posicionales no se puede contar leyendo el texto, y forzarlo daría un falso
    positivo. Son pocas y deliberadas.
    """
    arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr in METODOS
                and not any(isinstance(a, ast.Starred) for a in nodo.args)):
            yield nodo.func.attr, nodo.lineno, len(nodo.args), {k.arg for k in nodo.keywords}


@ficha(
    id_caso="TC-AUTO-058",
    nombre="Ninguna llamada al analizador queda desfasada de su firma, incluidas las "
           "de los modulos que la integracion continua omite",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="el contenedor sin entorno grafico omite los diez modulos de "
                         "tests/e2e/, asi que una llamada desfasada dentro de ellos pasa "
                         "la suite completa aqui y solo falla en el equipo de destino. "
                         "Ocurrio el 30-sep-2026 al anadir timestamp_ms a analyze_tsuki: "
                         "se actualizaron los dieciseis puntos de llamada visibles y "
                         "quedaron dos invisibles. La comprobacion estatica alcanza a "
                         "los modulos que este entorno no puede importar, que es la "
                         "unica forma de verificarlos desde aqui",
    componente="expert_system/analyzer.py (firmas publicas) contra todo el repositorio",
    requisitos="RNF-03",
    precondiciones="Ninguna: se lee el arbol sintactico, no se ejecuta ningun modulo",
    datos_entrada="Todos los archivos .py del repositorio, excluyendo .git, "
                  "__pycache__ y entornos virtuales",
    pasos=[
        Paso("Leer la firma real de cada metodo publico del analizador con inspect",
             "assert se obtiene el numero de argumentos posicionales que pide"),
        Paso("Recorrer el arbol sintactico de cada archivo buscando llamadas a esos "
             "metodos",
             "assert se encuentran las llamadas de main.py, gui/, test_rendimiento.py "
             "y las tres carpetas de pruebas"),
        Paso("Contrastar los argumentos de cada llamada contra la firma",
             "assert ninguna se queda corta ni se pasa, nombrando archivo y linea "
             "cuando falla"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz grafica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_toda_llamada_al_analizador_pasa_los_argumentos_de_su_firma():
    esperados = {nombre: _argumentos_que_pide(nombre) for nombre in METODOS}
    desfasadas = []

    for archivo in _archivos_de_python():
        for metodo, linea, posicionales, nombrados in _llamadas_a_los_metodos(archivo):
            if posicionales + len(nombrados) != esperados[metodo]:
                desfasadas.append(
                    f"{archivo.relative_to(RAIZ)}:{linea} llama a {metodo} con "
                    f"{posicionales + len(nombrados)} argumentos y la firma pide "
                    f"{esperados[metodo]}")

    assert not desfasadas, "llamadas desfasadas:\n  " + "\n  ".join(desfasadas)


def test_la_busqueda_encuentra_las_llamadas_que_debe():
    """
    La guarda de la guarda. Una prueba que recorre archivos y no encuentra nada
    pasa siempre, y pasaría también el día en que se renombre un método o se
    mueva una carpeta. Aquí se fija que sigue viendo los puntos de llamada del
    producto —no solo los de las pruebas— y en particular los de `tests/e2e/`,
    que son los que motivaron el módulo.
    """
    vistos = {}
    for archivo in _archivos_de_python():
        for metodo, _, _, _ in _llamadas_a_los_metodos(archivo):
            vistos.setdefault(str(archivo.relative_to(RAIZ)), set()).add(metodo)

    assert "main.py" in vistos, "el modo consola llama al analizador y debe verse"
    assert "gui/live_screen.py" in vistos, "la pantalla en vivo también"
    assert any(ruta.startswith("tests/e2e/") for ruta in vistos), \
        "si dejan de verse las llamadas de e2e, esta prueba ya no protege de nada"
    assert set(METODOS) <= {m for metodos in vistos.values() for m in metodos}, \
        "algún método del analizador dejó de tener llamadas: ¿se renombró?"
