"""
Pruebas de la herramienta que describe la base antes de apartarla.

La lógica es pura —recibe filas, no toca SQLite— así que corre en los dos
entornos. Lo que se protege es que la cifra que va a la tesis sea una cota
inferior de verdad: una herramienta que contara de más al describir su propio
defecto sería exactamente la clase de evidencia que no se puede presentar.
"""
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from revisar_base import (VENTANA_ALTERNANCIA_MS, alternancias_rapidas,
                          es_tsuki, resumen_por_tecnica)

pytestmark = pytest.mark.unitaria

BRAZO_IZQ = "Tsuki (brazo izquierdo)"


def _fila(t, diagnostico, correcto, tecnica=BRAZO_IZQ, sesion=1):
    return {"id_sesion": sesion, "nombre_tecnica": tecnica, "timestamp_ms": t,
            "diagnostico": diagnostico, "correcto": correcto}


def _brazo_en_reposo(n=6, t0=0, paso=33, sesion=1):
    """
    Lo que escribía el código viejo con alguien de pie: el ángulo tiembla
    alrededor de 175° y el veredicto alterna de un fotograma al siguiente.
    """
    return [_fila(t0 + i * paso,
                  f"IZQ - TSUKI: {'EXCELENTE' if i % 2 else 'HIPEREXTENDIDO (Peligro)'}",
                  i % 2 == 1, sesion=sesion)
            for i in range(n)]


def _golpes_reales(n=4, separacion=800):
    """Tsukis de verdad: separados cientos de milisegundos y con el mismo veredicto."""
    return [_fila(i * separacion, "IZQ - TSUKI: EXCELENTE", True) for i in range(n)]


@ficha(
    id_caso="TC-AUTO-059",
    nombre="La cota de contaminacion cuenta el reposo y no cuenta los golpes reales",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la cifra que produce esta herramienta esta destinada a la "
                         "seccion de validacion de la tesis, donde sostiene cuanto "
                         "contamino el historial el defecto del Tsuki del 30-sep. Una "
                         "herramienta que contara de mas al describir su propio defecto "
                         "produciria evidencia que la terna puede desmontar corriendo "
                         "la consulta, que es peor que no tener cifra. Por eso se "
                         "verifica en las dos direcciones: que detecte la firma del "
                         "brazo en reposo y que NO marque una serie de golpes reales",
    componente="revisar_base.py (alternancias_rapidas, resumen_por_tecnica)",
    requisitos="RF-07",
    precondiciones="Ninguna: la logica es pura y no abre la base de datos",
    datos_entrada="Dos series sinteticas de mediciones: un brazo en reposo alternando "
                  "veredictos cada 33 ms y cuatro Tsukis reales separados 800 ms",
    pasos=[
        Paso("Contar alternancias sobre la serie del brazo en reposo",
             "assert marca las filas implicadas: veredictos opuestos a menos de "
             "150 ms no pueden venir de dos golpes"),
        Paso("Contar alternancias sobre la serie de golpes reales",
             "assert no marca ninguna, aunque los veredictos sean cerrados"),
        Paso("Comprobar que no se mezclan dos sesiones distintas",
             "assert filas de sesiones diferentes con marcas cercanas no se cuentan "
             "como una alternancia"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz grafica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_la_cota_cuenta_el_reposo_y_respeta_los_golpes():
    assert alternancias_rapidas(_brazo_en_reposo(n=6)) == 6, \
        "las seis filas participan: se cuentan FILAS, no parejas"

    assert alternancias_rapidas(_golpes_reales()) == 0, \
        "cuatro Tsukis separados 800 ms no son contaminacion"

    # Dos sesiones distintas con marcas de tiempo cercanas: cada grabación lleva
    # su propio reloj, así que compararlas entre sí no significaría nada.
    cruzadas = [_fila(0, "IZQ - TSUKI: EXCELENTE", True, sesion=1),
                _fila(10, "IZQ - TSUKI: HIPEREXTENDIDO (Peligro)", False, sesion=2)]
    assert alternancias_rapidas(cruzadas) == 0


def test_dos_brazos_no_se_confunden_entre_si():
    """
    El izquierdo y el derecho se registran con marcas de tiempo idénticas
    —salen del mismo fotograma— así que compararlos daría una alternancia
    falsa en cada fotograma de cualquier sesión.
    """
    mismo_instante = [
        _fila(0, "IZQ - TSUKI: EXCELENTE", True, tecnica="Tsuki (brazo izquierdo)"),
        _fila(0, "DER - TSUKI: HIPEREXTENDIDO (Peligro)", False,
              tecnica="Tsuki (brazo derecho)"),
    ]

    assert alternancias_rapidas(mismo_instante) == 0


def test_la_cuenta_nunca_supera_el_total_de_filas():
    """
    Regresión de un error que solo se vio al contrastar contra una base real:
    sumando dos por cada pareja, una tanda alternante producía casi el doble de
    filas de las que existían. La primera corrida informó «190,4 % del total»,
    que es la clase de cifra que desmonta un capítulo entero.
    """
    filas = _brazo_en_reposo(n=40)

    assert alternancias_rapidas(filas) <= len(filas)


def test_una_alternancia_lenta_no_se_cuenta():
    """
    La cota es deliberadamente conservadora. Si la separación supera la ventana,
    no se cuenta aunque los veredictos sean opuestos: podrían ser dos golpes,
    uno bueno y uno bloqueado, que es exactamente lo que el sistema debe medir.
    """
    lenta = [_fila(0, "IZQ - TSUKI: EXCELENTE", True),
             _fila(VENTANA_ALTERNANCIA_MS + 1, "IZQ - TSUKI: HIPEREXTENDIDO (Peligro)", False)]

    assert alternancias_rapidas(lenta) == 0


def test_la_precision_solo_cuenta_veredictos_cerrados():
    """
    Mismo criterio que las consultas agregadas del sistema: un estado
    transitorio o una articulación fuera de cuadro no es un fallo del alumno.
    """
    filas = [_fila(0, "IZQ - TSUKI: EXCELENTE", True),
             _fila(100, "IZQ - TSUKI: FLEXIONADO", False),
             _fila(200, "BRAZO IZQ: OCULTO/NO VISIBLE", None)]

    resumen = resumen_por_tecnica(filas)[BRAZO_IZQ]

    assert resumen["total"] == 3
    assert resumen["cerradas"] == 2
    assert resumen["precision"] == 50.0


def test_una_tecnica_sin_veredictos_cerrados_no_reporta_cero_por_ciento():
    """
    Es la regla que gobierna toda la presentación del sistema: sin evaluaciones
    cerradas la precisión es desconocida, no nula. Un alumno sin medir no falla
    el 100 % de sus técnicas.
    """
    resumen = resumen_por_tecnica([_fila(0, "BRAZO IZQ: OCULTO/NO VISIBLE", None)])

    assert resumen[BRAZO_IZQ]["precision"] is None


def test_reconoce_las_dos_filas_de_tsuki_y_no_las_demas():
    assert es_tsuki("Tsuki (brazo izquierdo)")
    assert es_tsuki("Tsuki (brazo derecho)")
    assert not es_tsuki("Postura de piernas")
    assert not es_tsuki(None)
