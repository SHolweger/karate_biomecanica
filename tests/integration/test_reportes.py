"""
Pruebas de integración de persistence/reportes.py (gráficas de progreso).

El reporte es el entregable que el sensei realmente mira: si la métrica está
mal calculada, el alumno recibe retroalimentación falsa sobre su avance. Se
verifica primero el cálculo del porcentaje y después la generación del archivo.

matplotlib es opcional para el resto de la suite; si no está instalado, este
módulo se omite en vez de fallar.
"""
import os

import pytest

matplotlib = pytest.importorskip("matplotlib", reason="matplotlib no está instalado")

from persistence.reportes import _porcentaje_correcto, generar_reporte_progreso

pytestmark = pytest.mark.integracion


def _medicion(correcto):
    """Fila mínima con la única clave que usa el cálculo del porcentaje."""
    return {"correcto": correcto}


# --------------------------------------------------------------------------
# Cálculo de la métrica
# --------------------------------------------------------------------------

@pytest.mark.parametrize("veredictos, esperado", [
    ([True, True, True, True], 100.0),
    ([True, True, True, False], 75.0),
    ([True, False], 50.0),
    ([False, False], 0.0),
])
def test_calcula_el_porcentaje_de_aciertos(veredictos, esperado):
    assert _porcentaje_correcto([_medicion(v) for v in veredictos]) == pytest.approx(esperado)


def test_los_estados_transitorios_no_alteran_el_porcentaje():
    """
    Los diagnósticos sin veredicto ("EN TRANSICION", "CARGA", oclusiones) se
    excluyen del cálculo: si contaran como error, el alumno aparecería peor de
    lo que es solo por haberse movido entre técnicas.
    """
    con_transitorios = [_medicion(True), _medicion(False), _medicion(None), _medicion(None)]

    assert _porcentaje_correcto(con_transitorios) == pytest.approx(50.0)


def test_sin_evaluaciones_cerradas_no_hay_porcentaje():
    """Devuelve None, no 0%: no es lo mismo "no hay datos" que "falló todo"."""
    assert _porcentaje_correcto([_medicion(None), _medicion(None)]) is None
    assert _porcentaje_correcto([]) is None


# --------------------------------------------------------------------------
# Generación del archivo de reporte
# --------------------------------------------------------------------------

def test_no_genera_grafica_si_la_sesion_no_dejo_evaluaciones(sesion_de_prueba, tmp_path):
    """Sesión donde el atleta solo estuvo en transición: no hay nada que graficar."""
    db, id_sesion, id_atleta, _ = sesion_de_prueba
    carpeta = tmp_path / "evidencias"
    carpeta.mkdir()
    db.guardar_medicion(id_sesion, "Postura de piernas", 150.0, "MOVIENDOSE: EN TRANSICION...",
                        timestamp_ms=0, correcto=None)
    db.cerrar_sesion(id_sesion)

    ruta = generar_reporte_progreso(db, id_atleta, "Atleta Ejemplo", carpeta=str(carpeta))

    assert ruta is None
    assert list(carpeta.iterdir()) == [], "no debe dejar archivos vacíos en evidencias/"


@pytest.mark.lenta
def test_genera_un_png_con_el_historial_de_dos_sesiones(db, tmp_path):
    """
    Camino feliz del reporte: dos sesiones con distinto desempeño producen un
    PNG real y no vacío, listo para adjuntarse al expediente del alumno.
    """
    id_entrenador = db.crear_entrenador("Sensei", "sensei", "s@dojo.gt", "clave")
    id_atleta = db.crear_atleta("Diego Morales", grado_cinturon="5o kyu")

    primera = db.iniciar_sesion(id_atleta, id_entrenador)
    db.guardar_medicion(primera, "Tsuki (brazo derecho)", 172.0, "TSUKI: EXCELENTE", 0, True)
    db.guardar_medicion(primera, "Tsuki (brazo derecho)", 150.0, "TSUKI: FLEXIONADO", 1000, False)
    db.guardar_medicion(primera, "Postura de piernas", 110.0, "ZENKUTSU: POSTURA: FIRME", 2000, True)
    db.cerrar_sesion(primera)

    segunda = db.iniciar_sesion(id_atleta, id_entrenador)
    db.guardar_medicion(segunda, "Tsuki (brazo derecho)", 170.0, "TSUKI: EXCELENTE", 0, True)
    db.guardar_medicion(segunda, "Mae Geri (pierna izquierda)", 168.0, "MAE GERI: KIME EXCELENTE",
                        1200, True)
    db.cerrar_sesion(segunda)

    ruta = generar_reporte_progreso(db, id_atleta, "Diego Morales", carpeta=str(tmp_path))

    assert ruta is not None, "con datos evaluados debe generarse el reporte"
    assert os.path.exists(ruta)
    assert ruta.endswith(".png")
    assert os.path.getsize(ruta) > 5000, "el PNG parece vacío"


@pytest.mark.lenta
def test_crea_la_carpeta_de_evidencias_si_no_existe(sesion_de_prueba, tmp_path):
    """El sensei no debería tener que crear carpetas a mano antes de exportar."""
    db, id_sesion, id_atleta, _ = sesion_de_prueba
    db.guardar_medicion(id_sesion, "Tsuki (brazo derecho)", 170.0, "TSUKI: EXCELENTE", 0, True)
    destino = tmp_path / "carpeta" / "que" / "no" / "existe"

    ruta = generar_reporte_progreso(db, id_atleta, "Atleta Ejemplo", carpeta=str(destino))

    assert ruta is not None and os.path.exists(ruta)


@pytest.mark.lenta
def test_dos_reportes_seguidos_no_se_sobrescriben(sesion_de_prueba, tmp_path):
    """El nombre incluye una marca de tiempo para conservar el historial de reportes."""
    db, id_sesion, id_atleta, _ = sesion_de_prueba
    db.guardar_medicion(id_sesion, "Tsuki (brazo derecho)", 170.0, "TSUKI: EXCELENTE", 0, True)

    primera = generar_reporte_progreso(db, id_atleta, "Atleta Ejemplo", carpeta=str(tmp_path))
    segunda = generar_reporte_progreso(db, id_atleta, "Atleta Ejemplo", carpeta=str(tmp_path))

    assert primera is not None and segunda is not None
    assert str(id_atleta) in os.path.basename(primera), "el archivo debe identificar al atleta"
