"""
A qué velocidad son los Tsuki de verdad, y qué golpes reconoce el sistema.

Herramienta de diagnóstico, como `diagnostico_video.py` y `comparar_2d_3d.py`.
No escribe en la base ni toca el sistema: recorre una grabación, mide el codo
fotograma a fotograma y contesta dos preguntas que hoy están abiertas.

---------------------------------------------------------------------------
POR QUÉ EXISTE
---------------------------------------------------------------------------

`expert_system/tsuki.py` decide que hubo golpe cuando el codo se abre
`RECORRIDO_MINIMO` (35°) dentro de `VENTANA_RECORRIDO_MS` (500 ms). Los dos
números salen de la definición de la técnica, no de una medición, y quedaron
marcados como provisionales — pero gobiernan qué se registra y qué no.

El 30-sep-2026, probando en vivo, Sebastián observó que **un Tsuki lento o
sostenido no se detecta**. Es coherente con el criterio: 35° en 500 ms equivale
a exigir **70°/s**, y una ejecución deliberadamente lenta no llega. El módulo
llegó a decir que «una ejecución lenta frente al espejo sigue siendo un Tsuki»,
lo cual describía mal su propio umbral.

Y ahí hay una tensión real que conviene resolver con datos y no con criterio:
`expert_system/riesgos.py` recomienda literalmente «trabajar el Tsuki a
velocidad media frente al espejo». Un sistema que recomienda practicar despacio
y luego no mide cuando se practica despacio se contradice.

También observó que **al recoger el brazo el veredicto se encendió alguna vez**.
Eso sí sería un defecto: la máquina solo dispara al ABRIR el codo. Esta
herramienta lo comprueba fechando cada golpe, para poder abrir el video en ese
segundo y ver qué se estaba haciendo.

---------------------------------------------------------------------------
QUÉ CONTESTA
---------------------------------------------------------------------------

1. **Cada golpe reconocido**, con su marca de tiempo, de qué ángulo arrancó, el
   ángulo del Kime, cuánto recorrió, cuánto duró y a qué velocidad media. La
   marca de tiempo es lo que permite contrastarla contra el video.
2. **La distribución de velocidad angular del codo** en toda la grabación, por
   percentiles. Dice dónde cae el corte de 70°/s respecto de lo que el cuerpo
   hace de verdad.
3. **Un barrido de umbrales**: cuántos golpes se reconocerían con otras
   combinaciones. Es lo que permite elegir los números con datos.

La velocidad se mide desde el último instante en que el codo seguía abajo hasta
aquel en que la extensión llegó más arriba, y tiene **la resolución del
muestreo**: a 30 fps, ±33 ms sobre una extensión que dura 200. Eso basta para
decidir un umbral —lo que se compara son órdenes de magnitud, 70 contra 600—
pero conviene no citar la cifra con más precisión de la que tiene.

La herramienta **no sabe** cuántos golpes hubo en realidad: eso lo pone quien
grabó. Por eso `--golpes N` es opcional y, cuando se declara, el informe
contrasta lo reconocido contra lo ejecutado en vez de limitarse a contar.
"""
import argparse
import sys
from collections import namedtuple

from biomechanics.filters import MovingAverageFilter
from biomechanics.geometry import BiomechanicsMath
from expert_system.tsuki import (RECORRIDO_MINIMO, VENTANA_RECORRIDO_MS,
                                 TsukiStateMachine)

# Los mismos landmarks que usa `analyze_tsuki`, con el mismo cambio de lado:
# el hombro/codo/muñeca DERECHOS anatómicos caen en la mitad izquierda de la
# imagen, y el sistema los llama «izquierdo» porque ahí es donde se ven.
BRAZOS = {"izq": (12, 14, 16), "der": (11, 13, 15)}

VISIBILIDAD_MINIMA = 0.65

# Cuánto puede haber subido ya el codo y seguir contando como «todavía abajo»,
# al buscar dónde arrancó el golpe. Por encima del temblor que deja el filtro y
# muy por debajo del recorrido de cualquier Tsuki.
MARGEN_INICIO = 5.0

Golpe = namedtuple("Golpe", "brazo t_ms desde pico recorrido duracion_ms velocidad mensaje correcto")


# ---------------------------------------------------------------------------
# Lógica pura: recibe series de (t, ángulo). La verifica CI.
# ---------------------------------------------------------------------------

def velocidades_angulares(serie):
    """
    Grados por segundo entre fotogramas consecutivos, en valor absoluto.

    Se toma el valor absoluto porque lo que interesa es cuán deprisa se mueve
    la articulación, no hacia dónde: la comparación es contra un umbral de
    velocidad, y el sentido ya lo decide la máquina de estados.
    """
    salida = []
    for (t0, a0), (t1, a1) in zip(serie, serie[1:]):
        dt = t1 - t0
        if dt > 0:
            salida.append(abs(a1 - a0) / dt * 1000.0)
    return salida


def percentiles(valores, cortes=(50, 75, 90, 95, 99)):
    """Sin numpy: la herramienta tiene que correr donde corra el sistema."""
    if not valores:
        return {}
    ordenados = sorted(valores)
    salida = {}
    for corte in cortes:
        posicion = min(int(len(ordenados) * corte / 100), len(ordenados) - 1)
        salida[corte] = ordenados[posicion]
    return salida


def golpes_detectados(serie, recorrido_minimo=RECORRIDO_MINIMO,
                      ventana_ms=VENTANA_RECORRIDO_MS, brazo="", reglas=None):
    """
    Los golpes que la máquina reconoce sobre esta serie, con su contexto.

    Se usa la MISMA máquina que el sistema —no una reimplementación— para que
    lo que aquí se mida sea lo que allí ocurre. La única diferencia es que los
    umbrales se pasan como argumento, que es lo que permite barrerlos.

    Un golpe se anota cuando el mensaje pasa a ser un veredicto cerrado, no en
    cada fotograma que lo sostiene: es el mismo criterio con el que
    `MedicionLogger` decide escribir en la base.
    """
    maquina = TsukiStateMachine(reglas=reglas, recorrido_minimo=recorrido_minimo,
                                ventana_ms=ventana_ms)
    golpes = []
    anterior_mensaje = None
    # Dónde empezó la extensión en curso, para poder decir de qué ángulo salió
    # el golpe y cuánto tardó. Sin esto, un Kime a 175° no distingue un Tsuki
    # desde el Hikite de un brazo que ya estaba casi extendido.
    #
    # Es el MÍNIMO de la ventana reciente, no el ángulo del fotograma en que la
    # máquina disparó: para entonces el codo ya se había abierto
    # `recorrido_minimo` grados. La primera versión tomaba ese fotograma y
    # reportaba «de 90,7° a 172° en 198 ms = 411°/s» sobre un golpe que en
    # realidad salió de 50° y fue a 616°/s. La herramienta existe para elegir
    # umbrales de velocidad: subestimarla un 33 % habría llevado esa cifra a la
    # tesis.
    ventana = []
    # La serie completa ya recorrida, para poder buscar hacia atrás el fondo
    # de la flexión sin el límite de la ventana de deteccion.
    vistos = []
    inicio = None
    cima = None

    for t_ms, angulo in serie:
        vistos.append((t_ms, angulo))
        ventana.append((t_ms, angulo))
        while len(ventana) > 1 and t_ms - ventana[0][0] > ventana_ms:
            ventana.pop(0)

        diagnostico = maquina.update(angulo, t_ms)
        estado = maquina.estado

        if estado == "EXTENDIENDO" and inicio is None:
            # De dónde salió el golpe: se retrocede por la serie mientras el
            # codo siga viniendo de más abajo, hasta el fondo de la flexión.
            #
            # NO se busca dentro de `ventana`. Esa dura `ventana_ms` porque es
            # lo que necesita DETECTAR el golpe, y usarla también para MEDIRLO
            # recortaba el arranque: sobre grabación real los golpes salían de
            # 81, 94, 105 y 118 grados —nunca del Hikite— porque para cuando la
            # máquina disparaba, el fondo de la flexión ya había salido de la
            # ventana. Detectar y medir son dos cosas, y confundirlas
            # subestimaba el recorrido y la velocidad de todos los golpes.
            # Dos pasos, y hacen falta los dos. Retroceder hasta el fondo de la
            # flexión, y desde ahí volver al ÚLTIMO instante que siga en ese
            # fondo: el golpe empieza cuando el puño arranca, no cuando llegó
            # al Hikite. Sin el segundo paso, la duración se traga los cientos
            # de milisegundos que el puño lleva colocado esperando.
            i = len(vistos) - 1
            while i > 0 and vistos[i - 1][1] <= vistos[i][1] + MARGEN_INICIO:
                i -= 1
            fondo = vistos[i][1]
            while i + 1 < len(vistos) and vistos[i + 1][1] <= fondo + MARGEN_INICIO:
                i += 1
            inicio = vistos[i]

        # El instante en que la extensión llegó a su punto más alto. No es el
        # mismo en que se emite el veredicto: ese llega un fotograma después,
        # cuando el brazo ya empezó a volver, y usarlo alargaba la duración en
        # un fotograma entero.
        if estado == "EXTENDIENDO" and (cima is None or angulo > cima[1]):
            cima = (t_ms, angulo)

        cerrado = diagnostico["correcto"] is not None
        if cerrado and diagnostico["mensaje"] != anterior_mensaje:
            desde_t, desde_angulo = inicio if inicio else (t_ms, angulo)
            pico = maquina.pico if maquina.pico is not None else angulo
            hasta_t = cima[0] if cima else t_ms
            duracion = max(hasta_t - desde_t, 1)
            golpes.append(Golpe(
                brazo=brazo, t_ms=t_ms, desde=desde_angulo, pico=pico,
                recorrido=pico - desde_angulo, duracion_ms=duracion,
                velocidad=(pico - desde_angulo) / duracion * 1000.0,
                mensaje=diagnostico["mensaje"], correcto=diagnostico["correcto"]))
        if estado == "REPOSO":
            inicio = cima = None
        anterior_mensaje = diagnostico["mensaje"]

    return golpes


def barrido(serie, combinaciones, reglas=None):
    """Cuántos golpes se reconocerían con cada par (recorrido, ventana)."""
    return {(r, v): len(golpes_detectados(serie, r, v, reglas=reglas))
            for r, v in combinaciones}


def velocidad_implicada(recorrido_minimo, ventana_ms):
    """La velocidad mínima, en grados por segundo, que el par de umbrales exige."""
    return recorrido_minimo / (ventana_ms / 1000.0)


# ---------------------------------------------------------------------------
# Recorrido de la grabación
# ---------------------------------------------------------------------------

def medir(fuente, desde_seg=0.0, ventana_filtro=5):
    """Devuelve una serie (t_ms, ángulo) por brazo, con el mismo filtro del sistema."""
    from vision.camera import Camera
    from vision.tracker import PoseTracker

    camara = Camera(fuente, espejo=True)
    rastreador = PoseTracker()
    filtros = {lado: MovingAverageFilter(ventana_filtro) for lado in BRAZOS}
    series = {lado: [] for lado in BRAZOS}
    leidos = sin_pose = 0
    ocultos = {lado: 0 for lado in BRAZOS}

    try:
        while True:
            frame = camara.get_frame()
            if frame is None:
                break
            leidos += 1
            marca = camara.marca_de_tiempo_ms()
            if marca < desde_seg * 1000:
                continue

            resultado = rastreador.process_frame(frame, int(marca))
            if not resultado.pose_landmarks:
                sin_pose += 1
                continue
            landmarks = resultado.pose_landmarks[0]
            alto, ancho, _ = frame.shape

            for lado, (hombro, codo, muneca) in BRAZOS.items():
                if min(landmarks[i].visibility for i in (hombro, codo, muneca)) <= VISIBILIDAD_MINIMA:
                    # Mismo trato que en el sistema: el filtro se reinicia para
                    # no promediar con lo de antes de la oclusión.
                    filtros[lado].reset()
                    ocultos[lado] += 1
                    continue
                puntos = [(int(landmarks[i].x * ancho), int(landmarks[i].y * alto))
                          for i in (hombro, codo, muneca)]
                angulo = filtros[lado].update(BiomechanicsMath.calculate_angle(*puntos))
                series[lado].append((int(marca), angulo))
    finally:
        camara.release()

    return series, {"leidos": leidos, "sin_pose": sin_pose, "ocultos": ocultos}


def informar(series, cuentas, golpes_declarados=None, salida=sys.stdout):
    def escribir(texto=""):
        print(texto, file=salida)

    escribir(f"Fotogramas leidos: {cuentas['leidos']}   sin pose: {cuentas['sin_pose']}")
    escribir()

    todos = []
    for lado in sorted(series):
        serie = series[lado]
        if not serie:
            escribir(f"BRAZO {lado.upper()}: sin fotogramas utilizables "
                     f"({cuentas['ocultos'][lado]} ocultos)")
            continue
        golpes = golpes_detectados(serie, brazo=lado)
        todos.extend(golpes)

        escribir(f"BRAZO {lado.upper()}  ({len(serie)} fotogramas visibles, "
                 f"{cuentas['ocultos'][lado]} ocultos)")
        if not golpes:
            escribir("  Ningun golpe reconocido.")
        for g in golpes:
            escribir(f"  {g.t_ms / 1000:6.2f} s   {g.desde:5.1f} -> {g.pico:5.1f}  "
                     f"({g.recorrido:+5.1f} en {g.duracion_ms:4d} ms = "
                     f"{g.velocidad:6.1f} grados/s)   {g.mensaje}")
        escribir()

    # ---- la velocidad que el cuerpo produce de verdad ----
    escribir("VELOCIDAD ANGULAR DEL CODO (todos los fotogramas)")
    escribir(f"{'brazo':8} " + " ".join(f"P{c:<2}" .ljust(9) for c in (50, 75, 90, 95, 99)))
    for lado in sorted(series):
        if not series[lado]:
            continue
        p = percentiles(velocidades_angulares(series[lado]))
        escribir(f"{lado:8} " + " ".join(f"{p[c]:8.1f}" for c in (50, 75, 90, 95, 99)))
    escribir()
    escribir(f"El criterio vigente exige {velocidad_implicada(RECORRIDO_MINIMO, VENTANA_RECORRIDO_MS):.0f} grados/s "
             f"({RECORRIDO_MINIMO:.0f} grados en {VENTANA_RECORRIDO_MS} ms).")
    escribir("Si ese numero cae por encima del P95, el sistema esta exigiendo mas")
    escribir("velocidad de la que esta grabacion contiene, y por eso no reconoce.")
    escribir()

    # ---- que pasaria con otros umbrales ----
    escribir("BARRIDO DE UMBRALES (golpes reconocidos, sumando ambos brazos)")
    combinaciones = [(r, v) for r in (20, 25, 30, 35, 40) for v in (500, 750, 1000)]
    totales = {}
    for lado in sorted(series):
        if not series[lado]:
            continue
        for clave, cuantos in barrido(series[lado], combinaciones).items():
            totales[clave] = totales.get(clave, 0) + cuantos

    escribir(f"{'recorrido':>10} " + " ".join(f"{v} ms".rjust(9) for v in (500, 750, 1000)))
    for r in (20, 25, 30, 35, 40):
        fila = " ".join(f"{totales.get((r, v), 0):9d}" for v in (500, 750, 1000))
        marca = "  <- vigente" if r == RECORRIDO_MINIMO else ""
        escribir(f"{r:8.0f} deg {fila}{marca}")
    escribir()
    escribir("Cada celda lleva implicita una velocidad minima distinta:")
    escribir(f"{'recorrido':>10} " + " ".join(f"{v} ms".rjust(9) for v in (500, 750, 1000)))
    for r in (20, 25, 30, 35, 40):
        fila = " ".join(f"{velocidad_implicada(r, v):7.0f}/s" for v in (500, 750, 1000))
        escribir(f"{r:8.0f} deg {fila}")

    if golpes_declarados is not None:
        escribir()
        escribir("CONTRASTE CON LO EJECUTADO")
        escribir(f"  Declarados: {golpes_declarados}   reconocidos: {len(todos)}")
        if len(todos) < golpes_declarados:
            escribir(f"  Faltan {golpes_declarados - len(todos)}. Mirar el barrido: si bajando")
            escribir("  el recorrido aparecen, el umbral es el que sobra.")
        elif len(todos) > golpes_declarados:
            escribir(f"  Sobran {len(todos) - golpes_declarados}. Abrir el video en las marcas")
            escribir("  de tiempo de arriba: ahi esta lo que el sistema tomo por golpe.")
        else:
            escribir("  Coinciden.")
    else:
        escribir()
        escribir("Sin --golpes N no se puede decir si sobran o faltan: la herramienta")
        escribir("cuenta lo que el sistema reconoce, no lo que se ejecuto.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="A que velocidad son los Tsuki de esta grabacion, y cuales reconoce "
                    "el sistema. Solo lectura: no escribe en la base de datos.")
    parser.add_argument("fuente", help="ruta de la grabacion a analizar")
    parser.add_argument("--desde", type=float, default=0.0, metavar="SEG",
                        help="descarta los primeros segundos (util si la grabacion "
                             "empieza con el ejecutante caminando hacia su sitio)")
    parser.add_argument("--golpes", type=int, default=None, metavar="N",
                        help="cuantos Tsuki se ejecutaron de verdad, para contrastar")
    args = parser.parse_args(argv)

    series, cuentas = medir(args.fuente, desde_seg=args.desde)
    informar(series, cuentas, golpes_declarados=args.golpes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
