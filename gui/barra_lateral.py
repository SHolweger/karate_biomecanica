import customtkinter as ctk

from gui import theme
# La composición del menú y el texto del control de cambio de perfil viven en
# `gui/navegacion.py`, que no importa CustomTkinter: así la suite puede
# verificar qué secciones existen y cuántos clics cuesta cada tarea (RNF-04)
# también en integración continua, donde no hay entorno gráfico. Se reexportan
# aquí porque este sigue siendo el lugar donde se los busca al leer la barra.
from gui.navegacion import SECCIONES, etiqueta_cambiar_perfil


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

    def __init__(self, master, al_navegar, entrenador=None, seccion_activa="inicio"):
        super().__init__(master, fg_color=theme.CARD, width=self.ANCHO, corner_radius=0)
        self.al_navegar = al_navegar
        self.entrenador = entrenador
        self.seccion_activa = seccion_activa
        self.botones = {}
        self.acentos = {}
        self.boton_cambiar = None
        # Estado del hardware inercial (RF-02, RF-04). Mientras no haya sensores
        # armados el sistema lo dice con todas sus letras en vez de callarlo.
        self.texto_sensores = "Sin sensores IMU · solo visión"

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

            # Cada opción es una fila con una barra de acento a la izquierda. La
            # barra marca la sección activa con una señal que no depende del
            # color del texto ni del fondo, de modo que se distingue de un
            # vistazo y también para quien no diferencia bien esos tonos.
            fila = ctk.CTkFrame(caja, fg_color="transparent", height=38)
            fila.pack(fill="x", pady=1)
            fila.pack_propagate(False)

            acento = ctk.CTkFrame(fila, width=3, corner_radius=2,
                                  fg_color=theme.ACENTO_ROJO if activa else "transparent")
            acento.pack(side="left", fill="y", pady=6)
            acento.pack_propagate(False)

            boton = ctk.CTkButton(
                fila, text=etiqueta, anchor="w", height=36, corner_radius=8,
                font=(theme.FUENTE, 12.5, "bold" if activa else "normal"),
                fg_color=theme.CARD_HOVER if activa else "transparent",
                text_color=theme.TEXTO if activa else theme.TEXTO_MUTED,
                hover_color=theme.CARD_HOVER,
                command=lambda c=clave: self.al_navegar(c))
            boton.pack(side="left", fill="both", expand=True, padx=(7, 0))

            self.botones[clave] = boton
            self.acentos[clave] = acento

    def _pie(self):
        """
        Identidad activa y estado del equipo.

        El pie responde dos preguntas que el instructor se hace a mitad de una
        clase: quién está operando el sistema y si el hardware está listo. El
        estado de los sensores se declara aunque no haya ninguno — decir "sin
        sensores IMU" es información; omitir la línea dejaría creer que el
        sistema los está usando.
        """
        ctk.CTkFrame(self, fg_color=theme.BORDE, height=1).pack(fill="x")
        caja = ctk.CTkFrame(self, fg_color="transparent")
        caja.pack(fill="x", padx=20, pady=16)

        estado = ctk.CTkFrame(caja, fg_color="transparent")
        estado.pack(fill="x", anchor="w", pady=(0, 12))
        ctk.CTkLabel(estado, text="●", font=(theme.FUENTE, 11),
                     text_color=theme.TEXTO_TENUE).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(estado, text=self.texto_sensores, font=(theme.FUENTE, 10.5),
                     text_color=theme.TEXTO_TENUE).pack(side="left")

        if not self.entrenador:
            return

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

        # "Cambiar perfil" cuelga de la identidad activa y no de la lista de
        # secciones: no es un lugar del sistema al que se va, es cambiar quién
        # lo está usando.
        self.boton_cambiar = ctk.CTkButton(
            textos, text=etiqueta_cambiar_perfil(self.entrenador.get("rol")),
            height=16, fg_color="transparent", hover_color=theme.CARD_HOVER,
            text_color=theme.TEXTO_TENUE, font=(theme.FUENTE, 10), anchor="w",
            command=lambda: self.al_navegar("perfiles"))
        self.boton_cambiar.pack(anchor="w")

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
            self.acentos[clave].configure(
                fg_color=theme.ACENTO_ROJO if activa else "transparent")
