from biomechanics.geometry import BiomechanicsMath
from expert_system.knowledge_base import KarateRules

class TechniqueAnalyzer:
    def __init__(self, umbral_visibilidad=0.65):
        self.umbral = umbral_visibilidad

    def analyze_tsuki(self, landmarks, w, h):
        """
        Analiza la técnica de Tsuki en AMBOS brazos y devuelve una lista de resultados
        lista para que el Renderer los dibuje.
        """
        resultados = []
        
        # ---------------- BRAZO IZQUIERDO ----------------
        hombro_izq_lm, codo_izq_lm, muneca_izq_lm = landmarks[11], landmarks[13], landmarks[15]
        
        if (hombro_izq_lm.visibility > self.umbral and 
            codo_izq_lm.visibility > self.umbral and 
            muneca_izq_lm.visibility > self.umbral):
            
            hombro_izq = (int(hombro_izq_lm.x * w), int(hombro_izq_lm.y * h))
            codo_izq = (int(codo_izq_lm.x * w), int(codo_izq_lm.y * h))
            muneca_izq = (int(muneca_izq_lm.x * w), int(muneca_izq_lm.y * h))
            
            angulo_izq = BiomechanicsMath.calculate_angle(hombro_izq, codo_izq, muneca_izq)
            _, msg, color = KarateRules.evaluate_tsuki(angulo_izq)
            
            resultados.append({
                "angulo": angulo_izq, "pos_angulo": (codo_izq[0] + 20, codo_izq[1]),
                "mensaje": f"IZQ - {msg}", "color": color, "y_offset": 50
            })
        else:
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO IZQ: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 50
            })

        # ---------------- BRAZO DERECHO ----------------
        # Los puntos oficiales de MediaPipe para el lado derecho son 12, 14 y 16
        hombro_der_lm, codo_der_lm, muneca_der_lm = landmarks[12], landmarks[14], landmarks[16]
        
        if (hombro_der_lm.visibility > self.umbral and 
            codo_der_lm.visibility > self.umbral and 
            muneca_der_lm.visibility > self.umbral):
            
            hombro_der = (int(hombro_der_lm.x * w), int(hombro_der_lm.y * h))
            codo_der = (int(codo_der_lm.x * w), int(codo_der_lm.y * h))
            muneca_der = (int(muneca_der_lm.x * w), int(muneca_der_lm.y * h))
            
            angulo_der = BiomechanicsMath.calculate_angle(hombro_der, codo_der, muneca_der)
            _, msg, color = KarateRules.evaluate_tsuki(angulo_der)
            
            resultados.append({
                "angulo": angulo_der, "pos_angulo": (codo_der[0] - 60, codo_der[1]), # -60 para que no tape el codo
                "mensaje": f"DER - {msg}", "color": color, "y_offset": 90 # Más abajo para no chocar con el texto izq
            })
        else:
            resultados.append({
                "angulo": None, "pos_angulo": None,
                "mensaje": "BRAZO DER: OCULTO/NO VISIBLE", "color": (0, 165, 255), "y_offset": 90
            })

        return resultados