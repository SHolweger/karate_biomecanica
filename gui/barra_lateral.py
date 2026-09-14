import customtkinter as ctk

from gui import theme

# Secciones de la barra, en el orden en que se usan durante una clase: primero
# a quién se evalúa, luego con qué criterio, después qué resultó, y al final la
# configuración del equipo — que se toca una vez y casi nunca más.
SECCIONES = [
    ("perfiles",  "Entrenar"),
    ("historial", "Alumnos y progreso"),
    ("tecnicas",  "Técnicas"),
    ("umbrales",  "Calibración"),
    ("camara",    "Cámara"),
]


class BarraLateral(ctk.CTkFrame):
    """
    Navegación permanente del sistema.

    Antes, las opciones colgaban de la pantalla de selección de perfiles: para
    consultar el progreso de un alumno había que pasar por "¿quién entrena hoy?",
    lo que mezclaba dos cosas distintas —elegir a quién medir y administrar el
    sistema— y obligaba a volver al inicio para cambiar de sección.

    La barra resuelve eso haciendo visible el mapa completo: el instructor ve
    todo lo que el sistema hace sin tener que recorrerlo, y sabe siempre dónde
    está parado porque la sección activa queda marcada.

    No decide nada: emite el nombre de la sección elegida y la aplicación
    resuelve qué mostrar. Así la barra no necesita conocer ninguna pantalla.
    """

    ANCHO = 236

    def __init__(self, master, al_navegar, entrenador=None, seccion_activa="perfiles"):
        super().__init__(master, fg_color=theme.CARD, width=self.ANCHO, corner_radius=0)
        self.al_navegar = al_navegar
        self.entrenador = entrenador
        self.seccion_activa = seccion_activa
        self.botones = {}

        self.pack_propagate(False)
        self._marca()
        self._navegacion()
        self._pie()

    def _marca(self):
        caja = ctk.CTkFrame(self, fg_color="transparent")
        caja.pack(fill="x", padx=20, pady=(22, 18))

        ctk.CTkLabel(caja, text="空", width=38, height=38, corner_radius=10,
                     fg_color=theme.ACENTO_ROJO, text_color="white",
                     font=(theme.FUENTE, 17, "bold")).pack(side="left", padx=(0, 12))

        textos = ctk.CTkFrame(caja, fg_color="transparent")
        textos.pack(side="left", anchor="w")
        ctk.CTkLabel(textos, text="SHOTOKAN AI", font=(theme.FUENTE, 14, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w")
        ctk.CTkLabel(textos, text="ANÁLISIS BIOMECÁNICO", font=(theme.FUENTE, 9.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w")

        ctk.CTkFrame(self, fg_color=theme.BORDE, height=1).pack(fill="x")

    def _navegacion(self):
        caja = ctk.CTkFrame(self, fg_color="transparent")
        caja.pack(fill="both", expand=True, padx=10, pady=14)

        for clave, etiqueta in SECCIONES:
            activa = clave == self.seccion_activa
            boton = ctk.CTkButton(
                caja, text=etiqueta, anchor="w", height=36, corner_radius=8,
                font=(theme.FUENTE, 12.5, "bold" if activa else "normal"),
                fg_color=theme.CARD_HOVER if activa else "transparent",
                text_color=theme.TEXTO if activa else theme.TEXTO_MUTED,
                hover_color=theme.CARD_HOVER,
                command=lambda c=clave: self.al_navegar(c))
            boton.pack(fill="x", pady=1)
            self.botones[clave] = boton

    def _pie(self):
        ctk.CTkFrame(self, fg_color=theme.BORDE, height=1).pack(fill="x")
        caja = ctk.CTkFrame(self, fg_color="transparent")
        caja.pack(fill="x", padx=20, pady=16)

        if self.entrenador:
            iniciales = "".join(p[0] for p in self.entrenador["nombre"].split()[:2]).upper()
            fila = ctk.CTkFrame(caja, fg_color="transparent")
            fila.pack(fill="x", anchor="w")
            ctk.CTkLabel(fila, text=iniciales, width=26, height=26, corner_radius=13,
                         fg_color=theme.ACENTO_ROJO, text_color="white",
                         font=(theme.FUENTE, 10.5, "bold")).pack(side="left", padx=(0, 8))
            textos = ctk.CTkFrame(fila, fg_color="transparent")
            textos.pack(side="left", anchor="w")
            ctk.CTkLabel(textos, text=self.entrenador["nombre"], font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO).pack(anchor="w")
            ctk.CTkLabel(textos, text=self.entrenador.get("rol", "sensei").title(),
                         font=(theme.FUENTE, 10),
                         text_color=theme.TEXTO_TENUE).pack(anchor="w")

            ctk.CTkButton(caja, text="Cerrar sesión", height=28, fg_color="transparent",
                          text_color=theme.TEXTO_TENUE, hover_color=theme.CARD_HOVER,
                          font=(theme.FUENTE, 11),
                          command=lambda: self.al_navegar("salir")).pack(fill="x", pady=(10, 0))

    def marcar(self, seccion):
        """Resalta la sección activa sin reconstruir la barra."""
        self.seccion_activa = seccion
        for clave, boton in self.botones.items():
            activa = clave == seccion
            boton.configure(
                fg_color=theme.CARD_HOVER if activa else "transparent",
                text_color=theme.TEXTO if activa else theme.TEXTO_MUTED,
                font=(theme.FUENTE, 12.5, "bold" if activa else "normal"))
