"""
Pruebas de la deducción de guardia (qué pierna va adelante).

Corren en las unitarias —y por tanto también en integración continua, sin
cámara ni entorno gráfico— porque `expert_system/guardia.py` es geometría pura
sobre números: no importa MediaPipe ni OpenCV.

Lo que aquí se verifica no es un detalle de implementación. Zenkutsu Dachi y
Kokutsu Dachi son la misma postura con las piernas intercambiadas, así que la
guardia es lo ÚNICO que las distingue: equivocarla no produce un «no
reconocido», produce la otra postura con veredicto positivo, que entra a la
base de datos y contamina el historial del alumno.

Convenio de coordenadas en todo el módulo: cada punto es `(x, z)` en el plano
horizontal, con la x de la imagen y la z de profundidad de MediaPipe, donde
**menor z = más cerca de la cámara**.
"""
import pytest

from expert_system.guardia import (DER_ADELANTE, IZQ_ADELANTE,
                                   SEPARACION_MINIMA_EN_CADERAS,
                                   eje_sagital, orientacion_frente_a_camara,
                                   pierna_adelantada, separacion_sagital)
from reporte.plantilla import Paso as PasoFicha, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

# Persona de frente a la cámara: las dos caderas se separan solo en x.
CADERA_IZQ_DE_FRENTE = (0.58, 0.0)
CADERA_DER_DE_FRENTE = (0.42, 0.0)
ANCHO_DE_CADERA = 0.16

# La misma persona vista de perfil: ahora las caderas se separan en
# profundidad y casi nada en x, que es justo el caso inverso.
CADERA_IZQ_DE_PERFIL = (0.50, -0.08)
CADERA_DER_DE_PERFIL = (0.50, 0.08)


# ---------------------------------------------------------------------------
# El eje sagital
# ---------------------------------------------------------------------------

def test_de_frente_el_eje_sagital_apunta_a_la_camara():
    """
    Con la persona de frente, «adelante» es hacia el sensor: z decreciente.
    Es el convenio que el sistema ya usaba, y conservarlo es lo que permite
    que este módulo sustituya al cálculo anterior sin invertir ningún
    veredicto ya registrado.
    """
    eje, ancho = eje_sagital(CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE)

    assert ancho == pytest.approx(ANCHO_DE_CADERA)
    assert eje[0] == pytest.approx(0.0, abs=1e-9), "de frente no hay componente en x"
    assert eje[1] == pytest.approx(-1.0), "menor z es más cerca de la cámara"


def test_de_perfil_el_eje_sagital_pasa_a_ser_horizontal_en_la_imagen():
    """
    El punto de todo el módulo.

    De perfil, qué pie va adelante se ve en el eje X —la magnitud más fiable
    de MediaPipe— y no en la profundidad. El cálculo anterior miraba siempre
    la z, de modo que en la única toma donde la respuesta era fácil de ver
    estaba usando el peor dato disponible.
    """
    eje, _ancho = eje_sagital(CADERA_IZQ_DE_PERFIL, CADERA_DER_DE_PERFIL)

    assert abs(eje[0]) == pytest.approx(1.0), "de perfil el eje sagital vive en x"
    assert eje[1] == pytest.approx(0.0, abs=1e-9)


def test_sin_linea_de_caderas_no_hay_eje():
    """Dos caderas en el mismo punto no definen ninguna dirección."""
    eje, ancho = eje_sagital((0.5, 0.0), (0.5, 0.0))

    assert eje is None and ancho == 0.0


# ---------------------------------------------------------------------------
# La separación, y por qué se mide en anchos de cadera
# ---------------------------------------------------------------------------

def test_la_separacion_no_depende_de_la_distancia_a_la_camara():
    """
    Un mismo Zenkutsu grabado de cerca y de lejos tiene que dar el mismo
    número. Por eso la separación se divide entre el ancho de caderas de la
    propia persona en vez de expresarse en unidades normalizadas de MediaPipe:
    un umbral absoluto significaría cosas distintas según a qué distancia del
    sensor esté el ejecutante, y habría que recalibrarlo en cada dojo.
    """
    cerca = separacion_sagital(CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE,
                               (0.58, -0.16), (0.42, 0.16))

    # La misma postura a media distancia: todo el cuerpo a la mitad de escala.
    lejos = separacion_sagital((0.54, 0.0), (0.46, 0.0),
                               (0.54, -0.08), (0.46, 0.08))

    assert cerca == pytest.approx(lejos)


def test_el_signo_dice_cual_pierna_va_adelante():
    adelante_la_izquierda = separacion_sagital(
        CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE, (0.58, -0.3), (0.42, 0.3))
    adelante_la_derecha = separacion_sagital(
        CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE, (0.58, 0.3), (0.42, -0.3))

    assert adelante_la_izquierda > 0
    assert adelante_la_derecha < 0
    assert pierna_adelantada(adelante_la_izquierda) == IZQ_ADELANTE
    assert pierna_adelantada(adelante_la_derecha) == DER_ADELANTE


# ---------------------------------------------------------------------------
# La abstención — el caso que motivó el módulo
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-050",
    nombre="Sin separación suficiente entre los tobillos, el sistema no afirma qué "
           "pierna va adelante en lugar de elegir una",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="Zenkutsu Dachi y Kokutsu Dachi son la misma postura con las "
                         "piernas intercambiadas, de modo que la guardia es lo único que "
                         "las distingue. El cálculo anterior decidía por el signo de una "
                         "resta, sin zona muerta, así que el ruido de la estimación de "
                         "profundidad bastaba para reportar un Zenkutsu como Kokutsu "
                         "CON VEREDICTO POSITIVO: la medición se guardaba con la técnica "
                         "equivocada y contaminaba el historial y la gráfica de evolución "
                         "del alumno. Es el único defecto conocido que corrompe datos en "
                         "vez de limitarse a fallar",
    componente="expert_system/guardia.py (pierna_adelantada, separacion_sagital)",
    requisitos="RF-03, RF-08",
    precondiciones="Ninguna: el módulo es geometría pura sin dependencias gráficas",
    datos_entrada="Posiciones (x, z) de caderas y tobillos con separaciones sagitales "
                  "de 0,0, de justo por debajo del mínimo y de muy por encima",
    pasos=[
        PasoFicha("Medir la separación con los dos tobillos a la misma profundidad",
                  "assert separacion == 0 y pierna_adelantada(...) is None"),
        PasoFicha("Medir con una separación por debajo del mínimo exigido",
                  "assert pierna_adelantada(...) is None: el sistema se abstiene"),
        PasoFicha("Medir con la separación propia de una postura adelantada real",
                  "assert pierna_adelantada(...) == IZQ_ADELANTE, de modo que la "
                  "abstención anterior no se deba a un comprobador que nunca decide"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_sin_separacion_suficiente_la_guardia_queda_sin_definir():
    """
    `None` no es un fallo: es la respuesta correcta.

    Es el mismo criterio que ya gobierna el veredicto ternario del proyecto —
    la interfaz no muestra lo que el sistema no mide—, aplicado a una decisión
    que hasta ahora se tomaba siempre, tuviera o no fundamento.
    """
    pies_juntos = separacion_sagital(CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE,
                                     (0.58, 0.0), (0.42, 0.0))
    assert pies_juntos == pytest.approx(0.0)
    assert pierna_adelantada(pies_juntos) is None

    # Justo por debajo del mínimo: el ruido de la profundidad vive aquí.
    apenas = (SEPARACION_MINIMA_EN_CADERAS - 0.01) * ANCHO_DE_CADERA
    casi_nada = separacion_sagital(CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE,
                                   (0.58, -apenas), (0.42, 0.0))
    assert pierna_adelantada(casi_nada) is None

    # Y una postura adelantada de verdad SÍ se decide, para que la abstención
    # anterior no sea la de un comprobador que nunca se pronuncia.
    real = separacion_sagital(CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE,
                              (0.58, -0.3), (0.42, 0.3))
    assert pierna_adelantada(real) == IZQ_ADELANTE


def test_la_abstencion_es_simetrica():
    """Da igual hacia qué lado apunte la duda: si es pequeña, no se afirma."""
    minimo = SEPARACION_MINIMA_EN_CADERAS
    assert pierna_adelantada(minimo * 0.99) is None
    assert pierna_adelantada(-minimo * 0.99) is None
    assert pierna_adelantada(minimo * 1.01) == IZQ_ADELANTE
    assert pierna_adelantada(-minimo * 1.01) == DER_ADELANTE


# ---------------------------------------------------------------------------
# El aviso de plano
# ---------------------------------------------------------------------------

def test_la_orientacion_distingue_la_toma_frontal_de_la_de_perfil():
    """
    Sirve para avisar ANTES de medir que la toma no corresponde al plano de la
    técnica. Medido sobre la proyección: un codo realmente extendido a 175°
    lanzado hacia la cámara se proyecta como 90° y se informa como flexionado,
    porque la proyección 2D arrastra todo ángulo hacia 90° conforme el
    segmento apunta al sensor.
    """
    assert orientacion_frente_a_camara(
        CADERA_IZQ_DE_FRENTE, CADERA_DER_DE_FRENTE) == pytest.approx(1.0)
    assert orientacion_frente_a_camara(
        CADERA_IZQ_DE_PERFIL, CADERA_DER_DE_PERFIL) == pytest.approx(0.0, abs=1e-9)


def test_sin_caderas_utilizables_se_supone_la_toma_mas_desfavorable():
    """Sin información, el supuesto conservador es el que más avisa."""
    assert orientacion_frente_a_camara((0.5, 0.0), (0.5, 0.0)) == 1.0
