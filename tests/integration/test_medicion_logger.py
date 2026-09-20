"""
Pruebas de integración de persistence/medicion_logger.py.

El logger es el filtro entre el bucle de video (~30 diagnósticos por segundo)
y la base de datos: solo debe escribir cuando el diagnóstico de una categoría
CAMBIA. Sin esa regla, una sesión de 10 minutos generaría ~18000 filas
idénticas y el historial del alumno sería inútil.
"""
import pytest

from persistence.medicion_logger import NOMBRES_TECNICA, MedicionLogger
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion


def _diagnostico(categoria, mensaje, angulo=170.0, correcto=True):
    """Arma un diagnóstico con el mismo formato que produce TechniqueAnalyzer."""
    return [{"categoria": categoria, "mensaje": mensaje, "angulo": angulo,
             "color": (0, 255, 0), "correcto": correcto}]


def _filas(db, id_sesion):
    return db.conn.execute(
        "SELECT * FROM tecnica_evaluada WHERE id_sesion = ? ORDER BY id_medicion", (id_sesion,)
    ).fetchall()


@ficha(
    id_caso="TC-AUTO-011",
    nombre="Treinta cuadros consecutivos con el mismo diagnóstico generan un único "
           "registro en la base de datos",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="sin la regla, una sesión de 10 minutos generaría ~18 000 filas "
                         "idénticas",
    componente="persistence/medicion_logger.py (MedicionLogger)",
    requisitos="RF-07",
    precondiciones="Base temporal con entrenador, atleta y sesión abierta "
                   "(fixture `sesion_de_prueba`)",
    datos_entrada="30 diagnósticos idénticos: categoria=\"codo_izq\", "
                  "mensaje=\"IZQ - TSUKI: EXCELENTE\", timestamp_ms = frame * 33",
    pasos=[
        Paso("Instanciar `MedicionLogger(db, id_sesion)`",
             "Memoria de últimos mensajes vacía"),
        Paso("Invocar `logger.registrar(...)` 30 veces con el mismo mensaje",
             "Cada llamada retorna sin excepción"),
        Paso("Consultar `SELECT * FROM tecnica_evaluada WHERE id_sesion = ?`",
             "Se obtiene el conjunto de filas persistidas"),
        Paso("Verificar la deduplicación", "assert len(filas) == 1"),
    ],
    resultado_esperado="PASSED. Caso complementario: "
                       "test_cada_cambio_real_de_diagnostico_se_registra",
)
def test_treinta_frames_identicos_generan_una_sola_fila(sesion_de_prueba):
    """Un segundo de video sosteniendo la misma postura = 1 registro, no 30."""
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    for frame in range(30):
        logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: EXCELENTE"), timestamp_ms=frame * 33)

    assert len(_filas(db, id_sesion)) == 1


def test_cada_cambio_real_de_diagnostico_se_registra(sesion_de_prueba):
    """La secuencia de correcciones del entrenamiento debe quedar completa."""
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    for t, mensaje in enumerate(["IZQ - TSUKI: FLEXIONADO",
                                 "IZQ - TSUKI: EXCELENTE",
                                 "IZQ - TSUKI: HIPEREXTENDIDO (Peligro)"]):
        logger.registrar(_diagnostico("codo_izq", mensaje), timestamp_ms=t * 100)

    diagnosticos = [f["diagnostico"] for f in _filas(db, id_sesion)]
    assert diagnosticos == ["IZQ - TSUKI: FLEXIONADO",
                            "IZQ - TSUKI: EXCELENTE",
                            "IZQ - TSUKI: HIPEREXTENDIDO (Peligro)"]


def test_un_diagnostico_repetido_tras_cambiar_se_vuelve_a_registrar(sesion_de_prueba):
    """
    Volver a fallar después de haber acertado es información valiosa: el
    logger compara contra el ÚLTIMO mensaje, no contra todo el historial.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: FLEXIONADO"), 0)
    logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: EXCELENTE"), 100)
    logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: FLEXIONADO"), 200)

    assert len(_filas(db, id_sesion)) == 3


def test_las_categorias_se_rastrean_por_separado(sesion_de_prueba):
    """
    Que el brazo izquierdo no cambie no debe impedir registrar un cambio en la
    postura de piernas: cada categoría lleva su propia memoria.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: EXCELENTE"), 0)
    logger.registrar(_diagnostico("postura", "ZENKUTSU (IZQ ADELANTE): POSTURA: FIRME"), 0)
    logger.registrar(_diagnostico("codo_izq", "IZQ - TSUKI: EXCELENTE"), 33)
    logger.registrar(_diagnostico("postura", "KIBA DACHI: POSTURA: FIRME"), 33)

    tecnicas = [f["nombre_tecnica"] for f in _filas(db, id_sesion)]
    assert tecnicas == ["Tsuki (brazo izquierdo)", "Postura de piernas", "Postura de piernas"]


def test_traduce_la_categoria_interna_a_un_nombre_legible(sesion_de_prueba):
    """
    En la base de datos debe quedar "Mae Geri (pierna izquierda)", no
    "mae_geri_izq": el historial lo lee un sensei, no un programador.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    for categoria in NOMBRES_TECNICA:
        logger.registrar(_diagnostico(categoria, f"mensaje de {categoria}"), 0)

    guardados = {f["nombre_tecnica"] for f in _filas(db, id_sesion)}
    assert guardados == set(NOMBRES_TECNICA.values())


@pytest.mark.parametrize("diagnostico, motivo", [
    ({"categoria": "postura_der_numero", "mensaje": "", "angulo": 150.0, "correcto": True},
     "mensaje vacío (solo dibuja el número del ángulo en pantalla)"),
    ({"categoria": None, "mensaje": "algo", "angulo": 150.0, "correcto": True},
     "sin categoría"),
    ({"mensaje": "algo", "angulo": 150.0, "correcto": True},
     "diccionario incompleto"),
])
def test_ignora_entradas_que_no_son_diagnosticos_reales(sesion_de_prueba, diagnostico, motivo):
    """Entradas puramente visuales o incompletas no deben llegar a la base de datos."""
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar([diagnostico], timestamp_ms=0)

    assert _filas(db, id_sesion) == [], f"se registró una entrada con {motivo}"


def test_conserva_angulo_veredicto_y_marca_de_tiempo(sesion_de_prueba):
    """Los datos que después alimentan las gráficas de progreso deben llegar completos."""
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico("mae_geri_der", "DER - MAE GERI: KIME INCOMPLETO",
                                  angulo=142.7, correcto=False), timestamp_ms=4321)

    fila = _filas(db, id_sesion)[0]
    assert fila["angulo_promedio"] == pytest.approx(142.7)
    assert fila["correcto"] == 0
    assert fila["timestamp_ms"] == 4321


def test_registra_una_lista_completa_de_diagnosticos_de_un_frame(sesion_de_prueba):
    """
    En producción recibe la lista entera que devuelve el analizador (ambos
    brazos a la vez), no un diagnóstico suelto.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    frame = [
        {"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE", "angulo": 170.0, "correcto": True},
        {"categoria": "codo_der", "mensaje": "DER - TSUKI: FLEXIONADO", "angulo": 120.0, "correcto": False},
    ]
    logger.registrar(frame, timestamp_ms=0)

    assert len(_filas(db, id_sesion)) == 2


# ---------------------------------------------------------------------------
# Lo que la fila debe guardar para poder volver a juzgarse (RF-08)
#
# Antes de esta versión la fila guardaba un ángulo promedio y el `id_umbral` que
# la juzgó. Con eso el historial queda auditable —se sabe con qué criterio se
# midió— pero no re-evaluable: no dice qué postura se reconoció ni, en las
# posturas de dos articulaciones, cuál era el segundo ángulo. Corregir un umbral
# obligaba entonces a volver al dojo.
# ---------------------------------------------------------------------------

def _diagnostico_completo(categoria, mensaje, tecnica, angulos_regla, correcto=True):
    return [{"categoria": categoria, "mensaje": mensaje, "angulo": angulos_regla[0],
             "color": (0, 255, 0), "correcto": correcto,
             "tecnica": tecnica, "angulos_regla": angulos_regla}]


def test_la_fila_guarda_que_tecnica_se_detecto(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico_completo(
        "postura", "KOKUTSU (IZQ ADELANTE): POSTURA: ESTABLE",
        "kokutsu_dachi", (160.0, 105.0)), timestamp_ms=33)

    fila = _filas(db, id_sesion)[0]
    assert fila["tecnica_clave"] == "kokutsu_dachi"


def test_la_fila_guarda_los_dos_angulos_de_una_postura_de_dos_articulaciones(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico_completo(
        "postura", "KOKUTSU (IZQ ADELANTE): POSTURA: ESTABLE",
        "kokutsu_dachi", (160.0, 105.0)), timestamp_ms=33)

    fila = _filas(db, id_sesion)[0]
    assert fila["angulo_regla_1"] == pytest.approx(160.0)
    assert fila["angulo_regla_2"] == pytest.approx(105.0)


def test_una_tecnica_de_un_solo_angulo_deja_el_segundo_vacio(sesion_de_prueba):
    """Vacío, no cero: un cero se leería como un codo totalmente plegado."""
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico_completo(
        "codo_izq", "IZQ - TSUKI: EXCELENTE", "tsuki", (168.0,)), timestamp_ms=33)

    fila = _filas(db, id_sesion)[0]
    assert fila["angulo_regla_1"] == pytest.approx(168.0)
    assert fila["angulo_regla_2"] is None


def test_una_transicion_se_guarda_sin_tecnica_ni_angulos_de_regla(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar([{"categoria": "postura", "mensaje": "MOVIENDOSE: EN TRANSICION...",
                       "angulo": 145.0, "color": (0, 165, 255), "correcto": None,
                       "tecnica": None, "angulos_regla": None}], timestamp_ms=33)

    fila = _filas(db, id_sesion)[0]
    assert fila["tecnica_clave"] is None
    assert fila["angulo_regla_1"] is None


def test_un_diagnostico_sin_los_campos_nuevos_sigue_guardandose(sesion_de_prueba):
    """
    Compatibilidad hacia atrás: `main.py --consola` y cualquier productor de
    diagnósticos que no declare los campos nuevos debe seguir registrando.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico("codo_der", "DER - TSUKI: EXCELENTE"), timestamp_ms=33)

    fila = _filas(db, id_sesion)[0]
    assert fila["diagnostico"] == "DER - TSUKI: EXCELENTE"
    assert fila["tecnica_clave"] is None


def test_las_mediciones_reevaluables_excluyen_las_que_no_se_pueden_juzgar(sesion_de_prueba):
    """
    La consulta que alimenta el informe de recalibración debe traer solo filas
    completas. Una transición o un Mae Geri en la lista obligaría a cada
    consumidor a repetir el filtro.
    """
    db, id_sesion, _, _ = sesion_de_prueba
    logger = MedicionLogger(db, id_sesion)

    logger.registrar(_diagnostico_completo(
        "postura", "KOKUTSU (IZQ ADELANTE): POSTURA: ESTABLE",
        "kokutsu_dachi", (160.0, 105.0)), timestamp_ms=33)
    logger.registrar([{"categoria": "postura", "mensaje": "MOVIENDOSE: EN TRANSICION...",
                       "angulo": None, "color": (0, 165, 255), "correcto": None,
                       "tecnica": None, "angulos_regla": None}], timestamp_ms=66)

    filas = db.mediciones_reevaluables(tecnica_clave="kokutsu_dachi")

    assert len(filas) == 1
    assert filas[0]["tecnica_clave"] == "kokutsu_dachi"
    assert filas[0]["angulo_regla_2"] == pytest.approx(105.0)
