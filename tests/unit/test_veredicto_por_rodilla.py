"""
Pruebas del veredicto por rodilla en las posturas asimétricas (RF-05, RF-06).

Por qué existe este módulo
--------------------------
Zenkutsu y Kokutsu se juzgan con dos rangos distintos —uno para la rodilla
delantera y otro para la trasera—, pero hasta el 18-oct-2026 las dos reglas
devolvían el mismo veredicto que Kiba Dachi cuando algo fallaba:

    POSTURA: CORREGIR ALTURA

En una postura simétrica eso basta. En una asimétrica no dice nada accionable:
el alumno no sabe cuál de las dos rodillas corregir ni hacia dónde, y el sistema
tenía el dato —acababa de evaluar cada una contra su rango— y lo tiraba al
construir el mensaje.

Lo que estas pruebas fijan
--------------------------
1. El mensaje nombra la rodilla y el sentido de la corrección.
2. **El veredicto booleano no cambia.** Solo cambia el texto. Esto es lo que
   protege a la precisión del alumno, a su gráfica de evolución y a
   `expert_system/reevaluacion.py`, que compara por `correcto` y no por texto.
3. El sentido sale del rango vigente, no de números escritos aquí: si el cuerpo
   técnico recalibra, la corrección sigue al criterio nuevo.
4. Todo veredicto que la regla puede emitir tiene su corrección en el panel.
"""
import pytest

from expert_system import knowledge_base as kb
from expert_system.knowledge_base import KarateRules
from gui.coaching import CORRECCIONES, sin_traduccion, traducir
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@pytest.fixture
def reglas():
    return KarateRules()


# ---------------- el mensaje nombra la rodilla ----------------

@ficha(
    id_caso="TC-AUTO-067",
    nombre="En Zenkutsu y Kokutsu el veredicto dice qué rodilla corregir y hacia dónde",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "las dos posturas se juzgan con un rango por rodilla, pero respondían "
        "«CORREGIR ALTURA» igual que Kiba Dachi: el alumno no sabía cuál de las "
        "dos rodillas corregir ni en qué sentido, y el sistema tenía el dato y "
        "lo descartaba al redactar el veredicto"),
    componente="expert_system/knowledge_base.py (evaluate_zenkutsu_dachi, evaluate_kokutsu_dachi)",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna. Las reglas se instancian con los umbrales de literatura",
    datos_entrada=(
        "Zenkutsu (delantera 90–115°, trasera 165–180°) y Kokutsu (delantera "
        "145–175°, trasera 90–120°), con cada rodilla por debajo, dentro y por "
        "encima de su rango"),
    pasos=[
        Paso("Evaluar un Zenkutsu con la delantera a 125°",
             "assert mensaje == FLEXIONA_DELANTERA and correcto is False"),
        Paso("Evaluar un Zenkutsu con la trasera a 155°",
             "assert mensaje == EXTIENDE_TRASERA"),
        Paso("Evaluar un Kokutsu con la trasera a 128°",
             "assert mensaje == FLEXIONA_TRASERA"),
        Paso("Evaluar con las dos rodillas fuera de rango",
             "assert mensaje == CORREGIR_AMBAS"),
        Paso("Recorrer una rejilla de ángulos y comparar el booleano con el criterio",
             "assert correcto == (frontal dentro and trasera dentro)"),
    ],
    resultado_esperado="PASSED: el texto identifica la rodilla y el veredicto booleano no cambia",
)
@pytest.mark.parametrize("tecnica, frontal, trasera, esperado", [
    # Zenkutsu: delantera 90–115, trasera 165–180.
    ("zenkutsu_dachi", 125, 170, kb.FLEXIONA_DELANTERA),   # postura alta
    ("zenkutsu_dachi",  80, 170, kb.EXTIENDE_DELANTERA),   # demasiado profunda
    ("zenkutsu_dachi", 100, 155, kb.EXTIENDE_TRASERA),     # la de atrás se dobla
    ("zenkutsu_dachi", 125, 155, kb.CORREGIR_AMBAS),
    # Kokutsu: delantera 145–175, trasera 90–120.
    ("kokutsu_dachi",  142, 105, kb.EXTIENDE_DELANTERA),
    ("kokutsu_dachi",  178, 105, kb.FLEXIONA_DELANTERA),   # delantera bloqueada
    ("kokutsu_dachi",  160, 128, kb.FLEXIONA_TRASERA),     # el peso no va atrás
    ("kokutsu_dachi",  160,  85, kb.EXTIENDE_TRASERA),
    ("kokutsu_dachi",  142, 128, kb.CORREGIR_AMBAS),
])
def test_el_veredicto_nombra_la_rodilla_y_el_sentido(reglas, tecnica, frontal, trasera, esperado):
    evaluar = getattr(reglas, f"evaluate_{tecnica}")

    correcto, mensaje, color = evaluar(frontal, trasera)

    assert correcto is False
    assert mensaje == esperado
    assert color == kb.ROJO


@pytest.mark.parametrize("tecnica, frontal, trasera, esperado", [
    ("zenkutsu_dachi", 100, 170, "POSTURA: FIRME"),
    ("kokutsu_dachi",  160, 105, "POSTURA: ESTABLE"),
])
def test_una_postura_correcta_conserva_su_veredicto(reglas, tecnica, frontal, trasera, esperado):
    """Lo que ya estaba bien no cambia: ni el texto ni la clave de agrupación."""
    correcto, mensaje, color = getattr(reglas, f"evaluate_{tecnica}")(frontal, trasera)

    assert (correcto, mensaje, color) == (True, esperado, kb.VERDE)


@pytest.mark.parametrize("tecnica, frontal, trasera", [
    ("zenkutsu_dachi", 115, 165),   # los dos límites exactos
    ("zenkutsu_dachi",  90, 180),
    ("kokutsu_dachi",  145, 120),
    ("kokutsu_dachi",  175,  90),
])
def test_los_limites_del_rango_cuentan_como_dentro(reglas, tecnica, frontal, trasera):
    """El borde se decide igual que en `_dentro`: inclusivo por los dos lados."""
    correcto, _, _ = getattr(reglas, f"evaluate_{tecnica}")(frontal, trasera)

    assert correcto is True


def test_kiba_dachi_conserva_su_veredicto():
    """
    Kiba es simétrica: no hay rodilla delantera ni trasera que nombrar, así que
    su veredicto sigue siendo el de siempre.
    """
    correcto, mensaje, _ = KarateRules().evaluate_kiba_dachi(158, 158)

    assert correcto is False
    assert mensaje == "POSTURA: CORREGIR ALTURA"


# ---------------- el booleano no se mueve ----------------

@pytest.mark.parametrize("tecnica", ["zenkutsu_dachi", "kokutsu_dachi"])
def test_solo_cambia_el_texto_nunca_el_veredicto(reglas, tecnica):
    """
    La garantía que importa para el historial: en toda la rejilla de ángulos el
    booleano es exactamente «las dos rodillas dentro de su rango», que es lo que
    era antes del cambio. La precisión del alumno, su gráfica de evolución y la
    reevaluación del historial comparan por `correcto`, no por texto.
    """
    evaluar = getattr(reglas, f"evaluate_{tecnica}")
    for frontal in range(60, 181, 5):
        for trasera in range(60, 181, 5):
            correcto, _, _ = evaluar(frontal, trasera)
            esperado = (reglas.dentro(frontal, tecnica, "rodilla_frontal")
                        and reglas.dentro(trasera, tecnica, "rodilla_trasera"))
            assert correcto == esperado, (tecnica, frontal, trasera)


# ---------------- el sentido sigue al criterio vigente ----------------

def test_el_sentido_sale_del_rango_vigente_y_no_de_numeros_fijos():
    """
    Los umbrales son datos versionados. Si el cuerpo técnico recalibra el
    Zenkutsu para exigir la delantera entre 120 y 130, una delantera a 125 pasa
    a ser correcta y una a 110 pasa a pedir «extiende», no «flexiona».
    """
    recalibrado = KarateRules({
        ("zenkutsu_dachi", "rodilla_frontal"): {
            "valor_min": 120.0, "valor_max": 130.0, "id_umbral": 99},
    })

    assert recalibrado.evaluate_zenkutsu_dachi(125, 170)[0] is True
    assert recalibrado.evaluate_zenkutsu_dachi(110, 170)[1] == kb.EXTIENDE_DELANTERA


# ---------------- y llega traducido al panel ----------------

def test_todo_veredicto_por_rodilla_esta_declarado():
    """
    Guarda de la guarda. `sin_traduccion()` lee los veredictos declarados, así
    que uno que la regla pudiera emitir sin estar en la lista escaparía a la
    comprobación. Se recorre la rejilla y se contrasta.
    """
    reglas = KarateRules()
    emitidos = set()
    for tecnica in ("zenkutsu_dachi", "kokutsu_dachi"):
        evaluar = getattr(reglas, f"evaluate_{tecnica}")
        for frontal in range(60, 181, 5):
            for trasera in range(60, 181, 5):
                correcto, mensaje, _ = evaluar(frontal, trasera)
                if not correcto:
                    emitidos.add(mensaje)

    assert emitidos == set(kb.VEREDICTOS_POR_RODILLA)


def test_ningun_veredicto_por_rodilla_queda_sin_correccion():
    assert sin_traduccion() == []
    for veredicto in kb.VEREDICTOS_POR_RODILLA:
        assert veredicto in CORRECCIONES, veredicto


def test_el_panel_recibe_la_correccion_con_el_prefijo_de_postura():
    """Con el prefijo que pone el analizador, que es lo que el panel recibe."""
    instruccion, motivo = traducir(f"ZENKUTSU (IZQ ADELANTE): {kb.EXTIENDE_TRASERA}")

    # En lenguaje de dojo se dice «la pierna de atrás», no «la rodilla trasera».
    assert "atrás" in instruccion
    assert motivo is not None
