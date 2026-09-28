"""
Pruebas de la resolución de rutas del modelo y de la base de datos.

Corren en las unitarias porque `rutas.py` no importa MediaPipe, OpenCV ni
sqlite3: resuelve rutas y nada más.

Lo que aquí se protege es el arranque de la aplicación empaquetada, que es
justo lo que no puede probarse desde el entorno de desarrollo: todo el trabajo
se ha hecho ejecutando `python3 main.py` desde la carpeta del proyecto, donde
una ruta relativa funciona por casualidad.
"""
import os

import pytest

import rutas
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from rutas import (ModeloNoEncontrado, NOMBRE_BASE, NOMBRE_MODELO, VAR_BASE,
                   VAR_MODELO, base_de_datos, carpeta_de_datos, modelo)

pytestmark = pytest.mark.unitaria


def _con_modelo(carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / NOMBRE_MODELO).write_bytes(b"modelo falso")
    return carpeta


# ---------------------------------------------------------------------------
# El modelo
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-054",
    nombre="El modelo y la base de datos se resuelven sin depender del directorio "
           "desde el que se lanzó la aplicación",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="el modelo de pose se pedía como ruta relativa en seis "
                         "módulos y la base de datos en uno. Una ruta relativa se "
                         "resuelve contra el directorio de trabajo, que durante el "
                         "desarrollo coincide con la carpeta del proyecto y deja de "
                         "coincidir en cuanto la aplicación se empaqueta: un `.command` "
                         "abierto con doble clic arranca en la carpeta personal del "
                         "usuario. El fallo resultante impide arrancar y el error que "
                         "produce MediaPipe no nombra el archivo que falta",
    componente="rutas.py (modelo, base_de_datos, raiz_aplicacion)",
    requisitos="RF-01, RNF-02",
    precondiciones="Ninguna: el módulo no importa MediaPipe, OpenCV ni sqlite3",
    datos_entrada="Carpetas temporales que simulan la raíz de la aplicación y el "
                  "directorio personal, más un entorno declarado explícitamente",
    pasos=[
        Paso("Resolver el modelo con la raíz declarada y el archivo presente",
             "assert devuelve una ruta absoluta que apunta al archivo"),
        Paso("Resolver el modelo cuando el archivo no está",
             "assert lanza ModeloNoEncontrado y el mensaje nombra el archivo y la "
             "carpeta donde se buscó, en vez de dejar que falle MediaPipe"),
        Paso("Resolver la base de datos sin base heredada junto al código",
             "assert cae en la carpeta de datos del sistema operativo"),
        Paso("Resolver la base de datos con una base ya existente junto al código",
             "assert devuelve ESA y no la del sistema: actualizar el programa no "
             "puede dejar huérfano el historial de mediciones"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_las_rutas_no_dependen_del_directorio_de_trabajo(tmp_path):
    raiz = _con_modelo(tmp_path / "app")
    hogar = tmp_path / "hogar"

    assert modelo(entorno={}, raiz=raiz) == str(raiz / NOMBRE_MODELO)

    sin_modelo = tmp_path / "vacia"
    sin_modelo.mkdir()
    with pytest.raises(ModeloNoEncontrado) as error:
        modelo(entorno={}, raiz=sin_modelo)
    assert NOMBRE_MODELO in str(error.value)
    assert str(sin_modelo) in str(error.value)

    nueva = base_de_datos(entorno={}, raiz=raiz, inicio=hogar)
    assert str(hogar) in nueva, "una base nueva nace en la carpeta de datos"

    heredada = raiz / NOMBRE_BASE
    heredada.write_bytes(b"")
    assert base_de_datos(entorno={}, raiz=raiz, inicio=hogar) == str(heredada)


def test_una_base_ya_existente_nunca_se_abandona(tmp_path):
    """
    Es la garantía que evita perder el historial: todo el desarrollo escribió
    en `karate_sistema.db` dentro del repositorio, y si actualizar el programa
    empezara a escribir en otro sitio, la lista de alumnos aparecería vacía sin
    que nada avisara. Migrar es decisión del usuario, no efecto secundario.
    """
    raiz = _con_modelo(tmp_path / "app")
    (raiz / NOMBRE_BASE).write_bytes(b"historial")

    assert base_de_datos(entorno={}, raiz=raiz,
                         inicio=tmp_path / "hogar") == str(raiz / NOMBRE_BASE)


def test_lo_declarado_por_el_usuario_manda_sobre_todo(tmp_path):
    """Para las pruebas, una base compartida en el dojo, o mover los datos."""
    raiz = _con_modelo(tmp_path / "app")
    (raiz / NOMBRE_BASE).write_bytes(b"historial")
    otro_modelo = tmp_path / "otro.task"
    otro_modelo.write_bytes(b"x")

    entorno = {VAR_MODELO: str(otro_modelo), VAR_BASE: "/dojo/compartida.db"}

    assert modelo(entorno=entorno, raiz=raiz) == str(otro_modelo)
    assert base_de_datos(entorno=entorno, raiz=raiz) == "/dojo/compartida.db"


# ---------------------------------------------------------------------------
# La carpeta de datos
# ---------------------------------------------------------------------------

def test_la_carpeta_de_datos_se_crea_si_no_existe(tmp_path):
    carpeta = carpeta_de_datos(entorno={}, inicio=tmp_path)

    assert carpeta.is_dir()
    assert carpeta.name == rutas.CARPETA_DATOS


def test_la_carpeta_sigue_la_convencion_del_sistema(tmp_path):
    """
    El nombre de la carpeta es el mismo en los tres sistemas —para que una
    copia de seguridad hecha en uno se reconozca en otro— pero su ubicación no.
    """
    carpeta = str(carpeta_de_datos(entorno={}, inicio=tmp_path))

    if os.name == "nt":
        assert "AppData" in carpeta
    else:
        assert "Library/Application Support" in carpeta or ".local/share" in carpeta


def test_la_raiz_no_es_el_directorio_de_trabajo():
    """
    El punto de todo el módulo. `raiz_aplicacion()` se deduce de dónde vive
    este archivo, no de desde dónde se invocó el programa.
    """
    assert rutas.raiz_aplicacion() == rutas.Path(rutas.__file__).resolve().parent
