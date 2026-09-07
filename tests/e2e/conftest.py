"""
tests/e2e/conftest.py — Andamiaje común de las pruebas de interfaz.

Los imports de la GUI están DENTRO de las fixtures a propósito. Un conftest se
importa siempre, también en un contenedor headless donde CustomTkinter no está
instalado; si el import viviera arriba, la carpeta entera fallaría al
recolectarse en vez de producir el SKIPPED controlado que cada módulo declara
con `pytest.importorskip`. La distinción importa para la evidencia: un SKIPPED
documenta una limitación conocida del entorno, un ERROR parece una suite rota.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def requiere_entorno_grafico():
    """Sin servidor de ventanas (CI headless) Tkinter no puede crear la aplicación."""
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        pytest.skip("sin entorno gráfico disponible (DISPLAY no definido)")


@pytest.fixture
def app(db):
    """Aplicación real con la base de datos temporal, con la ventana oculta."""
    from gui.app import App
    from gui.live_screen import LiveScreen

    aplicacion = App(db=db)
    aplicacion.withdraw()
    yield aplicacion
    if isinstance(aplicacion.pantalla_actual, LiveScreen):
        aplicacion.pantalla_actual.cerrar()
    aplicacion.destroy()


@pytest.fixture
def entrenador_registrado(db):
    """Entrenador ya dado de alta, para partir de una sesión que puede autenticarse."""
    db.crear_entrenador("Sensei Ejemplo", "sensei", "sensei@dojo.gt", "clave123", rol="principal")
    return db.autenticar_entrenador("sensei", "clave123")
