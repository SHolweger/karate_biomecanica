"""
Pruebas unitarias de biomechanics/filters.py (MovingAverageFilter).

El filtro es la defensa del sistema contra el jitter de MediaPipe: sin él,
el ángulo de una articulación quieta oscila varios grados por frame y el
diagnóstico en pantalla parpadea entre "CORRECTO" e "INCORRECTO".
"""
import statistics

import pytest

from biomechanics.filters import MovingAverageFilter

pytestmark = pytest.mark.unitaria


def test_la_primera_medicion_se_devuelve_intacta():
    """Con el buffer vacío no hay historial que promediar."""
    filtro = MovingAverageFilter(window=5)

    assert filtro.update(170.0) == pytest.approx(170.0)


def test_promedia_mientras_el_buffer_se_llena():
    """Antes de completar la ventana promedia solo lo que ya recibió, sin ceros de relleno."""
    filtro = MovingAverageFilter(window=5)

    assert filtro.update(100.0) == pytest.approx(100.0)
    assert filtro.update(200.0) == pytest.approx(150.0)
    assert filtro.update(300.0) == pytest.approx(200.0)


def test_la_ventana_descarta_la_medicion_mas_antigua():
    """
    Con ventana=3, al llegar el cuarto valor el primero debe salir del cálculo.
    Es lo que evita que un ángulo de hace un segundo siga afectando el
    diagnóstico actual.
    """
    filtro = MovingAverageFilter(window=3)
    for valor in (0.0, 30.0, 60.0):
        filtro.update(valor)

    resultado = filtro.update(90.0)  # promedio de (30, 60, 90), sin el 0 inicial

    assert resultado == pytest.approx(60.0)


def test_ventana_de_uno_no_suaviza():
    """Configuración usada por las pruebas de la máquina de estados: pasa el valor tal cual."""
    filtro = MovingAverageFilter(window=1)

    assert filtro.update(45.0) == pytest.approx(45.0)
    assert filtro.update(170.0) == pytest.approx(170.0)


def test_reset_borra_el_historial():
    """
    Cuando la articulación se oculta y reaparece, el filtro debe partir de
    cero: promediar la posición nueva con la de antes de la oclusión
    produciría un ángulo que el karateka nunca ejecutó.
    """
    filtro = MovingAverageFilter(window=5)
    for _ in range(5):
        filtro.update(40.0)

    filtro.reset()

    assert filtro.update(180.0) == pytest.approx(180.0), \
        "tras reset, la primera medicion no debe mezclarse con valores previos"


def test_reduce_la_dispersion_del_ruido():
    """
    Prueba de la propiedad que justifica el módulo: alimentado con una señal
    ruidosa alrededor de 170 grados, la salida debe dispersarse menos que la
    entrada. Esto es lo que en la práctica elimina el parpadeo del diagnóstico.
    """
    ruido = [168.0, 174.0, 169.0, 173.0, 167.0, 175.0, 170.0, 172.0, 168.0, 174.0]
    filtro = MovingAverageFilter(window=5)

    suavizado = [filtro.update(v) for v in ruido]

    assert statistics.pstdev(suavizado) < statistics.pstdev(ruido) / 2, \
        "el filtro deberia reducir la dispersion del jitter al menos a la mitad"


def test_conserva_el_nivel_de_una_senal_estable():
    """El suavizado no debe introducir sesgo: una señal constante sale igual."""
    filtro = MovingAverageFilter(window=5)

    for _ in range(20):
        salida = filtro.update(155.0)

    assert salida == pytest.approx(155.0)


def test_converge_tras_un_cambio_brusco_de_postura():
    """
    Al pasar de una postura a otra, el filtro introduce retraso pero debe
    converger al valor nuevo dentro de la ventana (5 frames ~ 165 ms a 30 fps).
    Un filtro que no converja dejaría el diagnóstico permanentemente desfasado.
    """
    filtro = MovingAverageFilter(window=5)
    for _ in range(5):
        filtro.update(90.0)

    for _ in range(5):
        salida = filtro.update(170.0)

    assert salida == pytest.approx(170.0, abs=0.01)
