"""
Base de conocimientos del sistema experto.

Los umbrales dejaron de ser constantes escritas dentro de cada regla y pasaron
a ser DATOS consultables (RF-08). La clase se instancia con los umbrales
vigentes que entrega la base de datos; sin argumento cae en los valores de
literatura declarados abajo, de modo que la base de conocimientos sigue siendo
utilizable sin base de datos (pruebas automatizadas y arranque en frío).

Esto es lo que permite el modelo evolutivo de dos fases descrito en el
Capítulo 3: el sistema arranca con umbrales bibliográficos y los reemplaza por
los promediados de instructores de grado Dan sin modificar el código fuente.
"""

# Valores iniciales, tomados de la literatura del estilo Shotokan y del criterio
# del cuerpo técnico. Formato: (tecnica, articulacion) -> (min, max, unidad).
# Un máximo en None significa "sin límite superior".
UMBRALES_LITERATURA = {
    ("tsuki",          "codo"):              (160.0, 175.0, "grados"),
    ("age_uke",        "codo"):              (120.0, 140.0, "grados"),
    ("heiko_dachi",    "rodilla"):           (165.0, 180.0, "grados"),
    ("kiba_dachi",     "rodilla"):           (130.0, 150.0, "grados"),
    ("zenkutsu_dachi", "rodilla_frontal"):   ( 90.0, 115.0, "grados"),
    ("zenkutsu_dachi", "rodilla_trasera"):   (165.0, 180.0, "grados"),
    ("kokutsu_dachi",  "rodilla_frontal"):   (100.0, 120.0, "grados"),
    ("kokutsu_dachi",  "rodilla_trasera"):   ( 90.0, 110.0, "grados"),
    ("mae_geri",       "rodilla_kime"):      (160.0, 180.0, "grados"),
    ("mae_geri",       "velocidad_angular"): (400.0,  None, "grados/segundo"),
}

# Articulación que define a cada técnica. Se usa para saber qué versión de umbral
# anotar junto a la medición cuando una técnica se evalúa contra varios rangos
# (por ejemplo Zenkutsu Dachi, que contrasta rodilla frontal y trasera).
ARTICULACION_PRINCIPAL = {
    "tsuki": "codo",
    "age_uke": "codo",
    "heiko_dachi": "rodilla",
    "kiba_dachi": "rodilla",
    "zenkutsu_dachi": "rodilla_frontal",
    "kokutsu_dachi": "rodilla_frontal",
    "mae_geri": "rodilla_kime",
}

VERDE = (0, 255, 0)
ROJO = (0, 0, 255)
AMARILLO = (0, 255, 255)   # En BGR el amarillo es (0,255,255); (255,255,0) seria cian.


class KarateRules:
    """
    Reglas biomecánicas del Karate Shotokan.

    Cada método recibe magnitudes cinemáticas puras y devuelve una tupla
    (es_correcto, mensaje, color_BGR). Ninguna regla conoce MediaPipe, píxeles
    ni la resolución de la cámara: eso es lo que permite verificarlas con
    valores numéricos sintéticos.
    """

    def __init__(self, umbrales_bd=None):
        """
        umbrales_bd: lo que devuelve Database.cargar_umbrales_vigentes(),
        indexado por (tecnica, articulacion). Los valores de literatura se
        cargan siempre primero y la base de datos los sobrescribe, de modo que
        un umbral que todavía no exista en la tabla no deja al sistema sin regla.
        """
        self._rangos = {clave: (v_min, v_max)
                        for clave, (v_min, v_max, _u) in UMBRALES_LITERATURA.items()}
        self._ids = {clave: None for clave in UMBRALES_LITERATURA}

        for clave, fila in (umbrales_bd or {}).items():
            self._rangos[clave] = (fila["valor_min"], fila["valor_max"])
            self._ids[clave] = fila["id_umbral"]

    # ---------------- acceso a los umbrales ----------------

    def rango(self, tecnica, articulacion):
        """Devuelve (minimo, maximo) del umbral vigente. maximo puede ser None."""
        return self._rangos[(tecnica, articulacion)]

    def id_umbral_principal(self, tecnica):
        """
        Identificador de la versión de umbral con la que se evaluó la técnica.
        Es lo que se guarda junto a cada medición para que recalibrar no deje
        el historial sin criterio verificable. None si el umbral aún no
        proviene de la base de datos.
        """
        articulacion = ARTICULACION_PRINCIPAL.get(tecnica)
        return self._ids.get((tecnica, articulacion)) if articulacion else None

    def _dentro(self, valor, tecnica, articulacion):
        minimo, maximo = self.rango(tecnica, articulacion)
        return valor >= minimo and (maximo is None or valor <= maximo)

    # ---------------- GOLPES ----------------

    def evaluate_tsuki(self, elbow_angle):
        """
        Evalúa un golpe recto (Tsuki).
        El codo debe estar casi extendido en el punto de impacto (Kime).
        """
        minimo, maximo = self.rango("tsuki", "codo")
        if minimo <= elbow_angle <= maximo:
            return True, "TSUKI: EXCELENTE", VERDE
        elif elbow_angle > maximo:
            return False, "TSUKI: HIPEREXTENDIDO (Peligro)", ROJO
        else:
            return False, "TSUKI: FLEXIONADO", AMARILLO

    # ---------------- POSTURAS ----------------

    def evaluate_heiko_dachi(self, knee_angle):
        """
        Evalúa postura natural (Heiko Dachi).
        Ambas rodillas casi extendidas; el peso se reparte sin flexión marcada.
        """
        if self._dentro(knee_angle, "heiko_dachi", "rodilla"):
            return True, "HEIKO DACHI: CORRECTO", VERDE
        return False, "HEIKO DACHI: DEMASIADO FLEXIONADO", ROJO

    def evaluate_kiba_dachi(self, left_knee_angle, right_knee_angle):
        """
        Evalúa postura de jinete (Kiba Dachi).
        Postura simétrica y lateral: ambas rodillas flexionadas por igual, sin
        pierna delantera/trasera definida (a diferencia de Zenkutsu/Kokutsu).
        """
        if (self._dentro(left_knee_angle, "kiba_dachi", "rodilla")
                and self._dentro(right_knee_angle, "kiba_dachi", "rodilla")):
            return True, "POSTURA: FIRME", VERDE
        return False, "POSTURA: CORREGIR ALTURA", ROJO

    def evaluate_zenkutsu_dachi(self, front_knee_angle, back_knee_angle):
        """
        Evalúa postura adelantada.
        Rodilla delantera flexionada, rodilla trasera extendida y tensa.
        """
        if (self._dentro(front_knee_angle, "zenkutsu_dachi", "rodilla_frontal")
                and self._dentro(back_knee_angle, "zenkutsu_dachi", "rodilla_trasera")):
            return True, "POSTURA: FIRME", VERDE
        return False, "POSTURA: CORREGIR ALTURA", ROJO

    def evaluate_kokutsu_dachi(self, front_knee_angle, back_knee_angle):
        """
        Evalúa postura atrasada.
        Rodilla delantera ligeramente flexionada, rodilla trasera flexionada.
        """
        if (self._dentro(front_knee_angle, "kokutsu_dachi", "rodilla_frontal")
                and self._dentro(back_knee_angle, "kokutsu_dachi", "rodilla_trasera")):
            return True, "POSTURA: ESTABLE", VERDE
        return False, "POSTURA: CORREGIR ALTURA", ROJO

    # ---------------- PATADAS ----------------

    def evaluate_mae_geri(self, kime_angle, velocidad_pico):
        """
        Evalúa el Kime (extensión) de un Mae Geri.
        La rodilla debe extenderse casi por completo Y hacerlo con velocidad
        angular alta: un ángulo correcto alcanzado lentamente no es un Kime,
        es un levantamiento de pierna.
        """
        angulo_min, _ = self.rango("mae_geri", "rodilla_kime")
        velocidad_min, _ = self.rango("mae_geri", "velocidad_angular")

        if kime_angle < angulo_min:
            return False, "MAE GERI: KIME INCOMPLETO", ROJO
        elif velocidad_pico < velocidad_min:
            return False, "MAE GERI: FALTA EXPLOSIVIDAD", AMARILLO
        else:
            return True, "MAE GERI: KIME EXCELENTE", VERDE

    def evaluate_hikiashi(self, pie_recogido_antes_de_bajar):
        """
        Evalúa el recojo (Hikiashi): la rodilla debe volver a flexionarse ANTES
        de que el pie descienda al nivel del suelo. Si el pie ya estaba a nivel
        de reposo cuando la rodilla se flexiona, la pierna "cayó" en vez de
        recogerse. No consulta umbrales: es una comparación de orden temporal.
        """
        if pie_recogido_antes_de_bajar:
            return True, "HIKIASHI: CORRECTO", VERDE
        return False, "HIKIASHI: PIERNA CAYO SIN RECOGER", ROJO

    # ---------------- DEFENSAS ----------------

    def evaluate_age_uke(self, elbow_angle):
        """
        Evalúa defensa alta (Age Uke).
        El codo debe estar flexionado para bloquear efectivamente.
        """
        minimo, maximo = self.rango("age_uke", "codo")
        if minimo <= elbow_angle <= maximo:
            return True, "AGE UKE: EFECTIVO", VERDE
        elif elbow_angle < minimo:
            return False, "AGE UKE: DEMASIADO FLEXIONADO", ROJO
        else:
            return False, "AGE UKE: DEMASIADO EXTENDIDO", AMARILLO
