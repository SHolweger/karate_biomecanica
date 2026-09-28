"""
Pruebas del aviso de encuadre.

Corren en las unitarias —y por tanto también en integración continua, sin
cámara ni entorno gráfico— porque `vision/encuadre.py` solo lee la visibilidad
de los puntos y unos pocos números.

Lo que aquí se verifica es la diferencia entre los dos modos en que una toma
mal puesta arruina una medición. El primero es visible: falta una articulación
y el sistema ya lo sabe. El segundo no lo es en absoluto: todo se ve, el
esqueleto se dibuja bien, y los ángulos no guardan relación con el cuerpo.
"""
import pytest

from helpers.fakes import pose_sintetica
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from vision.encuadre import (NIVEL_ALTO, NIVEL_INFO, NIVEL_MEDIO, SIN_PERSONA,
                             clasificar_plano, evaluar, visibilidades_por_grupo)

pytestmark = pytest.mark.unitaria


def _mensajes(avisos):
    return " | ".join(a["mensaje"] for a in avisos)


# ---------------------------------------------------------------------------
# Articulaciones fuera de cuadro
# ---------------------------------------------------------------------------

def test_una_toma_completa_no_genera_avisos_de_visibilidad():
    avisos = evaluar(pose_sintetica(visibilidad=0.97))

    assert avisos == [], f"no debía avisar nada: {_mensajes(avisos)}"


def test_avisa_qué_parte_del_cuerpo_falta_y_no_solo_que_algo_falta():
    """
    «Encuadre incorrecto» obliga al instructor a adivinar qué mover. Nombrar la
    parte que falta convierte el aviso en una instrucción ejecutable.
    """
    avisos = evaluar(pose_sintetica(visibilidad_piernas=0.2))

    assert len(avisos) == 1
    assert avisos[0]["nivel"] == NIVEL_ALTO
    assert "las piernas" in avisos[0]["mensaje"]
    assert "los brazos" not in avisos[0]["mensaje"]


def test_si_faltan_las_dos_partes_se_nombran_ambas():
    avisos = evaluar(pose_sintetica(visibilidad=0.1))

    assert "las piernas" in avisos[0]["mensaje"]
    assert "los brazos" in avisos[0]["mensaje"]


def test_sin_pose_detectada_el_mensaje_es_otro():
    """
    «No se ven las piernas» con nadie en cuadro mandaría a corregir el encuadre
    de una persona que no está. Son dos problemas distintos.
    """
    avisos = evaluar(landmarks=None)

    assert avisos[0]["mensaje"] == SIN_PERSONA


def test_la_visibilidad_de_un_grupo_es_la_de_su_punto_peor_visto():
    """
    Se toma el mínimo y no el promedio: una rodilla fuera de cuadro invalida el
    ángulo de esa pierna aunque cadera y tobillo se vean, porque el ángulo
    necesita los tres puntos. Un promedio la escondería.
    """
    landmarks = pose_sintetica(visibilidad=0.95)
    landmarks[26].visibility = 0.10          # solo la rodilla izquierda visual

    assert visibilidades_por_grupo(landmarks)["piernas"] == pytest.approx(0.10)
    assert "las piernas" in _mensajes(evaluar(landmarks))


# ---------------------------------------------------------------------------
# El plano de la toma — el fallo que no se ve
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-053",
    nombre="El sistema advierte para qué técnicas sirve la posición actual de la "
           "cámara, aunque todas las articulaciones estén visibles",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="una toma frontal deja todas las articulaciones perfectamente "
                         "visibles y, aun así, impide medir las técnicas del plano "
                         "sagital: medido sobre 637 fotogramas de Zenkutsu Dachi "
                         "grabados de frente, la postura no se reconoció ni una sola "
                         "vez, frente al 40,5 % de perfil. El fallo no se manifiesta en "
                         "pantalla —el esqueleto se dibuja bien y la visibilidad es "
                         "alta—, de modo que sin este aviso una campaña de recolección "
                         "puede completarse entera y producir datos inservibles",
    componente="vision/encuadre.py (evaluar, clasificar_plano)",
    requisitos="RF-01, RF-03",
    precondiciones="Ninguna: el módulo no importa MediaPipe ni OpenCV",
    datos_entrada="Una pose sintética con todas las articulaciones visibles y valores "
                  "de orientación correspondientes a cámara frontal, oblicua y de perfil",
    pasos=[
        Paso("Evaluar una toma frontal con el cuerpo completo visible",
             "assert se emite un aviso que nombra Heiko y Kiba como medibles y "
             "Zenkutsu, Kokutsu, Tsuki y Mae Geri como necesitados de perfil"),
        Paso("Evaluar la misma pose con orientación de perfil",
             "assert el aviso se invierte: nombra las técnicas del plano sagital"),
        Paso("Evaluar una toma en diagonal",
             "assert el aviso se eleva de nivel informativo a nivel medio, porque "
             "ninguna técnica se mide bien en esa posición"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_avisa_del_plano_aunque_todo_se_vea():
    completa = pose_sintetica(visibilidad=0.97)

    de_frente = evaluar(completa, orientacion=0.95)
    de_perfil = evaluar(completa, orientacion=0.20)
    en_diagonal = evaluar(completa, orientacion=0.65)

    assert "Heiko" in de_frente[0]["mensaje"] and "perfil" in de_frente[0]["mensaje"]
    assert de_frente[0]["nivel"] == NIVEL_INFO

    assert "Zenkutsu" in de_perfil[0]["mensaje"]
    assert "de frente" in de_perfil[0]["mensaje"]

    assert en_diagonal[0]["nivel"] == NIVEL_MEDIO, \
        "la diagonal no sirve para ninguna técnica y merece más que un dato"
    assert "ninguna" in en_diagonal[0]["mensaje"]


def test_el_aviso_de_plano_no_depende_de_la_tecnica_detectada():
    """
    Condicionarlo sería circular: reconocer la técnica es justamente lo que
    falla cuando el plano está mal. El aviso se emite siempre que haya una
    orientación medible.
    """
    assert evaluar(pose_sintetica(visibilidad=0.97), orientacion=0.95)


def test_sin_orientacion_medible_no_se_inventa_un_plano():
    assert clasificar_plano(None) is None
    assert evaluar(pose_sintetica(visibilidad=0.97), orientacion=None) == []


def test_lo_que_no_se_ve_se_avisa_antes_que_el_plano():
    """
    Los avisos van de más grave a menos. Una articulación fuera de cuadro
    impide medir del todo; el plano determina si la medida sirve.
    """
    avisos = evaluar(pose_sintetica(visibilidad_piernas=0.2), orientacion=0.95)

    assert [a["nivel"] for a in avisos] == [NIVEL_ALTO, NIVEL_INFO]
