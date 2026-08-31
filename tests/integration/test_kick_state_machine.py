"""
Pruebas de integración de expert_system/kick_state_machine.py.

La máquina de estados coordina filtro + derivada de velocidad + reglas de
karate para evaluar un Mae Geri EN MOVIMIENTO (Reposo -> Carga -> Extensión
-> Recuperando). Se alimenta con secuencias sintéticas de (visible, ángulo,
ankle_y, t_ms): la clase está desacoplada de MediaPipe y de los píxeles, así
que una patada completa se puede reproducir sin cámara y de forma
determinista, cuadro por cuadro.
"""
import pytest

from expert_system.kick_state_machine import (
    CARGA, EXTENSION, RECUPERANDO, REPOSO,
    TIMEOUT_CARGA_MS, TIMEOUT_EXTENSION_MS, TOLERANCIA_FRAMES_OCULTO,
    MaeGeriStateMachine,
)

pytestmark = pytest.mark.integracion

PIE_EN_SUELO = 0.90   # coordenada Y normalizada del tobillo de pie
PIE_EN_AIRE = 0.50    # tobillo elevado durante la patada
FRAME_MS = 33         # ~30 fps


@pytest.fixture
def maquina():
    """Ventana de filtro 1: sin suavizado, para probar la lógica de estados pura."""
    return MaeGeriStateMachine(ventana_filtro=1)


def _poner_de_pie(maquina, t_ms=0):
    """Deja la máquina en REPOSO con la referencia de 'pie en el suelo' registrada."""
    maquina.update(True, 175, ankle_y=PIE_EN_SUELO, t_ms=t_ms)
    return maquina


def test_ciclo_completo_de_una_patada_correcta(maquina):
    """
    Camino feliz: recojo de rodilla, extensión explosiva, Hikiashi con el pie
    aún en el aire y regreso al apoyo. Es el caso que el sistema debe premiar.
    """
    _poner_de_pie(maquina)

    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    assert maquina.estado == CARGA

    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)
    assert maquina.estado == EXTENSION

    resultado = maquina.update(True, 45, ankle_y=PIE_EN_AIRE, t_ms=3 * FRAME_MS)
    assert maquina.estado == RECUPERANDO
    assert resultado["correcto"] is True
    assert "KIME EXCELENTE" in resultado["mensaje"]
    assert "HIKIASHI: CORRECTO" in resultado["mensaje"]

    maquina.update(True, 175, ankle_y=PIE_EN_SUELO, t_ms=4 * FRAME_MS)
    assert maquina.estado == REPOSO, "la maquina debe quedar lista para la siguiente patada"


def test_no_reporta_nada_mientras_el_atleta_esta_quieto(maquina):
    """En REPOSO no hay técnica en curso: no debe ensuciar la pantalla ni la base de datos."""
    for i in range(10):
        assert maquina.update(True, 175, ankle_y=PIE_EN_SUELO, t_ms=i * FRAME_MS) is None


def test_patada_lenta_se_diagnostica_sin_explosividad(maquina):
    """
    Misma trayectoria angular, pero extendida en el tiempo: la velocidad pico
    no alcanza el umbral y la técnica se rechaza por falta de explosividad,
    no por el ángulo.
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=100)
    for t, angulo in [(600, 90), (1100, 130), (1600, 165)]:
        maquina.update(True, angulo, ankle_y=PIE_EN_AIRE, t_ms=t)

    resultado = maquina.update(True, 45, ankle_y=PIE_EN_AIRE, t_ms=2100)

    assert resultado["correcto"] is False
    assert "EXPLOSIVIDAD" in resultado["mensaje"]


def test_hikiashi_incorrecto_cuando_la_pierna_cae_sin_recogerse(maquina):
    """
    El Kime puede ser perfecto y la técnica seguir siendo incorrecta: si el pie
    ya bajó al nivel de reposo cuando la rodilla se flexiona, la pierna cayó en
    vez de recogerse.
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)

    resultado = maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=3 * FRAME_MS)

    assert "KIME EXCELENTE" in resultado["mensaje"]
    assert "PIERNA CAYO SIN RECOGER" in resultado["mensaje"]
    assert resultado["correcto"] is False, "una fase incorrecta invalida la tecnica completa"


def test_mantiene_el_aviso_mientras_la_pierna_sigue_extendida(maquina):
    """
    Frames intermedios del Kime: mientras la rodilla siga extendida y no haya
    vencido el timeout, la máquina informa "EXTENSION..." sin emitir todavía
    un veredicto — la técnica aún no termina.
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)

    resultado = maquina.update(True, 168, ankle_y=PIE_EN_AIRE, t_ms=3 * FRAME_MS)

    assert maquina.estado == EXTENSION
    assert "EXTENSION" in resultado["mensaje"]
    assert resultado["correcto"] is None


def test_intento_abandonado_en_carga_se_descarta_por_timeout(maquina):
    """
    El atleta recoge la rodilla y no patea: pasado el timeout el intento se
    descarta en silencio (no es una patada mal hecha, es una patada que nunca
    ocurrió y no debe contarse como error en su historial).
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    assert maquina.estado == CARGA

    resultado = maquina.update(True, 120, ankle_y=0.7, t_ms=FRAME_MS + TIMEOUT_CARGA_MS + 1)

    assert resultado is None
    assert maquina.estado == REPOSO


def test_kime_sostenido_demasiado_tiempo_se_descarta_por_timeout(maquina):
    """Sostener la pierna extendida indefinidamente tampoco es un Mae Geri evaluable."""
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)
    assert maquina.estado == EXTENSION

    resultado = maquina.update(True, 168, ankle_y=PIE_EN_AIRE,
                               t_ms=2 * FRAME_MS + TIMEOUT_EXTENSION_MS + 1)

    assert resultado is None
    assert maquina.estado == REPOSO


def test_oclusion_breve_no_interrumpe_la_tecnica(maquina):
    """
    Perder la pierna de vista unos frames (la cadera la tapa al girar) es
    normal: la máquina debe conservar el estado y repetir el último
    diagnóstico en lugar de borrarlo en pleno movimiento.
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)

    for i in range(TOLERANCIA_FRAMES_OCULTO):
        resultado = maquina.update(False, None, ankle_y=None, t_ms=(2 + i) * FRAME_MS)
        assert maquina.estado == CARGA, "una oclusion breve no debe abortar la tecnica"
        assert "CARGA" in resultado["mensaje"]


def test_oclusion_prolongada_aborta_la_tecnica(maquina):
    """
    Si la pierna desaparece más allá de la tolerancia, el sistema no puede
    afirmar nada sobre la técnica: la aborta explícitamente y se reinicia, en
    vez de inventar un diagnóstico con datos incompletos.
    """
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)

    resultado = None
    for i in range(TOLERANCIA_FRAMES_OCULTO + 1):
        resultado = maquina.update(False, None, ankle_y=None, t_ms=(2 + i) * FRAME_MS)

    assert "TECNICA PERDIDA" in resultado["mensaje"]
    assert resultado["correcto"] is None, "una tecnica abortada no se califica"
    assert maquina.estado == REPOSO


def test_dos_patadas_seguidas_se_evaluan_de_forma_independiente(maquina):
    """
    Regresión: la velocidad pico y la extensión máxima deben reiniciarse entre
    patadas. Si se arrastraran, una primera patada explosiva haría aprobar una
    segunda lenta.
    """
    _poner_de_pie(maquina)

    # Patada 1: explosiva y correcta
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)
    primera = maquina.update(True, 45, ankle_y=PIE_EN_AIRE, t_ms=3 * FRAME_MS)
    maquina.update(True, 175, ankle_y=PIE_EN_SUELO, t_ms=4 * FRAME_MS)
    assert primera["correcto"] is True

    # Patada 2: misma trayectoria, ejecutada muy despacio
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=5000)
    for t, angulo in [(5600, 90), (6200, 140), (6800, 168)]:
        maquina.update(True, angulo, ankle_y=PIE_EN_AIRE, t_ms=t)
    segunda = maquina.update(True, 45, ankle_y=PIE_EN_AIRE, t_ms=7400)

    assert segunda["correcto"] is False, "la explosividad de la patada previa no debe heredarse"
    assert "EXPLOSIVIDAD" in segunda["mensaje"]


def test_reset_deja_la_maquina_como_recien_creada(maquina):
    """Reset manual: sin estado residual de la técnica interrumpida."""
    _poner_de_pie(maquina)
    maquina.update(True, 45, ankle_y=PIE_EN_SUELO, t_ms=FRAME_MS)
    maquina.update(True, 170, ankle_y=PIE_EN_AIRE, t_ms=2 * FRAME_MS)

    maquina.reset()

    assert maquina.estado == REPOSO
    assert maquina.velocidad_pico == 0.0
    assert maquina.ultimo_resultado is None
    assert maquina.angulo_anterior is None


def test_todo_diagnostico_trae_las_claves_que_consume_la_capa_visual(maquina):
    """
    Contrato con el renderer y con MedicionLogger: cada diagnóstico emitido
    debe traer ángulo, mensaje, color y la marca de si es correcto.
    """
    _poner_de_pie(maquina)
    secuencia = [
        (True, 45, PIE_EN_SUELO, FRAME_MS),
        (True, 170, PIE_EN_AIRE, 2 * FRAME_MS),
        (True, 45, PIE_EN_AIRE, 3 * FRAME_MS),
    ]

    for visible, angulo, ankle_y, t in secuencia:
        resultado = maquina.update(visible, angulo, ankle_y, t)
        assert set(resultado) >= {"angulo", "mensaje", "color", "correcto"}, \
            f"faltan claves en el diagnostico: {resultado}"
        assert isinstance(resultado["mensaje"], str) and resultado["mensaje"]
        assert len(resultado["color"]) == 3
