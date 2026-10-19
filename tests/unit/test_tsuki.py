"""
Pruebas de la máquina que decide cuándo hay un Tsuki que juzgar.

Corren en las unitarias porque `expert_system/tsuki.py` es puro: recibe un
ángulo y una marca de tiempo, y no sabe de MediaPipe, píxeles ni base de datos.

Lo que aquí se protege no es que el veredicto sea acertado —de eso se ocupa
`KarateRules.evaluate_tsuki`— sino algo anterior y más importante: que el
sistema **no califique un golpe que nadie dio**. Ese fallo no se nota mirando
la pantalla durante una ejecución correcta, porque cuando el alumno golpea de
verdad el veredicto es el mismo; se nota en el historial, semanas después,
cuando la precisión del alumno la dominan los minutos que pasó de pie.
"""
import random

import pytest

from expert_system.tsuki import (EN_EXTENSION, RECORRIDO_MINIMO, SIN_GOLPE, diferencia_angular,
                                 TsukiStateMachine, VENTANA_RECORRIDO_MS)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

# Cadencia de los fotogramas sintéticos. 33 ms es el intervalo que produce una
# cámara de 30 fps, que es a lo que corre el bucle real.
MS_POR_FOTOGRAMA = 33


def _reproducir(maquina, angulos, t0=0, paso=MS_POR_FOTOGRAMA):
    """Pasa una secuencia de ángulos por la máquina y devuelve los diagnósticos."""
    return [maquina.update(angulo, t0 + i * paso)
            for i, angulo in enumerate(angulos)]


def _veredictos(diagnosticos):
    """
    Los veredictos cerrados tal y como los cuenta la base de datos.

    Se descartan las repeticiones consecutivas del mismo mensaje porque la
    máquina sostiene el veredicto en pantalla mientras el brazo se recoge —igual
    que hace la del Mae Geri mientras la pierna se asienta— y `MedicionLogger`
    solo escribe cuando el mensaje de una categoría CAMBIA. Contar fotogramas
    en vez de cambios mediría la persistencia del texto, no los golpes.
    """
    cerrados, anterior = [], None
    for d in diagnosticos:
        if d["mensaje"] != anterior and d["correcto"] is not None:
            cerrados.append(d)
        anterior = d["mensaje"]
    return cerrados


def _brazo_quieto(grados, fotogramas=90):
    """
    Un brazo colgando al costado, con el temblor que deja el filtro.

    Los grados se toman de la prueba en vivo del 30-sep-2026: de pie, la
    pantalla medía el codo izquierdo entre 164 y 179°. El vaivén de ±2° cruza
    a propósito el límite de 175° del rango de evaluación, que es lo que hacía
    alternar «EXCELENTE» e «HIPEREXTENDIDO» y escribir una fila en cada cruce.
    """
    return [grados + (2 if i % 2 else -2) for i in range(fotogramas)]


def _un_golpe(desde=50.0, hasta=172.0, fotogramas_extension=6):
    """
    Un Tsuki completo: Hikite (puño en la cadera) -> extensión -> recogida.

    Seis fotogramas de extensión son unos 200 ms a 30 fps, que es lo que dura
    un Tsuki según la literatura que ya usa el proyecto para el Mae Geri.
    """
    subida = [desde + (hasta - desde) * (i + 1) / fotogramas_extension
              for i in range(fotogramas_extension)]
    bajada = list(reversed(subida))[1:]
    return [desde] * 5 + subida + bajada + [desde] * 5


# ---------------------------------------------------------------------------
# La regresión
# ---------------------------------------------------------------------------

@ficha(
    id_caso="TC-AUTO-056",
    nombre="Un brazo en reposo no produce veredicto de Tsuki, y un golpe produce "
           "exactamente uno",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="hasta el 30-sep-2026 el codo se evaluaba en cada fotograma "
                         "en que el brazo se viera, sin comprobar antes que hubiera un "
                         "golpe. Como el rango de evaluación del Tsuki es 160-175 grados "
                         "y un brazo colgando al costado mide entre 160 y 180, una "
                         "persona de pie recibía veredictos de Tsuki: EXCELENTE mientras "
                         "el ángulo quedaba dentro e HIPEREXTENDIDO (Peligro) al "
                         "cruzarlo. Esas filas entraban a la base con tecnica='tsuki' y "
                         "veredicto cerrado, de modo que contaminaban la precisión del "
                         "alumno, su gráfica de evolución y el informe de prevención de "
                         "lesiones, que cuenta hiperextensiones para advertir de bloqueo "
                         "articular. Es un fallo que corrompe datos en vez de limitarse "
                         "a fallar, del mismo tipo que el de la guardia del 28-sep",
    componente="expert_system/tsuki.py (TsukiStateMachine)",
    requisitos="RF-03, RF-07, RF-08",
    precondiciones="Ninguna: el módulo no importa MediaPipe, OpenCV ni sqlite3, y la "
                   "máquina se construye con los umbrales de literatura si no se le "
                   "pasa base de conocimientos",
    datos_entrada="Dos secuencias de ángulos de codo con marca de tiempo: un brazo "
                  "quieto a 164-179 grados durante tres segundos (las cifras medidas "
                  "en la prueba en vivo del 30-sep) y un Tsuki completo desde Hikite",
    pasos=[
        Paso("Reproducir tres segundos de brazo quieto cruzando el límite de 175 grados",
             "assert no se emite ningún veredicto cerrado: `correcto` es None en los "
             "noventa fotogramas, y el mensaje es el de abstención"),
        Paso("Reproducir un Tsuki completo (Hikite -> extensión -> recogida)",
             "assert se emite exactamente UN veredicto cerrado, no uno por fotograma"),
        Paso("Comprobar con qué ángulo se juzgó ese veredicto",
             "assert se juzgó con el máximo de la extensión (el Kime) y no con el "
             "ángulo del fotograma en que el brazo ya venía de vuelta"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_un_brazo_en_reposo_no_produce_veredicto_de_tsuki():
    maquina = TsukiStateMachine()

    quieto = _veredictos(_reproducir(maquina, _brazo_quieto(175)))
    assert quieto == [], (
        "un brazo colgando al costado no es un Tsuki y no puede calificarse como tal")

    maquina = TsukiStateMachine()
    diagnosticos = _reproducir(maquina, _un_golpe(hasta=172.0))
    veredictos = _veredictos(diagnosticos)

    assert len(veredictos) == 1, "un golpe, un veredicto"
    assert veredictos[0]["correcto"] is True
    assert veredictos[0]["angulos_regla"] == (172.0,), (
        "se juzga el ángulo del Kime, no el del fotograma en que el brazo vuelve")


def test_el_brazo_quieto_lo_dice_en_vez_de_callarse():
    """
    La abstención es informativa, no silencio. El sensei tiene que poder
    distinguir «no estás golpeando» de «el sistema se colgó», que es la misma
    razón por la que la postura dice «GUARDIA INDEFINIDA» en vez de no dibujar
    nada.
    """
    diagnosticos = _reproducir(TsukiStateMachine(), _brazo_quieto(170, fotogramas=10))

    assert all(d["mensaje"] == SIN_GOLPE for d in diagnosticos)


def test_el_angulo_se_informa_aunque_no_haya_veredicto():
    """
    El codo SÍ está medido; lo que falta es la técnica. El panel tiene que
    seguir mostrando los grados —es una medición legítima— y lo único que no
    puede hacer es llamarlos Tsuki.
    """
    diagnosticos = _reproducir(TsukiStateMachine(), [168.0, 169.0, 168.0])

    assert [d["angulo"] for d in diagnosticos] == [168.0, 169.0, 168.0]
    assert all(d["correcto"] is None and d["tecnica"] is None for d in diagnosticos)


# ---------------------------------------------------------------------------
# El golpe
# ---------------------------------------------------------------------------

def test_dos_golpes_seguidos_se_cuentan_como_dos():
    """
    El contrario del caso anterior: abstenerse no puede costar repeticiones
    reales. Si la máquina se quedara enganchada tras el primer golpe, el alumno
    entrenaría una serie completa y el historial registraría una sola.
    """
    maquina = TsukiStateMachine()
    secuencia = _un_golpe() + _un_golpe()

    assert len(_veredictos(_reproducir(maquina, secuencia))) == 2


def test_un_golpe_hiperextendido_se_sigue_detectando():
    """
    La prevención de lesiones depende de esto: la abstención no puede tragarse
    justo el veredicto que importa. Un golpe que bloquea el codo se cuenta.
    """
    veredictos = _veredictos(_reproducir(TsukiStateMachine(), _un_golpe(hasta=179.0)))

    assert len(veredictos) == 1
    assert veredictos[0]["correcto"] is False
    assert "HIPEREXTENDIDO" in veredictos[0]["mensaje"]


def test_el_brazo_que_se_queda_extendido_se_juzga_igual():
    """
    A diferencia del Mae Geri —donde sostener la pierna en el aire descarta el
    intento— aquí el golpe ya ocurrió. No recoger el puño es una observación
    sobre el Hikite, no motivo para no evaluar el Kime.
    """
    secuencia = [50.0] * 5 + [70.0, 100.0, 130.0, 160.0, 172.0] + [172.0] * 60

    veredictos = _veredictos(_reproducir(TsukiStateMachine(), secuencia))

    assert len(veredictos) == 1, "el golpe sostenido se juzga una vez, no en cada fotograma"


def test_una_extension_lenta_no_es_un_golpe():
    """
    Levantar el brazo despacio recorre los mismos grados que un Tsuki. Lo que
    los separa es el tiempo, y por eso el recorrido se mide sobre una ventana
    de milisegundos y no sobre los últimos N fotogramas.
    """
    lenta = [50.0 + i for i in range(126)]   # 50° -> 175° en 126 fotogramas (~4,2 s)

    assert _veredictos(_reproducir(TsukiStateMachine(), lenta)) == []


def test_entrar_en_cuadro_con_el_brazo_extendido_no_es_un_golpe():
    """
    Sin historia no se puede afirmar que haya habido recorrido. Suponer que sí
    produciría un golpe fantasma cada vez que el alumno entra en cuadro, que es
    exactamente el primer fotograma de cualquier grabación casera.
    """
    diagnosticos = _reproducir(TsukiStateMachine(), [174.0, 174.0, 175.0])

    assert _veredictos(diagnosticos) == []


def test_reiniciar_descarta_el_golpe_visto_a_medias():
    """
    Lo llama el analizador cuando el brazo sale de cuadro. Un golpe del que
    solo se vio la mitad no se juzga con esa mitad: se descarta.
    """
    maquina = TsukiStateMachine()
    _reproducir(maquina, [50.0] * 5 + [70.0, 100.0, 130.0])   # a media extensión
    maquina.reset()

    # Tras el reinicio, el brazo reaparece ya extendido: sin historia previa no
    # hay recorrido que medir, así que no se inventa un golpe.
    assert _veredictos(_reproducir(maquina, [172.0] * 10, t0=5000)) == []


# ---------------------------------------------------------------------------
# La guarda del criterio
# ---------------------------------------------------------------------------

def test_el_recorrido_minimo_separa_el_reposo_del_golpe_con_holgura():
    """
    Fija la razón por la que el umbral no es delicado, que es lo que permite
    declararlo provisional sin que el sistema dependa de acertarlo.

    Un brazo quieto recorre lo que tiembla el filtro, unos pocos grados. Un
    Tsuki desde Hikite recorre más de cien, y hasta un Kizami Tsuki desde kamae
    recorre unos cuarenta. El corte vive en un hueco ancho, igual que la
    separación en anchos de cadera de `guardia.py`.
    """
    temblor = max(_brazo_quieto(175)) - min(_brazo_quieto(175))
    kizami = 175.0 - 130.0

    assert temblor < RECORRIDO_MINIMO < kizami


def test_la_ventana_cubre_la_extension_mas_lenta_de_un_golpe():
    """
    Si la ventana fuera más corta que la extensión, el mínimo se desplazaría
    dentro del propio golpe: el recorrido medido sería un tramo y no el viaje
    completo desde el Hikite. Un Tsuki extiende el codo en 150-250 ms.
    """
    assert VENTANA_RECORRIDO_MS >= 250


def test_la_velocidad_minima_implicada_deja_fuera_el_gesto_y_dentro_el_golpe():
    """
    El par (recorrido, ventana) equivale a exigir una velocidad mínima, y es esa
    cifra la que hay que poder defender ante la terna, no los dos números
    sueltos. Un Tsuki extiende unos 125° en 150-250 ms —entre 500 y 800°/s—
    mientras que levantar el brazo sin intención de golpear ronda los 60°/s.

    La prueba fija que el corte cae claramente entre ambos. Es lo que permite
    declarar los umbrales provisionales sin que el sistema dependa de acertar
    el número exacto: hay casi un orden de magnitud de margen.
    """
    grados_por_segundo = RECORRIDO_MINIMO / (VENTANA_RECORRIDO_MS / 1000)
    tsuki_mas_lento = 125 / 0.250

    assert 60 < grados_por_segundo < tsuki_mas_lento / 4


# ---------------------------------------------------------------------------
# El veredicto mientras el brazo sostiene el Kime (18-oct-2026)
# ---------------------------------------------------------------------------
#
# Hasta esta fecha la máquina salía de RECOGIENDO por dos caminos: el brazo
# recogía, o la ventana de 500 ms dejaba de ver recorrido. El segundo es el que
# se dispara cuando el brazo se QUEDA en el Kime: la ventana se aplana, el
# recorrido cae a cero y el aviso volvía a «SIN TSUKI» con el brazo todavía
# extendido. En una demostración —donde el golpe se sostiene para que la terna
# lo vea— el texto desaparecía del video mientras la técnica seguía en pantalla.
#
# Lo que cambia es CUÁNTO SE VE el veredicto, nunca CUÁNTOS se emiten. Las
# pruebas de abajo fijan las dos mitades.

def _sostener(angulo, fotogramas):
    """El brazo quieto en el Kime, con el temblor de ±2° que deja el filtro."""
    return [angulo + (2 if i % 2 else -2) for i in range(fotogramas)]


def _golpe_sostenido(hasta=172.0, fotogramas_sostenidos=90):
    """Hikite -> extensión -> el brazo se queda arriba (90 fotogramas = 3 s)."""
    subida = [50.0 + (hasta - 50.0) * (i + 1) / 6 for i in range(6)]
    return [50.0] * 5 + subida + _sostener(hasta, fotogramas_sostenidos)


@ficha(
    id_caso="TC-AUTO-068",
    nombre="El veredicto del Tsuki sigue a la vista mientras el brazo sostiene el Kime",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "con el brazo quieto en el Kime la ventana de recorrido se aplana y el "
        "aviso volvía a «SIN TSUKI» a los 500 ms: en la demostración ante la "
        "terna, donde el golpe se sostiene para mostrarlo, el veredicto "
        "desaparecía del video con la técnica todavía en pantalla"),
    componente="expert_system/tsuki.py (TsukiStateMachine, estado RECOGIENDO)",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna. La máquina es pura y recibe ángulos sintéticos",
    datos_entrada=(
        "Un golpe de 50° a 172° sostenido 3 s con temblor de ±2°; la misma "
        "secuencia con recogida al final; dos golpes separados por sostenidos "
        "de 0 a 10 s"),
    pasos=[
        Paso("Reproducir un golpe y sostener el brazo 3 s",
             "assert diagnosticos[-1]['mensaje'] == 'TSUKI: EXCELENTE'"),
        Paso("Recoger el brazo al Hikite",
             "assert diagnosticos[-1]['mensaje'] == SIN_GOLPE"),
        Paso("Repetir dos golpes con sostenidos de distinta duración",
             "assert len(_veredictos(...)) == 2 en todos los casos"),
    ],
    resultado_esperado="PASSED: el veredicto dura lo que dura el Kime y el número de golpes no cambia",
)
def test_el_veredicto_sigue_a_la_vista_mientras_se_sostiene_el_kime():
    diagnosticos = _reproducir(TsukiStateMachine(), _golpe_sostenido())

    assert diagnosticos[-1]["mensaje"] == "TSUKI: EXCELENTE", (
        f"a los 3 s de sostener el Kime el aviso dice {diagnosticos[-1]['mensaje']!r}")


def test_al_recoger_el_brazo_el_veredicto_se_retira():
    """El veredicto acompaña al Kime, no se queda pegado después."""
    secuencia = _golpe_sostenido() + [130.0, 100.0, 70.0, 50.0] + [50.0] * 5

    assert _reproducir(TsukiStateMachine(), secuencia)[-1]["mensaje"] == SIN_GOLPE


def test_bajar_el_brazo_despacio_tambien_retira_el_veredicto():
    """
    No hace falta un Hikite enérgico: dejar caer el brazo poco a poco, que es
    lo que hace alguien al terminar de mostrar el golpe, también lo retira.
    """
    bajada_lenta = [172.0 - i for i in range(60)]   # 172° -> 113° en 2 s

    diagnosticos = _reproducir(TsukiStateMachine(), _golpe_sostenido() + bajada_lenta)

    assert diagnosticos[-1]["mensaje"] == SIN_GOLPE


@pytest.mark.parametrize("fotogramas_sostenidos", [0, 5, 15, 30, 90, 300])
def test_sostener_no_cambia_cuantos_golpes_se_cuentan(fotogramas_sostenidos):
    """
    La garantía que protege al historial: cuánto se sostiene el Kime no altera
    el número de veredictos ni su contenido. `MedicionLogger` escribe cuando el
    mensaje cambia, así que alargar la permanencia del mismo mensaje no añade
    filas.
    """
    golpe = (_golpe_sostenido(fotogramas_sostenidos=fotogramas_sostenidos)
             + [130.0, 90.0, 50.0] + [50.0] * 5)

    veredictos = _veredictos(_reproducir(TsukiStateMachine(), golpe + golpe))

    assert [v["mensaje"] for v in veredictos] == ["TSUKI: EXCELENTE"] * 2


def test_tras_sostener_se_detecta_el_golpe_siguiente_sin_volver_al_hikite():
    """
    El camino que la ventana aplanada cubría y no se puede perder: tras
    sostener, una recogida parcial —sin llegar al Hikite— seguida de otra
    extensión es un golpe nuevo.
    """
    primero = [50.0] * 5 + [70.0, 90.0, 110.0, 130.0, 150.0] + _sostener(150.0, 60)
    recogida_parcial = [145.0, 140.0, 135.0, 130.0] + [130.0] * 5
    segundo = [140.0, 150.0, 160.0, 170.0, 172.0] + [150.0, 120.0, 90.0, 60.0]

    veredictos = _veredictos(_reproducir(TsukiStateMachine(),
                                         primero + recogida_parcial + segundo))

    assert len(veredictos) == 2


# Los dos tramos reales que rompieron la primera versión del arreglo. Salen del
# generador de secuencias de la comparación contra la máquina anterior (semilla
# 20261018, secuencias 259 y 797), recortados al tramo que importa, y con la
# máquina anterior producen dos golpes cada uno — comprobado al extraerlos.

# Paso de 16 ms. Una extensión lenta que se juzga por TIEMPO_MAXIMO_EXTENSION_MS
# en torno a 127° y luego sigue subiendo, rápido, hasta 158°.
SIGUE_SUBIENDO_TRAS_JUZGARSE = [
    9.7, 4.8, 0.0, 1.0, 2.2, 3.3, 4.5, 5.6, 6.7, 7.9, 9.0, 10.2, 11.3, 12.5, 13.6,
    14.8, 15.9, 17.1, 18.2, 19.4, 20.5, 21.7, 22.8, 24.0, 25.1, 26.2, 27.4, 28.5,
    29.7, 30.8, 32.0, 33.1, 34.3, 35.4, 36.6, 37.7, 38.9, 40.0, 41.2, 42.3, 43.5,
    44.6, 45.7, 46.9, 48.0, 49.2, 50.3, 51.5, 52.6, 53.8, 54.9, 56.1, 57.2, 58.4,
    59.5, 60.7, 61.8, 63.0, 64.1, 65.3, 66.4, 67.5, 68.7, 69.8, 71.0, 72.1, 73.3,
    74.4, 75.6, 76.7, 77.9, 79.0, 80.2, 81.3, 82.5, 83.6, 84.8, 85.9, 87.0, 88.2,
    89.3, 90.5, 91.6, 92.8, 93.9, 95.1, 96.2, 97.4, 98.5, 99.7, 100.8, 102.0, 102.5,
    102.1, 102.9, 102.4, 101.4, 102.7, 101.2, 102.2, 101.3, 101.3, 101.2, 101.5,
    101.6, 102.8, 101.5, 101.5, 101.3, 101.1, 101.4, 102.4, 102.3, 101.3, 102.0,
    101.1, 101.4, 102.1, 101.8, 101.0, 101.3, 101.8, 102.8, 102.4, 108.2, 114.4,
    120.7, 126.9, 133.1, 139.4, 145.6, 151.8, 158.1, 128.4, 98.8, 69.1]

# Paso de 40 ms. Un golpe a 151°, una recogida parcial de 31° —menos que
# RECORRIDO_MINIMO— y otra extensión que atraviesa la altura del pico al subir.
RECOGIDA_PARCIAL_Y_OTRO_GOLPE = [
    51.4, 51.5, 50.0, 49.4, 47.6, 47.8, 50.5, 51.4, 51.6, 49.8, 51.4, 49.9, 50.8, 48.8,
    47.7, 51.0, 48.1, 48.1, 48.4, 49.2, 49.8, 75.2, 100.4, 125.6, 150.9, 143.1, 135.2,
    127.4, 119.6, 123.7, 127.7, 131.7, 135.8, 139.8, 143.8, 147.8, 151.9, 155.9, 159.9,
    164.0, 162.5, 165.3, 162.1, 165.4, 163.1, 162.8, 165.9, 161.9, 165.3, 163.3, 165.0,
    163.4, 162.1, 163.7, 164.9, 162.6, 162.7, 162.5, 161.8, 162.0, 161.7, 165.0, 165.3,
    165.8, 163.5, 165.2, 164.8, 165.8, 163.2, 163.5, 163.6, 163.8, 165.4, 166.4, 165.2,
    162.6, 165.9, 161.8, 162.7, 165.4]


@pytest.mark.parametrize("secuencia, paso", [
    (SIGUE_SUBIENDO_TRAS_JUZGARSE, 16),
    (RECOGIDA_PARCIAL_Y_OTRO_GOLPE, 40),
], ids=["sigue-subiendo-tras-juzgarse", "recogida-parcial-y-otro-golpe"])
def test_los_dos_casos_que_rompieron_la_primera_version(secuencia, paso):
    """
    Una primera versión de este arreglo cambiaba la condición de salida de
    RECOGIENDO y perdía el segundo golpe en estos dos tramos: leía como
    «sostener» una extensión que seguía subiendo y una que volvía a pasar por la
    altura del pico. Pasar por la altura del Kime no es sostenerlo.
    """
    assert len(_veredictos(_reproducir(TsukiStateMachine(), secuencia, paso=paso))) == 2


def _secuencia_aleatoria(rng):
    """Golpes, sostenidos, recogidas completas y parciales, extensiones lentas y temblor."""
    a, out = 50.0, []
    for _ in range(rng.randint(3, 10)):
        accion = rng.choice(["golpe", "sostener", "recoger", "parcial", "lento"])
        if accion == "sostener":
            out += [a + rng.uniform(-2.5, 2.5) for _ in range(rng.randint(5, 120))]
            continue
        destino = {"golpe": rng.uniform(140, 180), "recoger": rng.uniform(45, 70),
                   "parcial": a - rng.uniform(5, 50), "lento": rng.uniform(50, 178)}[accion]
        n = rng.randint(40, 120) if accion == "lento" else rng.randint(2, 12)
        out += [a + (destino - a) * (i + 1) / n for i in range(n)]
        a = destino
    return [min(180.0, max(0.0, x)) for x in out]


def _golpes(diagnosticos):
    """Cada golpe emitido: fotograma, mensaje y ángulo con que se juzgó."""
    eventos, anterior = [], None
    for i, d in enumerate(diagnosticos):
        if d["mensaje"] != anterior and d["correcto"] is not None:
            eventos.append((i, d["mensaje"], d["angulos_regla"]))
        anterior = d["mensaje"]
    return eventos


def test_sostener_solo_cambia_el_texto_nunca_los_golpes(monkeypatch):
    """
    La garantía, en forma de propiedad. Con el sostenido anulado, la máquina es
    exactamente la de antes del 18-oct-2026, porque el sostenido solo decide
    qué texto se muestra en los fotogramas de reposo. Sobre secuencias
    aleatorias de golpes, sostenidos, recogidas parciales y temblor, los golpes
    emitidos —fotograma, mensaje y ángulo— tienen que coincidir uno a uno.
    """
    rng = random.Random(20261018)
    casos = [(rng.choice([16, 33, 40]), _secuencia_aleatoria(rng)) for _ in range(800)]

    con_sostenido = [_golpes(_reproducir(TsukiStateMachine(), s, paso=p)) for p, s in casos]
    monkeypatch.setattr(TsukiStateMachine, "_sostiene_el_kime", lambda self: False)
    sin_sostenido = [_golpes(_reproducir(TsukiStateMachine(), s, paso=p)) for p, s in casos]

    assert sum(map(len, sin_sostenido)) > 300, "las secuencias no producen golpes que comparar"
    assert con_sostenido == sin_sostenido



# ---------------------------------------------------------------------------
# El sostenido mira también hacia dónde apunta el brazo (19-oct-2026)
# ---------------------------------------------------------------------------
#
# Visto en la Mac de Sebastián sobre «Zenkusu dachi.mp4»: «IZQ - TSUKI:
# EXCELENTE» seguía en pantalla con el brazo colgando junto a la cadera. El
# sostenido solo miraba el ángulo del codo, y bajar el brazo ESTIRADO lo deja
# en los mismos ~160°: para el codo, sostener el Kime y dejar caer el brazo
# son lo mismo. Hace falta la dirección del brazo.

def _reproducir_con_direccion(maquina, pares, paso=MS_POR_FOTOGRAMA):
    """Pares (ángulo del codo, dirección del brazo) a la cadencia de la cámara."""
    return [maquina.update(angulo, i * paso, direccion=direccion)
            for i, (angulo, direccion) in enumerate(pares)]


def _golpe_y_brazo_bajado(direccion_final=90.0):
    """
    Golpe al frente sostenido 1 s y luego el brazo, estirado, cae al costado.

    La dirección va en grados sobre la imagen, con y hacia abajo: 0° es el
    puño al frente y 90° el brazo colgando.
    """
    golpe = [(a, 0.0) for a in _golpe_sostenido(fotogramas_sostenidos=30)]
    caida = [(172.0 + (2 if i % 2 else -2), direccion_final * (i + 1) / 15) for i in range(15)]
    colgando = [(172.0 + (2 if i % 2 else -2), direccion_final) for i in range(30)]
    return golpe + caida + colgando


@ficha(
    id_caso="TC-AUTO-075",
    nombre="Bajar el brazo estirado retira el veredicto del Tsuki aunque el codo no cambie",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "el sostenido del 18-oct solo miraba el ángulo del codo, y con el brazo "
        "estirado ese ángulo es el mismo al frente que colgando: en la Mac se vio "
        "«TSUKI: EXCELENTE» con el brazo junto a la cadera. En la demostración "
        "el sistema afirmaría un Kime que no hay, y si el veredicto fuera "
        "incorrecto el anillo rojo seguiría sobre el codo"),
    componente="expert_system/tsuki.py (MARGEN_DIRECCION), expert_system/analyzer.py",
    requisitos=("RF-05", "RF-06"),
    precondiciones="Ninguna. La máquina es pura y recibe ángulos y direcciones sintéticos",
    datos_entrada=(
        "Un golpe sostenido 1 s y luego el brazo estirado que cae 90°; el mismo "
        "golpe sostenido 3 s con un vaivén de dirección de ±8°; 800 secuencias "
        "aleatorias con y sin dirección"),
    pasos=[
        Paso("Golpear, sostener y dejar caer el brazo estirado",
             "assert diagnosticos[-1]['mensaje'] == SIN_GOLPE"),
        Paso("Sostener el Kime con el vaivén natural de la dirección",
             "assert diagnosticos[-1]['mensaje'] == 'TSUKI: EXCELENTE'"),
        Paso("Comparar los golpes con dirección y sin ella en 800 secuencias",
             "assert los golpes emitidos son idénticos"),
    ],
    resultado_esperado="PASSED: el veredicto se retira al bajar el brazo y los golpes no cambian",
)
def test_bajar_el_brazo_estirado_retira_el_veredicto():
    diagnosticos = _reproducir_con_direccion(TsukiStateMachine(), _golpe_y_brazo_bajado())

    assert diagnosticos[-1]["mensaje"] == SIN_GOLPE, (
        f"con el brazo colgando el aviso dice {diagnosticos[-1]['mensaje']!r}")


def test_sin_la_direccion_el_codo_no_puede_distinguirlo():
    """
    Por qué hace falta la dirección: con el mismo recorrido del codo y sin
    decirle hacia dónde apunta el brazo, la máquina no tiene cómo saber que
    se bajó. Es el comportamiento de antes, que se conserva para quien no la
    informe, y es exactamente lo que se vio en la Mac.
    """
    angulos = [a for a, _ in _golpe_y_brazo_bajado()]
    assert _reproducir(TsukiStateMachine(), angulos)[-1]["mensaje"] == "TSUKI: EXCELENTE"


def test_el_vaiven_natural_de_sostener_no_retira_el_veredicto():
    pares = [(a, (8.0 if i % 2 else -8.0)) for i, a in enumerate(_golpe_sostenido())]
    assert _reproducir_con_direccion(TsukiStateMachine(), pares)[-1]["mensaje"] == "TSUKI: EXCELENTE"


def test_bajar_el_brazo_a_medias_tambien_lo_retira():
    """Del frente a 45° ya no es el Kime, aunque el brazo no llegue a colgar."""
    pares = _golpe_y_brazo_bajado(direccion_final=45.0)
    assert _reproducir_con_direccion(TsukiStateMachine(), pares)[-1]["mensaje"] == SIN_GOLPE


def test_la_direccion_solo_cambia_el_texto_nunca_los_golpes():
    """
    La misma garantía que el sostenido del 18-oct: sobre 800 secuencias
    aleatorias, con direcciones que vagan al azar, los golpes emitidos
    —fotograma, mensaje y ángulo— son idénticos a los de no informar dirección.
    """
    rng = random.Random(20261019)
    casos = []
    for _ in range(800):
        angulos = _secuencia_aleatoria(rng)
        direccion, direcciones = rng.uniform(-180, 180), []
        for _ in angulos:
            direccion += rng.uniform(-20, 20)
            direcciones.append(direccion)
        casos.append((rng.choice([16, 33, 40]), angulos, direcciones))

    sin = [_golpes(_reproducir(TsukiStateMachine(), a, paso=p)) for p, a, _ in casos]
    con = [_golpes(_reproducir_con_direccion(TsukiStateMachine(), list(zip(a, d)), paso=p))
           for p, a, d in casos]

    assert sum(map(len, sin)) > 300, "las secuencias no producen golpes que comparar"
    assert con == sin


@pytest.mark.parametrize("a, b, esperado", [(10, 350, 20), (170, -170, 20), (0, 90, 90), (-90, 90, 180)])
def test_la_diferencia_de_direccion_no_salta_en_360(a, b, esperado):
    assert diferencia_angular(a, b) == pytest.approx(esperado)


def test_el_analizador_informa_la_direccion_del_brazo(monkeypatch):
    """La costura: sin esto el arreglo existiría en la máquina y no en la pantalla."""
    from expert_system.analyzer import TechniqueAnalyzer
    from helpers.fakes import pose_sintetica

    recibidas = []
    original = TsukiStateMachine.update

    def espia(self, angulo, t_ms, direccion=None):
        recibidas.append(direccion)
        return original(self, angulo, t_ms, direccion=direccion)

    monkeypatch.setattr(TsukiStateMachine, "update", espia)
    TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1).analyze_tsuki(
        pose_sintetica(), 1000, 1000, 0)

    assert len(recibidas) == 2 and all(d is not None for d in recibidas)
