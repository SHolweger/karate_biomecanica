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
import pytest

from expert_system.tsuki import (EN_EXTENSION, RECORRIDO_MINIMO, SIN_GOLPE,
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
