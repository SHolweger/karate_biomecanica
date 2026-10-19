"""
El reporte de sesión: lo medido contra el criterio que lo juzgó (TC-AUTO-074).

El prototipo mostraba «Ángulo de rodilla delantera · ideal 115–125° · 118° ✓»
con cifras de adorno. Estas pruebas fijan la versión con datos: que la mediana
sale de los argumentos con que se juzgó cada medición —no del número que se
dibuja en pantalla—, que el rango es el que regía al empezar la sesión y que
el ✓ no se confunde con «todas las repeticiones cupieron».
"""
import pytest

from expert_system.analyzer import TechniqueAnalyzer
from expert_system.knowledge_base import UMBRALES_LITERATURA
from gui import medido_contra_rango as mcr
from helpers.fakes import pose_sintetica
from persistence.medicion_logger import MedicionLogger
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


def _fila(tecnica, a1, a2=None, correcto=True):
    return {"tecnica_clave": tecnica, "angulo_regla_1": a1, "angulo_regla_2": a2,
            "correcto": correcto}


def _literatura(tecnica, articulacion):
    minimo, maximo, _ = UMBRALES_LITERATURA[(tecnica, articulacion)]
    return (minimo, maximo)


@ficha(
    id_caso="TC-AUTO-074",
    nombre="El reporte resume cada articulación juzgada con su mediana, el rango que "
           "regía y cuántas evaluaciones cupieron",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="el sensei lee este resumen para decidir qué corregir. Con "
                         "la rodilla delantera y la trasera intercambiadas, o contra "
                         "el rango de hoy en vez del que juzgó la sesión, diría lo "
                         "contrario de lo que se midió; y un ✓ sobre la mediana que "
                         "escondiera las repeticiones fuera daría por dominada una "
                         "técnica que no lo está",
    componente="gui/medido_contra_rango.py, persistence/database.py (umbral_en), "
               "gui/reporte_screen.py",
    requisitos=("RF-07", "RF-08"),
    precondiciones="Ninguna: filas escritas a mano y una base SQLite temporal",
    datos_entrada="Zenkutsu con tres evaluaciones, una fuera de rango; un Kokutsu con la "
                  "derecha adelante pasado por el analizador real; una recalibración",
    pasos=[
        Paso("Resumir tres evaluaciones de Zenkutsu",
             "assert mediana, rango y «2 de 3 dentro» son los calculados a mano"),
        Paso("Pasar un Kokutsu con la derecha adelante por analizador, registro y base",
             "assert la delantera y la trasera no salen intercambiadas"),
        Paso("Recalibrar después de la sesión y pedir el rango de entonces",
             "assert umbral_en devuelve la versión que regía al empezarla"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_resume_cada_articulacion_con_mediana_rango_y_cuantas_cupieron():
    filas = [_fila("zenkutsu_dachi", 105.0, 172.0),
             _fila("zenkutsu_dachi", 120.0, 175.0, correcto=False),
             _fila("zenkutsu_dachi", 108.0, 168.0)]
    delantera, trasera = mcr.puntos_de_control(filas, _literatura)

    assert delantera["etiqueta"] == "Rodilla delantera"
    assert delantera["mediana"] == 108.0 and delantera["rango"] == (90.0, 115.0)
    assert (delantera["dentro"], delantera["total"], delantera["cumple"]) == (2, 3, True)
    assert trasera["mediana"] == 172.0 and (trasera["dentro"], trasera["total"]) == (3, 3)
    assert mcr.texto_punto(delantera) == "mediana 108° · criterio 90–115° · 2 de 3 dentro"


def test_la_mediana_dentro_no_esconde_las_repeticiones_fuera():
    """
    Con dos de cinco fuera, la mediana puede caer dentro. El ✓ lo dice de la
    mediana; las repeticiones fuera las dice la cifra de al lado.
    """
    filas = [_fila("tsuki", a) for a in (150.0, 155.0, 165.0, 168.0, 170.0)]
    (codo,) = mcr.puntos_de_control(filas, _literatura)
    assert codo["cumple"] is True
    assert (codo["dentro"], codo["total"]) == (3, 5)


def test_kiba_resume_las_dos_rodillas_juntas_y_sin_nombrar_el_lado():
    """Modo espejo y toma frontal: la «izquierda» de la pantalla es la pierna derecha."""
    (rodillas,) = mcr.puntos_de_control([_fila("kiba_dachi", 140.0, 156.0)], _literatura)
    assert rodillas["etiqueta"] == "Rodillas"
    assert rodillas["total"] == 2 and rodillas["dentro"] == 1
    assert "izquierda" not in rodillas["etiqueta"].lower()


def test_solo_cuentan_los_veredictos_cerrados_con_angulos():
    filas = [_fila("tsuki", 170.0),
             _fila("tsuki", 179.0, correcto=None),       # transitorio: no se juzgó
             _fila("tsuki", None),                       # anterior al 19-sep: sin ángulos
             _fila(None, 120.0),                         # transición
             {"tecnica_clave": "mae_geri", "angulo_regla_1": 170.0, "correcto": True}]
    (codo,) = mcr.puntos_de_control(filas, _literatura)
    assert codo["total"] == 1 and codo["mediana"] == 170.0


def test_la_mae_geri_no_se_resume_por_el_angulo():
    """Su veredicto depende también de la velocidad pico, que la fila no guarda."""
    assert "mae_geri" not in mcr.ARGUMENTOS
    assert mcr.puntos_de_control([_fila("mae_geri", 170.0)], _literatura) == []


def test_sin_rango_conocido_la_articulacion_no_se_resume():
    assert mcr.puntos_de_control([_fila("tsuki", 170.0)], lambda t, a: None) == []


def test_un_criterio_sin_maximo_acepta_todo_lo_que_supera_el_minimo():
    (codo,) = mcr.puntos_de_control([_fila("tsuki", 179.0)], lambda t, a: (160.0, None))
    assert codo["cumple"] and codo["dentro"] == 1


def test_un_kokutsu_con_la_derecha_adelante_no_intercambia_las_rodillas(sesion_de_prueba):
    """
    El recorrido real: analizador, registro, base y resumen. Con la derecha
    adelante, la rodilla que se dibuja junto a la izquierda de la pantalla es
    la trasera; si el resumen leyera ese número, saldrían intercambiadas.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)
    pose = pose_sintetica(angulo_rodilla_izq=105, angulo_rodilla_der=165,
                          z_tobillo_izq=0.3, z_tobillo_der=-0.3)
    logger = MedicionLogger(db, id_sesion)
    for t_ms in range(0, 600, 33):  # sostenida 0,6 s, como en vivo
        resultados = analizador.analyze_stance(pose, 1000, 1000)
        logger.registrar(resultados, t_ms)
    assert "KOKUTSU (DER ADELANTE)" in next(
        r for r in resultados if r["categoria"] == "postura")["mensaje"]

    instante = db.detalle_sesion(id_sesion)["hora_inicio"]

    def rango_de(tecnica, articulacion):
        umbral = db.umbral_en(tecnica, articulacion, instante)
        return (umbral["valor_min"], umbral["valor_max"])

    puntos = {p["etiqueta"]: p for p in mcr.puntos_de_control(
        db.mediciones_reevaluables(id_sesion=id_sesion), rango_de)}
    assert puntos["Rodilla delantera"]["mediana"] == pytest.approx(165, abs=1)
    assert puntos["Rodilla trasera"]["mediana"] == pytest.approx(105, abs=1)
    assert puntos["Rodilla delantera"]["rango"] == (145.0, 175.0)


def test_el_rango_es_el_que_regia_al_empezar_la_sesion(sesion_de_prueba):
    """
    Un reporte viejo leído después de recalibrar tiene que decir contra qué se
    midió, no contra qué se mediría hoy.
    """
    db, id_sesion, _, id_entrenador = sesion_de_prueba
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    antes = db.cargar_umbrales_vigentes()[("zenkutsu_dachi", "rodilla_frontal")]
    instante_de_la_sesion = antes["fecha_modificacion"]

    db.actualizar_umbral("zenkutsu_dachi", "rodilla_frontal", 100.0, 120.0,
                         id_entrenador=id_entrenador)

    entonces = db.umbral_en("zenkutsu_dachi", "rodilla_frontal", instante_de_la_sesion)
    hoy = db.umbral_en("zenkutsu_dachi", "rodilla_frontal", "9999-12-31T00:00:00")
    assert (entonces["valor_min"], entonces["valor_max"]) == (90.0, 115.0)
    assert (hoy["valor_min"], hoy["valor_max"]) == (100.0, 120.0)


def test_antes_de_toda_version_se_toma_la_mas_antigua(sesion_de_prueba):
    db, _, _, _ = sesion_de_prueba
    db.sembrar_umbrales(UMBRALES_LITERATURA)
    umbral = db.umbral_en("tsuki", "codo", "2000-01-01T00:00:00")
    assert (umbral["valor_min"], umbral["valor_max"]) == (160.0, 175.0)
    assert db.umbral_en("tecnica_que_no_existe", "codo", "2026-10-19") is None
