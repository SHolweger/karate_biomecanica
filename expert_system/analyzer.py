import math

from biomechanics.geometry import BiomechanicsMath
from biomechanics.filters import MovingAverageFilter
from expert_system.guardia import (IZQ_ADELANTE, orientacion_frente_a_camara,
                                   pierna_adelantada, separacion_sagital)
from expert_system.knowledge_base import KarateRules
from expert_system.kick_state_machine import MaeGeriStateMachine
from expert_system.tsuki import TsukiStateMachine

# ---------------------------------------------------------------------------
# CORTES DEL CLASIFICADOR DE POSTURAS
#
# Son distintos de los umbrales de evaluación y por eso viven aquí y no en la
# base de datos. Los umbrales de `umbral_referencia` responden "¿está bien
# ejecutada esta postura?"; estos cortes responden antes "¿qué postura es?".
# Confundirlos sería un error de diseño: un entrenador que endurece el criterio
# de calidad de un Zenkutsu no debería, con ello, hacer que el sistema deje de
# reconocer la postura.
#
# Se mantienen deliberadamente más amplios que los umbrales de evaluación: el
# clasificador debe reconocer también las ejecuciones incorrectas, porque una
# postura mal hecha que no se identifica tampoco se puede corregir. Hasta el
# 21-oct-2026 eso no se cumplía; ver «LA CÁMARA DECIDE» más abajo.
# ---------------------------------------------------------------------------
RODILLA_EXTENDIDA = 160.0      # por encima: pierna esencialmente recta
RODILLA_FLEXIONADA = 130.0     # por debajo: flexión marcada
ZENKUTSU_TRASERA_MINIMA = 150.0   # la pierna de atrás del Zenkutsu va tensa y larga

# Kokutsu: pierna frontal casi extendida y trasera flexionada, que es la
# distribución de peso inversa a la del Zenkutsu (corregido el 14-sep-2026;
# antes exigía la frontal flexionada y la postura nunca se reconocía).
KOKUTSU_FRONTAL_MINIMA = 140.0
KOKUTSU_TRASERA_MAXIMA = 135.0

# ---------------------------------------------------------------------------
# LA CÁMARA DECIDE QUÉ SE PUEDE RECONOCER (21-oct-2026)
#
# Los cortes de arriba solo dejaban pasar ejecuciones casi correctas, al revés
# de lo que dice su propio encabezado. Sobre las tomas con errores a propósito
# del protocolo del 19-oct, ninguna recibió su corrección: el Zenkutsu alto
# salía Heiko —y el sistema decía «Estira las piernas», lo contrario de lo que
# hacía falta—, el Zenkutsu con la trasera doblada salía transición, y el Kiba
# alto, el muy bajo y el de peso cargado, también. Las frases existían y no
# llegaban nunca.
#
# Ampliar los cortes sin más inventa posturas: con la delantera hasta 140°, un
# Kiba de peso cargado filmado de frente (135°/162°) se registraba como
# Zenkutsu, porque de frente la pierna adelantada la decide la profundidad, que
# es ruido. Así que cada ampliación vale **solo desde la toma en que la postura
# se puede medir** —la regla de planos del protocolo, ahora dentro del código—:
#
#   de perfil  (orientación < 0,5): Zenkutsu con la delantera hasta 140° o la
#              trasera doblada, siempre que la delantera sea la más doblada.
#   de perfil y con el cuerpo de frente al avance (< 0,25): Zenkutsu alto, con
#              las dos rodillas casi rectas y el paso largo. El límite más
#              estricto es lo que lo separa del Kokutsu filmado de perfil, que
#              da las mismas rodillas —la trasera se dobla hacia la cámara y se
#              ve recta— con la cadera de medio lado (0,38–0,46 medido).
#   de frente  (orientación ≥ 0,65) y con los pies abiertos: Kiba con las
#              rodillas entre 90° y 165°, para que lleguen «Sube un poco» y
#              «Baja más».
#
# Lo que reconocían los cortes de arriba se sigue reconociendo desde cualquier
# toma: nada de lo que funcionaba se pierde. Cifras medidas sobre las tomas del
# 19-oct (rodillas en los tramos sostenidos, orientación y apertura):
# ---------------------------------------------------------------------------
ZENKUTSU_FRONTAL_MAXIMA = 140.0   # Zenkutsu de clase: delantera 123–134° (medido)
PERFIL_MAXIMO = 0.5               # orientación de las tomas de Zenkutsu: 0,05–0,17
AVANCE_DE_FRENTE_MAXIMO = 0.25    # Zenkutsu ≤ 0,17; Kokutsu de perfil 0,38–0,46
FRENTE_MINIMO = 0.65              # Kiba: 0,81–0,98
PASO_LARGO_EN_CADERAS = 0.45      # Zenkutsu alto: 0,55–0,68; de pie, ~0
KIBA_APERTURA_MINIMA = 2.5        # tobillos / caderas en x: Kiba 2,7–3,1; de pie 1,3–2,3
KIBA_AMPLIADO = (90.0, 165.0)     # Kiba muy bajo 111/124°; alto 158/165°


def clasificar_postura(angulo_izq, angulo_der, guardia, separacion=0.0, vista=None,
                       apertura=None):
    """
    Qué postura dibujan las rodillas: la clave de técnica, o «guardia_indefinida»
    o «transicion».

    `vista` es `orientacion_frente_a_camara` (0 de perfil, 1 de frente) y
    `apertura` la separación de los tobillos en x medida en anchos de cadera.
    Sin ellas —`None`— solo se aplican los cortes que valen desde cualquier
    toma, que es lo que el clasificador hacía hasta el 21-oct-2026.

    Puro y sin estado: lo usan `analyze_stance` y `comparar_2d_3d.py`, para que
    la herramienta de medición no tenga que copiar el árbol.
    """
    de_perfil = vista is not None and vista < PERFIL_MAXIMO
    de_frente = vista is not None and vista >= FRENTE_MINIMO
    if guardia is not None:
        frontal, trasero = ((angulo_izq, angulo_der) if guardia == IZQ_ADELANTE
                            else (angulo_der, angulo_izq))

    paso_largo_de_perfil = (de_perfil and guardia is not None
                            and abs(separacion) >= PASO_LARGO_EN_CADERAS)
    if (paso_largo_de_perfil and vista < AVANCE_DE_FRENTE_MAXIMO
            and min(angulo_izq, angulo_der) >= ZENKUTSU_FRONTAL_MAXIMA):
        return "zenkutsu_dachi"   # alto: el paso largo lo distingue de Heiko

    if angulo_izq > RODILLA_EXTENDIDA and angulo_der > RODILLA_EXTENDIDA:
        # De perfil, un pie bien adelantado no es una postura natural: con la
        # cadera de medio lado es el Kokutsu, cuya rodilla trasera se ve recta,
        # y llamarlo Heiko le decía «Estira las piernas».
        return "transicion" if paso_largo_de_perfil else "heiko_dachi"

    if (RODILLA_FLEXIONADA <= angulo_izq <= RODILLA_EXTENDIDA
            and RODILLA_FLEXIONADA <= angulo_der <= RODILLA_EXTENDIDA):
        return "kiba_dachi"
    if (de_frente and apertura is not None and apertura >= KIBA_APERTURA_MINIMA
            and KIBA_AMPLIADO[0] <= angulo_izq <= KIBA_AMPLIADO[1]
            and KIBA_AMPLIADO[0] <= angulo_der <= KIBA_AMPLIADO[1]):
        return "kiba_dachi"

    if guardia is not None:
        if frontal < RODILLA_FLEXIONADA and trasero > ZENKUTSU_TRASERA_MINIMA:
            return "zenkutsu_dachi"
        if de_perfil and frontal < ZENKUTSU_FRONTAL_MAXIMA and frontal < trasero:
            return "zenkutsu_dachi"
        if frontal >= KOKUTSU_FRONTAL_MINIMA and trasero <= KOKUTSU_TRASERA_MAXIMA:
            return "kokutsu_dachi"
    elif (min(angulo_izq, angulo_der) <= KOKUTSU_TRASERA_MAXIMA
          and max(angulo_izq, angulo_der) >= KOKUTSU_FRONTAL_MINIMA):
        return "guardia_indefinida"

    return "transicion"

#Brazos
class TechniqueAnalyzer:
    def __init__(self, umbral_visibilidad=0.65, ventana_filtro=5, reglas=None):
        self.umbral = umbral_visibilidad
        # Base de conocimientos con los umbrales vigentes. Sin argumento usa los
        # valores de literatura, para poder analizar sin base de datos.
        self.reglas = reglas or KarateRules()
        # ANTI-JITTER: un filtro con memoria por cada articulación medida.
        # Suaviza el ángulo ANTES de que el clasificador y las reglas lo evalúen.
        self.filtros = {
            "codo_izq": MovingAverageFilter(ventana_filtro),
            "codo_der": MovingAverageFilter(ventana_filtro),
            "rodilla_izq": MovingAverageFilter(ventana_filtro),
            "rodilla_der": MovingAverageFilter(ventana_filtro),
            # Suaviza la separación de los tobillos sobre el eje sagital, que es
            # lo que decide qué pierna está adelante (ver expert_system/guardia.py).
            # Sin filtrar, la guardia detectada puede "parpadear" entre IZQ y DER
            # de un fotograma a otro aunque el ejecutante esté quieto.
            "guardia": MovingAverageFilter(ventana_filtro),
            # La orientación decide qué posturas se pueden reconocer desde esta
            # toma (ver `clasificar_postura`); filtrada por el mismo motivo.
            "vista": MovingAverageFilter(ventana_filtro),
        }
        # Una máquina de estados independiente por pierna: cualquiera de las dos
        # puede ser la que patea, no depende de la guardia/eje Z (ver diseño en
        # kick_state_machine.py).
        self.maquinas_patada = {
            "izq": MaeGeriStateMachine(ventana_filtro, self.reglas),
            "der": MaeGeriStateMachine(ventana_filtro, self.reglas),
        }
        # Una máquina por brazo, por el mismo motivo: el Tsuki es una
        # transición y no un estado, así que hace falta memoria para saber si
        # hubo golpe. Sin ella el sistema calificaba de Tsuki a un brazo en
        # reposo — el porqué completo está en expert_system/tsuki.py.
        self.maquinas_tsuki = {
            "izq": TsukiStateMachine(self.reglas),
            "der": TsukiStateMachine(self.reglas),
        }

    def analyze_tsuki(self, landmarks, w, h, timestamp_ms):
        """
        Analiza la técnica de Tsuki en AMBOS brazos y devuelve una lista de resultados
        lista para que el Renderer los dibuje.

        El veredicto NO se decide aquí: lo decide una máquina de estados por
        brazo, que solo califica cuando efectivamente hubo un golpe. Hasta el
        30-sep-2026 este método evaluaba el codo en cada fotograma, de modo que
        un brazo colgando al costado —entre 160 y 180°— se reportaba como
        «TSUKI: EXCELENTE» o «TSUKI: HIPEREXTENDIDO (Peligro)» y esas filas
        entraban a la base como mediciones de Tsuki. El porqué completo está en
        expert_system/tsuki.py.

        Recibe `timestamp_ms` por el mismo motivo que `analyze_mae_geri`: el
        recorrido del golpe se mide contra el reloj de la grabación, no contra
        el número de fotogramas que alcance a procesar esta máquina.
        """
        resultados = []

        # ---------------- BRAZO IZQUIERDO ----------------
        # Los puntos oficiales de MediaPipe para el lado derecho son 11, 13 y 15
        hombro_izq_lm, codo_izq_lm, muneca_izq_lm = landmarks[12], landmarks[14], landmarks[16] #Invertimos los puntos para no confundir al usuario con el modo espejo y que sea mas comodo visualmente.

        if (hombro_izq_lm.visibility > self.umbral and
            codo_izq_lm.visibility > self.umbral and
            muneca_izq_lm.visibility > self.umbral):

            hombro_izq = (int(hombro_izq_lm.x * w), int(hombro_izq_lm.y * h))
            codo_izq = (int(codo_izq_lm.x * w), int(codo_izq_lm.y * h))
            muneca_izq = (int(muneca_izq_lm.x * w), int(muneca_izq_lm.y * h))

            # Ángulo crudo (con jitter) -> filtro -> ángulo suavizado
            angulo_crudo = BiomechanicsMath.calculate_angle(hombro_izq, codo_izq, muneca_izq)
            angulo_izq = self.filtros["codo_izq"].update(angulo_crudo)
            # Hacia dónde apunta el brazo: solo la usa el sostenido del Kime,
            # para no seguir mostrando el golpe con el brazo ya bajado.
            direccion = math.degrees(math.atan2(muneca_izq[1] - hombro_izq[1],
                                                muneca_izq[0] - hombro_izq[0]))
            diagnostico = self.maquinas_tsuki["izq"].update(angulo_izq, timestamp_ms,
                                                               direccion=direccion)

            resultados.append(dict(
                diagnostico,
                pos_angulo=(codo_izq[0] + 20, codo_izq[1]),
                # Dónde está la articulación juzgada, sin el desplazamiento del
                # número. Es lo que permite marcarla sobre el video cuando falla.
                pos_articulacion=codo_izq,
                mensaje=f"IZQ - {diagnostico['mensaje']}",
                y_offset=50, categoria="codo_izq",
            ))
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer,
            # y la máquina para no juzgar con un golpe visto a medias.
            self.filtros["codo_izq"].reset()
            self.maquinas_tsuki["izq"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO IZQ: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 50,
                "categoria": "codo_izq", "correcto": None,
                "tecnica": None, "angulos_regla": None
            })

        # ---------------- BRAZO DERECHO ----------------
        # Los puntos oficiales de MediaPipe para el lado derecho son 12, 14 y 16
        hombro_der_lm, codo_der_lm, muneca_der_lm = landmarks[11], landmarks[13], landmarks[15] #Invertimos los puntos para no confundir al usuario con el modo espejo y que sea mas comodo visualmente.

        if (hombro_der_lm.visibility > self.umbral and
            codo_der_lm.visibility > self.umbral and
            muneca_der_lm.visibility > self.umbral):

            hombro_der = (int(hombro_der_lm.x * w), int(hombro_der_lm.y * h))
            codo_der = (int(codo_der_lm.x * w), int(codo_der_lm.y * h))
            muneca_der = (int(muneca_der_lm.x * w), int(muneca_der_lm.y * h))

            # Ángulo crudo (con jitter) -> filtro -> ángulo suavizado
            angulo_crudo = BiomechanicsMath.calculate_angle(hombro_der, codo_der, muneca_der)
            angulo_der = self.filtros["codo_der"].update(angulo_crudo)
            # Hacia dónde apunta el brazo: solo la usa el sostenido del Kime,
            # para no seguir mostrando el golpe con el brazo ya bajado.
            direccion = math.degrees(math.atan2(muneca_der[1] - hombro_der[1],
                                                muneca_der[0] - hombro_der[0]))
            diagnostico = self.maquinas_tsuki["der"].update(angulo_der, timestamp_ms,
                                                               direccion=direccion)

            resultados.append(dict(
                diagnostico,
                pos_angulo=(codo_der[0] - 60, codo_der[1]),  # -60 para que no tape el codo
                pos_articulacion=codo_der,
                mensaje=f"DER - {diagnostico['mensaje']}",
                y_offset=90, categoria="codo_der",           # más abajo para no chocar con el texto izq
            ))
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer,
            # y la máquina para no juzgar con un golpe visto a medias.
            self.filtros["codo_der"].reset()
            self.maquinas_tsuki["der"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO DER: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 90,
                "categoria": "codo_der", "correcto": None,
                "tecnica": None, "angulos_regla": None
            })

        return resultados
    
    #Piernas
    def analyze_stance(self, landmarks, w, h):
        """
        Analiza las piernas, detecta QUÉ postura estás haciendo y luego la evalúa.
        """
        resultados = []
        
        # 1. MODO ESPEJO: Invertimos los puntos para que coincidan con la pantalla
        cadera_izq_lm, rodilla_izq_lm, tobillo_izq_lm = landmarks[24], landmarks[26], landmarks[28]
        cadera_der_lm, rodilla_der_lm, tobillo_der_lm = landmarks[23], landmarks[25], landmarks[27]

        if (cadera_izq_lm.visibility > self.umbral and rodilla_izq_lm.visibility > self.umbral and tobillo_izq_lm.visibility > self.umbral and
            cadera_der_lm.visibility > self.umbral and rodilla_der_lm.visibility > self.umbral and tobillo_der_lm.visibility > self.umbral):
            
            # Transformamos a píxeles 2D
            cadera_izq = (int(cadera_izq_lm.x * w), int(cadera_izq_lm.y * h))
            rodilla_izq = (int(rodilla_izq_lm.x * w), int(rodilla_izq_lm.y * h))
            tobillo_izq = (int(tobillo_izq_lm.x * w), int(tobillo_izq_lm.y * h))

            cadera_der = (int(cadera_der_lm.x * w), int(cadera_der_lm.y * h))
            rodilla_der = (int(rodilla_der_lm.x * w), int(rodilla_der_lm.y * h))
            tobillo_der = (int(tobillo_der_lm.x * w), int(tobillo_der_lm.y * h))

            # Calculamos ángulos de ambas rodillas (crudos) y los suavizamos con el filtro.
            # Suavizar ANTES del clasificador también evita el parpadeo entre
            # posturas cuando el ángulo baila justo en el límite (ej. 130°).
            angulo_izq = self.filtros["rodilla_izq"].update(
                BiomechanicsMath.calculate_angle(cadera_izq, rodilla_izq, tobillo_izq))
            angulo_der = self.filtros["rodilla_der"].update(
                BiomechanicsMath.calculate_angle(cadera_der, rodilla_der, tobillo_der))

            # Qué pierna va adelante. Se proyecta la separación de los tobillos
            # sobre el eje sagital del cuerpo —deducido de la línea de caderas—
            # en vez de mirar solo el eje Z de la cámara: así la decisión usa el
            # eje que mejor la informa según la toma (X de perfil, Z de frente).
            # El porqué completo, y por qué la respuesta puede ser "no lo sé",
            # están en expert_system/guardia.py.
            separacion = self.filtros["guardia"].update(
                separacion_sagital((cadera_izq_lm.x, cadera_izq_lm.z),
                                   (cadera_der_lm.x, cadera_der_lm.z),
                                   (tobillo_izq_lm.x, tobillo_izq_lm.z),
                                   (tobillo_der_lm.x, tobillo_der_lm.z)))
            guardia = pierna_adelantada(separacion)

            # `None` cuando los tobillos no se separan lo suficiente para
            # afirmar nada. Frontal y trasera quedan sin definir a propósito:
            # ninguna rama que dependa de la guardia debe poder usarlas.
            if guardia is None:
                angulo_frontal = angulo_trasero = None
            elif guardia == IZQ_ADELANTE:
                angulo_frontal, angulo_trasero = angulo_izq, angulo_der
            else:
                angulo_frontal, angulo_trasero = angulo_der, angulo_izq

            # ---------------------------------------------------------
            # EL CLASIFICADOR (¿En qué postura está el usuario?)
            # ---------------------------------------------------------
            vista = self.filtros["vista"].update(orientacion_frente_a_camara(
                (cadera_izq_lm.x, cadera_izq_lm.z), (cadera_der_lm.x, cadera_der_lm.z)))
            ancho_caderas = abs(cadera_izq_lm.x - cadera_der_lm.x)
            apertura = (abs(tobillo_izq_lm.x - tobillo_der_lm.x) / ancho_caderas
                        if ancho_caderas > 1e-6 else None)
            postura = clasificar_postura(angulo_izq, angulo_der, guardia, separacion,
                                         vista, apertura)
            
            # CASO 1: ambas rodillas esencialmente rectas -> postura natural
            # (Heiko Dachi / Hachiji Dachi).
            if postura == "heiko_dachi":
                # Se evalúa la rodilla MÁS flexionada de las dos y no una
                # cualquiera. Con un máximo de 180°, exigir que la peor esté
                # dentro del rango equivale a exigirlo de ambas, que es el
                # contrato que ya cumple Kiba Dachi. Antes se pasaba
                # `angulo_frontal`, lo que hacía que el veredicto de una postura
                # simétrica dependiera de la guardia — y la guardia ahora puede
                # ser None, que aquí no significa nada: en Heiko no hay pierna
                # adelantada que encontrar.
                angulo_peor = min(angulo_izq, angulo_der)
                es_correcto, msg, color = self.reglas.evaluate_heiko_dachi(angulo_peor)
                postura_detectada = "POSTURA NATURAL"
                tecnica = "heiko_dachi"
                angulos_regla = (angulo_peor,)
                criterio_izq = criterio_der = ("heiko_dachi", "rodilla")

            # CASO 2: AMBAS rodillas flexionadas por igual -> Kiba Dachi (postura
            # de jinete). Es simétrica y lateral: no depende de qué pierna esté
            # "adelante" según el eje Z, por eso usa izq/der y no frontal/trasera.
            elif postura == "kiba_dachi":
                es_correcto, msg, color = self.reglas.evaluate_kiba_dachi(angulo_izq, angulo_der)
                postura_detectada = "KIBA DACHI"
                tecnica = "kiba_dachi"
                # Kiba es simétrica: la regla compara izquierda contra derecha,
                # no frontal contra trasera.
                angulos_regla = (angulo_izq, angulo_der)
                criterio_izq = criterio_der = ("kiba_dachi", "rodilla")

            # CASO 3: peso ADELANTE — rodilla frontal flexionada y trasera
            # extendida y tensa -> Zenkutsu Dachi (postura adelantada).
            # `guardia is not None` no es una comprobación defensiva: es la
            # condición que impide volver a confundir un Zenkutsu con un
            # Kokutsu. Son la misma postura con las piernas intercambiadas, así
            # que sin saber cuál va adelante NO se puede elegir entre las dos, y
            # elegir igualmente producía la otra postura con veredicto positivo.
            # Desde el 21-oct-2026 también de perfil con la delantera hasta 140°,
            # con la trasera doblada o alto: ver `clasificar_postura`.
            elif postura == "zenkutsu_dachi":
                es_correcto, msg, color = self.reglas.evaluate_zenkutsu_dachi(angulo_frontal, angulo_trasero)
                postura_detectada = f"ZENKUTSU ({guardia})"
                tecnica = "zenkutsu_dachi"
                angulos_regla = (angulo_frontal, angulo_trasero)
                criterio_frontal = ("zenkutsu_dachi", "rodilla_frontal")
                criterio_trasero = ("zenkutsu_dachi", "rodilla_trasera")
                criterio_izq, criterio_der = (
                    (criterio_frontal, criterio_trasero) if guardia == IZQ_ADELANTE
                    else (criterio_trasero, criterio_frontal))

            # CASO 4: peso ATRÁS — rodilla frontal casi extendida y trasera
            # flexionada -> Kokutsu Dachi (postura atrasada). Es la distribución
            # inversa del caso anterior, y es exactamente lo que la versión previa
            # tenía al revés: exigía la frontal flexionada, de modo que un Kokutsu
            # bien ejecutado (frontal ~160°, trasera ~105°) no coincidía con
            # ninguna rama y terminaba reportado como "EN TRANSICION".
            elif postura == "kokutsu_dachi":
                es_correcto, msg, color = self.reglas.evaluate_kokutsu_dachi(angulo_frontal, angulo_trasero)
                postura_detectada = f"KOKUTSU ({guardia})"
                tecnica = "kokutsu_dachi"
                angulos_regla = (angulo_frontal, angulo_trasero)
                criterio_frontal = ("kokutsu_dachi", "rodilla_frontal")
                criterio_trasero = ("kokutsu_dachi", "rodilla_trasera")
                criterio_izq, criterio_der = (
                    (criterio_frontal, criterio_trasero) if guardia == IZQ_ADELANTE
                    else (criterio_trasero, criterio_frontal))

            # CASO 5: Transición (el usuario se está moviendo entre posturas) — no es una
            # evaluación (nada que calificar de correcto/incorrecto), por eso es_correcto=None.
            # CASO 5a: el cuerpo SÍ dibuja una postura asimétrica —una rodilla
            # flexionada y la otra extendida, que es la firma de Zenkutsu y
            # Kokutsu— pero no se distingue cuál pierna va adelante. Merece un
            # mensaje propio y no el de transición: el ejecutante no se está
            # moviendo, es la toma la que no permite decidir. Decirlo convierte
            # un fallo mudo en una instrucción accionable (grabar de perfil).
            elif postura == "guardia_indefinida":
                es_correcto = None
                msg = "NO SE DISTINGUE QUE PIERNA VA ADELANTE"
                color = (0, 165, 255)  # Naranja
                postura_detectada = "GUARDIA INDEFINIDA"
                tecnica = None
                angulos_regla = None
                criterio_izq = criterio_der = None

            # CASO 5b: Transición (el usuario se está moviendo entre posturas) — no es una
            # evaluación (nada que calificar de correcto/incorrecto), por eso es_correcto=None.
            else:
                es_correcto = None
                msg = "EN TRANSICION..."
                color = (0, 165, 255) # Naranja
                postura_detectada = "MOVIENDOSE"
                tecnica = None  # una transicion no se juzga contra ningun umbral
                angulos_regla = None  # ...asi que tampoco hay nada que volver a juzgar
                criterio_izq = criterio_der = None


            # Agregamos los resultados visuales
            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (rodilla_izq[0] + 20, rodilla_izq[1]),
                "mensaje": f"{postura_detectada}: {msg}", "color": color, "y_offset": 130,
                "categoria": "postura", "correcto": es_correcto,
                "id_umbral": self.reglas.id_umbral_principal(tecnica) if tecnica else None,
                # `angulo` (arriba) es el de la rodilla IZQUIERDA, porque es el
                # número que se dibuja junto a esa rodilla en pantalla.
                # `angulos_regla` es otra cosa: los argumentos con que se juzgó,
                # ordenados como los consume la regla. Separarlos es lo que evita
                # que un Kokutsu con la derecha adelante quede guardado con la
                # rodilla trasera en el lugar de la frontal.
                "tecnica": tecnica, "angulos_regla": angulos_regla
            })
            resultados.append({
                "angulo": angulo_der, "pos_angulo": (rodilla_der[0] - 60, rodilla_der[1]),
                "mensaje": "", "color": color, "y_offset": 130, "categoria": "postura_der_numero",
                "correcto": es_correcto,
                # Esta entrada solo pinta el número de la rodilla derecha; no se
                # persiste (mensaje vacío), por eso no arrastra técnica.
                "tecnica": None, "angulos_regla": None
            })

            # Una fila por rodilla para el panel en vivo. `gui/panel_vivo.py` ya
            # declaraba "Rodilla izquierda" y "Rodilla derecha", pero los
            # diagnósticos de postura viajan bajo la categoría `postura`, que
            # nunca coincide con las que el panel busca: las dos filas llevaban
            # desde siempre un guion, aunque los ángulos se midieran, se
            # filtraran y se usaran para clasificar.
            #
            # Cada rodilla trae SU propio veredicto, contra el rango que le
            # corresponde: en un Zenkutsu la frontal y la trasera se juzgan con
            # criterios distintos, así que teñir ambas con el veredicto global
            # escondería cuál de las dos hay que corregir. Sin postura
            # reconocida no hay criterio, y el veredicto es None.
            #
            # Van con `mensaje` vacío a propósito: el registro de la postura ya
            # lo lleva la entrada `postura`, y duplicarlo llenaría la base de
            # datos y el panel de correcciones con la misma medición dos veces.
            for categoria, angulo_rodilla, criterio, rodilla in (
                    ("rodilla_izq", angulo_izq, criterio_izq, rodilla_izq),
                    ("rodilla_der", angulo_der, criterio_der, rodilla_der)):
                resultados.append({
                    "angulo": angulo_rodilla, "pos_angulo": None,
                    "pos_articulacion": rodilla,
                    "mensaje": "", "color": color, "y_offset": 130,
                    "categoria": categoria,
                    "correcto": (None if criterio is None
                                 else self.reglas.dentro(angulo_rodilla, *criterio)),
                    "tecnica": None, "angulos_regla": None
                })
        else:
            # Piernas ocultas: reseteamos los filtros para no arrastrar valores viejos
            self.filtros["rodilla_izq"].reset()
            self.filtros["rodilla_der"].reset()
            self.filtros["guardia"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "PIERNAS: OCULTAS/NO VISIBLES", "color": (0, 165, 255), "y_offset": 130,
                "categoria": "postura", "correcto": None,
                "tecnica": None, "angulos_regla": None
            })

        return resultados

    #Patadas
    def analyze_mae_geri(self, landmarks, w, h, timestamp_ms):
        """
        Analiza el Mae Geri en AMBAS piernas usando una máquina de estados
        (Carga -> Extension/Kime -> Recuperando/Hikiashi). A diferencia de
        analyze_stance, aquí no importa qué pierna está "adelante": cualquiera
        de las dos puede ser la que patea.
        """
        resultados = []

        # Mismo mapeo de espejo que analyze_stance: 24/26/28 = "izq" visual
        piernas = {
            "izq": (landmarks[24], landmarks[26], landmarks[28], self.maquinas_patada["izq"], 170),
            "der": (landmarks[23], landmarks[25], landmarks[27], self.maquinas_patada["der"], 200),
        }

        for lado, (cadera_lm, rodilla_lm, tobillo_lm, maquina, y_offset) in piernas.items():
            visible = (cadera_lm.visibility > self.umbral and
                       rodilla_lm.visibility > self.umbral and
                       tobillo_lm.visibility > self.umbral)

            angulo_crudo, rodilla_px = None, None
            if visible:
                cadera = (int(cadera_lm.x * w), int(cadera_lm.y * h))
                rodilla_px = (int(rodilla_lm.x * w), int(rodilla_lm.y * h))
                tobillo = (int(tobillo_lm.x * w), int(tobillo_lm.y * h))
                angulo_crudo = BiomechanicsMath.calculate_angle(cadera, rodilla_px, tobillo)

            # tobillo_lm.y normalizado (0-1), no en píxeles: así el margen de
            # "pie en el aire" no depende de la resolución de la cámara.
            res = maquina.update(visible, angulo_crudo, tobillo_lm.y, timestamp_ms)
            if res is not None:
                resultados.append({
                    "angulo": res["angulo"],
                    "pos_angulo": (rodilla_px[0] + 20, rodilla_px[1]) if rodilla_px else None,
                    "pos_articulacion": rodilla_px,
                    "mensaje": f"{lado.upper()} - {res['mensaje']}",
                    "color": res["color"],
                    "y_offset": y_offset,
                    "categoria": f"mae_geri_{lado}",
                    "correcto": res.get("correcto"),
                    "id_umbral": res.get("id_umbral"),
                    # Sin `angulos_regla`: el Kime se juzga por ángulo Y por
                    # velocidad angular pico, y esa segunda magnitud la observa
                    # la máquina de estados a lo largo de varios fotogramas. Con
                    # un solo ángulo, recalcular el veredicto lo inventaría.
                    "tecnica": "mae_geri", "angulos_regla": None,
                })

        return resultados