import customtkinter as ctk

from gui import componentes as cp
from gui import theme


class HistorialScreen(ctk.CTkFrame):
    """
    Alumnos y progreso (RF-07).

    Es la vista de conjunto del dojo: un renglón por alumno con cuántas sesiones
    lleva, cuándo entrenó por última vez y qué porcentaje de sus técnicas resultó
    correcto. Responde la pregunta con la que un instructor empieza la clase —
    "¿cómo viene cada quién?"— sin tener que abrir perfil por perfil.

    Los alumnos sin mediciones aparecen igual, con la precisión en blanco. Es una
    decisión deliberada: un alumno recién inscrito debe estar en la lista, y
    mostrarle 0 % afirmaría que falla todo cuando en realidad nunca fue medido.
    """

    def __init__(self, master, db, entrenador=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.master_app = master
        self.db = db
        self.entrenador = entrenador
        self.resumen = []

        cp.encabezado(
            self, "Alumnos y progreso",
            "Estado de cada atleta a partir de sus sesiones registradas",
            acciones=[("Volver", self._volver, False),
                      ("Actualizar", self.recargar, False)],
        )

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(expand=True, fill="both", padx=28, pady=(0, 20))

        self.recargar()

    # ---------------- datos ----------------

    def recargar(self):
        for w in self.lista.winfo_children():
            w.destroy()

        self.resumen = self.db.resumen_atletas()
        if not self.resumen:
            cp.vacio(self.lista, "Todavía no hay alumnos registrados.",
                     "Se registran desde la pantalla de selección de perfiles.")
            return

        self._cabecera()
        for atleta in self.resumen:
            self._fila(atleta)

    def _cabecera(self):
        fila = ctk.CTkFrame(self.lista, fg_color="transparent")
        fila.pack(fill="x", pady=(0, 4))
        for texto, ancho in [("Alumno", 250), ("Grado", 120), ("Sesiones", 90),
                             ("Última", 130), ("Precisión", 230), ("", 110)]:
            ctk.CTkLabel(fila, text=texto, width=ancho, anchor="w",
                         font=(theme.FUENTE, 11, "bold"),
                         text_color=theme.TEXTO_TENUE).pack(side="left", padx=4)

    def _fila(self, atleta):
        caja = cp.tarjeta(self.lista)

        ctk.CTkLabel(caja, text=atleta["nombre"], width=250, anchor="w",
                     font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(side="left", padx=4, pady=10)
        ctk.CTkLabel(caja, text=atleta["grado_cinturon"] or "—", width=120, anchor="w",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(caja, text=str(atleta["sesiones"]), width=90, anchor="w",
                     font=(theme.FUENTE, 12),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(caja, text=atleta["ultima_fecha"] or "—", width=130, anchor="w",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)

        medida = ctk.CTkFrame(caja, fg_color="transparent", width=230)
        medida.pack(side="left", padx=4)
        precision = atleta["precision"]
        ctk.CTkLabel(medida, text=cp.texto_precision(precision), width=60, anchor="w",
                     font=(theme.FUENTE, 13, "bold"),
                     text_color=cp.color_precision(precision)).pack(side="left")
        cp.barra_progreso(medida, precision, ancho=150).pack(side="left", padx=(4, 0))

        ctk.CTkButton(caja, text="Ver perfil", width=110, fg_color="transparent",
                      text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                      font=(theme.FUENTE, 11.5),
                      command=lambda a=atleta: self._abrir(a)).pack(side="left", padx=4)

    # ---------------- navegación ----------------

    def _abrir(self, atleta):
        self.master_app.on_abrir_alumno(atleta["id_atleta"])

    def _volver(self):
        self.master_app.on_volver_a_perfiles()
