"""
Pruebas del nombre legible de las cámaras del sistema (RF-01).

Un entrenador con tres dispositivos conectados no puede elegir entre «Cámara 0»,
«Cámara 1» y «Cámara 2»: los tres nombres son igual de informativos, es decir,
nada. Lo que se verifica aquí es el análisis de la respuesta de cada sistema
operativo, que se puede ejercitar sin cámaras — y que ningún fallo de esa
consulta impida enumerar los dispositivos, porque el nombre es una ayuda y no un
requisito.
"""
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from vision.nombres_camara import (analizar_nombre_v4l2, analizar_salida_macos,
                                   nombres_del_sistema)

pytestmark = pytest.mark.unitaria

SALIDA_MACOS = """
{
  "SPCameraDataType" : [
    {
      "_name" : "FaceTime HD Camera",
      "spcamera_model-id" : "UVC Camera VendorID_1452"
    },
    {
      "_name" : "Logitech C920",
      "spcamera_model-id" : "UVC Camera VendorID_1133"
    }
  ]
}
"""


def test_los_nombres_de_macos_salen_en_el_orden_en_que_el_sistema_los_reporta():
    """
    El orden importa: es el mismo con el que AVFoundation numera los
    dispositivos, así que la posición en la lista es el índice de OpenCV.
    """
    assert analizar_salida_macos(SALIDA_MACOS) == ["FaceTime HD Camera", "Logitech C920"]


@pytest.mark.parametrize("texto", ["", "   ", "no es json", None, "{}", '{"otra": []}'])
def test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones(texto):
    """
    `system_profiler` puede cambiar de formato entre versiones de macOS. El
    sistema debe quedarse sin nombres, no dejar de enumerar cámaras.
    """
    assert analizar_salida_macos(texto) == []


@ficha(
    id_caso="TC-AUTO-035",
    nombre="Una cámara sin nombre se omite de la lista en vez de desplazar a las siguientes, "
           "de modo que ningún dispositivo quede etiquetado con el nombre de otro",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la posición en la lista ES el índice del dispositivo, así que un hueco "
                         "correría a todas las cámaras posteriores y el entrenador elegiría la "
                         "webcam integrada creyendo que elige la cámara del tatami; una etiqueta "
                         "equivocada es peor que no tener etiqueta, porque induce a confiar en "
                         "ella",
    componente="vision/nombres_camara.py (analizar_salida_macos)",
    requisitos="RF-01",
    precondiciones="Ninguna; la función es pura y no consulta el sistema operativo",
    datos_entrada="Respuesta de `system_profiler` con dos entradas, la primera sin campo "
                  "`_name` ni `spcamera_model-id`",
    pasos=[
        Paso("Analizar la salida con la primera entrada incompleta",
             "assert el resultado contiene solo el nombre de la segunda cámara"),
        Paso("Comprobar que no se insertó un marcador de posición",
             "assert len(nombres) == 1, no 2"),
    ],
    resultado_esperado="PASSED. La cámara sin nombre se muestra por su índice y las demás "
                       "conservan el suyo.",
    evidencia="Reporte de consola de pytest.",
)
def test_una_camara_sin_nombre_se_omite_en_vez_de_correr_las_demas():
    """
    Si una entrada viniera sin `_name`, insertar un hueco desplazaría a todas
    las siguientes y cada cámara quedaría etiquetada con el nombre de otra —
    peor que no tener nombres.
    """
    salida = '{"SPCameraDataType": [{"sin_nombre": 1}, {"_name": "Logitech C920"}]}'

    assert analizar_salida_macos(salida) == ["Logitech C920"]


def test_se_usa_el_modelo_cuando_falta_el_nombre_amistoso():
    salida = '{"SPCameraDataType": [{"spcamera_model-id": "UVC Camera VendorID_1133"}]}'

    assert analizar_salida_macos(salida) == ["UVC Camera VendorID_1133"]


@pytest.mark.parametrize("texto, esperado", [
    ("Integrated Camera: Integrated C\n", "Integrated Camera: Integrated C"),
    ("  HD Pro Webcam C920  ", "HD Pro Webcam C920"),
    ("\n", None),
    ("", None),
    (None, None),
])
def test_el_nombre_de_linux_se_limpia(texto, esperado):
    assert analizar_nombre_v4l2(texto) == esperado


def test_un_sistema_operativo_sin_soporte_devuelve_un_diccionario_vacio(monkeypatch):
    monkeypatch.setattr("vision.nombres_camara.platform.system", lambda: "Windows")

    assert nombres_del_sistema([0, 1]) == {}


def test_un_fallo_de_la_consulta_no_interrumpe_la_enumeracion(monkeypatch):
    """
    Si `system_profiler` no existe, tarda demasiado o devuelve basura, la
    pantalla de cámaras debe seguir funcionando con el índice y la miniatura.
    """
    def explota(*_args, **_kwargs):
        raise OSError("system_profiler no está disponible")

    monkeypatch.setattr("vision.nombres_camara.platform.system", lambda: "Darwin")
    monkeypatch.setattr("vision.nombres_camara.subprocess.run", explota)

    assert nombres_del_sistema([0, 1]) == {}


def test_solo_se_devuelven_los_indices_pedidos(monkeypatch):
    monkeypatch.setattr("vision.nombres_camara.platform.system", lambda: "Darwin")
    monkeypatch.setattr("vision.nombres_camara._nombres_macos",
                        lambda: ["FaceTime HD Camera", "Logitech C920", "OBS Virtual Camera"])

    assert nombres_del_sistema([0, 2]) == {0: "FaceTime HD Camera", 2: "OBS Virtual Camera"}


def test_un_indice_fuera_de_la_lista_no_inventa_nombre(monkeypatch):
    monkeypatch.setattr("vision.nombres_camara.platform.system", lambda: "Darwin")
    monkeypatch.setattr("vision.nombres_camara._nombres_macos", lambda: ["FaceTime HD Camera"])

    assert nombres_del_sistema([0, 5]) == {0: "FaceTime HD Camera"}
