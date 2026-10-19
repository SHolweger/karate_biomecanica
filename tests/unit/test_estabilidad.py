"""
Una postura se registra cuando se sostiene medio segundo (TC-AUTO-076), y una
grabación de sesión se re-analiza con los mismos lados que en vivo (TC-AUTO-077).

Las dos reglas salieron de la misma sesión real de Sebastián (s10, 19-oct-2026,
107 s a 11 fps), pasada por el sistema tal como corrió en vivo. La prueba del
parpadeo usa un tramo de esa sesión —segundos 70 a 88—, no una secuencia
inventada: la lección del doble de MediaPipe es que un dato escrito a mano
confirma lo que uno supuso.
"""
import pytest

from expert_system.estabilidad import (CATEGORIAS_DE_ESTADO, SOSTENIDO_MINIMO_MS,
                                       Estabilizador)
from gui.panel_vivo import FeedCorrecciones
from persistence.medicion_logger import MedicionLogger
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

# ---------------- el tramo real ----------------

# Los mensajes de la categoría `postura`, con su veredicto, tal como los emitió
# el analizador sobre la sesión s10 entre los segundos 70,1 y 87,9.
MENSAJES = [
    ("GUARDIA INDEFINIDA: NO SE DISTINGUE QUE PIERNA VA ADELANTE", None),
    ("KIBA DACHI: POSTURA: FLEXIONA MAS LAS RODILLAS", False),
    ("KOKUTSU (DER ADELANTE): POSTURA: FLEXIONA MAS LA RODILLA TRASERA", False),
    ("MOVIENDOSE: EN TRANSICION...", None),
    ("POSTURA NATURAL: HEIKO DACHI: CORRECTO", True),
    ("POSTURA NATURAL: HEIKO DACHI: DEMASIADO FLEXIONADO", False),
    ("ZENKUTSU (IZQ ADELANTE): POSTURA: CORREGIR AMBAS RODILLAS", False),
    ("ZENKUTSU (IZQ ADELANTE): POSTURA: EXTIENDE LA RODILLA TRASERA", False),
]

# Tramos consecutivos: (índice del mensaje, fotogramas que duró). La grabación
# va a 11,02 fps constantes, así que los instantes salen exactos de la cuenta.
TRAMO_S10 = [
    (0, 4), (3, 1), (5, 2), (3, 10), (1, 2), (0, 2), (6, 1), (3, 1), (6, 1), (7, 1),
    (0, 3), (3, 1), (5, 1), (3, 4), (5, 7), (3, 4), (1, 1), (2, 1), (0, 2), (6, 1),
    (1, 2), (6, 1), (0, 4), (2, 1), (3, 1), (5, 17), (3, 3), (1, 2), (0, 2), (6, 1),
    (1, 1), (6, 1), (7, 1), (0, 4), (3, 1), (5, 5), (4, 1), (5, 2), (3, 2), (1, 1),
    (0, 2), (6, 1), (0, 5), (2, 1), (3, 1), (5, 3), (4, 20), (5, 1), (3, 15), (5, 6),
    (4, 8), (5, 4), (4, 4), (5, 3), (4, 21),
]
MS_POR_FOTOGRAMA = 1000 / 11.02


def _fotogramas_del_tramo():
    """Un diagnóstico de postura por fotograma, con su instante en el video."""
    k = 0
    for indice, duracion in TRAMO_S10:
        mensaje, correcto = MENSAJES[indice]
        for _ in range(duracion):
            yield k * MS_POR_FOTOGRAMA, [{"categoria": "postura", "mensaje": mensaje,
                                          "correcto": correcto, "angulo": 150.0}]
            k += 1


def _registrar_tramo(db, id_sesion, minimo_ms):
    logger = MedicionLogger(db, id_sesion, sostenido_minimo_ms=minimo_ms)
    for t_ms, diagnosticos in _fotogramas_del_tramo():
        logger.registrar(diagnosticos, int(t_ms))
    return db.conn.execute(
        "SELECT diagnostico, correcto FROM tecnica_evaluada WHERE id_sesion = ? "
        "AND correcto IS NOT NULL ORDER BY id_medicion", (id_sesion,)).fetchall()


@ficha(
    id_caso="TC-AUTO-076",
    nombre="Una postura se registra cuando se sostiene medio segundo, no cuando asoma",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="sobre una sesión real, el 74 % de los veredictos de postura "
                         "duraba menos de medio segundo: temblor sobre el límite del "
                         "rango del Heiko Dachi y fotogramas de paso entre posturas. La "
                         "precisión registrada era del 26 %, y del 58 % contando solo "
                         "los sostenidos. Un alumno quieto fallaba por temblor, y cada "
                         "sesión de la campaña habría quedado contaminada",
    componente="expert_system/estabilidad.py, persistence/medicion_logger.py, "
               "gui/panel_vivo.py (FeedCorrecciones)",
    requisitos=("RF-03", "RF-07"),
    precondiciones="Base SQLite temporal con una sesión abierta (fixture sesion_de_prueba)",
    datos_entrada="Segundos 70 a 88 de la sesión real s10: 198 fotogramas de postura "
                  "en 55 tramos, la mayoría de uno o dos fotogramas",
    pasos=[
        Paso("Registrar el tramo sin la regla (espera 0)",
             "assert se escriben 34 veredictos cerrados"),
        Paso("Registrar el mismo tramo con la regla de 500 ms",
             "assert se escriben 3, todos de un Heiko Dachi sostenido"),
        Paso("Pasar el mismo tramo por la lista de correcciones",
             "assert tampoco anota posturas que no se sostuvieron"),
    ],
    resultado_esperado="PASSED: de 34 veredictos de parpadeo quedan 3 sostenidos",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_el_parpadeo_de_una_sesion_real_deja_de_registrarse(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba
    sin_regla = _registrar_tramo(db, id_sesion, minimo_ms=0)
    assert len(sin_regla) == 34

    db.conn.execute("DELETE FROM tecnica_evaluada WHERE id_sesion = ?", (id_sesion,))
    con_regla = _registrar_tramo(db, id_sesion, minimo_ms=SOSTENIDO_MINIMO_MS)

    assert len(con_regla) == 3
    assert all("HEIKO DACHI" in f["diagnostico"] for f in con_regla), (
        "solo el Heiko Dachi se sostuvo medio segundo en ese tramo")


def test_la_lista_de_correcciones_sigue_la_misma_regla():
    """
    Sin la regla, la lista se llenaba con el mismo parpadeo que la base. Con
    ella quedan dos entradas y no tres: la lista ya no repetía una corrección
    vigente cuando entre medio solo hubo una transición, y el tercer Heiko del
    registro es justo ese caso (CORRECTO, transición, CORRECTO).
    """
    sin_regla = FeedCorrecciones(maximo=100, sostenido_minimo_ms=0)
    con_regla = FeedCorrecciones(maximo=100)
    for t_ms, diagnosticos in _fotogramas_del_tramo():
        sin_regla.registrar(diagnosticos, int(t_ms))
        con_regla.registrar(diagnosticos, int(t_ms))

    assert len(sin_regla.entradas) > 20
    assert [e["mensaje"] for e in reversed(con_regla.entradas)] == [
        "POSTURA NATURAL: HEIKO DACHI: DEMASIADO FLEXIONADO",
        "POSTURA NATURAL: HEIKO DACHI: CORRECTO"]


def test_un_parpadeo_no_parte_en_dos_una_postura_sostenida():
    """«CORRECTO», 0,2 s de otra cosa y «CORRECTO» otra vez: una sola evaluación."""
    e = Estabilizador()
    vistos, ultimo = [], None
    secuencia = (["CORRECTO"] * 20) + (["FLEXIONADO"] * 2) + (["CORRECTO"] * 20)
    for k, mensaje in enumerate(secuencia):
        if e.sostenido("postura", mensaje, k * 100) and mensaje != ultimo:
            ultimo = mensaje
            vistos.append(mensaje)
    assert vistos == ["CORRECTO"]


def test_una_postura_sostenida_se_registra_al_cumplir_el_medio_segundo():
    e = Estabilizador()
    assert not e.sostenido("postura", "KIBA", 0)
    assert not e.sostenido("postura", "KIBA", SOSTENIDO_MINIMO_MS - 1)
    assert e.sostenido("postura", "KIBA", SOSTENIDO_MINIMO_MS)


def test_los_golpes_y_las_patadas_no_esperan():
    """Sus máquinas ya juzgan una transición: esperar medio segundo perdería el Kime."""
    e = Estabilizador()
    for categoria in ("codo_izq", "codo_der", "mae_geri_izq", "mae_geri_der"):
        assert categoria not in CATEGORIAS_DE_ESTADO
        assert e.sostenido(categoria, "TSUKI: EXCELENTE", 0)


def test_cada_categoria_lleva_su_propia_cuenta():
    e = Estabilizador()
    e.sostenido("postura", "KIBA", 0)
    assert e.sostenido("codo_izq", "IZQ - TSUKI: EXCELENTE", 100)
    assert e.sostenido("postura", "KIBA", 600)


# ---------------- la grabación, sin espejo ----------------

@ficha(
    id_caso="TC-AUTO-077",
    nombre="La cámara entrega el fotograma volteado y conserva el crudo para grabarlo",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="la sesión se grababa ya volteada y al re-analizarla —los "
                         "archivos también se voltean— el espejo se aplicaba dos veces: "
                         "izquierda y derecha quedaban intercambiadas respecto de la "
                         "sesión en vivo. Medido sobre s10: la guardia izquierda en 56 "
                         "fotogramas en vivo pasaba a 38 al re-analizar",
    componente="vision/camera.py (fotograma_crudo), gui/live_screen.py",
    requisitos=("RF-01", "RF-08"),
    precondiciones="OpenCV instalado",
    datos_entrada="Un video de tres fotogramas con la mitad izquierda blanca",
    pasos=[
        Paso("Leer un fotograma con la cámara en modo espejo",
             "assert el entregado tiene la mitad derecha blanca"),
        Paso("Mirar el fotograma crudo",
             "assert conserva la mitad izquierda blanca, como el archivo"),
        Paso("Leer pasado el final",
             "assert sin fotograma tampoco queda un crudo viejo"),
    ],
    resultado_esperado="PASSED en los dos entornos donde haya OpenCV",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_la_camara_conserva_el_fotograma_sin_espejo(tmp_path):
    cv2 = pytest.importorskip("cv2", reason="OpenCV no está instalado")
    np = pytest.importorskip("numpy")
    from vision.camera import Camera

    ruta = str(tmp_path / "mitad.avi")
    escritor = cv2.VideoWriter(ruta, cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for _ in range(3):
        fotograma = np.zeros((48, 64, 3), dtype=np.uint8)
        fotograma[:, :32] = 255
        escritor.write(fotograma)
    escritor.release()

    camara = Camera(ruta, espejo=True)
    try:
        entregado = camara.get_frame()
        assert entregado[:, 48:].mean() > 200 and entregado[:, :16].mean() < 50
        crudo = camara.fotograma_crudo
        assert crudo[:, :16].mean() > 200 and crudo[:, 48:].mean() < 50

        while camara.get_frame() is not None:
            pass
        assert camara.fotograma_crudo is None
    finally:
        camara.release()
