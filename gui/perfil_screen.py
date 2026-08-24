import customtkinter as ctk
from gui import theme


class PerfilScreen(ctk.CTkFrame):
    """
    Selección de perfil de atleta al estilo Netflix (sin contraseña — a
    diferencia de LoginScreen, esto no es control de acceso, solo indica
    a quién pertenece la sesión de medición. Ver Bitácora 2026-08-12).
    """

    def __init__(self, master, db, entrenador):
        super().__init__(master, fg_color=theme.FONDO)
        self.db = db
        self.master_app = master
        self.entrenador = entrenador

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(contenedor, text=f"Bienvenido, {entrenador['nombre']}",
                     font=(theme.FUENTE, 15), text_color=theme.TEXTO_MUTED).pack(pady=(0, 6))
        ctk.CTkLabel(contenedor, text="¿Quién entrena hoy?", font=(theme.FUENTE, 22, "bold"),
                     text_color=theme.TEXTO).pack(pady=(0, 24))

        self.fila_perfiles = ctk.CTkFrame(contenedor, fg_color="transparent")
        self.fila_perfiles.pack()

        self.form_nuevo = None
        self._render_perfiles()

    def _render_perfiles(self):
        for w in self.fila_perfiles.winfo_children():
            w.destroy()

        atletas = self.db.listar_atletas()
        for atleta in atletas:
            self._tarjeta_atleta(atleta)
        self._tarjeta_agregar()

    def _tarjeta_atleta(self, atleta):
        iniciales = "".join(p[0] for p in atleta["nombre"].split()[:2]).upper()
        tarjeta = ctk.CTkFrame(self.fila_perfiles, fg_color=theme.CARD, border_color=theme.BORDE,
                               border_width=1, corner_radius=14, width=150, height=170)
        tarjeta.pack(side="left", padx=9)
        tarjeta.pack_propagate(False)

        ctk.CTkLabel(tarjeta, text=iniciales, width=76, height=76, corner_radius=38,
                     fg_color=theme.ACENTO_ROJO, text_color="white",
                     font=(theme.FUENTE, 22, "bold")).pack(pady=(22, 10))
        ctk.CTkLabel(tarjeta, text=atleta["nombre"], font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack()
        ctk.CTkLabel(tarjeta, text=atleta.get("grado_cinturon") or "Sin grado registrado",
                     font=(theme.FUENTE, 11), text_color=theme.TEXTO_MUTED).pack()

        for widget in (tarjeta, *tarjeta.winfo_children()):
            widget.bind("<Button-1>", lambda e, a=atleta: self._elegir(a))

    def _tarjeta_agregar(self):
        tarjeta = ctk.CTkFrame(self.fila_perfiles, fg_color="transparent", border_color=theme.BORDE_CLARO,
                               border_width=1, corner_radius=14, width=150, height=170)
        tarjeta.pack(side="left", padx=9)
        tarjeta.pack_propagate(False)

        ctk.CTkLabel(tarjeta, text="+", width=76, height=76, corner_radius=38,
                     fg_color="transparent", border_color=theme.BORDE_CLARO, border_width=1,
                     text_color=theme.TEXTO_TENUE, font=(theme.FUENTE, 30)).pack(pady=(22, 10))
        ctk.CTkLabel(tarjeta, text="Agregar perfil", font=(theme.FUENTE, 12),
                     text_color=theme.TEXTO_TENUE).pack()

        for widget in (tarjeta, *tarjeta.winfo_children()):
            widget.bind("<Button-1>", lambda e: self._abrir_form_nuevo())

    def _elegir(self, atleta):
        self.master_app.on_perfil_elegido(atleta)

    def _abrir_form_nuevo(self):
        if self.form_nuevo is not None:
            return  # ya está abierto

        self.form_nuevo = ctk.CTkToplevel(self)
        self.form_nuevo.title("Nuevo perfil")
        self.form_nuevo.geometry("340x260")
        self.form_nuevo.configure(fg_color=theme.CARD)
        self.form_nuevo.protocol("WM_DELETE_WINDOW", self._cerrar_form_nuevo)

        nombre_var = ctk.StringVar()
        grado_var = ctk.StringVar()

        ctk.CTkLabel(self.form_nuevo, text="Registrar nuevo alumno", font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(padx=22, pady=(20, 14), anchor="w")

        # CustomTkinter desactiva su placeholder_text cuando el campo tiene un
        # textvariable asignado, por eso las etiquetas son necesarias, no decorativas.
        ctk.CTkLabel(self.form_nuevo, text="Nombre completo", font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(padx=22, pady=(0, 2), anchor="w")
        ctk.CTkEntry(self.form_nuevo, textvariable=nombre_var, width=290).pack(padx=22)

        ctk.CTkLabel(self.form_nuevo, text="Grado (ej. 5º kyu, opcional)", font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(padx=22, pady=(10, 2), anchor="w")
        ctk.CTkEntry(self.form_nuevo, textvariable=grado_var, width=290).pack(padx=22)

        def guardar():
            nombre = nombre_var.get().strip()
            if not nombre:
                return
            self.db.crear_atleta(nombre, grado_cinturon=grado_var.get().strip() or None)
            self._cerrar_form_nuevo()
            self._render_perfiles()

        ctk.CTkButton(self.form_nuevo, text="Guardar alumno", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER, command=guardar,
                      width=290).pack(padx=22, pady=18)

    def _cerrar_form_nuevo(self):
        if self.form_nuevo is not None:
            self.form_nuevo.destroy()
            self.form_nuevo = None
