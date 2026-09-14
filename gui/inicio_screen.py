import customtkinter as ctk

from gui import componentes as cp
from gui import theme
from gui.umbrales_screen import NOMBRE_TECNICA

# Estado del subsistema inercial (RF-02, RF-04). Mientras el hardware no esté
# armado, la tarjeta lo declara en vez de mostrar un contador en cero, que se
# leería como "hay sensores y ninguno responde" — un diagnóstico distinto y
# falso. Cuando los IMU entren, este texto se reemplaza por su conteo real.
SENSORES_IMU_DISPONIBLES = False
TEXTO_SIN_SENSORES = "Sin sensores IMU"
DETALLE_SIN_SENSORES = "análisis por visión"


class InicioScreen(ctk.CTkFrame):
    """
    Panel de inicio: el estado del dojo de un vistazo (RF-07).

    Es lo primero que el instructor ve al entrar, y responde las preguntas con
    las que empieza una clase: cuánto se ha entrenado esta semana, quiénes están
    viniendo, qué tal viene saliendo la técnica y qué se está practicando más.

    Todas las cifras salen de consultas agregadas sobre las mediciones reales; no
    hay ningún número de ejemplo. Donde no existe el dato, la pantalla lo dice —
    esa es la razón de que la precisión pueda aparecer como guion y de que la
    tarjeta de sensores declare su ausencia en vez de mostrar «0».
    """

    def __init__(self, master, db, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador

        nombre = (entrenador or {}).get("nombre", "sensei")
        cp.encabezado(
            self, f"Bienvenido, {nombre}",
            "Estado del dojo y actividad reciente",
            acciones=[("Iniciar análisis en vivo", self._abrir_vivo, True)],
        )

        self.cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cuerpo.pack(expand=True, fill="both", padx=28, pady=(0, 20))

        self.recargar()

    # ---------------- datos ----------------

    def recargar(self):
        for w in self.cuerpo.winfo_children():
            w.destroy()

        self.metricas = self.db.metricas_dojo()
        self.recientes = self.db.sesiones_recientes(limite=5)
        self.practicadas = self.db.tecnicas_mas_practicadas(limite=5)

        self._tarjetas_metricas()
        self._columnas()

    def _tarjetas_metricas(self):
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(fill="x", pady=(4, 14))

        dias = self.metricas["dias"]
        precision = self.metricas["precision"]
        activos = self.metricas["alumnos_activos"]
        inscritos = self.metricas["alumnos_inscritos"]

        tarjetas = [
            ("Sesiones", str(self.metricas["sesiones"]), f"últimos {dias} días", theme.TEXTO),
            ("Alumnos activos", str(activos),
             f"de {inscritos} inscrito{'s' if inscritos != 1 else ''}", theme.TEXTO),
            ("Precisión promedio", cp.texto_precision(precision),
             self._detalle_precision(), cp.color_precision(precision)),
        ]
        if SENSORES_IMU_DISPONIBLES:  # pragma: no cover - aún no hay hardware
            tarjetas.append(("Sensores IMU", "—", "conectados", theme.TEXTO))
        else:
            tarjetas.append(("Sensores IMU", TEXTO_SIN_SENSORES, DETALLE_SIN_SENSORES,
                             theme.TEXTO_TENUE))

        for titulo, valor, detalle, color in tarjetas:
            caja = ctk.CTkFrame(fila, fg_color=theme.CARD, border_color=theme.BORDE,
                                border_width=1, corner_radius=10)
            caja.pack(side="left", expand=True, fill="both", padx=(0, 10))
            ctk.CTkLabel(caja, text=titulo, font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_MUTED).pack(anchor="w", padx=16, pady=(14, 2))
            # Las cifras van grandes; el texto de "sin sensores" no cabría a ese
            # tamaño y además no es una cifra, así que se compone más pequeño.
            tamano = 24 if valor != TEXTO_SIN_SENSORES else 14
            ctk.CTkLabel(caja, text=valor, font=(theme.FUENTE, tamano, "bold"),
                         text_color=color).pack(anchor="w", padx=16)
            ctk.CTkLabel(caja, text=detalle, font=(theme.FUENTE, 10.5),
                         text_color=theme.TEXTO_TENUE).pack(anchor="w", padx=16, pady=(2, 14))

    def _detalle_precision(self):
        evaluaciones = self.metricas["evaluaciones"]
        if evaluaciones == 0:
            return "aún sin mediciones"
        return f"sobre {evaluaciones} evaluacion{'es' if evaluaciones != 1 else ''}"

    # ---------------- columnas ----------------

    def _columnas(self):
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(fill="both", expand=True)

        izquierda = ctk.CTkFrame(fila, fg_color=theme.CARD, border_color=theme.BORDE,
                                 border_width=1, corner_radius=10)
        izquierda.pack(side="left", expand=True, fill="both", padx=(0, 10))
        self._sesiones_recientes(izquierda)

        derecha = ctk.CTkFrame(fila, fg_color=theme.CARD, border_color=theme.BORDE,
                               border_width=1, corner_radius=10, width=340)
        derecha.pack(side="left", fill="both")
        derecha.pack_propagate(False)
        self._tecnicas_practicadas(derecha)

    def _sesiones_recientes(self, padre):
        cabecera = ctk.CTkFrame(padre, fg_color="transparent")
        cabecera.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(cabecera, text="Sesiones recientes", font=(theme.FUENTE, 14, "bold"),
                     text_color=theme.TEXTO).pack(side="left")
        ctk.CTkButton(cabecera, text="Ver historial", width=110, height=24,
                      fg_color="transparent", hover_color=theme.CARD_HOVER,
                      text_color=theme.ACENTO_VERDE, font=(theme.FUENTE, 11),
                      command=self._abrir_historial).pack(side="right")

        if not self.recientes:
            cp.vacio(padre, "Todavía no se ha registrado ninguna sesión.",
                     "Elige «Análisis en vivo» para tomar la primera medición.")
            return

        for sesion in self.recientes:
            self._fila_sesion(padre, sesion)
        ctk.CTkFrame(padre, fg_color="transparent", height=10).pack()

    def _fila_sesion(self, padre, sesion):
        fila = ctk.CTkFrame(padre, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=3)

        iniciales = "".join(p[0] for p in sesion["atleta"].split()[:2]).upper()
        ctk.CTkLabel(fila, text=iniciales, width=32, height=32, corner_radius=16,
                     fg_color=theme.BORDE, text_color=theme.TEXTO,
                     font=(theme.FUENTE, 11, "bold")).pack(side="left", padx=(0, 10))

        textos = ctk.CTkFrame(fila, fg_color="transparent")
        textos.pack(side="left", anchor="w")
        ctk.CTkLabel(textos, text=sesion["atleta"], font=(theme.FUENTE, 12.5, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w")
        ctk.CTkLabel(textos, text=f"{cp.fecha_legible(sesion['hora_inicio'])} · "
                                  f"{sesion['evaluaciones']} evaluaciones",
                     font=(theme.FUENTE, 10.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w")

        precision = sesion["precision"]
        ctk.CTkLabel(fila, text=cp.texto_precision(precision), font=(theme.FUENTE, 13, "bold"),
                     text_color=cp.color_precision(precision)).pack(side="right", padx=(0, 6))

    def _tecnicas_practicadas(self, padre):
        ctk.CTkLabel(padre, text="Técnicas más practicadas", font=(theme.FUENTE, 14, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", padx=18, pady=(16, 12))

        if not self.practicadas:
            cp.vacio(padre, "Sin técnicas evaluadas todavía.")
            return

        # La barra es proporcional a la técnica más practicada, no al total: lo
        # que interesa comparar es el peso relativo de cada una en el tatami.
        tope = max(t["evaluaciones"] for t in self.practicadas)
        for tecnica in self.practicadas:
            self._fila_tecnica(padre, tecnica, tope)

    def _fila_tecnica(self, padre, tecnica, tope):
        clave = tecnica["nombre_tecnica"]
        caja = ctk.CTkFrame(padre, fg_color="transparent")
        caja.pack(fill="x", padx=18, pady=(0, 10))

        encabezado = ctk.CTkFrame(caja, fg_color="transparent")
        encabezado.pack(fill="x")
        ctk.CTkLabel(encabezado, text=NOMBRE_TECNICA.get(clave, cp.nombre_legible(clave)),
                     font=(theme.FUENTE, 12), text_color=theme.TEXTO).pack(side="left")
        ctk.CTkLabel(encabezado, text=str(tecnica["evaluaciones"]), font=(theme.FUENTE, 12, "bold"),
                     text_color=theme.TEXTO_MUTED).pack(side="right")

        canal = ctk.CTkFrame(caja, fg_color=theme.BORDE, height=6, corner_radius=3)
        canal.pack(fill="x", pady=(5, 0))
        canal.pack_propagate(False)
        relleno = ctk.CTkFrame(canal, fg_color=cp.color_precision(tecnica["precision"]),
                               height=6, corner_radius=3)
        relleno.place(relx=0, rely=0, relwidth=tecnica["evaluaciones"] / tope, relheight=1)

    # ---------------- navegación ----------------

    def _abrir_vivo(self):
        self.master_app.on_abrir_vivo()

    def _abrir_historial(self):
        self.master_app.on_abrir_historial()
