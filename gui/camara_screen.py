import customtkinter as ctk

from gui import theme
from vision.camera import CamaraNoDisponible, Camera, describir, es_url, listar_camaras

# Clave con la que se recuerda la fuente elegida en la tabla `configuracion`.
CLAVE_FUENTE = "fuente_video"


class CamaraScreen(ctk.CTkFrame):
    """
    Selección de la fuente de video (RF-01).

    Resuelve un riesgo concreto de la puesta en marcha: hasta ahora el índice de
    cámara estaba escrito en el código y correspondía al equipo de desarrollo.
    En cualquier otra máquina —la del aula donde se defienda el proyecto, o la
    del dojo— ese índice no existe, y el sistema fallaba sin decir por qué.

    Ofrece las dos vías que un dojo necesita: los dispositivos que el sistema
    operativo ya expone (webcam integrada, cámara USB, OBS o Camo, que macOS
    presenta como cámaras normales) y una cámara IP por red local, que es como
    se conecta un teléfono sin cables ni aplicaciones propietarias.

    La elección se guarda en la base de datos y se reutiliza en el siguiente
    arranque: configurar la cámara es una tarea de instalación, no algo que el
    entrenador deba repetir cada sesión.
    """

    # Alto de la vista previa de cada cámara. Suficiente para reconocer la
    # escena, pequeño para que la lista siga siendo una lista.
    ALTO_MINIATURA = 54

    def __init__(self, master, db, al_terminar=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación. Desde que existe la barra lateral son objetos
        # distintos: el contenedor es el área de contenido, no la ventana.
        self.master_app = app if app is not None else master
        self.db = db
        self.al_terminar = al_terminar

        self.disponibles = []
        # Las miniaturas se conservan porque Tk no retiene la referencia a una
        # imagen: sin esto el recolector las borra y las tarjetas salen vacías.
        self.miniaturas = []
        self.seleccion = ctk.StringVar(value=str(db.leer_config(CLAVE_FUENTE, "")))
        self.url_var = ctk.StringVar()
        self.error_var = ctk.StringVar(value="")
        self.estado_var = ctk.StringVar(value="")

        self._construir_encabezado()

        # La fuente guardada, tal como quedó en la base. Se conserva aparte de
        # `self.seleccion` porque esa variable cambia mientras se arma la
        # pantalla (el bloque de cámara IP la reemplaza por su valor interno) y
        # comparar contra ella producía diagnósticos falsos.
        self.fuente_guardada = self.seleccion.get()

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(expand=True, fill="both", padx=28, pady=(0, 6))

        self._construir_pie()
        self.buscar_camaras()

    # ---------------- armado ----------------

    def _construir_encabezado(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=28, pady=(20, 4))

        titulos = ctk.CTkFrame(barra, fg_color="transparent")
        titulos.pack(side="left", anchor="w")
        ctk.CTkLabel(titulos, text="Cámara y fuente de video", font=(theme.FUENTE, 20, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w")
        ctk.CTkLabel(titulos, text="De dónde toma el sistema el video que analiza",
                     font=(theme.FUENTE, 12), text_color=theme.TEXTO_MUTED).pack(anchor="w")

        ctk.CTkButton(barra, text="Volver", fg_color="transparent", border_width=1,
                      border_color=theme.BORDE_CLARO, text_color=theme.TEXTO,
                      hover_color=theme.CARD_HOVER, width=110,
                      command=self._volver).pack(side="right")
        ctk.CTkButton(barra, text="Buscar cámaras", fg_color="transparent", border_width=1,
                      border_color=theme.BORDE_CLARO, text_color=theme.TEXTO_MUTED,
                      hover_color=theme.CARD_HOVER, width=150,
                      command=self.buscar_camaras).pack(side="right", padx=(0, 8))

    def _construir_pie(self):
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.pack(fill="x", padx=28, pady=(0, 18))

        ctk.CTkLabel(pie, textvariable=self.error_var, text_color=theme.ACENTO_ROJO,
                     font=(theme.FUENTE, 11.5), justify="left", wraplength=560).pack(side="left")
        ctk.CTkLabel(pie, textvariable=self.estado_var, text_color=theme.ACENTO_VERDE,
                     font=(theme.FUENTE, 11.5)).pack(side="left", padx=(10, 0))

        ctk.CTkButton(pie, text="Usar esta cámara", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER, width=170,
                      command=self.guardar_seleccion).pack(side="right")
        ctk.CTkButton(pie, text="Probar", fg_color="transparent", width=110,
                      border_width=1, border_color=theme.BORDE_CLARO,
                      text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                      command=self.probar_seleccion).pack(side="right", padx=(0, 8))

    def _tarjeta(self, valor, titulo, detalle, muestra=None):
        fila = ctk.CTkFrame(self.lista, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        fila.pack(fill="x", pady=3)
        ctk.CTkRadioButton(fila, text="", variable=self.seleccion, value=valor,
                           width=24, radiobutton_width=18, radiobutton_height=18,
                           fg_color=theme.ACENTO_ROJO,
                           border_color=theme.BORDE_CLARO).pack(side="left", padx=(14, 6), pady=12)

        # La miniatura es lo único que identifica una cámara sin lugar a dudas.
        # El nombre del sistema ayuda, pero dos webcams del mismo modelo se
        # llaman igual; ver la imagen no admite confusión. Sale gratis: es el
        # fotograma que la enumeración ya leyó para comprobar que funciona.
        if muestra is not None:
            self._miniatura(fila, muestra)

        textos = ctk.CTkFrame(fila, fg_color="transparent")
        textos.pack(side="left", anchor="w")
        ctk.CTkLabel(textos, text=titulo, font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO, anchor="w").pack(anchor="w")
        ctk.CTkLabel(textos, text=detalle, font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED, anchor="w").pack(anchor="w")

    def _miniatura(self, padre, frame):
        """Vista previa pequeña del fotograma que entregó esa cámara."""
        try:
            import cv2
            from PIL import Image

            alto, ancho = frame.shape[:2]
            escala = self.ALTO_MINIATURA / alto
            imagen = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            vista = ctk.CTkImage(light_image=imagen, dark_image=imagen,
                                 size=(max(1, int(ancho * escala)), self.ALTO_MINIATURA))
        except Exception:
            # Una miniatura es una ayuda, no un requisito: si el fotograma viene
            # en un formato inesperado, la lista debe seguir siendo utilizable.
            return None

        etiqueta = ctk.CTkLabel(padre, text="", image=vista)
        etiqueta.image = vista       # evita que el recolector la borre
        etiqueta.pack(side="left", padx=(4, 12), pady=8)
        self.miniaturas.append(vista)
        return etiqueta

    # ---------------- datos ----------------

    @staticmethod
    def _titulo_camara(cam):
        """
        El nombre que da el sistema operativo, si lo hay.

        Antes la etiqueta era "Cámara integrada" para el índice 0 y "Cámara N"
        para el resto — una suposición, no un dato: el índice 0 no siempre es la
        integrada, y con tres dispositivos conectados los títulos no distinguían
        ninguno. Cuando el sistema no da nombres se dice el índice y ya, sin
        adivinar de qué dispositivo se trata.
        """
        nombre = cam.get("nombre")
        return nombre if nombre else f"Cámara {cam['indice']}"

    @staticmethod
    def _detalle_camara(cam):
        detalle = f"Índice {cam['indice']} · {cam['ancho']}×{cam['alto']} px"
        if not cam.get("nombre"):
            detalle += " · el sistema no reporta su nombre"
        return detalle

    def buscar_camaras(self):
        """
        Sondea los dispositivos del sistema y redibuja la lista.

        La búsqueda abre y cierra cada índice, así que tarda un momento y no se
        hace sola en cada navegación: se dispara al entrar y con el botón.
        """
        for w in self.lista.winfo_children():
            w.destroy()
        self.miniaturas = []

        self.estado_var.set("")
        self.error_var.set("")

        # Abrir cada dispositivo toma su tiempo y bloquea el ciclo de eventos de
        # Tkinter: sin este aviso la ventana parece congelada y el entrenador
        # vuelve a pulsar el botón, encadenando búsquedas. `update_idletasks`
        # fuerza a que el texto llegue a la pantalla ANTES de empezar a sondear.
        buscando = ctk.CTkLabel(self.lista, text="Buscando cámaras conectadas…",
                                font=(theme.FUENTE, 12.5), text_color=theme.TEXTO_MUTED)
        buscando.pack(pady=16)
        self.update_idletasks()

        try:
            self.disponibles = listar_camaras()
        finally:
            buscando.destroy()

        if self.disponibles:
            for cam in self.disponibles:
                indice = cam["indice"]
                self._tarjeta(str(indice), self._titulo_camara(cam),
                              self._detalle_camara(cam), muestra=cam.get("muestra"))
        else:
            ctk.CTkLabel(self.lista,
                         text="No se detectó ninguna cámara conectada al equipo.",
                         font=(theme.FUENTE, 12.5), text_color=theme.TEXTO_MUTED).pack(pady=16)

        self._tarjeta_ip()

        # Si el dispositivo guardado ya no existe (se desconectó la cámara USB),
        # se avisa en vez de dejar seleccionada en silencio una fuente que va a
        # fallar. Se compara contra `fuente_guardada` y no contra la selección
        # actual: para entonces el bloque de cámara IP ya puede haber puesto su
        # valor interno, y compararlo daba el aviso falso
        # "La cámara configurada (índice __ip__) no está disponible".
        guardada = self.fuente_guardada
        if guardada and not es_url(guardada):
            if guardada not in [str(c["indice"]) for c in self.disponibles]:
                self.error_var.set(
                    f"La cámara configurada (índice {guardada}) no está disponible ahora. "
                    f"Elige otra o vuelve a conectarla.")

    def _tarjeta_ip(self):
        """Bloque de cámara IP: un teléfono en la red local del dojo."""
        caja = ctk.CTkFrame(self.lista, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        caja.pack(fill="x", pady=(10, 3))

        cabecera = ctk.CTkFrame(caja, fg_color="transparent")
        cabecera.pack(fill="x", padx=14, pady=(12, 2))
        ctk.CTkRadioButton(cabecera, text="", variable=self.seleccion, value="__ip__",
                           width=24, radiobutton_width=18, radiobutton_height=18,
                           fg_color=theme.ACENTO_ROJO,
                           border_color=theme.BORDE_CLARO).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(cabecera, text="Celular o cámara IP", font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(side="left")

        ctk.CTkLabel(caja, text="El teléfono corre una app de cámara IP y entrega el video por "
                               "la red local del dojo. No requiere cable ni depender de macOS.",
                     font=(theme.FUENTE, 11.5), text_color=theme.TEXTO_MUTED,
                     wraplength=620, justify="left").pack(anchor="w", padx=(44, 14), pady=(0, 8))

        # Si lo guardado era una URL, se precarga para poder corregirla.
        if es_url(self.fuente_guardada):
            self.url_var.set(self.fuente_guardada)
            self.seleccion.set("__ip__")

        # CustomTkinter desactiva su placeholder_text cuando el campo tiene un
        # textvariable asignado (mismo caso documentado en login_screen.py), así
        # que el ejemplo va en una etiqueta visible: sin él, el entrenador no
        # tiene forma de saber qué formato espera el campo.
        ctk.CTkLabel(caja, text="Dirección del flujo de video", font=(theme.FUENTE, 11),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", padx=(44, 14), pady=(0, 2))
        ctk.CTkEntry(caja, textvariable=self.url_var, width=420).pack(anchor="w", padx=(44, 14))
        ctk.CTkLabel(caja, text="Ejemplo:  http://192.168.1.50:8080/video",
                     font=(theme.FUENTE_MONO, 11), text_color=theme.TEXTO_TENUE).pack(
            anchor="w", padx=(44, 14), pady=(4, 14))

    # ---------------- acciones ----------------

    def fuente_elegida(self):
        """La fuente que representa la selección actual, o None si está incompleta."""
        valor = self.seleccion.get()
        if valor == "__ip__":
            url = self.url_var.get().strip()
            return url or None
        return valor or None

    def probar_seleccion(self):
        """
        Abre la fuente y lee un fotograma real antes de confirmarla.

        Es la diferencia entre descubrir que la cámara no sirve ahora o
        descubrirlo frente al alumno con la sesión ya iniciada.
        """
        fuente = self.fuente_elegida()
        if fuente is None:
            self.estado_var.set("")
            self.error_var.set("Elige una cámara o escribe la dirección de la cámara IP.")
            return False

        try:
            camara = Camera(fuente)
        except CamaraNoDisponible as error:
            self.estado_var.set("")
            self.error_var.set(str(error))
            return False

        try:
            frame = camara.get_frame()
        finally:
            camara.release()

        if frame is None:
            self.estado_var.set("")
            self.error_var.set(
                f"La {describir(fuente).lower()} se abrió pero no entregó imagen. "
                f"Puede estar en uso por otra aplicación.")
            return False

        alto, ancho = frame.shape[:2]
        self.error_var.set("")
        self.estado_var.set(f"Imagen recibida: {ancho}×{alto} px.")
        return True

    def guardar_seleccion(self):
        """Verifica la fuente y, si entrega imagen, la deja configurada."""
        if not self.probar_seleccion():
            return False

        self.db.guardar_config(CLAVE_FUENTE, self.fuente_elegida())
        self.estado_var.set("Cámara configurada. Se usará en la próxima sesión de análisis.")
        return True

    def _volver(self):
        if self.al_terminar is not None:
            self.al_terminar()
        else:
            self.master_app.on_volver_a_perfiles()


def fuente_configurada(db, por_defecto=0):
    """
    Fuente de video guardada, lista para pasarle a `Camera`.

    Vive aquí y no en `Camera` porque la cámara no debe conocer la base de
    datos: es la capa de presentación la que sabe dónde se guardó la
    preferencia del equipo.
    """
    valor = db.leer_config(CLAVE_FUENTE)
    return por_defecto if valor in (None, "") else valor
