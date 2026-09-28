import os
import time
import tkinter

import cv2
import customtkinter as ctk
from PIL import Image

from biomechanics.renderer import SkeletonRenderer
from expert_system.analyzer import TechniqueAnalyzer
from expert_system.knowledge_base import KarateRules
from gui import theme
from gui import coaching
from gui.camara_screen import fuente_configurada
from gui.panel_vivo import (FeedCorrecciones, espera_hasta_el_siguiente, PUNTOS_IMU, SIN_ALUMNOS, SIN_DATO,
                            etiqueta_alumno, metricas_articulares, veredicto_legible)
from expert_system.guardia import orientacion_frente_a_camara
from vision.encuadre import NIVEL_ALTO, NIVEL_MEDIO
from vision.encuadre import evaluar as evaluar_encuadre
from persistence.medicion_logger import MedicionLogger
from vision.camera import Camera
from vision.fuentes import es_archivo
from vision.grabacion import (ANALIZANDO_GRABACION, CLAVE_DIRECTORIO, CLAVE_GRABAR,
                              aviso_en_vivo, directorio_configurado, grabacion_activada)
from vision.grabador import GrabadorSesion
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
    # Con el hardware inercial montado, este interruptor pasa a True y el
    # bloque de sensores arranca desplegado (RF-02, RF-04).
    SENSORES_DISPONIBLES = False

    def __init__(self, master, db, entrenador, atleta=None, cam=None, app=None,
                 monitor=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja; `app` resuelve la navegación.
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador
        self.atleta = atleta

        # Instrumentación opcional (RNF-01, RF-01). Sin monitor, el bucle no
        # paga nada: ni una llamada al reloj. Se inyecta desde fuera, y no se
        # enciende desde la propia pantalla, para que medir no sea una
        # funcionalidad del producto sino algo que una herramienta externa le
        # pide — ver test_rendimiento_interfaz.py.
        #
        # Existe porque `test_rendimiento.py` mide el encadenamiento de análisis
        # con una ventana de OpenCV, y esa ventana no es la que usa el dojo. La
        # interfaz real convierte el fotograma a imagen de CustomTkinter,
        # refresca las métricas articulares y el panel de correcciones, y escribe
        # en la base: etapas que aquella medición no incluye.
        self.monitor = monitor

        self.alumnos = db.listar_atletas()
        self.id_sesion = None
        self.logger_mediciones = None
        self.feed = FeedCorrecciones()
        self.cam = None
        self.tracker = None
        self.analyzer = None
        self.grabador = None
        # Qué pasó con el video, en una frase. Se conserva tras cerrar la sesión
        # para poder decírselo al sensei: enterarse de que no hubo grabación al
        # ir a buscar el archivo, semanas después, no sirve de nada.
        self.resumen_grabacion = None
        self._activo = False
        self._after_id = None
        self._cam_inyectada = cam

        # Guardia de reentrada del bucle de análisis. Ver _actualizar_frame.
        self._en_curso = False
        # Por qué se detuvo el bucle, si se detuvo. None mientras corre.
        self._motivo_detencion = None
        # Fotogramas nulos seguidos. Cero mientras la fuente entrega.
        self._sin_fotograma = 0

        self.filas_metricas = {}
        self.estado_var = ctk.StringVar(value="")
        self.veredicto_var = ctk.StringVar(value=SIN_DATO)
        # Grabando o solo midiendo, a la vista durante toda la sesión. Nadie
        # debería descubrir que lo estaban filmando después.
        self.grabacion_var = ctk.StringVar(value=(
            ANALIZANDO_GRABACION if es_archivo(fuente_configurada(db))
            else aviso_en_vivo(grabacion_activada(db.leer_config(CLAVE_GRABAR)))))

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
        # El aviso no entra en `values`: si fuera una opción del desplegable,
        # elegirlo buscaría un alumno llamado "Elige un alumno".
        self.alumno_var = ctk.StringVar(value=etiqueta_alumno(self.atleta, nombres))
        self.selector_alumno = ctk.CTkOptionMenu(
            fila, values=nombres or [SIN_ALUMNOS], variable=self.alumno_var,
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

        # El estado de grabación va junto a la cámara y no escondido en un
        # menú: es parte de las condiciones en que se está midiendo, igual que
        # de qué fuente viene el video y a quién se mide.
        self.etiqueta_grabacion = ctk.CTkLabel(
            fila, textvariable=self.grabacion_var, font=(theme.FUENTE, 11.5, "bold"),
            text_color=theme.ACENTO_ROJO if self._graba() else theme.TEXTO_TENUE)
        self.etiqueta_grabacion.pack(side="left", padx=(22, 0))

        ctk.CTkLabel(fila, textvariable=self.estado_var, font=(theme.FUENTE, 11.5),
                     text_color=theme.ACENTO_AMARILLO).pack(side="right")

    def _fuente_es_grabacion(self):
        """¿Se está analizando un archivo en vez de una cámara en vivo?"""
        return es_archivo(fuente_configurada(self.db))

    def _graba(self):
        """
        ¿Hay que escribir video de esta sesión?

        No, cuando la fuente ya es una grabación: la ejecución ya está
        conservada, y volver a escribirla produciría un duplicado —diez minutos
        en Full HD no son poca cosa— y un segundo archivo compitiendo con el
        original como evidencia de la misma sesión.
        """
        if self._fuente_es_grabacion():
            return False
        return grabacion_activada(self.db.leer_config(CLAVE_GRABAR))

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
        """
        Estado del subsistema inercial, plegable.

        Mientras no haya sensores montados el bloque arranca plegado: cuatro
        puntos apagados ocupan un tercio de la columna para decir lo mismo que
        una línea, y ese espacio le hace falta a las correcciones. Cuando el
        hardware entre, la lista pasará a tener contenido vivo y convendrá
        dejarla desplegada por defecto (ver `SENSORES_DISPONIBLES`).

        Plegado no es lo mismo que oculto: la cabecera sigue diciendo que el
        subsistema existe y está pendiente. Quitarlo dejaría creer que el
        análisis en curso ya usa los sensores, cuando hoy es solo visión.
        """
        caja = ctk.CTkFrame(padre, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        caja.pack(fill="x", pady=(0, 10))

        cabecera = ctk.CTkButton(
            caja, text="", fg_color="transparent", hover_color=theme.CARD_HOVER,
            height=38, corner_radius=8, command=self._alternar_sensores)
        cabecera.pack(fill="x", padx=8, pady=(8, 0))

        contenido = ctk.CTkFrame(cabecera, fg_color="transparent")
        contenido.place(relx=0, rely=0.5, anchor="w", x=8)
        self.flecha_sensores = ctk.CTkLabel(contenido, text="▸", font=(theme.FUENTE, 10),
                                            text_color=theme.TEXTO_MUTED, width=14)
        self.flecha_sensores.pack(side="left")
        ctk.CTkLabel(contenido, text="Sensores IMU", font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(side="left", padx=(2, 8))
        ctk.CTkLabel(contenido, text="PENDIENTE", font=(theme.FUENTE, 9, "bold"),
                     text_color=theme.ACENTO_AMARILLO).pack(side="left")

        self.detalle_sensores = ctk.CTkFrame(caja, fg_color="transparent")
        for punto in PUNTOS_IMU:
            fila = ctk.CTkFrame(self.detalle_sensores, fg_color="transparent")
            fila.pack(fill="x", padx=16, pady=1)
            ctk.CTkLabel(fila, text="○", font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_TENUE).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(fila, text=punto, font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_TENUE).pack(side="left")
        ctk.CTkLabel(self.detalle_sensores,
                     text="Sin sensores conectados · medición por visión",
                     font=(theme.FUENTE, 10), text_color=theme.TEXTO_TENUE,
                     wraplength=self.ANCHO_TEXTO_PANEL, justify="left").pack(
            anchor="w", padx=16, pady=(8, 4))

        self.sensores_desplegados = self.SENSORES_DISPONIBLES
        self._pintar_sensores()

    def _alternar_sensores(self):
        self.sensores_desplegados = not self.sensores_desplegados
        self._pintar_sensores()
        return self.sensores_desplegados

    def _pintar_sensores(self):
        self.flecha_sensores.configure(text="▾" if self.sensores_desplegados else "▸")
        if self.sensores_desplegados:
            self.detalle_sensores.pack(fill="x", pady=(4, 10))
        else:
            self.detalle_sensores.pack_forget()

    def _panel_correcciones(self, padre):
        caja = ctk.CTkFrame(padre, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        caja.pack(expand=True, fill="both")

        ctk.CTkLabel(caja, text="Correcciones", font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", padx=16, pady=(14, 8))

        # Aviso de encuadre. Va ENCIMA de las correcciones y no dentro de la
        # lista porque no es una corrección de técnica: dice si lo que se está
        # midiendo sirve. Una toma frontal deja todo visible y aun así impide
        # medir Zenkutsu; mezclarlo con «extiende más el brazo» lo escondería.
        self.etiqueta_encuadre = ctk.CTkLabel(
            caja, text="", font=(theme.FUENTE, 11), justify="left",
            wraplength=300, text_color=theme.TEXTO_TENUE)
        self.etiqueta_encuadre.pack(anchor="w", padx=16, pady=(0, 6))
        self._ultimo_aviso_encuadre = None

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
        # Grabación del video crudo de la sesión. Es lo que permite volver a
        # analizar la ejecución cuando el criterio cambie, en vez de tener que
        # repetirla —y una ejecución repetida es otra ejecución, de otro día.
        # Si la grabación falla, la sesión sigue midiendo (ver vision/grabador.py).
        # Apagable por equipo: en un dojo se entrena con menores, y filmar a un
        # menor requiere el consentimiento de quien lo tiene a cargo. Apagada,
        # la sesión se mide igual; solo deja de quedar el video.
        if self._graba():
            self.grabador = GrabadorSesion(
                self.id_sesion, self.atleta["nombre"],
                directorio=directorio_configurado(self.db.leer_config(CLAVE_DIRECTORIO)))
        elif self._fuente_es_grabacion():
            # El video de esta sesión es el archivo que se analizó. Dejar la
            # columna vacía haría que el reporte dijera «Sin video» sobre una
            # sesión que nació precisamente de uno.
            self.grabador = None
            fuente = fuente_configurada(self.db)
            self.db.registrar_video_de_sesion(self.id_sesion, fuente)
            self.resumen_grabacion = f"Se analizó la grabación {os.path.basename(fuente)}."
        else:
            self.grabador = None
            self.resumen_grabacion = "La grabación de video está desactivada en este equipo."
        self._activo = True
        self._actualizar_frame()

    def _actualizar_frame(self):
        """
        Un fotograma: capturar, estimar, analizar, registrar y dibujar.

        La guardia de reentrada no es defensiva por si acaso: sin ella esto se
        desborda en macOS. CustomTkinter llama a `update_idletasks()` por su
        cuenta al dibujar widgets —y `_pintar_correcciones` crea varios—, y en
        macOS esa llamada atiende los temporizadores ya vencidos. Como el
        siguiente refresco se programa con el tiempo que falta, y el trabajo de
        un fotograma ya supera el intervalo, ese temporizador está vencido
        siempre: dibujar una corrección reentraba aquí, que volvía a dibujar,
        hasta agotar la pila con un RecursionError.

        En Linux no ocurre, porque allí `update_idletasks()` no llega a
        atenderlo. Es la misma diferencia entre sistemas que ya costó dos
        intentos en las pruebas de navegación (ver CLAUDE.md).
        """
        if not self._activo or self._en_curso:
            return

        self._en_curso = True
        try:
            self._procesar_fotograma()
        finally:
            self._en_curso = False

    def _procesar_fotograma(self):
        inicio = time.perf_counter()
        if self.monitor is not None:
            self.monitor.iniciar_frame()

        frame = self.cam.get_frame()
        if self.monitor is not None:
            self.monitor.marcar("captura")
        if frame is None:
            # Sobre una grabación esto es el final del archivo; con una cámara,
            # que dejó de entregar. El bucle sigue reprogramándose —una cámara
            # puede recuperarse— pero deja constancia desde el primer fallo.
            self._sin_fotograma += 1
            if self._motivo_detencion is None:
                self._motivo_detencion = "la fuente dejó de entregar fotogramas"
        else:
            self._sin_fotograma = 0
        if frame is not None:
            # La marca la da la fuente, no el reloj de pared. Con una cámara
            # en vivo ambas coinciden; con una grabación no, y usar el reloj
            # haría que la misma grabación diera velocidades angulares
            # distintas en equipos distintos (ver Camera.marca_de_tiempo_ms).
            timestamp_ms = int(self.cam.marca_de_tiempo_ms())
            h, w, _ = frame.shape

            # Antes de dibujar nada: lo que se graba es el fotograma crudo. El
            # video anotado se regenera del crudo cuando se quiera; al revés no
            # se puede, y grabar el anotado dejaría las conclusiones de hoy
            # cocidas dentro de la evidencia.
            if self.grabador is not None:
                self.grabador.escribir(frame, timestamp_ms)
            if self.monitor is not None:
                self.monitor.marcar("grabacion")

            result = self.tracker.process_frame(frame, timestamp_ms)
            if self.monitor is not None:
                self.monitor.marcar("estimacion_pose")

            frame = self.renderer.draw(frame, result.pose_landmarks)

            landmarks = result.pose_landmarks[0] if result.pose_landmarks else None
            self._refrescar_encuadre(landmarks)

            if landmarks is not None:
                diagnosticos = [
                    self.analyzer.analyze_tsuki(landmarks, w, h),
                    self.analyzer.analyze_stance(landmarks, w, h),
                    self.analyzer.analyze_mae_geri(landmarks, w, h, timestamp_ms),
                ]
                if self.monitor is not None:
                    self.monitor.marcar("analisis")

                for diagnostico in diagnosticos:
                    frame = self.renderer.draw_diagnostics(frame, diagnostico)
                if self.monitor is not None:
                    self.monitor.marcar("renderizado")

                for diagnostico in diagnosticos:
                    self.logger_mediciones.registrar(diagnostico, timestamp_ms)
                if self.monitor is not None:
                    self.monitor.marcar("persistencia")

                if self.feed.registrar(diagnosticos, timestamp_ms):
                    self._pintar_correcciones()
                self._refrescar_metricas(diagnosticos)
            if self.monitor is not None:
                self.monitor.marcar("panel")

            if not self._mostrar_frame(frame):
                # El bucle se detiene aquí y no se reprograma. Antes eso no
                # dejaba rastro: la imagen quedaba congelada, la sesión seguía
                # abierta y nadie sabía que el análisis había parado. Dejar
                # dicho el motivo es lo que permite distinguir «se detuvo» de
                # «está lento», que desde fuera se ven igual.
                self._motivo_detencion = ("la ventana dejó de aceptar el fotograma "
                                          "(TclError al volcarlo)")
                return
            if self.monitor is not None:
                self.monitor.marcar("despliegue")
                self.monitor.cerrar_frame()

        # Se descuenta lo que este fotograma ya costó: reprogramar con el
        # intervalo entero lo sumaba al trabajo en vez de solaparlo.
        espera = espera_hasta_el_siguiente(self.INTERVALO_MS,
                                           (time.perf_counter() - inicio) * 1000)
        self._after_id = self.after(espera, self._actualizar_frame)

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
        alto, ancho = frame.shape[:2]
        destino = self._escalar(ancho, alto)
        # Se reduce ANTES de convertir. El fotograma llega a 2 MP y se dibuja en
        # menos de 0,25: convertir los 2 MP a imagen de CustomTkinter para que
        # ella los reduzca después cuesta unos 14 ms por fotograma que no
        # compran nada — medido el 28-sep-2026, 20,1 ms contra 5,9. A 30 fps eso
        # es casi medio presupuesto gastado en píxeles que nadie ve.
        frame = cv2.resize(frame, destino, interpolation=cv2.INTER_AREA)
        imagen_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imagen_ctk = ctk.CTkImage(light_image=imagen_pil, dark_image=imagen_pil,
                                  size=destino)
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

    def _refrescar_encuadre(self, landmarks):
        """
        Avisa si la cámara está donde hace falta. Ver vision/encuadre.py.

        Solo toca el widget cuando el texto CAMBIA. El bucle en vivo corre a
        decenas de fotogramas por segundo y reconfigurar una etiqueta en cada
        uno cuesta tiempo de Tk sin que nadie lo note: es la misma lección que
        dejó la medición de rendimiento del 28-sep.
        """
        orientacion = None
        if landmarks is not None:
            orientacion = orientacion_frente_a_camara(
                (landmarks[24].x, landmarks[24].z),
                (landmarks[23].x, landmarks[23].z))

        avisos = evaluar_encuadre(landmarks, orientacion)
        texto = "\n".join(a["mensaje"] for a in avisos)
        if texto == self._ultimo_aviso_encuadre:
            return
        self._ultimo_aviso_encuadre = texto

        peor = avisos[0]["nivel"] if avisos else None
        color = {NIVEL_ALTO: theme.ACENTO_ROJO,
                 NIVEL_MEDIO: theme.ACENTO_ROJO}.get(peor, theme.TEXTO_TENUE)
        self.etiqueta_encuadre.configure(text=texto, text_color=color)

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

            # El veredicto del motor se traduce a la frase que el sensei diría en
            # el tatami. Lo que corrige a un alumno no es saber que su codo está
            # a 178°, sino oír "no bloquees el codo al impacto". El texto técnico
            # sigue siendo el que se guarda en la base: es la clave con la que se
            # agrupan los errores frecuentes de la sesión.
            instruccion, motivo = coaching.traducir(entrada["mensaje"])

            textos = ctk.CTkFrame(fila, fg_color="transparent")
            textos.pack(side="left", fill="x", expand=True, pady=6)
            ctk.CTkLabel(textos, text=entrada["tiempo"], font=(theme.FUENTE_MONO, 9.5),
                         text_color=theme.TEXTO_TENUE).pack(anchor="w")
            ctk.CTkLabel(textos, text=instruccion, font=(theme.FUENTE, 11.5, "bold"),
                         text_color=theme.TEXTO, wraplength=self.ANCHO_TEXTO_PANEL,
                         justify="left").pack(anchor="w")
            if motivo:
                ctk.CTkLabel(textos, text=motivo, font=(theme.FUENTE, 10),
                             text_color=theme.TEXTO_MUTED,
                             wraplength=self.ANCHO_TEXTO_PANEL,
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
        # El orden importa: primero se cierra el video, porque la ruta solo se
        # conoce cuando la escritura termina, y esa ruta hay que anotarla en la
        # sesión antes de soltar su identificador.
        if self.grabador is not None:
            self.resumen_grabacion = self.grabador.cerrar()
            if self.id_sesion is not None and self.grabador.ruta_si_existe:
                self.db.registrar_video_de_sesion(self.id_sesion,
                                                  self.grabador.ruta_si_existe)
            self.grabador = None
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
