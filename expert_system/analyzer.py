from biomechanics.geometry import BiomechanicsMath
from biomechanics.filters import MovingAverageFilter
from expert_system.knowledge_base import KarateRules
from expert_system.kick_state_machine import MaeGeriStateMachine

#Brazos
class TechniqueAnalyzer:
    def __init__(self, umbral_visibilidad=0.65, ventana_filtro=5):
        self.umbral = umbral_visibilidad
        # ANTI-JITTER: un filtro con memoria por cada articulación medida.
        # Suaviza el ángulo ANTES de que el clasificador y las reglas lo evalúen.
        self.filtros = {
            "codo_izq": MovingAverageFilter(ventana_filtro),
            "codo_der": MovingAverageFilter(ventana_filtro),
            "rodilla_izq": MovingAverageFilter(ventana_filtro),
            "rodilla_der": MovingAverageFilter(ventana_filtro),
            # Suaviza la diferencia de profundidad (Z) usada para decidir qué pierna
            # está adelante. El eje Z de MediaPipe es más ruidoso que X/Y, y sin
            # filtrar, la guardia detectada puede "parpadear" entre IZQ/DER ADELANTE.
            "guardia_z": MovingAverageFilter(ventana_filtro),
        }
        # Una máquina de estados independiente por pierna: cualquiera de las dos
        # puede ser la que patea, no depende de la guardia/eje Z (ver diseño en
        # kick_state_machine.py).
        self.maquinas_patada = {
            "izq": MaeGeriStateMachine(ventana_filtro),
            "der": MaeGeriStateMachine(ventana_filtro),
        }

    def analyze_tsuki(self, landmarks, w, h):
        """
        Analiza la técnica de Tsuki en AMBOS brazos y devuelve una lista de resultados
        lista para que el Renderer los dibuje.
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
            es_correcto, msg, color = KarateRules.evaluate_tsuki(angulo_izq)

            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (codo_izq[0] + 20, codo_izq[1]),
                "mensaje": f"IZQ - {msg}", "color": color, "y_offset": 50, "categoria": "codo_izq",
                "correcto": es_correcto
            })
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer
            self.filtros["codo_izq"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO IZQ: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 50,
                "categoria": "codo_izq", "correcto": None
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
            es_correcto, msg, color = KarateRules.evaluate_tsuki(angulo_der)

            resultados.append({
                "angulo": angulo_der, "pos_angulo": (codo_der[0] - 60, codo_der[1]), # -60 para que no tape el codo
                "mensaje": f"DER - {msg}", "color": color, "y_offset": 90, "categoria": "codo_der",
                "correcto": es_correcto
                # Más abajo para no chocar con el texto izq
            })
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer
            self.filtros["codo_der"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO DER: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 90,
                "categoria": "codo_der", "correcto": None
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

            # Lógica de Profundidad (Eje Z) para saber qué pierna está adelante.
            # Filtramos la diferencia Z (no solo los ángulos) porque es la señal
            # más ruidosa: sin suavizarla, la guardia puede "parpadear" de un
            # frame a otro aunque el usuario esté completamente quieto.
            z_diff_crudo = tobillo_izq_lm.z - tobillo_der_lm.z
            z_diff = self.filtros["guardia_z"].update(z_diff_crudo)

            if z_diff < 0:
                angulo_frontal = angulo_izq
                angulo_trasero = angulo_der
                guardia = "IZQ ADELANTE"
            else:
                angulo_frontal = angulo_der
                angulo_trasero = angulo_izq
                guardia = "DER ADELANTE"

            # ---------------------------------------------------------
            # EL CLASIFICADOR (¿En qué postura está el usuario?)
            # ---------------------------------------------------------
            
            # CASO 1: Si ambas rodillas están casi estiradas (> 160°), asume postura natural (Heiko Dachi / Hachiji Dachi)
            if angulo_izq > 160 and angulo_der > 160:
                es_correcto, msg, color = KarateRules.evaluate_heiko_dachi(angulo_frontal) # Puedes pasarle cualquiera de los dos, o crear una regla específica para las rodillas en Heiko
                postura_detectada = "POSTURA NATURAL"

            # CASO 2: Si AMBAS rodillas están moderadamente flexionadas por igual (130-160),
            # es Kiba Dachi (postura de jinete). Es simétrica, no depende de qué pierna
            # esté "adelante" según el eje Z (por eso usa izq/der directo, no frontal/trasero).
            elif 130 <= angulo_izq <= 160 and 130 <= angulo_der <= 160:
                es_correcto, msg, color = KarateRules.evaluate_kiba_dachi(angulo_izq, angulo_der)
                postura_detectada = "KIBA DACHI"

            # CASO 3: Si la pierna frontal está flexionada (< 130) y la trasera estirada (> 150), es un Zenkutsu
            elif angulo_frontal < 130 and angulo_trasero > 150:
                es_correcto, msg, color = KarateRules.evaluate_zenkutsu_dachi(angulo_frontal, angulo_trasero)
                postura_detectada = f"ZENKUTSU ({guardia})"

            # CASO 4: Pierna frontal flexionada (< 130) y trasera no llega a estirarse del todo
            # (<= 150) -> se acerca más a un Kokutsu Dachi que a una transición real.
            elif angulo_frontal < 130 and angulo_trasero <= 150:
                 es_correcto, msg, color = KarateRules.evaluate_kokutsu_dachi(angulo_frontal, angulo_trasero)
                 postura_detectada = f"KOKUTSU ({guardia})"

            # CASO 5: Transición (el usuario se está moviendo entre posturas) — no es una
            # evaluación (nada que calificar de correcto/incorrecto), por eso es_correcto=None.
            else:
                es_correcto = None
                msg = "EN TRANSICION..."
                color = (0, 165, 255) # Naranja
                postura_detectada = "MOVIENDOSE"


            # Agregamos los resultados visuales
            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (rodilla_izq[0] + 20, rodilla_izq[1]),
                "mensaje": f"{postura_detectada}: {msg}", "color": color, "y_offset": 130,
                "categoria": "postura", "correcto": es_correcto
            })
            resultados.append({
                "angulo": angulo_der, "pos_angulo": (rodilla_der[0] - 60, rodilla_der[1]),
                "mensaje": "", "color": color, "y_offset": 130, "categoria": "postura_der_numero",
                "correcto": es_correcto
            })
        else:
            # Piernas ocultas: reseteamos los filtros para no arrastrar valores viejos
            self.filtros["rodilla_izq"].reset()
            self.filtros["rodilla_der"].reset()
            self.filtros["guardia_z"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "PIERNAS: OCULTAS/NO VISIBLES", "color": (0, 165, 255), "y_offset": 130,
                "categoria": "postura", "correcto": None
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
                    "mensaje": f"{lado.upper()} - {res['mensaje']}",
                    "color": res["color"],
                    "y_offset": y_offset,
                    "categoria": f"mae_geri_{lado}",
                    "correcto": res.get("correcto"),
                })

        return resultados