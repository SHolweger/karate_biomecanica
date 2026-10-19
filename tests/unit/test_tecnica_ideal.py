"""
Pruebas de la figura de la técnica ideal (TC-AUTO-072).

La figura es una guía para el alumno, y una guía equivocada es peor que no
tener guía: enseña a corregir hacia algo que el sistema después reprueba. Por
eso estas pruebas no miran el dibujo, sino lo que el propio sistema concluye
de él:

- medido con `BiomechanicsMath.calculate_angle` —la función con que se mide al
  alumno—, cada ángulo juzgado es el centro del rango vigente;
- el clasificador reconoce la postura que la figura dice ser, con la guardia
  que tiene dibujada, y la regla la aprueba;
- recalibrar el criterio cambia la figura, porque sale del mismo
  `KarateRules` que juzga;
- ningún segmento se estira para que el ángulo cuadre.

El prototipo `.dc.html` mostraba el mismo muñeco de puñetazo para todas las
técnicas, también para la Mae Geri. Estas pruebas son lo que impide que la
versión real vuelva a ser decoración.
"""
import math

import pytest

from biomechanics.geometry import BiomechanicsMath
from comparar_2d_3d import _clasificar
from expert_system.guardia import IZQ_ADELANTE
from expert_system.kick_state_machine import MARGEN_PIE_AIRE, UMBRAL_CARGA
from expert_system.knowledge_base import KarateRules
from expert_system.tsuki import RECORRIDO_MINIMO
from gui import tecnica_ideal as ti
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from vision.encuadre import PLANO as AVISO_DE_PLANO

pytestmark = pytest.mark.unitaria

ESCALA = 1000  # a píxeles enteros, como llegan los landmarks al analizador


def _medido(fase, articulacion):
    """El ángulo que mediría el sistema sobre la figura dibujada."""
    p = fase.puntos

    def px(nombre):
        return (round(p[nombre][0] * ESCALA), round(p[nombre][1] * ESCALA))

    a, c = articulacion.extremos
    return BiomechanicsMath.calculate_angle(px(a), px(articulacion.vertice), px(c))


def _centro(rango):
    minimo, maximo = rango
    return minimo if maximo is None else (minimo + maximo) / 2


def _juzgada(fase, etiqueta):
    return next(a for a in fase.juzgadas if a.etiqueta == etiqueta)


@ficha(
    id_caso="TC-AUTO-072",
    nombre="La figura de la técnica ideal la mide, la reconoce y la aprueba el propio sistema",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="la figura se muestra al alumno como guía. Si sus ángulos "
                         "no fueran los del criterio vigente, el alumno corregiría "
                         "hacia una postura que el sistema reprueba, y lo haría "
                         "confiando en la pantalla. El prototipo mostraba el mismo "
                         "muñeco para todas las técnicas, incluida la Mae Geri",
    componente="gui/tecnica_ideal.py",
    requisitos="RF-05",
    precondiciones="Ninguna: el módulo es geometría pura y no importa CustomTkinter",
    datos_entrada="Las seis técnicas que el sistema evalúa en vivo, con los rangos de "
                  "literatura y con un rango recalibrado",
    pasos=[
        Paso("Medir cada articulación juzgada con calculate_angle sobre la figura",
             "assert abs(medido - centro_del_rango) < 1.0"),
        Paso("Clasificar las rodillas dibujadas con la guardia de la figura",
             "assert la postura reconocida es la que la figura dice ser"),
        Paso("Evaluar los ángulos medidos con la regla de la técnica",
             "assert la regla devuelve correcto = True"),
        Paso("Recalibrar el rango y volver a dibujar",
             "assert la figura cambia y sigue al centro del rango nuevo"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
@pytest.mark.parametrize("tecnica", ti.TECNICAS)
def test_cada_angulo_juzgado_es_el_centro_del_rango_vigente(tecnica):
    figura = ti.figura(tecnica)
    fase_final = figura.fases[-1] if tecnica == "tsuki" else figura.fases[0]
    if tecnica == "mae_geri":
        fase_final = next(f for f in figura.fases if f.nombre == "Kime")
    for articulacion in fase_final.juzgadas:
        assert abs(_medido(fase_final, articulacion) - _centro(articulacion.rango)) < 1.0, (
            f"{tecnica}: {articulacion.etiqueta} se dibujó a "
            f"{_medido(fase_final, articulacion):.1f}° y el centro de su rango es "
            f"{_centro(articulacion.rango):.1f}°")


@pytest.mark.parametrize("tecnica", ti.TECNICAS)
def test_lo_que_se_dibuja_es_lo_que_se_declara(tecnica):
    """Cada fase declara el ángulo que dibujó, y es el que se mide."""
    for fase in ti.figura(tecnica).fases:
        for articulacion in fase.juzgadas:
            assert abs(_medido(fase, articulacion) - articulacion.angulo) < 1.0


@pytest.mark.parametrize("tecnica, evaluar", [
    ("zenkutsu_dachi", "evaluate_zenkutsu_dachi"),
    ("kokutsu_dachi", "evaluate_kokutsu_dachi"),
])
def test_las_posturas_de_paso_se_reconocen_y_se_aprueban(tecnica, evaluar):
    fase = ti.figura(tecnica).fases[0]
    delantera = _medido(fase, _juzgada(fase, "Rodilla delantera"))
    trasera = _medido(fase, _juzgada(fase, "Rodilla trasera"))

    # La figura está de perfil mirando a +x: la pierna delantera va adelante.
    assert fase.puntos["tobillo_del"][0] > fase.puntos["tobillo_tras"][0]
    assert _clasificar(delantera, trasera, IZQ_ADELANTE) == tecnica
    correcto, mensaje, _ = getattr(KarateRules(), evaluar)(delantera, trasera)
    assert correcto, f"{tecnica}: la regla reprueba la figura ideal ({mensaje})"


def test_las_posturas_de_frente_se_reconocen_y_se_aprueban():
    reglas = KarateRules()
    for tecnica in ("heiko_dachi", "kiba_dachi"):
        fase = ti.figura(tecnica).fases[0]
        izq, der = (_medido(fase, a) for a in fase.juzgadas)
        assert _clasificar(izq, der, None) == tecnica
    assert reglas.evaluate_heiko_dachi(min(
        _medido(f, a) for f in ti.figura("heiko_dachi").fases for a in f.juzgadas))[0]
    fase = ti.figura("kiba_dachi").fases[0]
    assert reglas.evaluate_kiba_dachi(*(_medido(fase, a) for a in fase.juzgadas))[0]


def test_el_tsuki_dibujado_es_un_golpe_que_la_maquina_reconoceria():
    """Del Hikite al Kime el codo recorre más que el mínimo que exige la detección."""
    hikite, kime = ti.figura("tsuki").fases
    salida = _medido(hikite, hikite.juzgadas[0])
    llegada = _medido(kime, kime.juzgadas[0])
    assert llegada - salida >= RECORRIDO_MINIMO
    assert KarateRules().evaluate_tsuki(llegada)[0]


def test_la_mae_geri_dibujada_cierra_el_ciclo_de_la_maquina():
    """Carga por debajo del umbral, Kime aprobado y pie en el aire al recoger."""
    carga, kime, hikiashi = ti.figura("mae_geri").fases
    assert _medido(carga, carga.juzgadas[0]) < UMBRAL_CARGA
    assert _medido(hikiashi, hikiashi.juzgadas[0]) < UMBRAL_CARGA
    velocidad = KarateRules().rango("mae_geri", "velocidad_angular")[0]
    assert KarateRules().evaluate_mae_geri(_medido(kime, kime.juzgadas[0]), velocidad)[0]
    # y crece hacia abajo: el tobillo recogido queda más arriba que el de apoyo.
    pie_en_el_aire = hikiashi.puntos["tobillo_tras"][1] - hikiashi.puntos["tobillo_del"][1]
    assert pie_en_el_aire > MARGEN_PIE_AIRE


def test_recalibrar_cambia_la_figura():
    """
    La figura sale del criterio vigente, no de números escritos aquí. Si el
    cuerpo técnico mueve el rango de la rodilla delantera del Zenkutsu, la
    guía tiene que moverse con él.
    """
    recalibrado = {("zenkutsu_dachi", "rodilla_frontal"): {
        "valor_min": 100.0, "valor_max": 120.0, "id_umbral": 99}}
    reglas = KarateRules(umbrales_bd=recalibrado)
    antes = ti.figura("zenkutsu_dachi").fases[0]
    despues = ti.figura("zenkutsu_dachi", reglas).fases[0]

    medido = _medido(despues, _juzgada(despues, "Rodilla delantera"))
    assert abs(medido - 110.0) < 1.0
    assert antes.puntos["rodilla_del"] != despues.puntos["rodilla_del"]
    assert _juzgada(despues, "Rodilla delantera").rango == (100.0, 120.0)


@pytest.mark.parametrize("tecnica", ti.TECNICAS)
def test_ningun_segmento_se_estira_para_que_el_angulo_cuadre(tecnica):
    largos = {("pelvis", "rodilla_del"): ti.MUSLO, ("rodilla_del", "tobillo_del"): ti.PIERNA,
              ("pelvis", "rodilla_tras"): ti.MUSLO, ("rodilla_tras", "tobillo_tras"): ti.PIERNA,
              ("cadera_izq", "rodilla_izq"): ti.MUSLO, ("rodilla_izq", "tobillo_izq"): ti.PIERNA,
              ("cadera_der", "rodilla_der"): ti.MUSLO, ("rodilla_der", "tobillo_der"): ti.PIERNA,
              ("codo_a", "muneca_a"): ti.ANTEBRAZO, ("codo_b", "muneca_b"): ti.ANTEBRAZO}
    for fase in ti.figura(tecnica).fases:
        p = fase.puntos
        for (a, b), largo in largos.items():
            if a in p and b in p:
                assert math.dist(p[a], p[b]) == pytest.approx(largo, abs=1e-6), (
                    f"{tecnica} / {fase.nombre}: {a}-{b} mide {math.dist(p[a], p[b]):.4f}")


@pytest.mark.parametrize("tecnica", ti.TECNICAS)
def test_los_pies_quedan_en_el_suelo_y_la_figura_dentro_del_cuadro(tecnica):
    for fase in ti.figura(tecnica).fases:
        ys = [y for _, y in fase.puntos.values()]
        assert min(ys) > 0.0 and max(ys) <= 1.0 + 1e-9
        apoyos = [fase.puntos[n][1] for n in ("tobillo_tras", "tobillo_izq", "tobillo_der")
                  if n in fase.puntos]
        assert apoyos and all(y == pytest.approx(1.0 - ti.ALTURA_TOBILLO) for y in apoyos)


@pytest.mark.parametrize("tecnica", ti.TECNICAS)
def test_el_plano_de_la_figura_es_el_del_aviso_de_encuadre(tecnica):
    """
    La figura se dibuja en el plano en que se filma la técnica. El aviso de la
    pantalla en vivo ya lo dice con palabras, y los dos no pueden discrepar.
    """
    nombre = ti.NOMBRES[tecnica].replace(" Dachi", "")
    clave = "perfil" if ti.PLANO[tecnica] == ti.PERFIL else "frontal"
    primera_frase = AVISO_DE_PLANO[clave].split(".")[0]
    assert nombre in primera_frase, (
        f"{tecnica} se dibuja {ti.PLANO[tecnica]} pero el aviso dice: {primera_frase}")


def test_hay_figura_para_cada_tecnica_que_se_evalua_en_vivo():
    assert set(ti.TECNICAS) == {"heiko_dachi", "kiba_dachi", "zenkutsu_dachi",
                                "kokutsu_dachi", "tsuki", "mae_geri"}
    with pytest.raises(KeyError):
        ti.figura("age_uke")


@pytest.mark.parametrize("rango, texto", [((90.0, 115.0), "90–115°"), ((400.0, None), "≥ 400°")])
def test_el_rango_se_escribe_como_lo_lee_el_sensei(rango, texto):
    assert ti.texto_rango(rango) == texto
