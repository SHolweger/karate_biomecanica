"""
comparar_2d_3d.py — ¿conviene medir los ángulos en 2D o en 3D?

El sistema calcula todos sus ángulos sobre `result.pose_landmarks`, que son
coordenadas del plano de la imagen: descartan la profundidad. Eso tiene un
coste medido (ver `tests/unit/test_geometry.py`): la proyección deforma el
ángulo cuando el plano de la técnica no es paralelo al sensor, siempre
empujándolo hacia 90°, de modo que un codo extendido se lee como flexionado.

MediaPipe entrega además `result.pose_world_landmarks`: coordenadas en metros
relativas al centro de las caderas, calculadas en el MISMO paso de inferencia.
Su coste ya está pagado en cada fotograma y hoy se descartan.

La pregunta abierta es si usarlas mejora el análisis. **No es obvia**: la
profundidad de un modelo monocular es estimada, no medida, y puede ser peor
que la proyección en algunos casos. Por eso esto es una herramienta de
medición y no un cambio: contrasta las dos formas de medir sobre la misma
grabación y deja que decidan los datos.

Uso:
    python3 comparar_2d_3d.py "grabacion.mp4"
    python3 comparar_2d_3d.py "grabacion.mp4" --esperado zenkutsu_dachi
    python3 comparar_2d_3d.py "grabacion.mp4" --desde 10 --cada 3

    --esperado  qué postura se está ejecutando en el video. Con este dato la
                herramienta responde la pregunta que importa —cuál de las dos
                formas de medir reconoce la postura correcta más veces— en vez
                de limitarse a informar que difieren.
    --desde     descarta los primeros segundos. Los de un video casero son la
                persona caminando hacia su sitio después de pulsar grabar.
    --cada      analiza uno de cada N fotogramas. Con 1 se analizan todos.

Conviene correrlo sobre DOS grabaciones de la misma técnica, una de frente y
otra de perfil. La de perfil mide en el plano correcto y sirve de referencia:
si el 3D de la toma frontal se le parece y el 2D no, la respuesta está clara.
"""
import argparse
import sys
from collections import Counter

from biomechanics.geometry import BiomechanicsMath
from expert_system.analyzer import (KOKUTSU_FRONTAL_MINIMA, KOKUTSU_TRASERA_MAXIMA,
                                    RODILLA_EXTENDIDA, RODILLA_FLEXIONADA,
                                    ZENKUTSU_TRASERA_MINIMA)
from expert_system.guardia import (DER_ADELANTE, IZQ_ADELANTE,
                                   orientacion_frente_a_camara,
                                   pierna_adelantada, separacion_sagital)

# Mismo mapeo de espejo que usa `analyze_stance`: los índices "izquierdos" son
# los del lado derecho anatómico, para que coincidan con lo que el usuario ve.
CADERA_IZQ, RODILLA_IZQ, TOBILLO_IZQ = 24, 26, 28
CADERA_DER, RODILLA_DER, TOBILLO_DER = 23, 25, 27

# Tramos de angulo de camara. El intermedio existe porque la eleccion real no
# es "de frente o de perfil": el perfil resuelve el escorzo pero esconde la
# pierna mas lejana detras de la cercana, y el punto dulce puede estar enmedio.
TRAMOS = ("de frente", "a 45 grados", "de perfil")


def _tramo(orientacion):
    if orientacion > 0.80:
        return "de frente"
    if orientacion < 0.50:
        return "de perfil"
    return "a 45 grados"


# Que articulacion juzga cada postura, en el orden (frontal, trasera) en que
# la consume su regla.
ARTICULACIONES_DE = {
    "zenkutsu_dachi": ("rodilla_frontal", "rodilla_trasera"),
    "kokutsu_dachi": ("rodilla_frontal", "rodilla_trasera"),
    "heiko_dachi": ("rodilla", "rodilla"),
    "kiba_dachi": ("rodilla", "rodilla"),
}

POSTURAS = ("heiko_dachi", "kiba_dachi", "zenkutsu_dachi", "kokutsu_dachi",
            "guardia_indefinida", "transicion")


def _clasificar(angulo_izq, angulo_der, guardia):
    """
    El mismo árbol de decisión que `analyze_stance`, reducido a su respuesta.

    Se replica aquí en vez de invocar al analizador porque este script tiene
    que alimentarlo con DOS juegos de ángulos distintos —los proyectados y los
    tridimensionales— sobre los mismos landmarks, y el analizador calcula los
    suyos por dentro. Si el árbol de `analyze_stance` cambia, este hay que
    actualizarlo: es una herramienta de medición, no parte del sistema.
    """
    if angulo_izq > RODILLA_EXTENDIDA and angulo_der > RODILLA_EXTENDIDA:
        return "heiko_dachi"
    if (RODILLA_FLEXIONADA <= angulo_izq <= RODILLA_EXTENDIDA
            and RODILLA_FLEXIONADA <= angulo_der <= RODILLA_EXTENDIDA):
        return "kiba_dachi"

    if guardia is not None:
        frontal, trasero = ((angulo_izq, angulo_der) if guardia == IZQ_ADELANTE
                            else (angulo_der, angulo_izq))
        if frontal < RODILLA_FLEXIONADA and trasero > ZENKUTSU_TRASERA_MINIMA:
            return "zenkutsu_dachi"
        if frontal >= KOKUTSU_FRONTAL_MINIMA and trasero <= KOKUTSU_TRASERA_MAXIMA:
            return "kokutsu_dachi"
    elif (min(angulo_izq, angulo_der) <= KOKUTSU_TRASERA_MAXIMA
          and max(angulo_izq, angulo_der) >= KOKUTSU_FRONTAL_MINIMA):
        return "guardia_indefinida"

    return "transicion"


def _angulos_2d(landmarks, ancho, alto):
    """Como los mide el sistema hoy: píxeles del plano de la imagen."""
    def px(indice):
        return (int(landmarks[indice].x * ancho), int(landmarks[indice].y * alto))

    return (BiomechanicsMath.calculate_angle(px(CADERA_IZQ), px(RODILLA_IZQ), px(TOBILLO_IZQ)),
            BiomechanicsMath.calculate_angle(px(CADERA_DER), px(RODILLA_DER), px(TOBILLO_DER)))


def _angulos_3d(mundo):
    """Sobre las coordenadas métricas, sin proyectar."""
    def xyz(indice):
        return (mundo[indice].x, mundo[indice].y, mundo[indice].z)

    return (BiomechanicsMath.calculate_angle_3d(xyz(CADERA_IZQ), xyz(RODILLA_IZQ), xyz(TOBILLO_IZQ)),
            BiomechanicsMath.calculate_angle_3d(xyz(CADERA_DER), xyz(RODILLA_DER), xyz(TOBILLO_DER)))


def _guardia_de(puntos):
    """La guardia deducida de un juego de puntos, cada uno con `.x` y `.z`."""
    return pierna_adelantada(separacion_sagital(
        (puntos[CADERA_IZQ].x, puntos[CADERA_IZQ].z),
        (puntos[CADERA_DER].x, puntos[CADERA_DER].z),
        (puntos[TOBILLO_IZQ].x, puntos[TOBILLO_IZQ].z),
        (puntos[TOBILLO_DER].x, puntos[TOBILLO_DER].z)))


def _invertir(guardia):
    """La guardia contraria. None sigue siendo None: no hay nada que invertir."""
    if guardia is None:
        return None
    return DER_ADELANTE if guardia == IZQ_ADELANTE else IZQ_ADELANTE


def _estadisticas(serie):
    if not serie:
        return None
    ordenada = sorted(serie)
    n = len(ordenada)
    return {
        "media": sum(ordenada) / n,
        "mediana": ordenada[n // 2],
        "p5": ordenada[max(0, int(n * 0.05))],
        "p95": ordenada[min(n - 1, int(n * 0.95))],
        "max": ordenada[-1],
    }


def comparar(fuente, desde_seg=0.0, cada=1, esperado=None, umbral_visibilidad=0.65):
    from vision.camera import Camera
    from vision.tracker import PoseTracker

    camara = Camera(fuente, espejo=True)
    rastreador = PoseTracker()

    izq_2d, der_2d, izq_3d, der_3d = [], [], [], []
    diferencias = []
    clasifica_2d, clasifica_3d = Counter(), Counter()
    # Con la guardia al revés: si la postura declarada aparece aquí y no en la
    # clasificación normal, el fallo no es de medida sino de signo.
    clasifica_invertida = Counter()
    orientaciones = []
    # La misma cuenta, separada por el angulo de camara. Es lo que convierte
    # el informe en un protocolo: dice desde donde hay que grabar cada tecnica.
    por_angulo = {tramo: [] for tramo in TRAMOS}
    # Con que guardia se reconocio cada postura. Si una postura solo aparece
    # con una de las dos, el sistema esta viendo un lado y no el otro.
    guardia_de_la_postura = Counter()
    # La guardia sobre TODOS los fotogramas, no solo sobre los reconocidos. Si
    # una de las dos no aparece nunca, el problema esta en deducirla; si
    # aparece pero la postura no se reconoce, esta en medir esa pierna.
    guardia_global = Counter()
    # Los dos angulos de rodilla, separados segun que guardia se dedujo. Es lo
    # que dice si el problema esta en la guardia o en el angulo: con la
    # izquierda adelante, la rodilla izquierda TIENE que ser la flexionada.
    angulos_por_guardia = {}
    # Cruce guardia x angulo de camara: separa un sesgo de pierna de uno de
    # encuadre, que hasta ahora estaban confundidos en la misma cifra.
    cruce = {}
    # Los angulos con que se juzgaria cada postura reconocida, para contestar
    # algo que el informe no contestaba: reconocerla no es aprobarla.
    juzgados = []
    # Visibilidad media de cada pierna, y cuantos fotogramas se descartan por
    # no verse. Una pierna sistematicamente menos visible que la otra explica
    # que solo se reconozca una guardia.
    visibilidad_izq, visibilidad_der = [], []
    descartados_visibilidad = 0
    # x de las dos caderas, para leer sobre datos REALES cuál landmark cae a la
    # izquierda de la pantalla. El doble de prueba lo supone al revés que
    # MediaPipe, y de ese supuesto salió el signo del eje sagital.
    x_cadera_24, x_cadera_23 = [], []
    leidos = analizados = sin_pose = sin_mundo = 0

    try:
        while True:
            frame = camara.get_frame()
            if frame is None:
                break
            leidos += 1

            marca = camara.marca_de_tiempo_ms()
            if marca < desde_seg * 1000:
                continue
            if (leidos % cada) != 0:
                continue

            resultado = rastreador.process_frame(frame, int(marca))
            if not resultado.pose_landmarks:
                sin_pose += 1
                continue

            landmarks = resultado.pose_landmarks[0]
            mundo = (resultado.pose_world_landmarks[0]
                     if getattr(resultado, "pose_world_landmarks", None) else None)
            if mundo is None:
                sin_mundo += 1
                continue

            pierna_izq = (CADERA_IZQ, RODILLA_IZQ, TOBILLO_IZQ)
            pierna_der = (CADERA_DER, RODILLA_DER, TOBILLO_DER)
            v_izq = min(landmarks[i].visibility for i in pierna_izq)
            v_der = min(landmarks[i].visibility for i in pierna_der)
            visibilidad_izq.append(v_izq)
            visibilidad_der.append(v_der)
            if v_izq <= umbral_visibilidad or v_der <= umbral_visibilidad:
                descartados_visibilidad += 1
                continue

            alto, ancho = frame.shape[:2]
            a2_izq, a2_der = _angulos_2d(landmarks, ancho, alto)
            a3_izq, a3_der = _angulos_3d(mundo)

            izq_2d.append(a2_izq); der_2d.append(a2_der)
            izq_3d.append(a3_izq); der_3d.append(a3_der)
            diferencias.append(abs(a2_izq - a3_izq))
            diferencias.append(abs(a2_der - a3_der))

            # La guardia de cada método sale de SUS propias coordenadas: en 2D
            # de la z normalizada de los landmarks de imagen, en 3D de la z
            # métrica. Compararlas es parte de lo que se quiere saber.
            guardia_2d = _guardia_de(landmarks)
            clasifica_2d[_clasificar(a2_izq, a2_der, guardia_2d)] += 1
            clasifica_3d[_clasificar(a3_izq, a3_der, _guardia_de(mundo))] += 1
            clasifica_invertida[_clasificar(a2_izq, a2_der, _invertir(guardia_2d))] += 1

            orientacion = orientacion_frente_a_camara(
                (landmarks[CADERA_IZQ].x, landmarks[CADERA_IZQ].z),
                (landmarks[CADERA_DER].x, landmarks[CADERA_DER].z))
            guardia_global[guardia_2d or "indefinida"] += 1
            clase_2d = _clasificar(a2_izq, a2_der, guardia_2d)
            if clase_2d == esperado:
                if guardia_2d is None:
                    juzgados.append((min(a2_izq, a2_der), max(a2_izq, a2_der)))
                elif guardia_2d == IZQ_ADELANTE:
                    juzgados.append((a2_izq, a2_der))
                else:
                    juzgados.append((a2_der, a2_izq))
            if guardia_2d is not None:
                frontal = a2_izq if guardia_2d == IZQ_ADELANTE else a2_der
                cruce.setdefault((_tramo(orientacion), guardia_2d), []).append(frontal)
            angulos_por_guardia.setdefault(
                guardia_2d or "indefinida", []).append((a2_izq, a2_der))
            if guardia_2d is not None:
                guardia_de_la_postura[
                    (_clasificar(a2_izq, a2_der, guardia_2d), guardia_2d)] += 1
            por_angulo[_tramo(orientacion)].append(
                (_clasificar(a2_izq, a2_der, guardia_2d),
                 _clasificar(a3_izq, a3_der, _guardia_de(mundo))))
            orientaciones.append(orientacion_frente_a_camara(
                (landmarks[CADERA_IZQ].x, landmarks[CADERA_IZQ].z),
                (landmarks[CADERA_DER].x, landmarks[CADERA_DER].z)))
            x_cadera_24.append(landmarks[CADERA_IZQ].x)
            x_cadera_23.append(landmarks[CADERA_DER].x)
            analizados += 1

            if analizados % 100 == 0:
                print(f"  {analizados} fotogramas comparados...", flush=True)
    finally:
        camara.release()
        rastreador.close()

    return {
        "leidos": leidos, "analizados": analizados,
        "sin_pose": sin_pose, "sin_mundo": sin_mundo,
        "angulos": {"izq 2D": izq_2d, "izq 3D": izq_3d,
                    "der 2D": der_2d, "der 3D": der_3d},
        "diferencias": diferencias,
        "clasifica_2d": clasifica_2d, "clasifica_3d": clasifica_3d,
        "clasifica_invertida": clasifica_invertida,
        "orientaciones": orientaciones, "por_angulo": por_angulo,
        "guardia_de_la_postura": guardia_de_la_postura,
        "guardia_global": guardia_global,
        "angulos_por_guardia": angulos_por_guardia,
        "cruce": cruce, "juzgados": juzgados,
        "visibilidad_izq": visibilidad_izq, "visibilidad_der": visibilidad_der,
        "descartados_visibilidad": descartados_visibilidad,
        "x_cadera_24": x_cadera_24, "x_cadera_23": x_cadera_23,
        "esperado": esperado,
    }


def informar(r):
    if r["analizados"] == 0:
        print("\nNo se pudo comparar ningún fotograma.")
        print(f"  leídos: {r['leidos']}   sin pose: {r['sin_pose']}   "
              f"sin coordenadas 3D: {r['sin_mundo']}")
        print("Si 'sin pose' es alto, revisa el encuadre con diagnostico_video.py.")
        return

    orientaciones = r["orientaciones"]
    o = _estadisticas(orientaciones)
    de_frente = sum(1 for v in orientaciones if v > 0.80)
    de_perfil = sum(1 for v in orientaciones if v < 0.50)
    total = r["analizados"]
    print(f"\n=== CÓMO SE GRABÓ ({total} fotogramas) ===")
    print(f"  orientación media: {o['media']:.2f}   (1,00 = de frente, 0,00 = de perfil)")
    print(f"  fotogramas de frente (>0,80): {de_frente:5d} ({100*de_frente/total:3.0f}%)")
    print(f"  fotogramas de perfil (<0,50): {de_perfil:5d} ({100*de_perfil/total:3.0f}%)")
    print("  Zenkutsu, Kokutsu, Tsuki y Mae Geri ocurren en el plano sagital y")
    print("  quieren perfil. Heiko y Kiba son frontales.")

    print(f"\n=== QUE SE DESCARTO Y POR QUE ===")
    print(f"  fotogramas leidos del video:        {r['leidos']:6d}")
    print(f"  sin pose detectada:                 {r['sin_pose']:6d}")
    print(f"  descartados por poca visibilidad:   {r['descartados_visibilidad']:6d}")
    print(f"  comparados:                         {total:6d}")
    vi = _estadisticas(r["visibilidad_izq"])
    vd = _estadisticas(r["visibilidad_der"])
    if vi and vd:
        print(f"  visibilidad media pierna izq: {vi['media']:.3f}   (P5 {vi['p5']:.3f})")
        print(f"  visibilidad media pierna der: {vd['media']:.3f}   (P5 {vd['p5']:.3f})")
        if abs(vi["media"] - vd["media"]) > 0.10:
            peor = "izquierda" if vi["media"] < vd["media"] else "derecha"
            print(f"  La pierna {peor} se ve notablemente peor. Eso basta para que")
            print( "  el sistema reconozca una guardia y no la otra.")

    g = r["guardia_global"]
    print(f"\n=== GUARDIA DEDUCIDA EN TODOS LOS FOTOGRAMAS ===")
    for clave in (IZQ_ADELANTE, DER_ADELANTE, "indefinida"):
        n = g[clave]
        print(f"  {clave:16s} {n:6d} ({100*n/total if total else 0:3.0f}%)")
    print(f"\n=== ANGULOS DE RODILLA SEGUN LA GUARDIA DEDUCIDA ===")
    print(f"{'Guardia':16s} {'n':>6s} {'rodilla izq':>22s} {'rodilla der':>22s}")
    print(f"{'':16s} {'':>6s} {'mediana   P5':>22s} {'mediana   P5':>22s}")
    for clave in (IZQ_ADELANTE, DER_ADELANTE, "indefinida"):
        muestras = r["angulos_por_guardia"].get(clave)
        if not muestras:
            continue
        ei = _estadisticas([i for i, _ in muestras])
        ed = _estadisticas([d for _, d in muestras])
        print(f"{clave:16s} {len(muestras):6d} "
              f"{ei['mediana']:13.1f} {ei['p5']:8.1f} "
              f"{ed['mediana']:13.1f} {ed['p5']:8.1f}")
    if r["cruce"]:
        print(f"\n=== RODILLA DELANTERA: ANGULO DE CAMARA x GUARDIA ===")
        print(f"{'Angulo':14s} {'guardia':16s} {'n':>6s} {'mediana':>9s} {'P5':>8s}")
        for tramo in TRAMOS:
            for guardia in (IZQ_ADELANTE, DER_ADELANTE):
                serie = r["cruce"].get((tramo, guardia))
                if not serie:
                    continue
                e = _estadisticas(serie)
                print(f"{tramo:14s} {guardia:16s} {len(serie):6d} "
                      f"{e['mediana']:9.1f} {e['p5']:8.1f}")
        print("  Si la diferencia entre guardias desaparece dentro de cada tramo,")
        print("  no habia sesgo de pierna sino de encuadre.")

    print("  Con una guardia declarada, la rodilla DELANTERA tiene que ser la")
    print("  flexionada. Si con IZQ ADELANTE la que se dobla es la derecha, la")
    print("  guardia esta mal en esos fotogramas; si no se dobla ninguna, no")
    print("  hay postura que reconocer y son transiciones.")

    x24 = _estadisticas(r["x_cadera_24"])["mediana"]
    x23 = _estadisticas(r["x_cadera_23"])["mediana"]
    print(f"\n=== CONVENIO DE EJES (medido, no supuesto) ===")
    print(f"  x mediana de la cadera 24: {x24:.3f}")
    print(f"  x mediana de la cadera 23: {x23:.3f}")
    if x24 < x23:
        print("  El landmark 24 cae a la IZQUIERDA de la pantalla.")
        print("  Los dobles de prueba lo colocan al revés (24 en x=0,58), así que")
        print("  el signo del eje sagital deducido de ellos queda INVERTIDO aquí.")
    else:
        print("  El landmark 24 cae a la DERECHA de la pantalla, como suponen los")
        print("  dobles de prueba.")

    print(f"\n=== ÁNGULOS DE RODILLA ({r['analizados']} fotogramas) ===")
    print(f"{'Serie':10s} {'media':>8s} {'mediana':>9s} {'P5':>8s} {'P95':>8s}")
    for nombre, serie in r["angulos"].items():
        e = _estadisticas(serie)
        print(f"{nombre:10s} {e['media']:8.1f} {e['mediana']:9.1f} {e['p5']:8.1f} {e['p95']:8.1f}")

    d = _estadisticas(r["diferencias"])
    print(f"\n=== DIFERENCIA |2D - 3D| POR ARTICULACIÓN ===")
    print(f"  media {d['media']:.1f}°   mediana {d['mediana']:.1f}°   "
          f"P95 {d['p95']:.1f}°   máx {d['max']:.1f}°")
    if d["mediana"] < 3.0:
        print("  Las dos formas de medir coinciden: la toma ya está en el plano")
        print("  correcto, y pasar a 3D no cambiaría los veredictos.")
    else:
        print("  Difieren de forma apreciable. Cuál de las dos acierta lo dice")
        print("  la clasificación de abajo, no esta cifra por sí sola.")

    print(f"\n=== POSTURA RECONOCIDA ===")
    print(f"{'Postura':22s} {'2D':>12s} {'3D':>12s}")
    total = r["analizados"]
    for postura in POSTURAS:
        n2, n3 = r["clasifica_2d"][postura], r["clasifica_3d"][postura]
        if n2 or n3:
            print(f"{postura:22s} {n2:6d} ({100*n2/total:3.0f}%) {n3:6d} ({100*n3/total:3.0f}%)")

    esperado = r["esperado"]
    if esperado:
        acierto_2d = 100 * r["clasifica_2d"][esperado] / total
        acierto_3d = 100 * r["clasifica_3d"][esperado] / total
        invertida = 100 * r["clasifica_invertida"][esperado] / total

        print(f"\n=== ACIERTO SOBRE LA POSTURA DECLARADA ({esperado}) ===")
        print(f"  midiendo en 2D:                        {acierto_2d:5.1f} %")
        print(f"  midiendo en 3D:                        {acierto_3d:5.1f} %")
        print(f"  en 2D pero con la GUARDIA INVERTIDA:   {invertida:5.1f} %")

        # El orden importa: si invertir la guardia recupera la postura, discutir
        # 2D contra 3D es discutir el decorado. Se dice primero.
        if invertida > max(acierto_2d, acierto_3d) + 10:
            print("\n  La postura aparece al invertir qué pierna va adelante.")
            print("  El fallo NO es de medida ni de plano: es de SIGNO en la guardia.")
            print("  Ni cambiar a 3D ni volver a grabar lo arreglarían.")
        elif acierto_3d > acierto_2d + 10:
            print("\n  Las coordenadas 3D reconocen la postura bastante mejor.")
        elif acierto_2d > acierto_3d + 10:
            print("\n  La medida 2D reconoce mejor: la profundidad estimada empeora")
            print("  el análisis en esta grabación. Conviene no adoptarla.")
        elif max(acierto_2d, acierto_3d, invertida) < 5:
            print("\n  Ninguna de las tres reconoce la postura. No es el plano ni el")
            print("  signo: revisa los cortes del clasificador contra los ángulos de")
            print("  arriba, porque la postura declarada no cabe en ninguna rama.")
        else:
            print("\n  Empate entre 2D y 3D. Con esta grabación el cambio no se")
            print("  justifica.")

        print(f"\n=== ACIERTO SEGÚN EL ÁNGULO DE CÁMARA ({esperado}) ===")
        print(f"{'Ángulo':14s} {'fotogramas':>11s} {'2D':>8s} {'3D':>8s}")
        for tramo in TRAMOS:
            muestras = r["por_angulo"][tramo]
            if not muestras:
                continue
            n = len(muestras)
            a2 = 100 * sum(1 for c2, _ in muestras if c2 == esperado) / n
            a3 = 100 * sum(1 for _, c3 in muestras if c3 == esperado) / n
            print(f"{tramo:14s} {n:11d} {a2:7.1f}% {a3:7.1f}%")
        print("  Esto es lo que fija el protocolo de grabación del dojo: desde qué")
        print("  ángulo conviene filmar cada técnica. Ojo, un tramo con pocos")
        print("  fotogramas no decide nada.")

        con_izq = r["guardia_de_la_postura"][(esperado, IZQ_ADELANTE)]
        con_der = r["guardia_de_la_postura"][(esperado, DER_ADELANTE)]
        reconocidas = con_izq + con_der
        if reconocidas:
            print(f"\n=== CON QUÉ PIERNA ADELANTE SE RECONOCIÓ ({esperado}) ===")
            print(f"  izquierda adelante: {con_izq:5d} ({100*con_izq/reconocidas:3.0f}%)")
            print(f"  derecha adelante:   {con_der:5d} ({100*con_der/reconocidas:3.0f}%)")
            if min(con_izq, con_der) < 0.1 * reconocidas:
                print("  La postura se reconoce practicamente con una sola guardia.")
                print("  Si en el video se ejecuta de los dos lados, el sistema está")
                print("  ciego a uno de ellos, y eso no lo explica el ángulo de cámara.")

        juzgados = r["juzgados"]
        if juzgados and esperado in ARTICULACIONES_DE:
            from expert_system.knowledge_base import KarateRules
            reglas = KarateRules()
            art_frontal, art_trasera = ARTICULACIONES_DE[esperado]
            ok_f = sum(1 for f, _ in juzgados if reglas.dentro(f, esperado, art_frontal))
            ok_t = sum(1 for _, tr in juzgados if reglas.dentro(tr, esperado, art_trasera))
            ok = sum(1 for f, tr in juzgados
                     if reglas.dentro(f, esperado, art_frontal)
                     and reglas.dentro(tr, esperado, art_trasera))
            n = len(juzgados)
            rf = reglas.rango(esperado, art_frontal)
            rt = reglas.rango(esperado, art_trasera)
            print(f"\n=== DE LAS RECONOCIDAS, CUANTAS SE JUZGAN CORRECTAS ===")
            print(f"  reconocidas en 2D:                    {n:6d}")
            print(f"  con la delantera dentro de {rf}: {ok_f:6d} ({100*ok_f/n:3.0f}%)")
            print(f"  con la trasera dentro de {rt}:  {ok_t:6d} ({100*ok_t/n:3.0f}%)")
            print(f"  veredicto CORRECTO:                   {ok:6d} ({100*ok/n:3.0f}%)")
            print("  Reconocer la postura no es aprobarla. Si el veredicto correcto")
            print("  es casi nulo sobre una ejecucion que el sensei da por buena, lo")
            print("  que hay que recalibrar son los umbrales (RF-08), no el codigo.")

        print("\n  Cuidado: esto compara contra lo DECLARADO en --esperado, así que")
        print("  solo vale si el video contiene esa postura y poco más. Sobre una")
        print("  grabación con varias técnicas encadenadas, la cifra no significa nada.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Contrasta medir los ángulos en 2D (como hoy) contra medirlos "
                    "sobre las coordenadas 3D que MediaPipe ya calcula.")
    parser.add_argument("fuente", help="ruta de la grabación a analizar")
    parser.add_argument("--esperado", choices=[p for p in POSTURAS
                                               if p.endswith("_dachi")],
                        help="postura que se está ejecutando en el video")
    parser.add_argument("--desde", type=float, default=0.0, metavar="SEG",
                        help="descarta los primeros segundos (default: 0)")
    parser.add_argument("--cada", type=int, default=1, metavar="N",
                        help="analiza uno de cada N fotogramas (default: 1)")
    args = parser.parse_args(argv)

    print(f"Comparando 2D contra 3D sobre {args.fuente}")
    if args.desde:
        print(f"Descartando los primeros {args.desde:.0f} s.")
    informar(comparar(args.fuente, desde_seg=args.desde, cada=max(1, args.cada),
                      esperado=args.esperado))
    return 0


if __name__ == "__main__":
    sys.exit(main())
