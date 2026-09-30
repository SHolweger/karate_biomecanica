"""
Pruebas de la herramienta que mide la velocidad de los Tsuki.

La lógica es pura —recibe series de (t, ángulo)— así que corre en los dos
entornos. Lo que se protege es que la herramienta sirva para DECIDIR: si contara
mal los golpes, o si el barrido de umbrales no reflejara lo que hace la máquina
real, el número que salga de aquí acabaría en la tesis siendo falso.

Y una cosa más, que es la que motivó el módulo: aquí se reproduce lo que
Sebastián observó en vivo el 30-sep-2026 —que un Tsuki lento no se reconoce— y
se comprueba que recoger el brazo NO produce veredicto.
"""
import pytest

from expert_system.tsuki import RECORRIDO_MINIMO, VENTANA_RECORRIDO_MS
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from revisar_tsuki import (barrido, golpes_detectados, percentiles,
                           velocidad_implicada, velocidades_angulares)

pytestmark = pytest.mark.unitaria


def _rampa(desde, hasta, duracion_ms, t0=0, paso_ms=33):
    """Una extensión lineal del codo, de `desde` a `hasta`, en `duracion_ms`."""
    pasos = max(int(duracion_ms / paso_ms), 1)
    return [(t0 + i * paso_ms, desde + (hasta - desde) * i / pasos)
            for i in range(pasos + 1)]


def _quieto(grados, duracion_ms, t0=0, paso_ms=33):
    return [(t0 + i * paso_ms, grados) for i in range(int(duracion_ms / paso_ms) + 1)]


def _golpe(desde=50, hasta=172, subida_ms=200, t0=0):
    """Hikite -> extensión -> recogida, con una pausa a cada lado."""
    serie = _quieto(desde, 300, t0=t0)
    fin_reposo = serie[-1][0] + 33
    subida = _rampa(desde, hasta, subida_ms, t0=fin_reposo)
    fin_subida = subida[-1][0] + 33
    bajada = _rampa(hasta, desde, subida_ms, t0=fin_subida)
    return serie + subida + bajada


@ficha(
    id_caso="TC-AUTO-061",
    nombre="La herramienta reconoce el Tsuki rapido, no el lento, y ninguno al recoger",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="los dos umbrales del Tsuki (35 grados en 500 ms) salieron de "
                         "la definicion de la tecnica y no de una medicion, y gobiernan "
                         "que se registra. Probando en vivo el 30-sep-2026 aparecio que "
                         "un Tsuki lento no se reconoce --coherente con exigir 70 "
                         "grados/s-- y la sospecha de que recoger el brazo encendia el "
                         "veredicto, que si seria un defecto. Esta herramienta es la que "
                         "va a fijar los numeros con datos reales, asi que si ella "
                         "cuenta mal, el error pasa directo a la tesis",
    componente="revisar_tsuki.py sobre expert_system/tsuki.py",
    requisitos="RF-03, RF-07",
    precondiciones="Ninguna: la logica es pura y no abre video ni base de datos",
    datos_entrada="Series sinteticas de angulo de codo con marca de tiempo: un Tsuki "
                  "rapido (122 grados en 200 ms), uno lento (los mismos grados en "
                  "3 segundos) y una recogida sin golpe previo",
    pasos=[
        Paso("Pasar un Tsuki rapido por la herramienta",
             "assert reconoce exactamente un golpe, y reporta de que angulo salio, "
             "a cual llego y a que velocidad"),
        Paso("Pasar el mismo recorrido repartido en tres segundos",
             "assert NO lo reconoce con el umbral vigente, que es lo observado en "
             "vivo, y el barrido muestra con que umbral si aparecería"),
        Paso("Pasar una recogida del brazo, sin extension previa",
             "assert no se reconoce ningun golpe: la maquina solo dispara al abrir "
             "el codo"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz grafica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_reconoce_el_golpe_rapido_y_no_el_lento_ni_la_recogida():
    rapidos = golpes_detectados(_golpe(subida_ms=200), brazo="izq")
    assert len(rapidos) == 1, "un Tsuki de 122 grados en 200 ms tiene que reconocerse"
    assert rapidos[0].pico == pytest.approx(172, abs=1)
    assert rapidos[0].velocidad > 450, "la velocidad reportada describe el golpe"

    lentos = golpes_detectados(_golpe(subida_ms=3000), brazo="izq")
    assert lentos == [], (
        "con el umbral vigente un Tsuki de tres segundos NO se reconoce: es lo que "
        "se observo en vivo, y sale de exigir 70 grados por segundo")

    # Y con una ventana mas larga si aparece. Es lo que el barrido pone a la vista.
    assert len(golpes_detectados(_golpe(subida_ms=3000), recorrido_minimo=20,
                                 ventana_ms=1000, brazo="izq")) == 1

    # Recoger el brazo, sin ninguna extension previa.
    recogida = _quieto(172, 600) + _rampa(172, 50, 400, t0=633)
    assert golpes_detectados(recogida, brazo="izq") == [], (
        "la maquina solo dispara al ABRIR el codo; recogerlo no es un golpe")


def test_estar_quieto_no_produce_ningun_golpe():
    """La regresión de siempre, ahora vista desde la herramienta."""
    assert golpes_detectados(_quieto(175, 5000), brazo="der") == []


def test_dos_golpes_seguidos_se_listan_por_separado():
    """
    Si los fundiera en uno, el contraste con «cuántos hiciste» mentiría en la
    dirección más difícil de notar: hacia abajo.
    """
    serie = _golpe(t0=0)
    serie += _golpe(t0=serie[-1][0] + 33)

    assert len(golpes_detectados(serie, brazo="izq")) == 2


def test_el_barrido_refleja_lo_que_hace_la_maquina_real():
    """
    El barrido tiene que usar la MISMA máquina del sistema, no una copia. Si
    divergieran, elegir umbrales con esta tabla sería elegirlos para otro
    programa.
    """
    serie = _golpe(subida_ms=800)
    tabla = barrido(serie, [(35, 500), (20, 1000)])

    assert tabla[(35, 500)] == len(golpes_detectados(serie, 35, 500))
    assert tabla[(20, 1000)] == len(golpes_detectados(serie, 20, 1000))
    assert tabla[(20, 1000)] >= tabla[(35, 500)], \
        "un criterio mas permisivo no puede reconocer MENOS golpes"


def test_la_velocidad_implicada_es_la_que_gobierna_de_verdad():
    """
    Los dos umbrales no son independientes: juntos son una velocidad, y esa es
    la cifra que hay que poder defender ante la terna. La herramienta la imprime
    para que no haya que deducirla.
    """
    assert velocidad_implicada(RECORRIDO_MINIMO, VENTANA_RECORRIDO_MS) == pytest.approx(70)
    assert velocidad_implicada(20, 1000) == pytest.approx(20)


def test_la_velocidad_angular_no_depende_de_los_fotogramas_por_segundo():
    """
    La misma extensión muestreada a 30 y a 60 fps tiene que dar la misma
    velocidad. Medirla por fotograma haría que la cifra describiera el equipo
    que analiza y no al ejecutante — el mismo error que se corrigió el 28-sep en
    `test_rendimiento.py`.
    """
    a_30 = velocidades_angulares(_rampa(50, 170, 400, paso_ms=33))
    a_60 = velocidades_angulares(_rampa(50, 170, 400, paso_ms=16))

    assert percentiles(a_30)[50] == pytest.approx(percentiles(a_60)[50], rel=0.1)


def test_sin_muestras_los_percentiles_no_inventan_un_cero():
    """Mismo criterio que el resto del sistema: lo que no se mide no vale cero."""
    assert percentiles([]) == {}
    assert velocidades_angulares([(0, 90.0)]) == []


def test_el_golpe_se_mide_desde_el_hikite_y_no_desde_donde_disparo():
    """
    Regresión de un error que solo se vio ejecutando la herramienta.

    Cuando la máquina dispara, el codo ya se abrió `RECORRIDO_MINIMO` grados.
    Tomar ESE fotograma como punto de partida subestima el recorrido y, con él,
    la velocidad: sobre un golpe de 50° a 172° en 198 ms —616°/s— la primera
    versión informaba «de 90,7° a 172°, 411°/s». Un 33 % por debajo, en la
    única cifra para la que existe la herramienta.
    """
    golpes = golpes_detectados(_golpe(desde=50, hasta=172, subida_ms=200), brazo="izq")

    assert len(golpes) == 1
    assert golpes[0].desde == pytest.approx(50, abs=2), \
        "el golpe sale del Hikite, no del punto en que la maquina se entero"
    assert golpes[0].velocidad > 450, \
        "122 grados en 200 ms rondan los 600 grados/s, no 410 ni 205"


def test_el_arranque_no_lo_recorta_la_ventana_de_deteccion():
    """
    Regresión encontrada sobre grabación real el 30-sep-2026.

    Detectar el golpe y medirlo son dos cosas. La ventana dura lo que necesita
    la DETECCIÓN; usarla también para medir recortaba el arranque, porque para
    cuando la máquina dispara, el fondo de la flexión ya salió de la ventana.
    Sobre el video de Sebastián los cuatro golpes salían de 81°, 94°, 105° y
    118° — ninguno del Hikite — y con ellos el recorrido y la velocidad iban
    subestimados.

    Aquí el golpe dura 900 ms, muy por encima de la ventana de 500, y aun así
    tiene que reportarse desde donde de verdad empezó.
    """
    subida = _rampa(45, 170, 900, t0=633)
    # La recogida hace falta: el Kime se cierra cuando el brazo vuelve.
    lento = _quieto(45, 600) + subida + _rampa(170, 45, 400, t0=subida[-1][0] + 33)

    golpes = golpes_detectados(lento, brazo="izq")

    assert len(golpes) == 1
    assert golpes[0].desde == pytest.approx(45, abs=6), \
        "el arranque sale de la serie, no de la ventana de deteccion"
    assert golpes[0].recorrido > 100, \
        "un recorrido de 125 grados no puede reportarse como 60"
