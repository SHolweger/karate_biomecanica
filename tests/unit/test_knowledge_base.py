"""
Pruebas unitarias de expert_system/knowledge_base.py (KarateRules).

Aquí vive el conocimiento del sensei codificado como umbrales. La técnica de
diseño aplicada es ANÁLISIS DE VALORES LÍMITE: cada regla se prueba justo
dentro, justo fuera y exactamente sobre la frontera, porque es donde un
sistema de evaluación técnica se equivoca — un Tsuki de 175.0 grados es
correcto y uno de 175.1 es una hiperextensión peligrosa para la articulación.
"""
import pytest

from expert_system.knowledge_base import KarateRules

pytestmark = pytest.mark.unitaria

VERDE = (0, 255, 0)
ROJO = (0, 0, 255)
AMARILLO = (0, 255, 255)

TODAS_LAS_REGLAS = [
    ("evaluate_tsuki", (170,)),
    ("evaluate_heiko_dachi", (170,)),
    ("evaluate_kiba_dachi", (140, 140)),
    ("evaluate_zenkutsu_dachi", (100, 170)),
    ("evaluate_kokutsu_dachi", (110, 100)),
    ("evaluate_mae_geri", (170, 800)),
    ("evaluate_hikiashi", (True,)),
    ("evaluate_age_uke", (130,)),
]


# --------------------------------------------------------------------------
# GOLPES — Tsuki (golpe recto)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("angulo", [160, 165, 170, 175])
def test_tsuki_correcto_dentro_del_rango_de_kime(angulo, reglas):
    """160-175 grados es el rango de extensión válido en el punto de impacto."""
    correcto, mensaje, color = reglas.evaluate_tsuki(angulo)

    assert correcto is True
    assert "EXCELENTE" in mensaje
    assert color == VERDE


@pytest.mark.parametrize("angulo", [175.1, 178, 180])
def test_tsuki_hiperextendido_se_marca_como_peligro(angulo, reglas):
    """Pasar de 175 grados bloquea la articulación: riesgo de lesión, no un acierto."""
    correcto, mensaje, color = reglas.evaluate_tsuki(angulo)

    assert correcto is False
    assert "HIPEREXTENDIDO" in mensaje
    assert color == ROJO


@pytest.mark.parametrize("angulo", [0, 90, 159.9])
def test_tsuki_flexionado_no_alcanza_el_kime(angulo, reglas):
    """Por debajo de 160 grados el golpe no llegó a extenderse: aviso, no peligro."""
    correcto, mensaje, color = reglas.evaluate_tsuki(angulo)

    assert correcto is False
    assert "FLEXIONADO" in mensaje
    assert color == AMARILLO


@pytest.mark.parametrize("angulo, esperado", [
    (159.9, False), (160.0, True),    # frontera inferior
    (175.0, True), (175.1, False),    # frontera superior
])
def test_tsuki_fronteras_exactas(angulo, esperado, reglas):
    """Los extremos 160 y 175 pertenecen al rango correcto (comparación inclusiva)."""
    assert reglas.evaluate_tsuki(angulo)[0] is esperado


# --------------------------------------------------------------------------
# POSTURAS
# --------------------------------------------------------------------------

@pytest.mark.parametrize("angulo, esperado", [
    (164.9, False), (165.0, True), (172.0, True), (180.0, True),
])
def test_heiko_dachi_exige_rodillas_extendidas(angulo, esperado, reglas):
    """Postura natural: rodillas casi rectas (165-180 grados)."""
    correcto, mensaje, _ = reglas.evaluate_heiko_dachi(angulo)

    assert correcto is esperado
    assert ("CORRECTO" in mensaje) is esperado


@pytest.mark.parametrize("izq, der, esperado", [
    (140, 140, True),    # simétrica y en rango
    (130, 150, True),    # ambas fronteras inclusivas
    (129, 140, False),   # izquierda demasiado flexionada
    (140, 151, False),   # derecha demasiado alta
    (170, 170, False),   # de pie, no es Kiba Dachi
])
def test_kiba_dachi_exige_simetria_en_ambas_rodillas(izq, der, esperado, reglas):
    """
    Postura de jinete: NO tiene pierna delantera ni trasera, así que ambas
    rodillas deben cumplir el rango 130-150 de forma independiente.
    """
    assert reglas.evaluate_kiba_dachi(izq, der)[0] is esperado


@pytest.mark.parametrize("frontal, trasero, esperado", [
    (100, 170, True),    # ejecución correcta
    (90, 165, True),     # ambas fronteras inferiores
    (115, 180, True),    # ambas fronteras superiores
    (120, 170, False),   # rodilla delantera poco flexionada
    (100, 160, False),   # pierna trasera sin tensar
])
def test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera(frontal, trasero, esperado, reglas):
    """Postura adelantada: delantera flexionada 90-115, trasera extendida 165-180."""
    assert reglas.evaluate_zenkutsu_dachi(frontal, trasero)[0] is esperado


@pytest.mark.parametrize("frontal, trasero, esperado", [
    (110, 100, True),
    (100, 90, True),     # fronteras inferiores
    (120, 110, True),    # fronteras superiores
    (130, 100, False),   # delantera demasiado extendida
    (110, 130, False),   # trasera sin flexionar: sería Zenkutsu, no Kokutsu
])
def test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera(frontal, trasero, esperado, reglas):
    """Postura atrasada: la trasera (90-110) va más flexionada que la delantera (100-120)."""
    assert reglas.evaluate_kokutsu_dachi(frontal, trasero)[0] is esperado


def test_zenkutsu_y_kokutsu_no_aprueban_la_misma_ejecucion(reglas):
    """
    Regla de negocio: una misma pareja de ángulos no puede ser simultáneamente
    un Zenkutsu y un Kokutsu correctos, o el clasificador estaría premiando dos
    posturas incompatibles con la misma evidencia.
    """
    for frontal in range(85, 130, 5):
        for trasero in range(85, 185, 5):
            zen = reglas.evaluate_zenkutsu_dachi(frontal, trasero)[0]
            kok = reglas.evaluate_kokutsu_dachi(frontal, trasero)[0]
            assert not (zen and kok), f"ambigüedad en frontal={frontal}, trasero={trasero}"


# --------------------------------------------------------------------------
# PATADAS — Mae Geri e Hikiashi
# --------------------------------------------------------------------------

def test_mae_geri_excelente_con_kime_y_explosividad(reglas):
    """Extensión >=160 grados Y velocidad angular >=400 grados/seg."""
    correcto, mensaje, color = reglas.evaluate_mae_geri(kime_angle=170, velocidad_pico=800)

    assert correcto is True
    assert "KIME EXCELENTE" in mensaje
    assert color == VERDE


@pytest.mark.parametrize("kime, velocidad", [(159.9, 900), (120, 900), (90, 2000)])
def test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz(kime, velocidad, reglas):
    """
    La extensión manda sobre la velocidad: una pierna rápida que no se extiende
    no es una patada, y el mensaje debe señalar el Kime, no la explosividad.
    """
    correcto, mensaje, color = reglas.evaluate_mae_geri(kime, velocidad)

    assert correcto is False
    assert "KIME INCOMPLETO" in mensaje
    assert color == ROJO


@pytest.mark.parametrize("velocidad", [0, 200, 399.9])
def test_mae_geri_rechaza_extension_lenta(velocidad, reglas):
    """Levantar la pierna despacio hasta la extensión no es un Mae Geri: falta explosividad."""
    correcto, mensaje, color = reglas.evaluate_mae_geri(kime_angle=170, velocidad_pico=velocidad)

    assert correcto is False
    assert "EXPLOSIVIDAD" in mensaje
    assert color == AMARILLO


@pytest.mark.parametrize("kime, velocidad, esperado", [
    (159.9, 400, False), (160.0, 400.0, True),   # frontera de extensión
    (170, 399.9, False), (170, 400, True),       # frontera de velocidad
])
def test_mae_geri_fronteras_exactas(kime, velocidad, esperado, reglas):
    assert reglas.evaluate_mae_geri(kime, velocidad)[0] is esperado


@pytest.mark.parametrize("recogido, esperado", [(True, True), (False, False)])
def test_hikiashi_evalua_el_recojo_de_la_pierna(recogido, esperado, reglas):
    """La pierna debe recogerse antes de bajar; si cae, la técnica queda expuesta."""
    correcto, mensaje, _ = reglas.evaluate_hikiashi(recogido)

    assert correcto is esperado
    assert ("CORRECTO" in mensaje) is esperado


# --------------------------------------------------------------------------
# DEFENSAS — Age Uke
# --------------------------------------------------------------------------

@pytest.mark.parametrize("angulo, esperado_correcto, fragmento", [
    (119.9, False, "DEMASIADO FLEXIONADO"),
    (120.0, True, "EFECTIVO"),
    (130.0, True, "EFECTIVO"),
    (140.0, True, "EFECTIVO"),
    (140.1, False, "DEMASIADO EXTENDIDO"),
])
def test_age_uke_bloquea_solo_en_su_rango(angulo, esperado_correcto, fragmento, reglas):
    """Defensa alta: el codo debe quedar entre 120 y 140 grados para desviar el ataque."""
    correcto, mensaje, _ = reglas.evaluate_age_uke(angulo)

    assert correcto is esperado_correcto
    assert fragmento in mensaje


# --------------------------------------------------------------------------
# Contrato común de la base de conocimiento
# --------------------------------------------------------------------------

@pytest.mark.parametrize("nombre_regla, argumentos", TODAS_LAS_REGLAS)
def test_toda_regla_devuelve_el_contrato_esperado(nombre_regla, argumentos, reglas):
    """
    Contrato que el renderer y la capa de persistencia dan por hecho:
    (bool, texto no vacío, color BGR de 3 componentes válidas). Si una regla
    nueva lo rompe, la aplicación falla en tiempo de ejecución al dibujar.
    """
    correcto, mensaje, color = getattr(reglas, nombre_regla)(*argumentos)

    assert isinstance(correcto, bool), f"{nombre_regla} no devolvió un booleano"
    assert isinstance(mensaje, str) and mensaje.strip(), f"{nombre_regla} devolvió un mensaje vacío"
    assert isinstance(color, tuple) and len(color) == 3, f"{nombre_regla} devolvió un color inválido"
    assert all(isinstance(c, int) and 0 <= c <= 255 for c in color), \
        f"{nombre_regla} devolvió componentes BGR fuera de rango: {color}"
