from biomechanics.geometry import BiomechanicsMath
from biomechanics.filters import MovingAverageFilter
from expert_system.knowledge_base import KarateRules

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
            _, msg, color = KarateRules.evaluate_tsuki(angulo_izq)
            
            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (codo_izq[0] + 20, codo_izq[1]),
                "mensaje": f"IZQ - {msg}", "color": color, "y_offset": 50
            })
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer
            self.filtros["codo_izq"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO IZQ: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 50
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
            _, msg, color = KarateRules.evaluate_tsuki(angulo_der)
            
            resultados.append({
                "angulo": angulo_der, "pos_angulo": (codo_der[0] - 60, codo_der[1]), # -60 para que no tape el codo
                "mensaje": f"DER - {msg}", "color": color, "y_offset": 90 # Más abajo para no chocar con el texto izq
            })
        else:
            # Brazo oculto: reseteamos el filtro para no promediar con datos viejos al reaparecer
            self.filtros["codo_der"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO DER: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 90
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

            # Lógica de Profundidad (Eje Z) para saber qué pierna está adelante
            if tobillo_izq_lm.z < tobillo_der_lm.z:
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
                
            # CASO 2: Si la pierna frontal está flexionada (< 130) y la trasera estirada (> 150), es un Zenkutsu
            elif angulo_frontal < 130 and angulo_trasero > 150:
                es_correcto, msg, color = KarateRules.evaluate_zenkutsu_dachi(angulo_frontal, angulo_trasero)
                postura_detectada = f"ZENKUTSU ({guardia})"
                
            # CASO 3: Si ambas rodillas están flexionadas, podría ser Kokutsu Dachi o Kiba Dachi
            elif angulo_frontal < 130 and angulo_trasero < 130:
                 es_correcto, msg, color = KarateRules.evaluate_kokutsu_dachi(angulo_frontal, angulo_trasero)
                 postura_detectada = f"KOKUTSU/KIBA ({guardia})"
                 
            # CASO 4: Transición (El usuario se está moviendo)
            else:
                msg = "EN TRANSICION..."
                color = (0, 165, 255) # Naranja
                postura_detectada = "MOVIENDOSE"


            # Agregamos los resultados visuales
            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (rodilla_izq[0] + 20, rodilla_izq[1]),
                "mensaje": f"{postura_detectada}: {msg}", "color": color, "y_offset": 130
            })
            resultados.append({
                "angulo": angulo_der, "pos_angulo": (rodilla_der[0] - 60, rodilla_der[1]),
                "mensaje": "", "color": color, "y_offset": 130 
            })
        else:
            # Piernas ocultas: reseteamos ambos filtros para no arrastrar valores viejos
            self.filtros["rodilla_izq"].reset()
            self.filtros["rodilla_der"].reset()
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "PIERNAS: OCULTAS/NO VISIBLES", "color": (0, 165, 255), "y_offset": 130
            })

        return resultados