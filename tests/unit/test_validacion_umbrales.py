"""
Pruebas unitarias de la validación del formulario de calibración (RF-08).

Verifican la regla que decide qué escribe y qué rechaza la pantalla de umbrales
ANTES de tocar la base de datos. Corren en cualquier entorno, incluido el CI
headless, porque `gui/validacion_umbrales.py` no importa CustomTkinter: es la
razón por la que la validación se separó del widget.
"""
import pytest

from gui.validacion_umbrales import (
    LIMITE_ANGULAR,
    ValorInvalido,
    formatear_valor,
    interpretar_rango,
)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@pytest.mark.parametrize("texto_min, texto_max, esperado", [
    ("160", "175", (160.0, 175.0)),
    ("160.5", "175.5", (160.5, 175.5)),
    ("160,5", "175", (160.5, 175.0)),      # coma decimal: convención local de escritura
    ("  160 ", " 175 ", (160.0, 175.0)),   # espacios al pegar desde otra parte
    ("0", "180", (0.0, 180.0)),            # los extremos exactos del rango articular
])
def test_acepta_las_formas_validas_de_escribir_un_rango(texto_min, texto_max, esperado):
    assert interpretar_rango(texto_min, texto_max) == esperado


@pytest.mark.parametrize("texto_max", ["", "   ", "-", "—", "sin límite", "Sin Limite", "ninguno"])
def test_un_maximo_vacio_significa_sin_limite_superior(texto_max):
    """
    El Mae Geri exige al menos 400 °/s de velocidad angular y no tiene techo.
    Traducir ese campo a 0.0 en vez de None invertiría la regla: cualquier
    patada quedaría por encima del máximo.
    """
    assert interpretar_rango("400", texto_max, unidad="grados/segundo") == (400.0, None)


def test_el_texto_mostrado_para_sin_limite_vuelve_a_leerse_como_sin_limite():
    """
    Contrato entre lo que la pantalla escribe en el campo y lo que después
    relee de él: sin este viaje de ida y vuelta, abrir la pantalla y guardar
    sin tocar nada convertiría el umbral sin techo en uno con techo.
    """
    mostrado = formatear_valor(None)
    assert interpretar_rango("400", mostrado, unidad="grados/segundo") == (400.0, None)


@ficha(
    id_caso="TC-AUTO-020",
    nombre="El formulario de calibración rechaza todo rango imposible antes de escribirlo en "
           "la base de datos",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="un umbral invertido o fuera del rango articular medible haría que "
                         "una técnica no pueda aprobarse nunca, y el atleta recibiría "
                         "correcciones imposibles de satisfacer sin que nada delate el error",
    componente="gui/validacion_umbrales.py (interpretar_rango)",
    requisitos="RF-08",
    precondiciones="Ninguna. `interpretar_rango` es una función pura, sin estado ni "
                   "dependencias de la interfaz gráfica",
    datos_entrada="Cinco rangos inválidos: mínimo vacío, mínimo no numérico, máximo menor que "
                  "el mínimo (175–160), valor negativo (-5) y ángulo de 200° (fuera del "
                  "rango articular de 0–180°)",
    pasos=[
        Paso("Invocar `interpretar_rango(texto_min, texto_max)` con cada rango inválido",
             "assert se levanta `ValorInvalido` en los cinco casos"),
        Paso("Leer el mensaje de la excepción",
             "assert el fragmento esperado aparece en el mensaje (indica al entrenador "
             "cuál campo corregir, no un rastro técnico)"),
    ],
    resultado_esperado="PASSED. Ningún rango inválido llega a `Database.actualizar_umbral`, "
                       "de modo que no se crea una versión de umbral inservible",
)
@pytest.mark.parametrize("texto_min, texto_max, fragmento_esperado", [
    ("", "175", "mínimo es obligatorio"),
    ("ciento sesenta", "175", "no es un número"),
    ("175", "160", "no puede ser menor"),
    ("-5", "10", "no puede ser negativo"),
    ("160", "200", f"supera los {LIMITE_ANGULAR:g}"),
])
def test_rechaza_los_rangos_imposibles(texto_min, texto_max, fragmento_esperado):
    with pytest.raises(ValorInvalido) as error:
        interpretar_rango(texto_min, texto_max)
    assert fragmento_esperado in str(error.value)


def test_el_techo_de_180_grados_solo_aplica_a_los_angulos():
    """
    El límite de 180° es una propiedad del ángulo articular interno, no una
    cota general: la velocidad angular del Kime supera los 400 °/s por
    definición y aplicarle el mismo techo dejaría la regla sin poder calibrarse.
    """
    assert interpretar_rango("400", "900", unidad="grados/segundo") == (400.0, 900.0)

    with pytest.raises(ValorInvalido):
        interpretar_rango("400", "900", unidad="grados")


@pytest.mark.parametrize("valor, esperado", [
    (160.0, "160"),        # sin el .0 que delata el tipo interno
    (160.5, "160.5"),      # el decimal se conserva cuando sí distingue
    (None, "sin límite"),
])
def test_el_valor_mostrado_es_legible_para_el_entrenador(valor, esperado):
    assert formatear_valor(valor) == esperado
