"""
tests/conftest.py — Fixtures compartidas por toda la suite.

Centralizar aquí la creación de bases de datos temporales y de poses
sintéticas evita que cada archivo de prueba repita el mismo andamiaje
(principio de reusabilidad de scripts exigido por el plan de automatización).
"""
import pytest

from persistence.database import Database
from expert_system.knowledge_base import KarateRules
from helpers.fakes import CamaraSintetica



@pytest.fixture
def reglas():
    """
    Base de conocimientos con los umbrales de literatura, sin base de datos.

    KarateRules dejó de ser una clase de métodos estáticos cuando los umbrales
    pasaron a ser datos parametrizados (RF-08): ahora se instancia. Sin
    argumento carga los valores bibliográficos, que es justo lo que las
    pruebas unitarias necesitan — un criterio fijo y conocido, independiente
    de lo que un entrenador haya recalibrado en la base de datos.
    """
    return KarateRules()


@pytest.fixture
def ruta_db_temporal(tmp_path):
    """Ruta a un archivo .db que aún no existe: Database lo crea desde cero."""
    return str(tmp_path / "karate_prueba.db")


@pytest.fixture
def db(ruta_db_temporal):
    """
    Base de datos SQLite vacía y aislada por prueba.

    Cada prueba recibe un archivo nuevo bajo tmp_path, así que el orden de
    ejecución nunca cambia el resultado (pruebas independientes y repetibles).
    """
    conexion = Database(ruta_db_temporal)
    yield conexion
    conexion.close()


@pytest.fixture
def sesion_de_prueba(db):
    """
    Base de datos con un entrenador, un atleta y una sesión abierta: el estado
    previo mínimo para poder guardar mediciones.

    Devuelve (db, id_sesion, id_atleta, id_entrenador).
    """
    id_entrenador = db.crear_entrenador("Sensei Ejemplo", "sensei", "sensei@dojo.gt",
                                        "clave123", rol="principal")
    id_atleta = db.crear_atleta("Atleta Ejemplo", grado_cinturon="5o kyu")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)
    return db, id_sesion, id_atleta, id_entrenador


@pytest.fixture
def camara_sintetica():
    """Cámara falsa reutilizable para las pruebas de GUI y del pipeline de video."""
    return CamaraSintetica()


@pytest.fixture
def dimensiones_frame():
    """Resolución usada al convertir landmarks normalizados a píxeles (ancho, alto)."""
    return 1000, 1000


def pytest_report_header(config):
    """Encabezado del reporte: deja constancia del entorno en la evidencia de ejecución."""
    return "proyecto: Shotokan AI - Sistema experto de biomecanica del karate (suite pytest)"
