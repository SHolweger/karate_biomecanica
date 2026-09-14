import time
import tkinter

import cv2
import customtkinter as ctk
from PIL import Image

from biomechanics.renderer import SkeletonRenderer
from expert_system.analyzer import TechniqueAnalyzer
from expert_system.knowledge_base import KarateRules
from gui import theme
from gui.camara_screen import fuente_configurada
from gui.panel_vivo import (FeedCorrecciones, PUNTOS_IMU, SIN_DATO, metricas_articulares,
                            veredicto_legible)
from persistence.medicion_logger import MedicionLogger
from vision.camera import Camera
from vision.tracker import PoseTracker


class LiveScreen(ctk.CTkFrame):
    """
    Análisis en vivo (RF-01, RF-03, RF-05, RF-06).

    Reutiliza exactamente el mismo encadenamiento que `main.py --consola`
    (Camera, PoseTracker, SkeletonRenderer, TechniqueAnalyzer); lo único distinto
    es el mecanismo de refresco: en vez del bucle bloqueante `while True` con
    `cv2.imshow`, aquí se usa `self.after(...)`, porque Tkinter necesita su propio
    ciclo de eventos y un bucle bloqueante congelaría la ventana entera.

    La pantalla se divide en dos. A la izquierda el video con las mediciones
    articulares debajo; a la derecha la referencia de la técnica, el estado del
    subsistema inercial y —lo que justifica el sistema— la lista de correcciones
    que el motor va emitiendo. Un porcentaje al final de la sesión no enseña
    nada; "no hiperextiendas el codo" en el momento en que ocurre, sí.

    Quién entrena se elige aquí, en el desplegable de alumno, y no en una
    pantalla previa: es parte de configurar la medición, igual que la fuente de
    video.

    El parámetro `cam` es opcional: por defecto abre la fuente que el entrenador
    dejó configurada (RF-01). Poder inyectarla es lo que permite ejercitar el
    encadenamiento completo con una cámara sintética, sin hardware — ver
    tests/e2e/.
    """

    INTERVALO_MS = 15
    # Ancho de la columna derecha y del texto que cabe dentro, descontando
    # los márgenes de la tarjeta. Separarlos en constantes evita que un
    # `wraplength` mayor que su contenedor recorte las frases por los lados.
    ANCHO_PANEL = 320
    ANCHO_TEXTO_PANEL = 232
    # Tamaño con el que se dibuja el primer fotograma, antes de que Tk haya
    # asignado su espacio al contenedor del video.
    VIDEO_ARRANQUE = (560, 420)

    def __init__(self, master, db, entrenador, atleta=None, cam=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja; `app` resuelve la navegación.
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador
        self.atleta = atleta

        self.alumnos = db.listar_atletas()
        self.id_sesion = None
        self.logger_mediciones = None
        self.feed = FeedCorrecciones()
        self.cam = None
        self.tracker = None
        self.analyzer = None
        self.start_time = time.time()
        self._activo = False
        self._after_id = None
        self._cam_inyectada = cam

        self.filas_metricas = {}
        self.estado_var = ctk.StringVar(value="")
        self.veredicto_var = ctk.StringVar(value=SIN_DATO)

        self._encabezado()
        self._controles()
        self._cuerpo()

        # Sin alumno elegido no se abre la cámara ni se crea una sesión: quedaría
        # un registro en la base a nombre de nadie.
        if self.atleta is not None:
            self._comenzar()
        else:
            self._pedir_alumno()

    # ---------------- estructura ----------------

    def _encabezado(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=22, pady=(16, 8))

        textos = ctk.CTkFrame(barra, fg_color="transparent")
        textos.pack(side="left", anchor="w")
        ctk.CTkLabel(textos, text="Análisis en vivo", font=(theme.FUENTE, 19, "bold"),
                     text_color=theme.TEXTO).pack(side="left")
        # El sistema evalúa las tres familias a la vez y decide por sí mismo qué
        # está viendo; no hay que seleccionar la técnica de antemano.
        ctk.CTkLabel(textos, text="AUTO", font=(theme.FUENTE, 10, "bold"),
                     fg_color=theme.ACENTO_ROJO, text_color="white", corner_radius=6,
                     width=54, height=22).pack(side="left", padx=(12, 0))
        ctk.CTkLabel(textos, text="Tsuki · Posturas · Mae Geri", font=(theme.FUENTE, 11),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=(10, 0))

        ctk.CTkButton(barra, text="Terminar sesión", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER, width=140,
                      command=self._terminar).pack(side="right")

        caja = ctk.CTkFrame(barra, fg_color=theme.CARD, corner_radius=8)
        caja.pack(side="right", padx=(0, 10))
        ctk.CTkLabel(caja, text="VEREDICTO", font=(theme.FUENTE, 9),
                     text_color=theme.TEXTO_TENUE).pack(padx=14, pady=(6, 0))
        self.etiqueta_veredicto = ctk.CTkLabel(caja, textvariable=self.veredicto_var,
                                               font=(theme.FUENTE, 14, "bold"),
                                               text_color=theme.TEXTO_TENUE)
        self.etiqueta_veredicto.pack(padx=14, pady=(0, 6))

    def _controles(self):
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=22, pady=(0, 10))

        ctk.CTkLabel(fila, text="ALUMNO", font=(theme.FUENTE, 10),
                     text_color=theme.TEXTO_TENUE).pack(side="left", padx=(0, 8))

        nombres = [a["nombre"] for a in self.alumnos]
        self.alumno_var = ctk.StringVar(
            value=self.atleta["nombre"] if self.atleta else (nombres[0] if nombres else ""))
        self.selector_alumno = ctk.CTkOptionMenu(
            fila, values=nombres or ["Sin alumnos registrados"], variable=self.alumno_var,
            width=210, fg_color=theme.CARD, button_color=theme.BORDE,
            button_hover_color=theme.CARD_HOVER, text_color=theme.TEXTO,
            font=(theme.FUENTE, 12), command=self._cambiar_alumno)
        self.selector_alumno.pack(side="left")
        if not nombres:
            self.selector_alumno.configure(state="disabled")

        ctk.CTkLabel(fila, text="CÁMARA", font=(theme.FUENTE, 10),
                     text_color=theme.TEXTO_TENUE).pack(side="left", padx=(22, 8))
        ctk.CTkLabel(fila, text=str(fuente_configurada(self.db)), font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left")

        ctk.CTkLabel(fila, textvariable=self.estado_var, font=(theme.FUENTE, 11.5),
                     text_color=theme.ACENTO_AMARILLO).pack(side="right")

    def _cuerpo(self):
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(expand=True, fill="both", padx=22, pady=(0, 18))

        izquierda = ctk.CTkFrame(cuerpo, fg_color="transparent")
        izquierda.pack(side="left", expand=True, fill="both", padx=(0, 12))

        marco_video = ctk.CTkFrame(izquierda, fg_color=theme.CARD, border_color=theme.BORDE,
                                   border_width=1, corner_radius=10)
        marco_video.pack(expand=True, fill="both")
        # Sin esto el marco crece hasta el tamaño del fotograma que contiene, y
        # como una cámara entrega 1280x720, el video empujaba al panel derecho
        # hasta dejarlo en 193 px de los 320 que pide. Fijado el marco, es la
        # imagen la que se ajusta al hueco (ver `_escalar`), y no al revés.
        marco_video.pack_propagate(False)
        self.video_label = ctk.CTkLabel(marco_video, text="")
        self.video_label.pack(expand=True, fill="both", padx=6, pady=6)

        self._tira_metricas(izquierda)

        derecha = ctk.CTkFrame(cuerpo, fg_color="transparent", width=self.ANCHO_PANEL)
        derecha.pack(side="left", fill="both")
        derecha.pack_propagate(False)
        self._panel_sensores(derecha)
        self._panel_correcciones(derecha)

    def _tira_metricas(self, padre):
        """Ángulos articulares bajo el video, en posición fija."""
        tira = ctk.CTkFrame(padre, fg_color="transparent")
        tira.pack(fill="x", pady=(10, 0))

        for fila in metricas_articulares([]):
            caja = ctk.CTkFrame(tira, fg_color=theme.CARD, border_color=theme.BORDE,
                                border_width=1, corner_radius=8)
            caja.pack(side="left", expand=True, fill="both", padx=(0, 8))
            ctk.CTkLabel(caja, text=fila["etiqueta"], font=(theme.FUENTE, 10),
                         text_color=theme.TEXTO_TENUE).pack(anchor="w", padx=12, pady=(10, 0))
            valor = ctk.CTkLabel(caja, text=fila["valor"], font=(theme.FUENTE, 18, "bold"),
                                 text_color=theme.TEXTO_TENUE)
            valor.pack(anchor="w", padx=12, pady=(0, 10))
            self.filas_metricas[fila["categoria"]] = valor

    def _panel_sensores(self, padre):
        caja = ctk.CTkFrame(padre, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        caja.pack(fill="x", pady=(0, 10))

        cabecera = ctk.CTkFrame(caja, fg_color="transparent")
        cabecera.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(cabecera, text="Sensores IMU", font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(side="left")
        ctk.CTkLabel(cabecera, text="PENDIENTE", font=(theme.FUENTE, 9, "bold"),
                     text_color=theme.ACENTO_AMARILLO).pack(side="right")

        # Los cuatro puntos se listan aunque no haya hardware: dicen dónde irán
        # los sensores cuando se monten. Omitir el panel dejaría creer que el
        # análisis en curso ya los usa, cuando hoy es solo visión (RF-02, RF-04).
        for punto in PUNTOS_IMU:
            fila = ctk.CTkFrame(caja, fg_color="transparent")
            fila.pack(fill="x", padx=16, pady=1)
            ctk.CTkLabel(fila, text="○", font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_TENUE).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(fila, text=punto, font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_TENUE).pack(side="left")

        ctk.CTkLabel(caja, text="Sin sensores conectados · medición por visión",
                     font=(theme.FUENTE, 10), text_color=theme.TEXTO_TENUE,
                     wraplength=self.ANCHO_TEXTO_PANEL, justify="left").pack(
            anchor="w", padx=16, pady=(8, 14))

    def _panel_correcciones(self, padre):
        caja = ctk.CTkFrame(padre, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        caja.pack(expand=True, fill="both")

        ctk.CTkLabel(caja, text="Correcciones", font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", padx=16, pady=(14, 8))

        self.lista_correcciones = ctk.CTkScrollableFrame(caja, fg_color="transparent")
        self.lista_correcciones.pack(expand=True, fill="both", padx=10, pady=(0, 12))
        self._pintar_correcciones()

    # ---------------- ciclo de análisis ----------------

    def _pedir_alumno(self):
        if self.alumnos:
            self.estado_var.set("Elige un alumno para comenzar a medir.")
        else:
            self.estado_var.set("No hay alumnos registrados. Inscríbelos en «Alumnos y progreso».")

    def _cambiar_alumno(self, nombre):
        """
        Cambiar de alumno cierra la sesión en curso y abre otra.

        Seguir registrando en la sesión anterior atribuiría a un alumno las
        mediciones de otro, que es el peor error posible en un historial.
        """
        elegido = next((a for a in self.alumnos if a["nombre"] == nombre), None)
        if elegido is None or (self.atleta and elegido["id_atleta"] == self.atleta["id_atleta"]):
            return
        self._detener()
        self.atleta = elegido
        self.feed = FeedCorrecciones()
        self._pintar_correcciones()
        self._comenzar()

    def _comenzar(self):
        self.estado_var.set("")
        self.cam = self._cam_inyectada if self._cam_inyectada is not None \
            else Camera(fuente_configurada(self.db))
        self.tracker = PoseTracker(model_path='pose_landmarker_full.task')
        self.renderer = SkeletonRenderer()
        # Umbrales vigentes desde la base de datos (RF-08), no constantes de código.
        self.analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65,
                                          reglas=KarateRules(self.db.cargar_umbrales_vigentes()))
        self.id_sesion = self.db.iniciar_sesion(self.atleta["id_atleta"],
                                                self.entrenador["id_entrenador"])
        self.logger_mediciones = MedicionLogger(self.db, self.id_sesion)
        self.start_time = time.time()
        self._activo = True
        self._actualizar_frame()

    def _actualizar_frame(self):
        if not self._activo:
            return

        frame = self.cam.get_frame()
        if frame is not None:
            timestamp_ms = int((time.time() - self.start_time) * 1000)
            h, w, _ = frame.shape

            result = self.tracker.process_frame(frame, timestamp_ms)
            frame = self.renderer.draw(frame, result.pose_landmarks)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                diagnosticos = [
                    self.analyzer.analyze_tsuki(landmarks, w, h),
                    self.analyzer.analyze_stance(landmarks, w, h),
                    self.analyzer.analyze_mae_geri(landmarks, w, h, timestamp_ms),
                ]
                for diagnostico in diagnosticos:
                    frame = self.renderer.draw_diagnostics(frame, diagnostico)
                    self.logger_mediciones.registrar(diagnostico, timestamp_ms)

                if self.feed.registrar(diagnosticos, timestamp_ms):
                    self._pintar_correcciones()
                self._refrescar_metricas(diagnosticos)

            if not self._mostrar_frame(frame):
                return

        self._after_id = self.after(self.INTERVALO_MS, self._actualizar_frame)

    def _escalar(self, ancho, alto):
        """
        Tamaño al que dibujar un fotograma de `ancho`x`alto` dentro del hueco
        disponible, conservando la proporción.

        Conservarla no es estético: el análisis se juzga por ángulos, y una
        imagen estirada en un eje muestra ángulos que no son los que el sistema
        midió — el sensei vería una rodilla más abierta de lo que está.

        Antes del primer dibujado el contenedor todavía no tiene tamaño asignado
        (Tk devuelve 1), así que se usa una medida de arranque y el siguiente
        fotograma ya se ajusta al hueco real.
        """
        hueco_ancho = self.video_label.winfo_width()
        hueco_alto = self.video_label.winfo_height()
        if hueco_ancho <= 1 or hueco_alto <= 1:
            hueco_ancho, hueco_alto = self.VIDEO_ARRANQUE

        escala = min(hueco_ancho / ancho, hueco_alto / alto)
        return max(1, int(ancho * escala)), max(1, int(alto * escala))

    def _mostrar_frame(self, frame):
        """Vuelca el fotograma en la etiqueta. Devuelve False si la ventana murió."""
        imagen_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imagen_ctk = ctk.CTkImage(light_image=imagen_pil, dark_image=imagen_pil,
                                  size=self._escalar(imagen_pil.width, imagen_pil.height))
        try:
            # Puede fallar si el usuario cerró la ventana justo entre el inicio de
            # este método (lectura de cámara + MediaPipe, que toma tiempo real) y
            # este punto: la ventana ya no existe. cerrar() cancela el siguiente
            # after(), pero el que ya estaba en curso alcanza a llegar hasta aquí.
            self.video_label.configure(image=imagen_ctk)
            self.video_label.image = imagen_ctk  # evita que el recolector la borre
        except tkinter.TclError:
            return False
        return True

    def _refrescar_metricas(self, diagnosticos):
        for fila in metricas_articulares(diagnosticos):
            etiqueta = self.filas_metricas.get(fila["categoria"])
            if etiqueta is None:
                continue
            color = theme.TEXTO_TENUE
            if fila["correcto"] is True:
                color = theme.ACENTO_VERDE
            elif fila["correcto"] is False:
                color = theme.ACENTO_ROJO
            etiqueta.configure(text=fila["valor"], text_color=color)

        veredictos = [f["correcto"] for f in metricas_articulares(diagnosticos)
                      if f["correcto"] is not None]
        # El veredicto de cabecera resume el fotograma: basta un fallo para que
        # la ejecución no sea correcta.
        resumen = None if not veredictos else all(veredictos)
        self.veredicto_var.set(veredicto_legible(resumen))
        self.etiqueta_veredicto.configure(
            text_color=theme.TEXTO_TENUE if resumen is None
            else (theme.ACENTO_VERDE if resumen else theme.ACENTO_ROJO))

    def _pintar_correcciones(self):
        for w in self.lista_correcciones.winfo_children():
            w.destroy()

        if not self.feed.entradas:
            ctk.CTkLabel(self.lista_correcciones,
                         text="Las correcciones aparecerán aquí\nconforme el alumno ejecute.",
                         font=(theme.FUENTE, 11), text_color=theme.TEXTO_TENUE,
                         justify="left").pack(anchor="w", padx=6, pady=10)
            return

        for entrada in self.feed.entradas:
            color = theme.ACENTO_VERDE if entrada["correcto"] else theme.ACENTO_ROJO
            fila = ctk.CTkFrame(self.lista_correcciones, fg_color=theme.FONDO, corner_radius=6)
            fila.pack(fill="x", pady=3)

            # La barra de color lleva altura propia: con `fill="y"` la fila se
            # estiraba para repartir el alto sobrante del panel y cada
            # corrección ocupaba media pantalla.
            marca = ctk.CTkFrame(fila, fg_color=color, width=3, height=34, corner_radius=2)
            marca.pack(side="left", padx=(8, 8), pady=8)
            marca.pack_propagate(False)

            textos = ctk.CTkFrame(fila, fg_color="transparent")
            textos.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(textos, text=entrada["tiempo"], font=(theme.FUENTE_MONO, 9.5),
                         text_color=theme.TEXTO_TENUE).pack(anchor="w")
            ctk.CTkLabel(textos, text=entrada["mensaje"], font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO, wraplength=self.ANCHO_TEXTO_PANEL,
                         justify="left").pack(anchor="w")

    # ---------------- cierre ----------------

    def _terminar(self):
        self.master_app.on_terminar_sesion()

    def _detener(self):
        """Corta el ciclo y libera el hardware, sin tocar la interfaz."""
        self._activo = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self.id_sesion is not None:
            self.db.cerrar_sesion(self.id_sesion)
            self.id_sesion = None
        if self.cam is not None:
            self.cam.release()
            self.cam = None
        if self.tracker is not None:
            self.tracker.close()
            self.tracker = None

    def cerrar(self):
        """Se llama al salir de esta pantalla o cerrar la app."""
        self._detener()
