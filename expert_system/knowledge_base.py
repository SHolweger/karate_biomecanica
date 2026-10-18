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
    # KOKUTSU DACHI — corregido el 14-sep-2026.
    # El modelo anterior (frontal 100-120, trasera 90-110) describía ambas
    # rodillas profundamente flexionadas, que no es un Kokutsu: en la postura
    # atrasada el peso va sobre la pierna de atrás, de modo que la rodilla
    # TRASERA se flexiona y la FRONTAL queda casi extendida. Con los valores
    # viejos, una ejecución correcta caía en "EN TRANSICION" y nunca se
    # reconocía (ver la prueba de regresión en tests/integration/test_analyzer.py).
    # Los rangos de abajo son provisionales, a confirmar con el cuerpo técnico.
    ("kokutsu_dachi",  "rodilla_frontal"):   (145.0, 175.0, "grados"),
    ("kokutsu_dachi",  "rodilla_trasera"):   ( 90.0, 120.0, "grados"),
    ("mae_geri",       "rodilla_kime"):      (160.0, 180.0, "grados"),
    ("mae_geri",       "velocidad_angular"): (400.0,  None, "grados/segundo"),
}

# Correcciones bibliográficas posteriores a la primera siembra. Una base de
# datos ya sembrada no recibe los valores nuevos de UMBRALES_LITERATURA, porque
# la siembra es idempotente a propósito (no debe pisar lo que un entrenador
# recalibró). Estas entradas se aplican al arrancar SOLO sobre umbrales cuya
# fuente vigente siga siendo 'literatura'; si un instructor ya los ajustó, su
# criterio manda. Ver Database.corregir_umbrales_de_literatura.
CORRECCIONES_LITERATURA = {
    # 14-sep-2026: el modelo original describía ambas rodillas flexionadas, que
    # no es un Kokutsu Dachi. El peso va atrás: trasera flexionada, frontal casi
    # extendida.
    ("kokutsu_dachi", "rodilla_frontal"): (145.0, 175.0),
    ("kokutsu_dachi", "rodilla_trasera"): (90.0, 120.0),
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

# Veredictos de las posturas ASIMÉTRICAS cuando fallan (18-oct-2026).
#
# Zenkutsu y Kokutsu se juzgan con un rango por rodilla, pero respondían
# «POSTURA: CORREGIR ALTURA» igual que Kiba Dachi. En una postura simétrica eso
# basta; en una asimétrica no dice qué rodilla corregir ni hacia dónde, y el
# sistema tenía el dato. Ahora el veredicto nombra la rodilla y el sentido.
#
# El sentido se lee del ángulo de la rodilla, donde 180° es la pierna recta:
# por debajo del rango la rodilla está más doblada de lo que pide la postura
# («EXTIENDE»); por encima, menos («FLEXIONA MAS»). Sale siempre del rango
# VIGENTE, así que sigue al criterio si el cuerpo técnico recalibra.
#
# Es una decisión que cambia la clave con la que la base agrupa los errores
# frecuentes, y se tomó a propósito ANTES de la campaña de recolección: lo
# medido antes del 30-sep ya no sirve para calcular precisión, y la base se
# aparta antes de empezar. El veredicto booleano no cambia —solo el texto—, así
# que la precisión, la gráfica de evolución y la reevaluación del historial,
# que comparan por `correcto`, no se ven afectadas.
FLEXIONA_DELANTERA = "POSTURA: FLEXIONA MAS LA RODILLA DELANTERA"
EXTIENDE_DELANTERA = "POSTURA: EXTIENDE LA RODILLA DELANTERA"
FLEXIONA_TRASERA = "POSTURA: FLEXIONA MAS LA RODILLA TRASERA"
EXTIENDE_TRASERA = "POSTURA: EXTIENDE LA RODILLA TRASERA"
CORREGIR_AMBAS = "POSTURA: CORREGIR AMBAS RODILLAS"

# Declarados aquí y no solo en los `return`: `gui/coaching.sin_traduccion()`
# lee los veredictos de este módulo para avisar si alguno llega al panel sin
# su corrección, y estos se construyen en un método en vez de en un `return`
# literal. Una prueba recorre la regla y comprueba que la lista está completa.
VEREDICTOS_POR_RODILLA = (FLEXIONA_DELANTERA, EXTIENDE_DELANTERA,
                          FLEXIONA_TRASERA, EXTIENDE_TRASERA, CORREGIR_AMBAS)

# Y los dos de la postura bien ejecutada, por el mismo motivo: ya no salen de
# un `return` literal sino de un argumento de `_veredicto_asimetrico`.
ZENKUTSU_CORRECTO = "POSTURA: FIRME"
KOKUTSU_CORRECTO = "POSTURA: ESTABLE"
VEREDICTOS_DECLARADOS = VEREDICTOS_POR_RODILLA + (ZENKUTSU_CORRECTO, KOKUTSU_CORRECTO)


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

    def dentro(self, valor, tecnica, articulacion):
        """
        Si una articulación suelta cumple su rango, sin emitir veredicto de técnica.

        Las reglas `evaluate_*` responden «¿está bien ejecutada la postura?»
        mirando todas las articulaciones que la definen. Esto responde algo más
        pequeño y distinto: «¿esta rodilla concreta está dentro de SU rango?».
        Es lo que permite que el panel en vivo señale CUÁL de las dos rodillas
        falla en vez de teñir ambas con el veredicto global — en un Zenkutsu la
        frontal y la trasera se juzgan contra rangos diferentes, así que un
        único color para las dos escondería exactamente el dato que el sensei
        necesita para corregir.
        """
        return self._dentro(valor, tecnica, articulacion)

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

    def _correccion(self, valor, tecnica, articulacion):
        """
        Hacia dónde hay que mover una rodilla para entrar en su rango, o None.

        «extender» si está más doblada de lo que pide el rango; «flexionar» si
        lo está menos. Usa los mismos límites inclusivos que `_dentro`, de modo
        que una rodilla que `_dentro` acepta nunca recibe corrección.
        """
        minimo, maximo = self.rango(tecnica, articulacion)
        if valor < minimo:
            return "extender"
        if maximo is not None and valor > maximo:
            return "flexionar"
        return None

    def _veredicto_asimetrico(self, tecnica, front_knee_angle, back_knee_angle, correcto):
        """
        Veredicto de una postura asimétrica: nombra la rodilla que falla.

        `correcto` es el mensaje de la postura bien ejecutada. El booleano es
        exactamente el de siempre —las dos rodillas dentro de su rango—; lo
        único que cambia respecto de antes del 18-oct-2026 es que, cuando
        falla, el texto dice cuál rodilla corregir y hacia dónde en vez de un
        «CORREGIR ALTURA» que valía igual para cualquiera de las dos.
        """
        delantera = self._correccion(front_knee_angle, tecnica, "rodilla_frontal")
        trasera = self._correccion(back_knee_angle, tecnica, "rodilla_trasera")

        if delantera is None and trasera is None:
            return True, correcto, VERDE
        if delantera is not None and trasera is not None:
            return False, CORREGIR_AMBAS, ROJO
        if delantera is not None:
            return False, (FLEXIONA_DELANTERA if delantera == "flexionar"
                           else EXTIENDE_DELANTERA), ROJO
        return False, (FLEXIONA_TRASERA if trasera == "flexionar"
                       else EXTIENDE_TRASERA), ROJO

    def evaluate_zenkutsu_dachi(self, front_knee_angle, back_knee_angle):
        """
        Evalúa postura adelantada.
        Rodilla delantera flexionada, rodilla trasera extendida y tensa.
        Si falla, el veredicto nombra la rodilla: ver `_veredicto_asimetrico`.
        """
        return self._veredicto_asimetrico("zenkutsu_dachi", front_knee_angle,
                                          back_knee_angle, ZENKUTSU_CORRECTO)

    def evaluate_kokutsu_dachi(self, front_knee_angle, back_knee_angle):
        """
        Evalúa la postura atrasada (Kokutsu Dachi).

        El peso descansa sobre la pierna trasera: esa rodilla se flexiona
        profundamente mientras la delantera permanece casi extendida. Es la
        distribución INVERSA a la del Zenkutsu Dachi, y es lo que distingue
        ambas posturas cuando se las mide por ángulos articulares.
        Si falla, el veredicto nombra la rodilla: ver `_veredicto_asimetrico`.
        """
        return self._veredicto_asimetrico("kokutsu_dachi", front_knee_angle,
                                          back_knee_angle, KOKUTSU_CORRECTO)

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
