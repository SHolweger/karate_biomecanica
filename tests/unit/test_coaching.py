"""
Pruebas de la traducción de veredictos a correcciones de entrenamiento (RF-06).

El requisito pide retroalimentación útil durante la ejecución. «TSUKI:
HIPEREXTENDIDO (Peligro)» es un veredicto correcto y, como instrucción para un
alumno de trece años, inservible. Lo que se fija aquí es que cada veredicto que
el motor puede emitir tenga su frase de dojo, y que el texto técnico siga siendo
el que se guarda — porque es la clave con la que la base agrupa los errores
frecuentes de una sesión, y cambiarlo partiría el historial en dos.
"""
import pytest

from gui.coaching import CORRECCIONES, separar_lado, sin_traduccion, traducir
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@ficha(
    id_caso="TC-AUTO-034",
    nombre="Todo veredicto que la base de conocimientos puede emitir tiene su corrección "
           "redactada para el alumno",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="el panel de correcciones es la forma en que el sistema cumple el "
                         "RF-06; si se agrega una regla nueva y se olvida su traducción, la "
                         "pantalla no falla —muestra el texto técnico— y el descuido pasa "
                         "inadvertido hasta que un instructor lee «MAE GERI: KIME INCOMPLETO» "
                         "en medio de una clase y tiene que interpretarlo él",
    componente="gui/coaching.py (CORRECCIONES) + expert_system/knowledge_base.py",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna; se inspecciona el código fuente de la base de conocimientos",
    datos_entrada="Los veredictos que `knowledge_base.py` devuelve en sus sentencias `return`",
    pasos=[
        Paso("Extraer de la base de conocimientos todos los veredictos que puede emitir",
             "assert la lista no viene vacía (si lo estuviera, la prueba no probaría nada)"),
        Paso("Restarle los veredictos que la tabla de correcciones cubre",
             "assert el conjunto resultante está vacío"),
    ],
    resultado_esperado="PASSED. Cada veredicto llega al alumno como una instrucción y no como "
                       "lenguaje de máquina.",
    evidencia="Reporte de consola de pytest.",
)
def test_ningun_veredicto_del_motor_se_queda_sin_correccion():
    faltantes = sin_traduccion()

    assert faltantes == [], (
        f"estos veredictos llegarían al panel en lenguaje técnico: {faltantes}. "
        "Agrega su corrección en gui/coaching.py")


def test_la_tabla_no_esta_vacia():
    """Guarda contra un `sin_traduccion()` que devuelva vacío por no leer nada."""
    assert len(CORRECCIONES) >= 15


def test_la_correccion_dice_que_hacer_y_por_que():
    instruccion, motivo = traducir("TSUKI: HIPEREXTENDIDO (Peligro)")

    assert instruccion == "No bloquees el codo al impacto"
    assert "lesiona" in motivo, "el porqué es lo que hace que el alumno lo corrija sin vigilancia"


@pytest.mark.parametrize("mensaje, lado_esperado", [
    ("IZQ - TSUKI: EXCELENTE", "izquierdo"),
    ("DER - TSUKI: EXCELENTE", "derecho"),
    ("POSTURA: FIRME", None),
])
def test_el_lado_se_separa_del_veredicto(mensaje, lado_esperado):
    veredicto, lado = separar_lado(mensaje)

    assert lado == lado_esperado
    assert not veredicto.startswith(("IZQ", "DER"))


def test_el_lado_aparece_en_la_instruccion():
    """
    Sin el lado, "extiende más el brazo" deja al alumno sin saber cuál. El
    analizador evalúa los dos brazos por separado justamente para poder decirlo.
    """
    instruccion, _ = traducir("DER - TSUKI: FLEXIONADO")

    assert "derecho" in instruccion


def test_un_veredicto_desconocido_se_muestra_tal_cual_en_vez_de_inventar_consejo():
    """
    Si mañana se agrega una regla y se olvida su traducción, el panel debe
    mostrar el texto técnico —feo pero cierto— y no un consejo que la regla no
    respalda. La prueba anterior es la que impide que eso se quede así.
    """
    instruccion, motivo = traducir("TECNICA NUEVA: ALGO")

    assert instruccion == "TECNICA NUEVA: ALGO"
    assert motivo is None


def test_un_mensaje_vacio_no_revienta():
    assert traducir("") == ("", None)
    assert traducir(None) == ("", None)
