"""
Pruebas unitarias del punto de entrada del sistema (RNF-04).

Verifican que `python main.py` abra la interfaz gráfica y que `--consola`
seleccione la versión de terminal. Parece trivial, pero es el primer contacto
de cualquier persona con el sistema: mientras `main.py` arrancaba la consola,
quien ejecutaba lo obvio terminaba en un formulario de terminal creyendo que el
programa no tenía interfaz.

No se levanta ninguna ventana: se sustituyen las dos funciones de arranque para
comprobar cuál se eligió. Así la prueba corre en el entorno de integración
continua, sin entorno gráfico.
"""
import pytest

import main
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@pytest.fixture
def arranques(monkeypatch):
    """Registra cuál de las dos vías se invocó, sin ejecutar ninguna."""
    invocadas = []
    monkeypatch.setattr(main, "main_grafico", lambda: invocadas.append("grafico"))
    monkeypatch.setattr(main, "main_consola",
                        lambda fuente=None: invocadas.append(("consola", fuente)))
    return invocadas


@ficha(
    id_caso="TC-AUTO-028",
    nombre="Ejecutar el programa sin argumentos abre la interfaz gráfica, no la versión de "
           "terminal",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="`python main.py` es lo primero que ejecuta cualquiera que reciba el "
                         "proyecto. Mientras ese comando abría la versión de consola, el "
                         "usuario terminaba en un formulario de terminal y concluía que el "
                         "sistema no tenía interfaz gráfica, cuando sí la tiene",
    componente="main.py (main)",
    requisitos="RNF-04",
    precondiciones="Las dos funciones de arranque se sustituyen por dobles; no se abre "
                   "ninguna ventana ni se toca la cámara",
    datos_entrada="Línea de comandos vacía, y la variante `--consola`",
    pasos=[
        Paso("Invocar `main.main()` con argv sin argumentos",
             "assert se eligió la vía gráfica y no la de consola"),
        Paso("Invocar `main.main()` con argv = ['--consola']",
             "assert se eligió la vía de consola"),
    ],
    resultado_esperado="PASSED. Ambas vías comparten el mismo motor de análisis; solo cambia "
                       "cómo se presentan los resultados",
)
@pytest.mark.parametrize("argumentos, esperado", [
    ([], "grafico"),
    (["--consola"], ("consola", None)),
])
def test_la_linea_de_comandos_elige_la_via_correcta(monkeypatch, arranques, argumentos, esperado):
    monkeypatch.setattr("sys.argv", ["main.py"] + argumentos)

    main.main()

    assert arranques == [esperado]


def test_si_falta_una_dependencia_grafica_se_explica_como_seguir(monkeypatch, capsys):
    """
    Una traza de ImportError no le dice nada a quien opera el sistema en el
    dojo. El mensaje debe nombrar la alternativa que sí funciona.
    """
    def sin_customtkinter():
        raise ImportError("No module named 'customtkinter'")

    monkeypatch.setattr(main, "main_grafico", sin_customtkinter)
    monkeypatch.setattr("sys.argv", ["main.py"])

    with pytest.raises(SystemExit) as salida:
        main.main()

    assert salida.value.code == 1
    mensaje = capsys.readouterr().out
    assert "requirements.txt" in mensaje
    assert "--consola" in mensaje


# ---------------- fuente por línea de comandos ----------------

def test_la_fuente_pedida_llega_a_la_consola(monkeypatch, arranques):
    """
    Es lo que convierte una grabación en una sesión analizada sin tener que
    reconfigurar la cámara en la interfaz y devolverla después a su sitio.
    """
    monkeypatch.setattr("sys.argv", ["main.py", "--consola", "--fuente", "sesion.mp4"])

    main.main()

    assert arranques == [("consola", "sesion.mp4")]


def test_sin_fuente_la_consola_usa_la_configurada(monkeypatch, arranques):
    """`None` no es un valor de fuente: es la señal de leer la configuración."""
    monkeypatch.setattr("sys.argv", ["main.py", "--consola"])

    main.main()

    assert arranques == [("consola", None)]


@pytest.mark.parametrize("fuente", ["2", "http://192.168.1.50:8080/video", "sesion.mp4"])
def test_la_fuente_se_pasa_tal_cual_sin_interpretarla(monkeypatch, arranques, fuente):
    """
    Decidir si es un índice, una cámara de red o un archivo es trabajo de
    `vision/fuentes.py`. El punto de entrada no debe adivinarlo: si lo hiciera,
    habría dos criterios distintos conviviendo.
    """
    monkeypatch.setattr("sys.argv", ["main.py", "--consola", "--fuente", fuente])

    main.main()

    assert arranques == [("consola", fuente)]


def test_pedir_una_fuente_sin_consola_se_rechaza(monkeypatch, arranques, capsys):
    """
    Ignorarlo en silencio dejaría creer que la interfaz gráfica está analizando
    el video que se le pasó por la terminal, cuando abriría la cámara guardada.
    """
    monkeypatch.setattr("sys.argv", ["main.py", "--fuente", "sesion.mp4"])

    with pytest.raises(SystemExit) as salida:
        main.main()

    assert salida.value.code == 2, "argparse sale con 2 ante un uso incorrecto"
    assert "--consola" in capsys.readouterr().err
    assert arranques == [], "no debió arrancar ninguna vía"
