"""
Pruebas unitarias de biomechanics/metrics.py (PerformanceMonitor).

No requieren cámara ni hardware: se inyecta un reloj determinista para
comprobar la aritmética de las mediciones contra valores conocidos de
antemano. Que el monitor reciba su fuente de tiempo por parámetro es
justamente lo que hace verificable una clase que mide tiempo real.
"""
import pytest
from biomechanics.metrics import MonitorConTope, PerformanceMonitor
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha


class RelojSimulado:
    """Reloj determinista: cada llamada devuelve el siguiente valor de la lista."""

    def __init__(self, valores):
        self.valores = list(valores)
        self.i = 0

    def __call__(self):
        v = self.valores[self.i]
        self.i += 1
        return v


@ficha(
    id_caso="TC-AUTO-015",
    nombre="El instrumento que mide la latencia del pipeline cronometra cada etapa por "
           "separado con un reloj determinista",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="es el instrumento con el que se declara el cumplimiento del "
                         "RNF-01; si mide mal, el resultado reportado en el capítulo 4 "
                         "no vale",
    componente="biomechanics/metrics.py (PerformanceMonitor)",
    requisitos=["RNF-01", "RF-01"],
    precondiciones="`PerformanceMonitor` construido con `descartar_iniciales=0` y un "
                   "reloj simulado inyectado por parámetro",
    datos_entrada="Secuencia de lecturas del reloj: iniciar=0.0 s, marcar('pose')=0.010 s, "
                  "marcar('analisis')=0.035 s, cerrar=0.040 s",
    pasos=[
        Paso("Inyectar el reloj determinista y abrir un fotograma",
             "El monitor no consulta el reloj real del sistema"),
        Paso("Marcar las etapas `pose` y `analisis` y cerrar el fotograma",
             "Cada marca queda asociada a su etapa"),
        Paso("Consultar `resumen_etapas()`",
             "assert abs(etapas['pose']['media'] - 10.0) < 1e-6 y "
             "abs(etapas['analisis']['media'] - 25.0) < 1e-6"),
        Paso("Consultar el total del fotograma",
             "assert abs(resumen_total()['media'] - 40.0) < 1e-6"),
    ],
    resultado_esperado="PASSED. La aritmética de las mediciones coincide con los valores "
                       "conocidos de antemano en milisegundos",
    evidencia="Reporte de consola de pytest; medición real del sistema en "
              "`evidencias/rendimiento_*.csv` y `evidencias/rendimiento_*.png`.",
)
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


# --------------------------------------------------------------------------
# El monitor que se detiene solo
#
# Nace de un defecto medido: una medición de 300 fotogramas procesó los 11 515
# del archivo entero —ocho minutos de cómputo— porque la cuota se comprobaba
# desde un temporizador de Tk al que el bucle de análisis dejaba sin turno.
# --------------------------------------------------------------------------

def test_el_monitor_avisa_exactamente_al_alcanzar_su_cuota():
    llamadas = []
    monitor = MonitorConTope(3, lambda: llamadas.append(len(monitor.totales)),
                             descartar_iniciales=0)

    for _ in range(3):
        monitor.iniciar_frame()
        monitor.cerrar_frame()

    assert llamadas == [3], "debe avisar al tercero, ni antes ni después"
    assert monitor.completado


def test_no_avisa_dos_veces_aunque_siga_midiendo():
    """
    El aviso detiene el bucle, pero el fotograma en curso puede alcanzar a
    cerrarse. Avisar de nuevo volvería a llamar a `quit()` sobre una interfaz
    ya cerrada.
    """
    llamadas = []
    monitor = MonitorConTope(2, lambda: llamadas.append(1), descartar_iniciales=0)

    for _ in range(5):
        monitor.iniciar_frame()
        monitor.cerrar_frame()

    assert llamadas == [1]


def test_antes_de_la_cuota_no_esta_completado():
    monitor = MonitorConTope(10, lambda: None, descartar_iniciales=0)
    monitor.iniciar_frame()
    monitor.cerrar_frame()

    assert not monitor.completado


def test_sigue_siendo_un_monitor_de_rendimiento():
    """Hereda el cronometraje: la cuota es lo único que añade."""
    monitor = MonitorConTope(99, lambda: None, descartar_iniciales=0)
    monitor.iniciar_frame()
    monitor.marcar("captura")
    monitor.cerrar_frame()

    assert len(monitor.totales) == 1
    assert "captura" in monitor.etapas


# ---------------------------------------------------------------------------
# La evidencia guarda la cadencia, no solo el cómputo (18-oct-2026)
# ---------------------------------------------------------------------------

def _monitor_como_la_interfaz(fotogramas=8, computo_s=0.034, periodo_s=0.049):
    """
    Fotogramas con la forma de la interfaz real: 34 ms de trabajo y el siguiente
    empieza 49 ms después del anterior, porque el bucle espera su intervalo fijo
    de 15 ms. Son las cifras de la corrida del 27-sep (cómputo mediano 33,8 ms)
    más `LiveScreen.INTERVALO_MS`.
    """
    valores = []
    for k in range(fotogramas):
        base = k * periodo_s
        valores += [base, base + 0.005, base + computo_s]   # iniciar, marcar, cerrar
    m = PerformanceMonitor(descartar_iniciales=0, reloj=RelojSimulado(valores))
    for _ in range(fotogramas):
        m.iniciar_frame()
        m.marcar("captura")
        m.cerrar_frame()
    return m


@ficha(
    id_caso="TC-AUTO-070",
    nombre="La evidencia de rendimiento guarda la cadencia entre fotogramas y no solo el cómputo",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "el CSV de evidencia solo guardaba el cómputo por fotograma, y de él se "
        "dedujo el 15-oct-2026 una tasa de 29,6 fps para la interfaz cuya "
        "cadencia real no pasaba de unos 20: el cómputo no incluye la espera "
        "fija del bucle. La cifra se escribió en la memoria del proyecto y se "
        "le comunicó al autor como «a 0,4 fps de cumplir el RF-01»"),
    componente="biomechanics/metrics.py (intervalos_ms) + test_rendimiento.py (reportar)",
    requisitos=("RF-01", "RNF-01"),
    precondiciones="Ninguna. Se inyecta un reloj determinista",
    datos_entrada="Ocho fotogramas de 34 ms de cómputo que empiezan cada 49 ms",
    pasos=[
        Paso("Medir los intervalos entre inicios de fotograma",
             "assert intervalos == [49.0] * 7 + [None]"),
        Paso("Comparar la tasa por intervalo con la tasa por cómputo",
             "assert 1000 / intervalo != 1000 / cómputo"),
        Paso("Escribir la evidencia con reportar()",
             "assert la columna intervalo_ms está en el CSV con 49 ms"),
    ],
    resultado_esperado="PASSED: la cadencia se puede recuperar de la evidencia guardada",
)
def test_los_intervalos_se_miden_entre_inicios_de_fotograma():
    m = _monitor_como_la_interfaz()

    intervalos = m.intervalos_ms()

    assert intervalos[-1] is None, "el último fotograma no tiene siguiente"
    assert all(abs(i - 49.0) < 1e-6 for i in intervalos[:-1]), intervalos
    assert len(intervalos) == len(m.totales)


def test_la_cadencia_no_se_deduce_del_computo():
    """
    El error del 15-oct-2026, escrito como prueba: 1000 / cómputo da el techo
    que tendría un bucle sin espera, no la tasa que ve el sensei.
    """
    m = _monitor_como_la_interfaz()
    computo = m.resumen_total()["media"]
    intervalo = sum(i for i in m.intervalos_ms() if i is not None) / (len(m.totales) - 1)

    assert abs(1000.0 / computo - 29.4) < 0.1     # lo que se dijo
    assert abs(1000.0 / intervalo - 20.4) < 0.1   # lo que era
    assert abs(m.resumen_fps()["medio"] - 1000.0 / intervalo) < 1e-6


def test_sin_fotogramas_no_hay_intervalos():
    assert PerformanceMonitor().intervalos_ms() == []


def test_el_csv_de_evidencia_guarda_el_intervalo(tmp_path):
    """
    La costura: lo que de verdad queda en `evidencias/`. Importa la herramienta
    de rendimiento, que necesita OpenCV; sin él, esta prueba concreta se omite.
    """
    pytest.importorskip("cv2", reason="test_rendimiento.py importa OpenCV")
    import csv as _csv
    from test_rendimiento import reportar

    reportar(_monitor_como_la_interfaz(), carpeta=str(tmp_path), etapas=["captura"])

    [ruta] = list(tmp_path.glob("rendimiento_*.csv"))
    filas = list(_csv.DictReader(open(ruta, newline="")))
    assert "intervalo_ms" in filas[0]
    assert all(abs(float(f["intervalo_ms"]) - 49.0) < 1e-3 for f in filas[:-1])
    assert filas[-1]["intervalo_ms"] == ""
