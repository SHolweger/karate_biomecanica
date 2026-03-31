class KarateRules:
    @staticmethod
    def evaluate_tsuki(elbow_angle):
        """
        Evalúa un golpe recto (Tsuki).
        El codo debe estar casi extendido (160°-175°) en el punto de impacto (Kime).
        """
        if 160 <= elbow_angle <= 175:
            # Devuelve: (Es correcto?, Mensaje, Color en formato BGR de OpenCV)
            return True, "TSUKI: EXCELENTE", (0, 255, 0)  # Verde
        elif elbow_angle > 175:
            return False, "TSUKI: HIPEREXTENDIDO (Peligro)", (0, 0, 255) # Rojo
        else:
            return False, "TSUKI: FLEXIONADO", (0, 165, 255) # Naranja

    @staticmethod
    def evaluate_zenkutsu_dachi(front_knee_angle, back_knee_angle):
        """
        Evalúa la postura frontal.
        Rodilla delantera flexionada (~90°-115°).
        Rodilla trasera extendida y tensa (~165°-180°).
        """
        front_correct = 90 <= front_knee_angle <= 115
        back_correct = 165 <= back_knee_angle <= 180

        if front_correct and back_correct:
            return True, "POSTURA: FIRME", (0, 255, 0)
        else:
            return False, "POSTURA: CORREGIR ALTURA", (0, 0, 255)