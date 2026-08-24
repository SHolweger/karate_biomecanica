from biomechanics.filters import MovingAverageFilter
from expert_system.knowledge_base import KarateRules

# Estados de la máquina
REPOSO = "REPOSO"
CARGA = "CARGA"
EXTENSION = "EXTENSION"
RECUPERANDO = "RECUPERANDO"

# Umbrales de ángulo de rodilla (grados). Provisionales, a calibrar con datos
# reales de karategui en la Semana 4 (misma filosofía que el resto de umbrales
# del proyecto: se parte de valores de la literatura y se ajustan después).
UMBRAL_CARGA = 75        # Rodilla muy flexionada = talón recogido. Calibrado el
                          # 12-ago-2026: la carga inicial real llegó a 52-55°, pero
                          # el recojo/hikiashi natural solo bajó a ~71-90° — con 60°
                          # el ciclo nunca cerraba porque el recojo no llegaba tan
                          # profundo como la carga deliberada del inicio.
UMBRAL_EXTENSION = 160   # Rodilla casi extendida = Kime (mismo criterio que evaluate_tsuki)
UMBRAL_APOYO = 140       # Pierna vuelve a estar bajo el cuerpo, lista para una nueva patada

# Timeouts anti-atasco: si la técnica no progresa, se descarta el intento.
# Calibrados el 12-ago-2026 contra grabación real: los valores originales
# (2000/1500ms) asumían una patada explosiva ininterrumpida y descartaban
# intentos deliberadamente lentos (ej. el practicante pausa para observar
# el diagnóstico en pantalla durante las pruebas). Se amplían para tolerar
# ejecuciones lentas sin perder la función de "anti-atasco" real.
TIMEOUT_CARGA_MS = 4000
TIMEOUT_EXTENSION_MS = 3000

# Oclusión: cuántos frames seguidos se tolera perder de vista la pierna antes
# de abortar la técnica en curso (~150-200ms a 30fps).
TOLERANCIA_FRAMES_OCULTO = 5

# Margen (coordenada Y normalizada 0-1) para decidir si el pie ya bajó al
# nivel de reposo o sigue recogido en el aire.
MARGEN_PIE_AIRE = 0.05

NARANJA = (0, 165, 255)


class MaeGeriStateMachine:
    """
    Máquina de estados para evaluar un Mae Geri (patada frontal) en movimiento,
    dividiéndolo en Carga -> Extension (Kime) -> Recuperando (Hikiashi) -> Reposo.

    No conoce MediaPipe ni píxeles: solo recibe el ángulo de rodilla ya calculado,
    visibilidad, la posición Y del tobillo (normalizada) y un timestamp. Esto
    permite probarla con números sintéticos, sin cámara (ver test_mae_geri_fsm.py).
    """

    def __init__(self, ventana_filtro=5):
        self.filtro_angulo = MovingAverageFilter(ventana_filtro)
        self._reset_estado()

    def _reset_estado(self):
        self.estado = REPOSO
        self.angulo_anterior = None
        self.t_anterior_ms = None
        self.velocidad_pico = 0.0
        self.angulo_maximo_extension = 0.0
        self.ankle_y_reposo = None
        self.tiempo_entrada_estado_ms = None
        self.frames_ocultos = 0
        self.ultimo_resultado = None

    def reset(self):
        """Reinicia la máquina por completo (oclusión prolongada a mitad de técnica)."""
        self.filtro_angulo.reset()
        self._reset_estado()

    def update(self, visible, angulo_crudo, ankle_y, t_ms):
        """
        Procesa un frame. Devuelve un dict de diagnóstico listo para el renderer,
        o None si no hay nada que mostrar (ej. estado REPOSO, sin técnica en curso).
        """
        if not visible:
            return self._manejar_oclusion()

        self.frames_ocultos = 0
        angulo = self.filtro_angulo.update(angulo_crudo)
        velocidad = self._calcular_velocidad(angulo, t_ms)

        if self.estado in (CARGA, EXTENSION):
            self.velocidad_pico = max(self.velocidad_pico, abs(velocidad))

        resultado = self._procesar_transicion(angulo, ankle_y, t_ms)
        if resultado is not None:
            self.ultimo_resultado = resultado
        return resultado

    def _manejar_oclusion(self):
        self.frames_ocultos += 1
        if self.frames_ocultos > TOLERANCIA_FRAMES_OCULTO and self.estado != REPOSO:
            resultado = {
                "angulo": None,
                "mensaje": "MAE GERI: TECNICA PERDIDA (oclusion)",
                "color": NARANJA,
                "correcto": None,  # técnica abortada, no hay nada que calificar
            }
            self.reset()
            return resultado
        # Oclusión breve: no tocamos el estado ni el filtro, repetimos el
        # último diagnóstico en vez de borrarlo justo en el momento crítico.
        return self.ultimo_resultado

    def _calcular_velocidad(self, angulo, t_ms):
        """Derivada discreta: (delta angulo / delta tiempo) en grados/segundo."""
        if self.angulo_anterior is None or self.t_anterior_ms is None:
            velocidad = 0.0
        else:
            dt_ms = t_ms - self.t_anterior_ms
            velocidad = 0.0 if dt_ms <= 0 else (angulo - self.angulo_anterior) / dt_ms * 1000.0
        self.angulo_anterior = angulo
        self.t_anterior_ms = t_ms
        return velocidad

    def _tiempo_en_estado_actual(self, t_ms):
        if self.tiempo_entrada_estado_ms is None:
            return 0
        return t_ms - self.tiempo_entrada_estado_ms

    def _entrar_estado(self, nuevo_estado, t_ms):
        self.estado = nuevo_estado
        self.tiempo_entrada_estado_ms = t_ms

    def _procesar_transicion(self, angulo, ankle_y, t_ms):
        if self.estado == REPOSO:
            # Guardamos la referencia de "pie en el suelo" mientras el usuario
            # está de pie, para comparar después si el Hikiashi recogió el pie
            # antes de bajarlo.
            self.ankle_y_reposo = ankle_y
            if angulo < UMBRAL_CARGA:
                self.velocidad_pico = 0.0
                self._entrar_estado(CARGA, t_ms)
                return {"angulo": angulo, "mensaje": "MAE GERI: CARGA", "color": NARANJA, "correcto": None}
            return None

        if self.estado == CARGA:
            if angulo > UMBRAL_EXTENSION:
                self.angulo_maximo_extension = angulo
                self._entrar_estado(EXTENSION, t_ms)
                return {"angulo": angulo, "mensaje": "MAE GERI: EXTENSION...", "color": NARANJA, "correcto": None}
            if self._tiempo_en_estado_actual(t_ms) > TIMEOUT_CARGA_MS:
                # Se quedó cargando sin abrir la pierna: se descarta el intento,
                # sin diagnóstico final (no fue una patada completa).
                self._entrar_estado(REPOSO, t_ms)
                return None
            return {"angulo": angulo, "mensaje": "MAE GERI: CARGA", "color": NARANJA, "correcto": None}

        if self.estado == EXTENSION:
            self.angulo_maximo_extension = max(self.angulo_maximo_extension, angulo)

            if angulo < UMBRAL_CARGA:
                # Se cierra el Kime y se evalúa el Hikiashi en el mismo instante.
                es_kime_ok, msg_kime, color_kime = KarateRules.evaluate_mae_geri(
                    self.angulo_maximo_extension, self.velocidad_pico)
                pie_recogido = ankle_y < (self.ankle_y_reposo - MARGEN_PIE_AIRE)
                es_hiki_ok, msg_hiki, color_hiki = KarateRules.evaluate_hikiashi(pie_recogido)

                # El peor de los dos resultados manda el color mostrado. La técnica
                # completa solo cuenta como "correcta" si AMBAS fases lo fueron.
                color = color_kime if not es_kime_ok else color_hiki
                es_correcto = es_kime_ok and es_hiki_ok

                self._entrar_estado(RECUPERANDO, t_ms)
                return {"angulo": angulo, "mensaje": f"{msg_kime} | {msg_hiki}", "color": color,
                        "correcto": es_correcto}

            if self._tiempo_en_estado_actual(t_ms) > TIMEOUT_EXTENSION_MS:
                # Sostuvo el Kime sin recoger la pierna: se descarta el intento.
                self._entrar_estado(REPOSO, t_ms)
                return None

            return {"angulo": angulo, "mensaje": "MAE GERI: EXTENSION...", "color": NARANJA, "correcto": None}

        if self.estado == RECUPERANDO:
            if angulo > UMBRAL_APOYO:
                self._entrar_estado(REPOSO, t_ms)
            # Seguimos mostrando el diagnóstico final del Kime/Hikiashi mientras
            # la pierna termina de asentarse.
            return self.ultimo_resultado

        return None
