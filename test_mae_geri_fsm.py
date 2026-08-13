"""
test_mae_geri_fsm.py — Verificación matemática de la máquina de estados de Mae Geri.

No abre cámara ni usa MediaPipe: alimenta secuencias sintéticas de
(visible, angulo, ankle_y, t_ms) directamente a MaeGeriStateMachine.update().
Esto es posible porque la clase está desacoplada de landmarks/píxeles (ver
diseño en expert_system/kick_state_machine.py).

Uso:
    ./venv/bin/python test_mae_geri_fsm.py
"""
from expert_system.kick_state_machine import MaeGeriStateMachine


def test_patada_perfecta():
    """Carga -> Extension explosiva -> Hikiashi correcto -> Reposo."""
    m = MaeGeriStateMachine(ventana_filtro=1)  # ventana=1: sin suavizado, prueba la lógica de estados pura

    m.update(True, 175, ankle_y=0.9, t_ms=0)       # de pie, pie en el suelo (ankle_y_reposo=0.9)
    r = m.update(True, 45, ankle_y=0.9, t_ms=33)   # rodilla se flexiona -> CARGA
    assert m.estado == "CARGA", f"esperaba CARGA, obtuve {m.estado}"

    r = m.update(True, 170, ankle_y=0.5, t_ms=66)  # extensión explosiva (dt chico) -> EXTENSION
    assert m.estado == "EXTENSION", f"esperaba EXTENSION, obtuve {m.estado}"

    # Hikiashi: rodilla se flexiona de nuevo, pie AÚN elevado (0.5 < 0.9-0.05)
    r = m.update(True, 45, ankle_y=0.5, t_ms=100)
    assert "KIME EXCELENTE" in r["mensaje"], f"mensaje inesperado: {r['mensaje']}"
    assert "HIKIASHI: CORRECTO" in r["mensaje"], f"mensaje inesperado: {r['mensaje']}"
    assert m.estado == "RECUPERANDO", f"esperaba RECUPERANDO, obtuve {m.estado}"

    m.update(True, 175, ankle_y=0.9, t_ms=133)     # pierna vuelve a apoyar
    assert m.estado == "REPOSO", f"esperaba REPOSO, obtuve {m.estado}"


def test_kime_incompleto_por_timeout():
    """La rodilla nunca supera el umbral de extensión: se descarta el intento por timeout."""
    m = MaeGeriStateMachine(ventana_filtro=1)

    m.update(True, 175, ankle_y=0.9, t_ms=0)
    m.update(True, 45, ankle_y=0.9, t_ms=33)       # entra a CARGA
    assert m.estado == "CARGA"

    m.update(True, 120, ankle_y=0.6, t_ms=66)      # se mueve pero no llega a 160
    r = m.update(True, 130, ankle_y=0.6, t_ms=4100)  # pasan >TIMEOUT_CARGA_MS (4000ms) desde que entró a CARGA
    assert r is None, f"esperaba None (intento descartado), obtuve {r}"
    assert m.estado == "REPOSO", f"esperaba REPOSO tras timeout, obtuve {m.estado}"


def test_patada_lenta_sin_explosividad():
    """Llega a >160° pero con velocidad angular baja (dt grandes) -> falta explosividad."""
    m = MaeGeriStateMachine(ventana_filtro=1)

    m.update(True, 175, ankle_y=0.9, t_ms=0)
    m.update(True, 45, ankle_y=0.9, t_ms=1000)       # CARGA
    m.update(True, 100, ankle_y=0.6, t_ms=1500)       # se abre lentamente (dt=500ms)
    m.update(True, 165, ankle_y=0.5, t_ms=2000)       # cruza 160, pero lento -> EXTENSION
    assert m.estado == "EXTENSION"

    r = m.update(True, 45, ankle_y=0.5, t_ms=2500)    # recojo, también lento
    assert "FALTA EXPLOSIVIDAD" in r["mensaje"], f"mensaje inesperado: {r['mensaje']}"


def test_pierna_cae_sin_recojo():
    """Kime explosivo correcto, pero el pie ya bajó al nivel de reposo -> Hikiashi incorrecto."""
    m = MaeGeriStateMachine(ventana_filtro=1)

    m.update(True, 175, ankle_y=0.9, t_ms=0)
    m.update(True, 45, ankle_y=0.9, t_ms=33)
    m.update(True, 170, ankle_y=0.5, t_ms=66)          # extensión explosiva

    # El pie ya está prácticamente al nivel de reposo (0.88 ~ 0.9) al momento de flexionar
    r = m.update(True, 45, ankle_y=0.88, t_ms=100)
    assert "PIERNA CAYO SIN RECOGER" in r["mensaje"], f"mensaje inesperado: {r['mensaje']}"


def test_oclusion_breve_no_reinicia():
    """Oclusión de 3 frames justo en el pico de extensión: el estado se congela, no se pierde."""
    m = MaeGeriStateMachine(ventana_filtro=1)

    m.update(True, 175, ankle_y=0.9, t_ms=0)
    m.update(True, 45, ankle_y=0.9, t_ms=33)
    m.update(True, 170, ankle_y=0.5, t_ms=66)
    assert m.estado == "EXTENSION"

    # 3 frames sin visibilidad (por debajo de la tolerancia de 5)
    for i, t in enumerate([100, 133, 166]):
        r = m.update(False, None, None, t_ms=t)
        assert m.estado == "EXTENSION", f"la oclusión breve no debería resetear el estado (frame {i})"

    # Reaparece y completa la técnica con normalidad
    r = m.update(True, 45, ankle_y=0.5, t_ms=199)
    assert "KIME EXCELENTE" in r["mensaje"] and "HIKIASHI: CORRECTO" in r["mensaje"], \
        f"la técnica debería completarse tras la oclusión breve, obtuve: {r['mensaje']}"


def test_oclusion_prolongada_reinicia():
    """Oclusión más allá de la tolerancia a mitad de técnica: se aborta con mensaje honesto."""
    m = MaeGeriStateMachine(ventana_filtro=1)

    m.update(True, 175, ankle_y=0.9, t_ms=0)
    m.update(True, 45, ankle_y=0.9, t_ms=33)     # entra a CARGA
    assert m.estado == "CARGA"

    r = None
    for i in range(6):  # 6 frames ocultos: supera TOLERANCIA_FRAMES_OCULTO (5)
        r = m.update(False, None, None, t_ms=66 + i * 33)

    assert r is not None and "TECNICA PERDIDA" in r["mensaje"], f"esperaba TECNICA PERDIDA, obtuve {r}"
    assert m.estado == "REPOSO", f"esperaba REPOSO tras aborto, obtuve {m.estado}"


def test_derivada_velocidad():
    """Sanity check de la derivada discreta: grados/segundo, y sin división por cero."""
    m = MaeGeriStateMachine(ventana_filtro=1)
    m._calcular_velocidad(100, t_ms=0)              # primer frame: no hay "anterior", no se evalúa
    v = m._calcular_velocidad(110, t_ms=33)           # 10° en 33ms -> ~303°/s
    esperado = (110 - 100) / 33 * 1000
    assert abs(v - esperado) < 0.5, f"velocidad calculada {v} distinta de la esperada {esperado}"

    # dt=0 no debe lanzar ZeroDivisionError
    m2 = MaeGeriStateMachine(ventana_filtro=1)
    m2._calcular_velocidad(100, t_ms=50)
    v2 = m2._calcular_velocidad(120, t_ms=50)
    assert v2 == 0.0, f"esperaba 0.0 con dt=0 (division protegida), obtuve {v2}"


if __name__ == "__main__":
    pruebas = [
        test_patada_perfecta,
        test_kime_incompleto_por_timeout,
        test_patada_lenta_sin_explosividad,
        test_pierna_cae_sin_recojo,
        test_oclusion_breve_no_reinicia,
        test_oclusion_prolongada_reinicia,
        test_derivada_velocidad,
    ]

    ok, fallidas = 0, 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"PASS - {prueba.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"FAIL - {prueba.__name__}: {e}")
            fallidas += 1

    print(f"\n{ok}/{len(pruebas)} pruebas pasaron.")
    if fallidas:
        raise SystemExit(1)
