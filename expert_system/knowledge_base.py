class KarateRules:
#GOLPES
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
            return False, "TSUKI: FLEXIONADO", (255, 255, 0) # Amarillo

    #POSTURAS    
    @staticmethod
    def evaluate_heiko_dachi(elbow_angle):
        """
        Evalúa postura básica (Heiko Dachi).
        El codo debe estar ligeramente flexionado (150°-170°) para mantener energía y preparación.
        """
        if 150 <= elbow_angle <= 170:
            return True, "HEIKO DACHI: CORRECTO", (0, 255, 0)
        elif elbow_angle < 150:
            return False, "HEIKO DACHI: DEMASIADO FLEXIONADO", (0, 0, 255)
        else:
            return False, "HEIKO DACHI: DEMASIADO EXTENDIDO", (255, 255, 0)

    @staticmethod
    def evaluate_zenkutsu_dachi(front_knee_angle, back_knee_angle):
        """
        Evalúa postura adelantada.
        Rodilla delantera flexionada (~90°-115°).
        Rodilla trasera extendida y tensa (~165°-180°).
        """
        front_correct = 90 <= front_knee_angle <= 115
        back_correct = 165 <= back_knee_angle <= 180

        if front_correct and back_correct:
            return True, "POSTURA: FIRME", (0, 255, 0)
        else:
            return False, "POSTURA: CORREGIR ALTURA", (0, 0, 255)
    
    @staticmethod 
    def evaluate_kokutsu_dachi(front_knee_angle, back_knee_angle): 
        """
        Evalúa postura atrasada.
        Rodilla delantera ligeramente flexionada (~100°-120°).
        Rodilla trasera flexionada (~90°-110°).
        """
        front_correct = 100 <= front_knee_angle <= 120
        back_correct = 90 <= back_knee_angle <= 110

        if front_correct and back_correct:
            return True, "POSTURA: ESTABLE", (0, 255, 0)
        else:
            return False, "POSTURA: CORREGIR ALTURA", (0, 0, 255)
        
#DEFENSAS
    @staticmethod
    def evaluate_age_uke(elbow_angle):
        """
        Evalúa defensa alta (Age Uke).
        El codo debe estar flexionado entre 120°-140° para bloquear efectivamente.
        """
        if 120 <= elbow_angle <= 140:
            return True, "AGE UKE: EFECTIVO", (0, 255, 0)
        elif elbow_angle < 120:
            return False, "AGE UKE: DEMASIADO FLEXIONADO", (0, 0, 255)
        else:
            return False, "AGE UKE: DEMASIADO EXTENDIDO", (255, 255, 0)