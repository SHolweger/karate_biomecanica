"""
Pruebas de `gui/ventanas.al_frente`.

Corren sin Tk: la ventana es un doble que anota lo que se le pide. Lo que se
fija es la decisión —en Windows se sube, en el resto no se toca— y que el paso
diferido no rompa nada si la ventana se cerró antes de ejecutarse.
"""
import pytest

from gui.ventanas import RETRASO_MS, al_frente
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


class _Principal:
    def winfo_toplevel(self):
        return self


class VentanaDoble:
    """Lo mínimo de una CTkToplevel que `al_frente` usa."""

    def __init__(self, existe=True):
        self.master = _Principal()
        self.existe = existe
        self.llamadas = []
        self.pendientes = []

    def transient(self, duena):
        self.llamadas.append(("transient", duena))

    def after(self, ms, funcion):
        self.pendientes.append((ms, funcion))

    def winfo_exists(self):
        return self.existe

    def lift(self):
        self.llamadas.append(("lift",))

    def focus_force(self):
        self.llamadas.append(("focus_force",))

    def ejecutar_pendientes(self):
        for _, funcion in self.pendientes:
            funcion()


@ficha(
    id_caso="TC-AUTO-088",
    nombre="En Windows, una ventana secundaria queda delante de la principal; "
           "en macOS y Linux no se toca",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="en Windows, «Registrar alumno» se abría y quedaba detrás de la "
                         "ventana principal: el sensei pulsaba el botón y la ventana "
                         "parecía no abrirse. Corregirlo en todos los sistemas cambiaría "
                         "el comportamiento ya verificado en la Mac",
    componente="gui/ventanas.py (al_frente)",
    requisitos="RNF-04",
    precondiciones="Ninguna: la ventana es un doble, no hace falta Tk",
    datos_entrada="Una ventana doble y la plataforma declarada",
    pasos=[
        Paso("Llamar a al_frente con plataforma win32 y ejecutar lo diferido",
             "assert la ventana se declara dependiente de la principal, se sube y toma el foco"),
        Paso("Llamar a al_frente con darwin y con linux",
             "assert no se le pide nada a la ventana"),
        Paso("Cerrar la ventana antes de que corra lo diferido",
             "assert no se sube ni falla"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_en_windows_la_ventana_queda_delante_de_la_principal():
    ventana = VentanaDoble()

    assert al_frente(ventana, plataforma="win32") is True
    assert ventana.llamadas == [("transient", ventana.master)]
    assert [ms for ms, _ in ventana.pendientes] == [RETRASO_MS]

    ventana.ejecutar_pendientes()
    assert ventana.llamadas[1:] == [("lift",), ("focus_force",)]


@pytest.mark.parametrize("plataforma", ["darwin", "linux"])
def test_fuera_de_windows_no_se_toca_la_ventana(plataforma):
    ventana = VentanaDoble()

    assert al_frente(ventana, plataforma=plataforma) is False
    assert ventana.llamadas == [] and ventana.pendientes == []


def test_una_ventana_cerrada_antes_de_subirla_no_falla():
    ventana = VentanaDoble(existe=False)
    al_frente(ventana, plataforma="win32")

    ventana.ejecutar_pendientes()
    assert ("lift",) not in ventana.llamadas
