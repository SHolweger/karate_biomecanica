import customtkinter as ctk

from gui import componentes as cp
from gui import theme
from gui.umbrales_screen import FUENTE_LEGIBLE, NOMBRE_ARTICULACION, NOMBRE_TECNICA

# Qué evalúa el sistema en cada técnica, en lenguaje del dojo. No sale de la
# base de datos porque no es un dato que se recalibre: es la explicación de la
# regla, y cambia solo si cambia el código que la implementa.
DESCRIPCION = {
    "tsuki": ("Golpe recto de puño. Se mide la extensión del codo en el punto de "
              "impacto (Kime): ni flexionado de más, ni hiperextendido, que es lesivo."),
    "age_uke": ("Defensa alta. El codo debe quedar flexionado para que el antebrazo "
                "desvíe el ataque; demasiada extensión deja pasar el golpe."),
    "heiko_dachi": ("Postura natural. Ambas rodillas casi extendidas, con el peso "
                    "repartido y sin flexión marcada."),
    "kiba_dachi": ("Postura de jinete. Simétrica y lateral: ambas rodillas flexionadas "
                   "por igual, sin pierna adelantada."),
    "zenkutsu_dachi": ("Postura adelantada. El peso va al frente: rodilla delantera "
                       "flexionada y trasera extendida y tensa."),
    "kokutsu_dachi": ("Postura atrasada. El peso va atrás: rodilla trasera flexionada "
                      "y delantera casi extendida. Es la distribución inversa al Zenkutsu."),
    "mae_geri": ("Patada frontal. Se evalúa por fases: carga, extensión con velocidad "
                 "(Kime) y recojo de la pierna antes de bajarla (Hikiashi)."),
}

# Técnicas que el motor evalúa pero que no se miden contra un rango angular, de
# modo que no aparecen en la tabla de umbrales. Declararlas evita que la
# biblioteca dé a entender que el sistema hace menos de lo que hace.
SIN_UMBRAL = {
    "hikiashi": ("Recojo de la pierna tras la patada. No se juzga por un ángulo sino "
                 "por orden temporal: la rodilla debe flexionarse ANTES de que el pie "
                 "descienda. Si el pie ya bajó, la pierna cayó en vez de recogerse."),
}


class TecnicasScreen(ctk.CTkFrame):
    """
    Biblioteca de técnicas evaluables (RF-05).

    Muestra qué sabe juzgar el sistema experto y con qué criterio. No es una
    pantalla de edición —para eso está la calibración de umbrales—, sino la
    respuesta a "¿qué evalúa exactamente este sistema?", que es de las primeras
    preguntas que hace un instructor que lo ve por primera vez.

    Los rangos se leen de la base de datos, no del código: si un entrenador
    recalibra un umbral, esta pantalla muestra el criterio nuevo. Por eso también
    señala el origen de cada valor, bibliográfico o de modelado experto.
    """

    def __init__(self, master, db, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación. Desde que existe la barra lateral son objetos
        # distintos: el contenedor es el área de contenido, no la ventana.
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador

        cp.encabezado(
            self, "Biblioteca de técnicas",
            "Lo que el sistema experto sabe evaluar y con qué criterio",
            acciones=[("Calibrar umbrales", self._abrir_umbrales, False)],
        )

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(expand=True, fill="both", padx=28, pady=(0, 20))

        self.recargar()

    # ---------------- datos ----------------

    def recargar(self):
        for w in self.lista.winfo_children():
            w.destroy()

        vigentes = self.db.cargar_umbrales_vigentes()
        if not vigentes:
            cp.vacio(self.lista, "No hay umbrales cargados en la base de datos.")
            return

        # Agrupa los umbrales por técnica conservando el orden de enseñanza.
        por_tecnica = {}
        for (tecnica, articulacion), umbral in vigentes.items():
            por_tecnica.setdefault(tecnica, []).append((articulacion, umbral))

        for tecnica in [t for t in NOMBRE_TECNICA if t in por_tecnica]:
            self._tarjeta_tecnica(tecnica, por_tecnica[tecnica])
        for tecnica in sorted(t for t in por_tecnica if t not in NOMBRE_TECNICA):
            self._tarjeta_tecnica(tecnica, por_tecnica[tecnica])

        for clave, descripcion in SIN_UMBRAL.items():
            self._tarjeta_sin_umbral(clave, descripcion)

    def _tarjeta_tecnica(self, tecnica, articulaciones):
        caja = cp.tarjeta(self.lista, pady=5)

        cabecera = ctk.CTkFrame(caja, fg_color="transparent")
        cabecera.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(cabecera, text=NOMBRE_TECNICA.get(tecnica, cp.nombre_legible(tecnica)),
                     font=(theme.FUENTE, 14, "bold"),
                     text_color=theme.TEXTO).pack(side="left")

        # Una técnica marcada como modelado experto ya fue ajustada por el dojo.
        if any(u["fuente"] == "modelado_experto" for _, u in articulaciones):
            ctk.CTkLabel(cabecera, text="CALIBRADA EN EL DOJO", font=(theme.FUENTE, 10),
                         text_color=theme.ACENTO_VERDE).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(caja, text=DESCRIPCION.get(tecnica, "Técnica evaluada por el sistema."),
                     font=(theme.FUENTE, 11.5), text_color=theme.TEXTO_MUTED,
                     wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(0, 10))

        for articulacion, umbral in sorted(articulaciones):
            fila = ctk.CTkFrame(caja, fg_color="transparent")
            fila.pack(fill="x", padx=18, pady=(0, 6))
            ctk.CTkLabel(fila, text=NOMBRE_ARTICULACION.get(articulacion,
                                                            cp.nombre_legible(articulacion)),
                         width=180, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO).pack(side="left")
            ctk.CTkLabel(fila, text=self._rango(umbral), width=170, anchor="w",
                         font=(theme.FUENTE_MONO, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left")
            ctk.CTkLabel(fila, text=FUENTE_LEGIBLE.get(umbral["fuente"], umbral["fuente"]),
                         anchor="w", font=(theme.FUENTE, 11),
                         text_color=theme.TEXTO_TENUE).pack(side="left")

        ctk.CTkFrame(caja, fg_color="transparent", height=6).pack()

    def _tarjeta_sin_umbral(self, clave, descripcion):
        caja = cp.tarjeta(self.lista, pady=5)
        ctk.CTkLabel(caja, text=cp.nombre_legible(clave), font=(theme.FUENTE, 14, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(caja, text=descripcion, font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED, wraplength=820,
                     justify="left").pack(anchor="w", padx=18, pady=(0, 6))
        ctk.CTkLabel(caja, text="Sin umbral angular · criterio de orden temporal",
                     font=(theme.FUENTE, 11), text_color=theme.TEXTO_TENUE).pack(
            anchor="w", padx=18, pady=(0, 14))

    @staticmethod
    def _rango(umbral):
        unidad = "°" if umbral["unidad"] == "grados" else f" {umbral['unidad']}"
        if umbral["valor_max"] is None:
            return f"≥ {umbral['valor_min']:g}{unidad}"
        return f"{umbral['valor_min']:g}{unidad} – {umbral['valor_max']:g}{unidad}"

    # ---------------- navegación ----------------

    def _abrir_umbrales(self):
        self.master_app.on_abrir_umbrales()

    def _volver(self):
        self.master_app.on_volver_a_perfiles()
