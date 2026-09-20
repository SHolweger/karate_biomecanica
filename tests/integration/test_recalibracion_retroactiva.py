"""
La cadena completa de la recalibración retroactiva (RF-08).

Este módulo verifica de punta a punta el escenario que motivó todo el trabajo,
y que es el que va a ocurrir de verdad:

    1. Se mide en el dojo. El sistema reconoce un Kokutsu Dachi y lo juzga
       correcto con los rangos vigentes, que son provisionales.
    2. Después, el cuerpo técnico confirma los rangos y corrige uno.
    3. La pregunta es cuánto del historial cambia de veredicto — y hay que
       responderla SIN volver a medir, porque juntar al grupo otra vez depende
       de agendas que el sistema no controla.

Las piezas se prueban por separado en `test_analyzer.py` (que el diagnóstico
lleve los argumentos de la regla), `test_medicion_logger.py` (que la fila los
guarde) y `test_reevaluacion.py` (que se pueda volver a juzgar). Lo que se
verifica aquí es que las tres encajen: una postura que entra como landmarks
sintéticos sale, al otro extremo, como una fila que se puede volver a juzgar.
"""
import pytest

from expert_system.analyzer import TechniqueAnalyzer
from expert_system.knowledge_base import KarateRules
from expert_system.reevaluacion import comparar
from helpers.fakes import pose_sintetica
from persistence.medicion_logger import MedicionLogger
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion

ANCHO, ALTO = 1000, 1000


def _medir_kokutsu(db, id_sesion, frontal, trasera):
    """Una ejecución sintética de Kokutsu Dachi, medida y registrada como en vivo."""
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)
    logger = MedicionLogger(db, id_sesion)

    pose = pose_sintetica(angulo_rodilla_izq=frontal, angulo_rodilla_der=trasera,
                          z_tobillo_izq=-0.3, z_tobillo_der=0.3)
    logger.registrar(analizador.analyze_stance(pose, ANCHO, ALTO), timestamp_ms=33)


@ficha(
    id_caso="TC-AUTO-040",
    nombre="Corregir un umbral revela qué mediciones del historial cambiarían de veredicto, "
           "sin repetir la toma de datos",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "los rangos de Kokutsu Dachi vigentes están pendientes de confirmación del cuerpo "
        "técnico; sin recalibración retroactiva, esa confirmación invalidaría toda la toma "
        "de datos de campo hecha antes"
    ),
    componente="expert_system/analyzer.py + persistence/medicion_logger.py + "
               "expert_system/reevaluacion.py",
    requisitos="RF-08",
    precondiciones="Base temporal con entrenador, atleta y sesión abierta "
                   "(fixture `sesion_de_prueba`)",
    datos_entrada="Kokutsu sintético: rodilla frontal 160°, trasera 105°, guardia izquierda",
    pasos=[
        Paso("Medir la postura con TechniqueAnalyzer y registrarla con MedicionLogger",
             "Una fila con tecnica_clave='kokutsu_dachi' y sus dos ángulos"),
        Paso("Recuperarla con Database.mediciones_reevaluables()",
             "La fila trae los argumentos de la regla"),
        Paso("Comparar contra un umbral de rodilla trasera corregido a 90-100°",
             "assert el informe reporta exactamente una medición que cambia de veredicto"),
    ],
    resultado_esperado="El informe identifica el cambio de Correcto a Incorrecto sin volver a medir",
)
def test_una_correccion_de_umbral_se_aplica_a_lo_ya_medido(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba

    # 1. Se midió en el dojo, con los umbrales provisionales vigentes.
    _medir_kokutsu(db, id_sesion, frontal=160, trasera=105)

    guardadas = db.mediciones_reevaluables(tecnica_clave="kokutsu_dachi")
    assert len(guardadas) == 1, "la postura debe quedar registrada como re-evaluable"
    assert guardadas[0]["correcto"] == 1, "con el umbral vigente (trasera 90-120°) es correcta"

    # 2. El cuerpo técnico confirma los rangos y ajusta la rodilla trasera.
    reglas_confirmadas = KarateRules(umbrales_bd={
        ("kokutsu_dachi", "rodilla_trasera"): {
            "valor_min": 90.0, "valor_max": 100.0, "id_umbral": 99},
    })

    # 3. Qué cambia — calculado sobre lo ya medido.
    informe = comparar(guardadas, reglas_confirmadas)

    assert len(informe["cambian"]) == 1
    assert informe["cambian"][0]["correcto_nuevo"] is False
    assert informe["no_juzgadas"] == [], "la medición traía todo lo necesario"


def test_una_correccion_que_no_afecta_nada_lo_dice_con_claridad(sesion_de_prueba):
    """
    Que ninguna medición cambie también es un resultado, y es el que le permite
    al sensei adoptar un ajuste con confianza.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    _medir_kokutsu(db, id_sesion, frontal=160, trasera=105)

    reglas_holgadas = KarateRules(umbrales_bd={
        ("kokutsu_dachi", "rodilla_trasera"): {
            "valor_min": 85.0, "valor_max": 130.0, "id_umbral": 99},
    })

    informe = comparar(db.mediciones_reevaluables(), reglas_holgadas)

    assert informe["cambian"] == []
    assert len(informe["sostienen"]) == 1


def test_la_recalibracion_no_reescribe_el_veredicto_registrado(sesion_de_prueba):
    """
    El informe se consulta; no se aplica solo. Reescribir `correcto` en el lugar
    borraría la evidencia de qué criterio regía al medir, que es exactamente lo
    que el versionado de umbrales existe para conservar.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    _medir_kokutsu(db, id_sesion, frontal=160, trasera=105)

    reglas_estrictas = KarateRules(umbrales_bd={
        ("kokutsu_dachi", "rodilla_trasera"): {
            "valor_min": 90.0, "valor_max": 100.0, "id_umbral": 99},
    })
    comparar(db.mediciones_reevaluables(), reglas_estrictas)

    fila = db.conn.execute(
        "SELECT correcto, id_umbral FROM tecnica_evaluada WHERE id_sesion = ?", (id_sesion,)
    ).fetchone()
    assert fila["correcto"] == 1, "el veredicto original debe seguir intacto"


def test_la_cobertura_avisa_cuando_el_informe_abarca_poco(sesion_de_prueba):
    """
    Una medición registrada por la vía de consola no lleva los campos nuevos.
    Si el informe se leyera sin la cobertura, "no cambia nada" ocultaría que la
    mitad del historial quedó fuera del recuento.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    _medir_kokutsu(db, id_sesion, frontal=160, trasera=105)
    db.guardar_medicion(id_sesion, "Postura de piernas", 158.0,
                        "KOKUTSU (IZQ ADELANTE): POSTURA: ESTABLE", 66, correcto=True)

    cobertura = db.cobertura_reevaluable()

    assert cobertura["juzgadas"] == 2
    assert cobertura["reevaluables"] == 1
