"""
La herramienta que dice, sin abrir la interfaz, qué correcciones habría leído
el alumno sobre una grabación (TC-AUTO-080).

Corre en CI porque la parte que decide —qué se anota, cuándo y en qué
palabras— es la lista de correcciones de la pantalla en vivo, que es lógica
pura. Lo que se fija aquí es que la herramienta use ESA lista y no una copia:
si dijera algo distinto de la pantalla, sus informes no servirían de evidencia.
"""
import pytest

import revisar_correcciones as rc
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

ALTO = "ZENKUTSU (DER ADELANTE): POSTURA: FLEXIONA MAS LA RODILLA DELANTERA"
BIEN = "POSTURA NATURAL: HEIKO DACHI: CORRECTO"


def _postura(mensaje, correcto):
    return [{"categoria": "postura", "mensaje": mensaje, "correcto": correcto}]


def _tramo(desde_ms, hasta_ms, diagnosticos, paso_ms=50):
    return [(t, diagnosticos) for t in range(desde_ms, hasta_ms, paso_ms)]


@ficha(
    id_caso="TC-AUTO-080",
    nombre="La revisión por consola dice las mismas correcciones que la pantalla en vivo, "
           "traducidas y en su segundo",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la Mae Geri y las tomas con errores a propósito solo se podían "
                         "revisar abriendo la interfaz video por video, con una base "
                         "aparte y una captura por reporte. Una herramienta de consola "
                         "que no usara la misma lista de correcciones —con la regla del "
                         "sostenido— diría otra cosa que la pantalla, y sus informes no "
                         "servirían como evidencia de lo que el alumno lee",
    componente="revisar_correcciones.py (correcciones_de, linea, resumen)",
    requisitos="RF-03, RF-05",
    precondiciones="Ninguna: diagnósticos escritos a mano, sin cámara ni MediaPipe",
    datos_entrada="Un Zenkutsu alto sostenido 1 s, un parpadeo de 0,2 s y un Tsuki juzgado",
    pasos=[
        Paso("Pasar un Zenkutsu alto sostenido un segundo",
             "assert aparece una vez, traducido como lo lee el alumno y en su segundo"),
        Paso("Intercalar un parpadeo de 0,2 s de otra postura",
             "assert no aparece: la regla del sostenido es la de la pantalla"),
        Paso("Resumir con un Tsuki correcto",
             "assert el resumen cuenta por técnica correctas e incorrectas"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_dice_lo_que_diria_la_pantalla():
    fotogramas = (_tramo(0, 1000, _postura(ALTO, False))
                  + _tramo(1000, 1200, _postura(BIEN, True))
                  + _tramo(1200, 2200, _postura(ALTO, False)))
    fotogramas.append((2200, [[{"categoria": "codo_izq", "correcto": True,
                                "mensaje": "IZQ - TSUKI: EXCELENTE"}]]))

    entradas = rc.correcciones_de(fotogramas)

    assert [e["mensaje"] for e in entradas] == [ALTO, "IZQ - TSUKI: EXCELENTE"]
    assert rc.linea(entradas[0]).startswith("00:00  ✗  Flexiona más la rodilla de adelante")
    assert rc.linea(entradas[1]).startswith("00:02  ✓  Kime correcto (izquierdo)")
    assert rc.resumen(entradas) == [("Postura", 0, 1), ("Tsuki", 1, 0)]


def test_un_veredicto_nulo_no_es_una_correccion():
    fotogramas = _tramo(0, 2000, _postura("MOVIENDOSE: EN TRANSICION...", None))
    assert rc.correcciones_de(fotogramas) == []


def test_sin_correcciones_lo_dice_en_vez_de_callar():
    salida = []
    rc.informar([], escribir=salida.append)
    assert "ninguna corrección" in salida[0]


def test_importarla_no_exige_camara_ni_mediapipe():
    """Lo que necesita hardware se importa dentro de `recorrer`, no arriba."""
    import ast
    import inspect

    arbol = ast.parse(inspect.getsource(rc))
    arriba = {nodo.module for nodo in arbol.body if isinstance(nodo, ast.ImportFrom)}
    assert not arriba & {"vision.camera", "vision.tracker", "expert_system.analyzer"}
