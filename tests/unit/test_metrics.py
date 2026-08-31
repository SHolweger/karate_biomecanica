"""
Pruebas unitarias de biomechanics/metrics.py (PerformanceMonitor).

No requieren cámara ni hardware: se inyecta un reloj determinista para
comprobar la aritmética de las mediciones contra valores conocidos de
antemano. Que el monitor reciba su fuente de tiempo por parámetro es
justamente lo que hace verificable una clase que mide tiempo real.
"""
import pytest
from biomechanics.metrics import PerformanceMonitor


class RelojSimulado:
    """Reloj determinista: cada llamada devuelve el siguiente valor de la lista."""

    def __init__(self, valores):
        self.valores = list(valores)
        self.i = 0

    def __call__(self):
        v = self.valores[self.i]
        self.i += 1
        return v


@pytest.mark.unitaria
def test_mide_cada_etapa_por_separado():
    # iniciar=0.0 | marcar('pose')=0.010 | marcar('analisis')=0.035 | cerrar=0.040
    reloj = RelojSimulado([0.0, 0.010, 0.035, 0.040])
    m = PerformanceMonitor(descartar_iniciales=0, reloj=reloj)

    m.iniciar_frame()
    m.marcar("pose")
    m.marcar("analisis")
    m.cerrar_frame()

    etapas = m.resumen_etapas()
    assert abs(etapas["pose"]["media"] - 10.0) < 1e-6, etapas["pose"]
    assert abs(etapas["analisis"]["media"] - 25.0) < 1e-6, etapas["analisis"]
    assert abs(m.resumen_total()["media"] - 40.0) < 1e-6, m.resumen_total()


@pytest.mark.unitaria
def test_descarta_fotogramas_de_calentamiento():
    # 4 fotogramas con etapa de 10, 20, 30 y 40 ms. Con descarte=2 solo
    # deben promediarse los dos ultimos.
    valores = []
    for k, dur in enumerate([0.010, 0.020, 0.030, 0.040]):
        base = float(k)
        valores += [base, base + dur, base + dur]  # iniciar, marcar, cerrar
    m = PerformanceMonitor(descartar_iniciales=2, reloj=RelojSimulado(valores))

    for _ in range(4):
        m.iniciar_frame()
        m.marcar("etapa")
        m.cerrar_frame()

    stats = m.resumen_etapas()["etapa"]
    assert stats["n"] == 2, f"deberia estadistiquear 2 fotogramas, no {stats['n']}"
    assert abs(stats["media"] - 35.0) < 1e-6, stats
    # El registro crudo conserva los 4, aunque las estadisticas usen 2.
    assert len(m.etapas["etapa"]) == 4


@pytest.mark.unitaria
def test_estadisticas_con_valores_conocidos():
    impares = PerformanceMonitor._estadisticas([30, 10, 50, 20, 40])
    assert impares["media"] == 30
    assert impares["mediana"] == 30
    assert impares["max"] == 50
    assert impares["p95"] == 50

    pares = PerformanceMonitor._estadisticas([10, 20, 30, 40])
    assert pares["mediana"] == 25, pares
    assert pares["p95"] == 40, pares

    assert PerformanceMonitor._estadisticas([]) is None


@pytest.mark.unitaria
def test_fps_se_calcula_entre_inicios_de_fotograma():
    # Fotogramas que arrancan cada 40 ms => 25 fps sostenidos.
    valores = []
    for k in range(4):
        base = k * 0.04
        valores += [base, base + 0.001]  # iniciar, cerrar
    m = PerformanceMonitor(descartar_iniciales=0, reloj=RelojSimulado(valores))

    for _ in range(4):
        m.iniciar_frame()
        m.cerrar_frame()

    fps = m.resumen_fps()
    assert abs(fps["medio"] - 25.0) < 1e-6, fps
    assert fps["fotogramas"] == 4, fps
    # El fps NO se deduce del tiempo de computo (1 ms), sino del intervalo real.
    assert abs(m.resumen_total()["media"] - 1.0) < 1e-6


@pytest.mark.unitaria
def test_marcar_sin_iniciar_frame_falla():
    m = PerformanceMonitor()
    try:
        m.marcar("pose")
    except RuntimeError:
        return
    raise AssertionError("marcar() sin iniciar_frame() deberia lanzar RuntimeError")


@pytest.mark.unitaria
def test_sin_datos_suficientes_no_revienta():
    m = PerformanceMonitor(descartar_iniciales=5)
    assert m.resumen_total() is None
    assert m.resumen_fps() is None
    assert m.resumen_etapas() == {}
