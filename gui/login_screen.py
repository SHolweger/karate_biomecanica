import customtkinter as ctk
from gui import theme


class LoginScreen(ctk.CTkFrame):
    """
    Pantalla de acceso del entrenador (RF-08). Si no hay ningún entrenador
    registrado todavía, arranca directo en modo "crear cuenta" — mismo
    comportamiento que persistence/cli_auth.py, ahora en GUI.
    """

    def __init__(self, master, db):
        super().__init__(master, fg_color=theme.FONDO)
        self.db = db
        self.master_app = master

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(contenedor, text="空", width=56, height=56, corner_radius=14,
                     fg_color=theme.ACENTO_ROJO, text_color="white",
                     font=(theme.FUENTE, 26, "bold")).pack(pady=(0, 14))
        ctk.CTkLabel(contenedor, text="SHOTOKAN AI", font=(theme.FUENTE, 22, "bold"),
                     text_color=theme.TEXTO).pack()
        ctk.CTkLabel(contenedor, text="Sistema experto de análisis biomecánico · Karate-Do Shotokan",
                     font=(theme.FUENTE, 12), text_color=theme.TEXTO_MUTED).pack(pady=(2, 28))

        self.caja = ctk.CTkFrame(contenedor, fg_color=theme.CARD, border_color=theme.BORDE,
                                  border_width=1, corner_radius=14, width=340)
        self.caja.pack()

        self.error_var = ctk.StringVar(value="")
        self.usuario_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.nombre_var = ctk.StringVar()
        self.correo_var = ctk.StringVar()

        if self.db.existe_algun_entrenador():
            self._render_login()
        else:
            self._render_registro(rol="principal", primer_uso=True)

    def _campo(self, etiqueta, variable, show=None):
        """
        Etiqueta + campo de entrada. CustomTkinter desactiva su propio
        placeholder_text cuando el campo tiene un textvariable asignado (así
        está diseñada la librería), así que la etiqueta visible es necesaria
        — no es decorativa, es la única forma de saber qué va en cada campo.
        """
        ctk.CTkLabel(self.caja, text=etiqueta, font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(padx=28, pady=(6, 2), anchor="w")
        ctk.CTkEntry(self.caja, textvariable=variable, show=show or "", width=284).pack(padx=28)

    # ---------------- Modo login ----------------
    def _render_login(self):
        for w in self.caja.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.caja, text="Acceso de entrenador", font=(theme.FUENTE, 16, "bold"),
                     text_color=theme.TEXTO).pack(padx=28, pady=(22, 4), anchor="w")
        ctk.CTkLabel(self.caja, text="Ingresa con tu cuenta del dojo", font=(theme.FUENTE, 12),
                     text_color=theme.TEXTO_MUTED).pack(padx=28, pady=(0, 18), anchor="w")

        self._campo("Usuario", self.usuario_var)
        self._campo("Contraseña", self.password_var, show="•")

        ctk.CTkLabel(self.caja, textvariable=self.error_var, text_color=theme.ACENTO_ROJO,
                     font=(theme.FUENTE, 11.5)).pack(padx=28, pady=(4, 0))

        ctk.CTkButton(self.caja, text="Ingresar", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER, command=self._intentar_login,
                      width=284).pack(padx=28, pady=(12, 6))
        ctk.CTkButton(self.caja, text="Crear cuenta nueva", fg_color="transparent",
                      text_color=theme.ACENTO_VERDE, hover_color=theme.CARD_HOVER,
                      command=lambda: self._render_registro(rol="sensei", primer_uso=False),
                      width=284).pack(padx=28, pady=(0, 22))

    def _intentar_login(self):
        entrenador = self.db.autenticar_entrenador(self.usuario_var.get().strip(), self.password_var.get())
        if entrenador is None:
            self.error_var.set("Usuario o contraseña incorrectos.")
            return
        self.master_app.on_login_exitoso(entrenador)

    # ---------------- Modo registro ----------------
    def _render_registro(self, rol, primer_uso):
        for w in self.caja.winfo_children():
            w.destroy()

        titulo = "Crear la primera cuenta" if primer_uso else "Crear cuenta nueva"
        subt = "No hay entrenadores registrados todavía" if primer_uso else "Se creará como cuenta de sensei"
        ctk.CTkLabel(self.caja, text=titulo, font=(theme.FUENTE, 16, "bold"),
                     text_color=theme.TEXTO).pack(padx=28, pady=(22, 4), anchor="w")
        ctk.CTkLabel(self.caja, text=subt, font=(theme.FUENTE, 12),
                     text_color=theme.TEXTO_MUTED).pack(padx=28, pady=(0, 18), anchor="w")

        self._campo("Nombre completo", self.nombre_var)
        self._campo("Nombre de usuario", self.usuario_var)
        self._campo("Correo", self.correo_var)
        self._campo("Contraseña", self.password_var, show="•")

        ctk.CTkLabel(self.caja, textvariable=self.error_var, text_color=theme.ACENTO_ROJO,
                     font=(theme.FUENTE, 11.5)).pack(padx=28, pady=(4, 0))

        ctk.CTkButton(self.caja, text="Crear cuenta", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER,
                      command=lambda: self._crear_cuenta(rol), width=284).pack(padx=28, pady=(12, 6))

        if not primer_uso:
            ctk.CTkButton(self.caja, text="Ya tengo cuenta", fg_color="transparent",
                          text_color=theme.ACENTO_VERDE, hover_color=theme.CARD_HOVER,
                          command=self._render_login, width=284).pack(padx=28, pady=(0, 22))
        else:
            ctk.CTkFrame(self.caja, fg_color="transparent", height=22).pack()

    def _crear_cuenta(self, rol):
        nombre = self.nombre_var.get().strip()
        usuario = self.usuario_var.get().strip()
        correo = self.correo_var.get().strip()
        password = self.password_var.get()

        if not nombre or not usuario or not password:
            self.error_var.set("Nombre, usuario y contraseña son obligatorios.")
            return

        self.db.crear_entrenador(nombre, usuario, correo, password, rol=rol)
        entrenador = self.db.autenticar_entrenador(usuario, password)
        self.master_app.on_login_exitoso(entrenador)
