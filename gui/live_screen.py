import time
import tkinter
import cv2
from PIL import Image
import customtkinter as ctk

from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer
from expert_system.analyzer import TechniqueAnalyzer
from persistence.medicion_logger import MedicionLogger
from gui import theme


class LiveScreen(ctk.CTkFrame):
    """
    Pantalla de análisis en vivo. Reutiliza EXACTAMENTE el mismo pipeline que
    main.py (Camera, PoseTracker, SkeletonRenderer, TechniqueAnalyzer) sin
    modificar ninguno de esos módulos — solo cambia el mecanismo de refresco:
    en vez del bucle bloqueante `while True` + cv2.imshow de main.py, aquí se
    usa `self.after(...)` porque Tkinter necesita su propio ciclo de eventos
    y un bucle bloqueante congelaría toda la ventana.

    El parámetro `cam` es opcional (por defecto usa la cámara real, índice 2,
    igual que main.py) para poder inyectar una cámara sintética en pruebas
    sin hardware — ver test_gui_live_screen.py.
    """

    def __init__(self, master, db, entrenador, atleta, cam=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.master_app = master
        self.db = db
        self.entrenador = entrenador
        self.atleta = atleta

        self.cam = cam if cam is not None else Camera(source=2)
        self.tracker = PoseTracker(model_path='pose_landmarker_full.task')
        self.renderer = SkeletonRenderer()
        self.analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65)

        self.id_sesion = db.iniciar_sesion(atleta["id_atleta"], entrenador["id_entrenador"])
        self.logger_mediciones = MedicionLogger(db, self.id_sesion)
        self.start_time = time.time()
        self._activo = True
        self._after_id = None

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(barra, text=f"Analizando a {atleta['nombre']}", font=(theme.FUENTE, 16, "bold"),
                     text_color=theme.TEXTO).pack(side="left")
        ctk.CTkButton(barra, text="Terminar sesión", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER,
                      command=self.master_app.on_terminar_sesion, width=150).pack(side="right")

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.pack(expand=True, fill="both", padx=20, pady=(0, 20))

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
                diagnostico_tsuki = self.analyzer.analyze_tsuki(landmarks, w, h)
                diagnostico_postura = self.analyzer.analyze_stance(landmarks, w, h)
                diagnostico_patada = self.analyzer.analyze_mae_geri(landmarks, w, h, timestamp_ms)
                frame = self.renderer.draw_diagnostics(frame, diagnostico_tsuki)
                frame = self.renderer.draw_diagnostics(frame, diagnostico_postura)
                frame = self.renderer.draw_diagnostics(frame, diagnostico_patada)

                self.logger_mediciones.registrar(diagnostico_tsuki, timestamp_ms)
                self.logger_mediciones.registrar(diagnostico_postura, timestamp_ms)
                self.logger_mediciones.registrar(diagnostico_patada, timestamp_ms)

            imagen_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imagen_pil = Image.fromarray(imagen_rgb)
            imagen_ctk = ctk.CTkImage(light_image=imagen_pil, dark_image=imagen_pil,
                                       size=(imagen_pil.width, imagen_pil.height))
            try:
                # Puede fallar si el usuario cerró la ventana justo entre el
                # inicio de este método (lectura de cámara + MediaPipe, que
                # toma tiempo real) y este punto — la ventana ya no existe.
                # cerrar() cancela el siguiente after(), pero el que ya estaba
                # en curso puede alcanzar a llegar hasta aquí.
                self.video_label.configure(image=imagen_ctk)
                self.video_label.image = imagen_ctk  # evita que el garbage collector la borre
            except tkinter.TclError:
                return

        self._after_id = self.after(15, self._actualizar_frame)

    def cerrar(self):
        """Se llama al salir de esta pantalla o cerrar la app: libera hardware y cierra la sesión en BD."""
        self._activo = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.db.cerrar_sesion(self.id_sesion)
        self.cam.release()
        self.tracker.close()
