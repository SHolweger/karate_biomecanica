import customtkinter as ctk

from gui import theme


class PerfilScreen(ctk.CTkFrame):
    """
    Selección del sensei que dirige la sesión (RF-08).

    Hasta el 14-sep-2026 esta pantalla listaba ALUMNOS y su botón «+» los
    inscribía, de modo que quien quisiera registrar a un sensei nuevo terminaba
    creando un alumno. Era una confusión de fondo, no de etiqueta: el perfil
    identifica a quién opera el sistema y firma cada medición; el alumno es a
    quién se mide, y se inscribe desde la sección de alumnos.

    A diferencia de un selector de perfiles al estilo Netflix, elegir una tarjeta
    aquí NO da acceso: pide la contraseña de ese sensei. Saltarse ese paso
    convertiría la pantalla en una puerta trasera al inicio de sesión —
    cualquiera podría operar como el sensei principal con un clic— y dejaría sin
    valor el hash SHA-256 del RNF-05, además de falsear la firma que queda en
    cada umbral recalibrado y en cada sesión registrada.

    Ocupa la ventana completa y sin barra lateral a propósito: mientras no haya
    un sensei identificado no hay nada que navegar.
    """

    def __init__(self, master, db, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.db = db
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación.
        self.master_app = app if app is not None else master
        self.entrenador = entrenador
        self.error_var = ctk.StringVar(value="")
        self.password_var = ctk.StringVar(value="")
        self.seleccionado = None
        self.tarjetas = {}

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.place(relx=0.5, rely=0.5, anchor="center")
        self.contenedor = contenedor

        ctk.CTkLabel(contenedor, text="SHOTOKAN AI", font=(theme.FUENTE, 12, "bold"),
                     text_color=theme.TEXTO_TENUE).pack(pady=(0, 6))
        ctk.CTkLabel(contenedor, text="¿Quién dirige la sesión?",
                     font=(theme.FUENTE, 22, "bold"),
                     text_color=theme.TEXTO).pack(pady=(0, 4))
        ctk.CTkLabel(contenedor, text="Cada medición queda firmada por el sensei que la tomó",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(pady=(0, 22))

        self.fila_perfiles = ctk.CTkFrame(contenedor, fg_color="transparent")
        self.fila_perfiles.pack()

        self.caja_clave = ctk.CTkFrame(contenedor, fg_color="transparent")

        ctk.CTkLabel(contenedor, textvariable=self.error_var, font=(theme.FUENTE, 11.5),
                     text_color=theme.ACENTO_ROJO, wraplength=520).pack(pady=(14, 0))

        self._render_perfiles()

    # ---------------- tarjetas ----------------

    def _render_perfiles(self):
        for w in self.fila_perfiles.winfo_children():
            w.destroy()
        self.tarjetas = {}

        for sensei in self.db.listar_entrenadores():
            self._tarjeta_sensei(sensei)

    def _tarjeta_sensei(self, sensei):
        iniciales = "".join(p[0] for p in sensei["nombre"].split()[:2]).upper()
        tarjeta = ctk.CTkFrame(self.fila_perfiles, fg_color=theme.CARD, border_color=theme.BORDE,
                               border_width=1, corner_radius=14, width=150, height=170)
        tarjeta.pack(side="left", padx=9)
        tarjeta.pack_propagate(False)

        ctk.CTkLabel(tarjeta, text=iniciales, width=76, height=76, corner_radius=38,
                     fg_color=theme.ACENTO_ROJO, text_color="white",
                     font=(theme.FUENTE, 22, "bold")).pack(pady=(22, 10))
        ctk.CTkLabel(tarjeta, text=sensei["nombre"], font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack()
        ctk.CTkLabel(tarjeta, text=(sensei.get("rol") or "sensei").title(),
                     font=(theme.FUENTE, 11), text_color=theme.TEXTO_MUTED).pack()

        for widget in (tarjeta, *tarjeta.winfo_children()):
            widget.bind("<Button-1>", lambda e, s=sensei: self._pedir_clave(s))
        self.tarjetas[sensei["id_entrenador"]] = tarjeta

    # ---------------- contraseña ----------------

    def _pedir_clave(self, sensei):
        """
        Marca el sensei elegido y despliega el campo de contraseña bajo las
        tarjetas. No se abre una ventana aparte: el paso es parte de elegir, no
        un trámite distinto.
        """
        self.seleccionado = sensei
        self.error_var.set("")
        self.password_var.set("")

        for id_entrenador, tarjeta in self.tarjetas.items():
            elegida = id_entrenador == sensei["id_entrenador"]
            tarjeta.configure(border_color=theme.ACENTO_ROJO if elegida else theme.BORDE,
                              border_width=2 if elegida else 1)

        for w in self.caja_clave.winfo_children():
            w.destroy()
        self.caja_clave.pack(pady=(22, 0))

        ctk.CTkLabel(self.caja_clave, text=f"Contraseña de {sensei['nombre']}",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(pady=(0, 6))

        fila = ctk.CTkFrame(self.caja_clave, fg_color="transparent")
        fila.pack()
        entrada = ctk.CTkEntry(fila, textvariable=self.password_var, show="•", width=240,
                               height=36)
        entrada.pack(side="left", padx=(0, 8))
        entrada.bind("<Return>", lambda e: self._entrar())
        entrada.focus_set()

        ctk.CTkButton(fila, text="Entrar", width=100, height=36, fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER,
                      command=self._entrar).pack(side="left")

    def _entrar(self):
        """Valida la contraseña contra la base; sin ella no se entra."""
        if self.seleccionado is None:
            self.error_var.set("Elige primero un perfil de sensei.")
            return 0

        sensei = self.db.autenticar_entrenador(self.seleccionado["usuario"],
                                               self.password_var.get())
        if sensei is None:
            self.error_var.set("Contraseña incorrecta.")
            self.password_var.set("")
            return 0

        self.master_app.on_login_exitoso(sensei)
        return 1
