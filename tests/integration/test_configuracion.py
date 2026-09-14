"""
Pruebas de integración de las preferencias del equipo (RF-01).

La fuente de video dejó de estar escrita en el código y pasó a ser una
preferencia guardada. Estas pruebas verifican que sobreviva al reinicio del
sistema, que es lo que convierte la configuración de la cámara en una tarea de
instalación y no en algo que el entrenador repita cada sesión.
"""
import pytest

from persistence.database import Database
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion


def test_una_preferencia_no_configurada_devuelve_el_valor_por_defecto(db):
    assert db.leer_config("fuente_video") is None
    assert db.leer_config("fuente_video", 0) == 0


@ficha(
    id_caso="TC-AUTO-024",
    nombre="La fuente de video configurada persiste entre ejecuciones del sistema",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="si la preferencia no sobreviviera al reinicio, configurar la cámara "
                         "dejaría de ser una tarea de instalación y pasaría a ser un paso que "
                         "el entrenador repite cada sesión, en contra del ciclo de uso breve "
                         "que exige el RNF-04",
    componente="persistence/database.py (guardar_config, leer_config)",
    requisitos="RF-01",
    precondiciones="Archivo de base de datos temporal; sin preferencias previas",
    datos_entrada="Fuente de video `http://192.168.1.50:8080/video` (cámara IP del dojo)",
    pasos=[
        Paso("Abrir la base, guardar la fuente con `guardar_config` y cerrar la conexión",
             "La escritura se confirma sin excepción"),
        Paso("Abrir de nuevo el MISMO archivo, como ocurre al reiniciar el programa",
             "assert leer_config('fuente_video') devuelve la dirección íntegra"),
    ],
    resultado_esperado="PASSED. La preferencia vive en el mismo archivo SQLite que el resto "
                       "del estado del dojo, de modo que un respaldo la incluye",
)
def test_la_preferencia_sobrevive_al_reinicio_del_sistema(ruta_db_temporal):
    """
    Se cierra la base y se vuelve a abrir el mismo archivo, que es exactamente
    lo que ocurre entre dos ejecuciones del programa en el equipo del dojo.
    """
    primera = Database(ruta_db_temporal)
    primera.guardar_config("fuente_video", "http://192.168.1.50:8080/video")
    primera.close()

    segunda = Database(ruta_db_temporal)
    try:
        assert segunda.leer_config("fuente_video") == "http://192.168.1.50:8080/video"
    finally:
        segunda.close()


def test_reconfigurar_reemplaza_en_vez_de_duplicar(db):
    """
    A diferencia de los umbrales, una preferencia del equipo no necesita
    historial: solo importa la vigente. Guardar dos veces deja una sola fila.
    """
    db.guardar_config("fuente_video", 2)
    db.guardar_config("fuente_video", 0)

    assert db.leer_config("fuente_video") == "0"
    filas = db.conn.execute(
        "SELECT COUNT(*) AS n FROM configuracion WHERE clave = 'fuente_video'").fetchone()
    assert filas["n"] == 1


def test_los_valores_se_guardan_como_texto(db):
    """
    SQLite es laxo con los tipos; fijar el contrato evita que un índice vuelva
    unas veces como int y otras como str según cómo se guardó.
    """
    db.guardar_config("fuente_video", 2)
    assert db.leer_config("fuente_video") == "2"


def test_la_migracion_no_toca_una_base_ya_existente(ruta_db_temporal):
    """
    La tabla `configuracion` se agregó cuando ya existían bases con datos
    reales. Abrirla de nuevo debe crear la tabla sin perder lo anterior.
    """
    primera = Database(ruta_db_temporal)
    id_atleta = primera.crear_atleta("Atleta Previo", grado_cinturon="5o kyu")
    primera.close()

    segunda = Database(ruta_db_temporal)
    try:
        assert [a["id_atleta"] for a in segunda.listar_atletas()] == [id_atleta]
        segunda.guardar_config("fuente_video", 1)
        assert segunda.leer_config("fuente_video") == "1"
    finally:
        segunda.close()
