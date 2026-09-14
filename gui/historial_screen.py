import customtkinter as ctk

from gui import componentes as cp
from gui import theme
from gui.registro_alumno import (COLORES_CINTA, DatosInvalidos, grados_de,
                                 interpretar_formulario, pide_grado)


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

    def __init__(self, master, db, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación. Desde que existe la barra lateral son objetos
        # distintos: el contenedor es el área de contenido, no la ventana.
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador
        self.resumen = []
        self.ventana_registro = None
        self.campos = {}
        self.error_registro = ctk.StringVar(value="")

        cp.encabezado(
            self, "Alumnos y progreso",
            "Estado de cada atleta a partir de sus sesiones registradas",
            acciones=[("Registrar alumno", self.abrir_registro, True),
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
                     "Usa «Registrar alumno» para inscribir al primero.")
            return

        self._cabecera()
        for atleta in self.resumen:
            self._fila(atleta)

    def _cabecera(self):
        fila = ctk.CTkFrame(self.lista, fg_color="transparent")
        fila.pack(fill="x", pady=(0, 4))
        for texto, ancho in [("Alumno", 210), ("Grado", 100), ("Sesiones", 80),
                             ("Última", 110), ("Precisión", 200), ("", 100)]:
            ctk.CTkLabel(fila, text=texto, width=ancho, anchor="w",
                         font=(theme.FUENTE, 11, "bold"),
                         text_color=theme.TEXTO_TENUE).pack(side="left", padx=4)

    def _fila(self, atleta):
        caja = cp.tarjeta(self.lista)

        ctk.CTkLabel(caja, text=atleta["nombre"], width=210, anchor="w",
                     font=(theme.FUENTE, 13, "bold"),
                     text_color=theme.TEXTO).pack(side="left", padx=4, pady=10)
        ctk.CTkLabel(caja, text=atleta["grado_cinturon"] or "—", width=100, anchor="w",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(caja, text=str(atleta["sesiones"]), width=80, anchor="w",
                     font=(theme.FUENTE, 12),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)
        ctk.CTkLabel(caja, text=atleta["ultima_fecha"] or "—", width=110, anchor="w",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)

        medida = ctk.CTkFrame(caja, fg_color="transparent", width=200)
        medida.pack(side="left", padx=4)
        precision = atleta["precision"]
        ctk.CTkLabel(medida, text=cp.texto_precision(precision), width=60, anchor="w",
                     font=(theme.FUENTE, 13, "bold"),
                     text_color=cp.color_precision(precision)).pack(side="left")
        cp.barra_progreso(medida, precision, ancho=128).pack(side="left", padx=(4, 0))

        ctk.CTkButton(caja, text="Ver perfil", width=100, fg_color="transparent",
                      text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                      font=(theme.FUENTE, 11.5),
                      command=lambda a=atleta: self._abrir(a)).pack(side="left", padx=4)

    # ---------------- navegación ----------------

    def _abrir(self, atleta):
        self.master_app.on_abrir_alumno(atleta["id_atleta"])

    def _volver(self):
        self.master_app.on_volver_a_perfiles()

    # ---------------- inscripción ----------------
    #
    # Los alumnos se inscriben aquí y no en la selección de perfiles: el perfil
    # identifica al sensei que opera el sistema, el alumno es a quién se mide.
    # Hasta el 14-sep-2026 el botón «+» de la selección de perfiles creaba
    # atletas, de modo que registrar a un instructor nuevo lo convertía en
    # alumno.

    def abrir_registro(self):
        if self.ventana_registro is not None:
            self.ventana_registro.focus()
            return self.ventana_registro

        self.error_registro.set("")
        self.campos = {clave: ctk.StringVar() for clave in
                       ("nombre", "edad", "peso", "color_cinta", "grado",
                        "tiempo_entrenando", "notas")}

        ventana = ctk.CTkToplevel(self)
        ventana.title("Registrar nuevo alumno")
        ventana.geometry("460x560")
        ventana.configure(fg_color=theme.CARD)
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar_registro)
        self.ventana_registro = ventana

        ctk.CTkLabel(ventana, text="Registrar nuevo alumno", font=(theme.FUENTE, 17, "bold"),
                     text_color=theme.TEXTO).pack(padx=26, pady=(22, 2), anchor="w")
        ctk.CTkLabel(ventana, text="Su progreso quedará registrado desde la primera sesión",
                     font=(theme.FUENTE, 11.5), text_color=theme.TEXTO_MUTED).pack(
            padx=26, pady=(0, 16), anchor="w")

        self._campo(ventana, "Nombre completo", "nombre")

        fila = ctk.CTkFrame(ventana, fg_color="transparent")
        fila.pack(fill="x", padx=26, pady=(10, 0))
        self._campo(fila, "Edad", "edad", ancho=190, lado="left")
        self._campo(fila, "Peso (kg)", "peso", ancho=190, lado="right")

        self._selector_cinta(ventana)
        self._campo(ventana, "Tiempo entrenando (ej. 2 años)", "tiempo_entrenando")
        self._campo(ventana, "Notas del sensei (lesiones, objetivos)", "notas", alto=70)

        ctk.CTkLabel(ventana, textvariable=self.error_registro, font=(theme.FUENTE, 11.5),
                     text_color=theme.ACENTO_ROJO, wraplength=400,
                     justify="left").pack(padx=26, pady=(10, 0), anchor="w")

        botones = ctk.CTkFrame(ventana, fg_color="transparent")
        botones.pack(fill="x", padx=26, pady=(12, 20))
        ctk.CTkButton(botones, text="Guardar alumno", fg_color=theme.ACENTO_ROJO,
                      hover_color=theme.ACENTO_ROJO_HOVER, width=170,
                      command=self.guardar_alumno).pack(side="right")
        ctk.CTkButton(botones, text="Cancelar", fg_color="transparent", border_width=1,
                      border_color=theme.BORDE_CLARO, text_color=theme.TEXTO,
                      hover_color=theme.CARD_HOVER, width=120,
                      command=self.cerrar_registro).pack(side="right", padx=(0, 8))
        return ventana

    def _campo(self, padre, etiqueta, clave, ancho=None, lado=None, alto=None):
        # CustomTkinter desactiva su placeholder cuando el campo tiene un
        # textvariable, así que las etiquetas son necesarias, no decorativas.
        caja = ctk.CTkFrame(padre, fg_color="transparent")
        caja.pack(side=lado, fill="x", padx=(0 if lado else 26),
                  pady=(0 if lado else 10, 0), expand=lado is not None)
        ctk.CTkLabel(caja, text=etiqueta, font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 3))
        entrada = ctk.CTkEntry(caja, textvariable=self.campos[clave],
                               width=ancho or 400, height=alto or 34)
        entrada.pack(anchor="w")
        return entrada

    def _selector_cinta(self, padre):
        """
        Color de cinta y, solo cuando corresponde, grado numérico.

        El grado aparece a partir del café porque hasta ahí el color ya
        determina el kyu; del café en adelante un mismo color abarca varios
        grados y el número sí agrega información.
        """
        caja = ctk.CTkFrame(padre, fg_color="transparent")
        caja.pack(fill="x", padx=26, pady=(10, 0))

        ctk.CTkLabel(caja, text="Color de cinta", font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 3))
        ctk.CTkOptionMenu(caja, values=COLORES_CINTA, variable=self.campos["color_cinta"],
                          width=190, fg_color=theme.FONDO, button_color=theme.BORDE,
                          button_hover_color=theme.CARD_HOVER, text_color=theme.TEXTO,
                          command=self._al_cambiar_cinta).pack(anchor="w")
        self.campos["color_cinta"].set(COLORES_CINTA[0])

        self.caja_grado = ctk.CTkFrame(padre, fg_color="transparent")
        self._al_cambiar_cinta(COLORES_CINTA[0])

    def _al_cambiar_cinta(self, color):
        for w in self.caja_grado.winfo_children():
            w.destroy()

        if not pide_grado(color):
            self.caja_grado.pack_forget()
            self.campos["grado"].set("")
            return

        self.caja_grado.pack(fill="x", padx=26, pady=(10, 0))
        ctk.CTkLabel(self.caja_grado, text="Grado (kyu / dan)", font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 3))
        opciones = grados_de(color)
        ctk.CTkOptionMenu(self.caja_grado, values=opciones, variable=self.campos["grado"],
                          width=190, fg_color=theme.FONDO, button_color=theme.BORDE,
                          button_hover_color=theme.CARD_HOVER,
                          text_color=theme.TEXTO).pack(anchor="w")
        self.campos["grado"].set(opciones[0])

    def guardar_alumno(self):
        """Valida, inscribe y refresca la lista. Devuelve el id o None si no guardó."""
        try:
            datos = interpretar_formulario(**{c: v.get() for c, v in self.campos.items()})
        except DatosInvalidos as error:
            self.error_registro.set(str(error))
            return None

        id_atleta = self.db.crear_atleta(**datos)
        self.cerrar_registro()
        self.recargar()
        return id_atleta

    def cerrar_registro(self):
        if self.ventana_registro is not None:
            self.ventana_registro.destroy()
            self.ventana_registro = None
