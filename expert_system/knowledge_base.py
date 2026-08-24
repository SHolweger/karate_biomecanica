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
            return False, "TSUKI: FLEXIONADO", (0, 255, 255) # Amarillo

    #POSTURAS
    @staticmethod
    def evaluate_heiko_dachi(knee_angle):
        """
        Evalúa postura natural (Heiko Dachi).
        Ambas rodillas casi extendidas (165°-180°); el peso se reparte sin flexión marcada.
        """
        if 165 <= knee_angle <= 180:
            return True, "HEIKO DACHI: CORRECTO", (0, 255, 0)
        else:
            return False, "HEIKO DACHI: DEMASIADO FLEXIONADO", (0, 0, 255)

    @staticmethod
    def evaluate_kiba_dachi(left_knee_angle, right_knee_angle):
        """
        Evalúa postura de jinete (Kiba Dachi).
        Postura simétrica y lateral: ambas rodillas flexionadas por igual (~130°-150°),
        sin pierna delantera/trasera definida (a diferencia de Zenkutsu/Kokutsu).
        """
        left_correct = 130 <= left_knee_angle <= 150
        right_correct = 130 <= right_knee_angle <= 150

        if left_correct and right_correct:
            return True, "POSTURA: FIRME", (0, 255, 0)
        else:
            return False, "POSTURA: CORREGIR ALTURA", (0, 0, 255)

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
        
#PATADAS
    @staticmethod
    def evaluate_mae_geri(kime_angle, velocidad_pico):
        """
        Evalúa el Kime (extensión) de un Mae Geri.
        La rodilla debe extenderse casi por completo (>160°, mismo criterio que
        evaluate_tsuki) Y hacerlo con velocidad angular alta (patada explosiva,
        no un simple levantamiento lento de la pierna). velocidad_pico en grados/segundo.
        """
        UMBRAL_VELOCIDAD_MIN = 400  # °/seg, provisional — calibrar con datos reales (Semana 4)

        if kime_angle < 160:
            return False, "MAE GERI: KIME INCOMPLETO", (0, 0, 255)
        elif velocidad_pico < UMBRAL_VELOCIDAD_MIN:
            return False, "MAE GERI: FALTA EXPLOSIVIDAD", (0, 255, 255)
        else:
            return True, "MAE GERI: KIME EXCELENTE", (0, 255, 0)

    @staticmethod
    def evaluate_hikiashi(pie_recogido_antes_de_bajar):
        """
        Evalúa el recojo (Hikiashi): la rodilla debe volver a flexionarse
        ANTES de que el pie descienda al nivel de suelo. Si el pie ya estaba
        a nivel de reposo cuando la rodilla se flexiona, la pierna "cayó" en
        vez de recogerse.
        """
        if pie_recogido_antes_de_bajar:
            return True, "HIKIASHI: CORRECTO", (0, 255, 0)
        else:
            return False, "HIKIASHI: PIERNA CAYO SIN RECOGER", (0, 0, 255)

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
            return False, "AGE UKE: DEMASIADO EXTENDIDO", (0, 255, 255)