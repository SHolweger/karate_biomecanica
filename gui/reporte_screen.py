import customtkinter as ctk

from gui import componentes as cp
from gui import theme


class ReporteScreen(ctk.CTkFrame):
    """
    Reporte de una sesión de entrenamiento (RF-07).

    Convierte las mediciones crudas de una sesión en algo que un instructor
    pueda usar al terminar la clase: qué porcentaje salió correcto, en qué
    técnicas, y —lo que realmente sirve— cuáles fueron los errores que más se
    repitieron.

    Ese último bloque es la diferencia entre un número y una corrección. Saber
    que el alumno acertó el 62 % no dice qué practicar mañana; saber que falló
    catorce veces por hiperextender el codo en el Tsuki, sí.

    El sistema no inventa recomendaciones: cada una nace de un diagnóstico que
    el motor de inferencia efectivamente emitió y que quedó registrado en la
    base de datos.
    """

    def __init__(self, master, db, id_sesion, entrenador=None):
        super().__init__(master, fg_color=theme.FONDO)
        self.master_app = master
        self.db = db
        self.id_sesion = id_sesion
        self.entrenador = entrenador

        self.sesion = db.detalle_sesion(id_sesion)
        titulo = "Reporte de sesión"
        subtitulo = "Sesión no encontrada"
        if self.sesion:
            subtitulo = (f"{self.sesion['atleta']} · {self.sesion['fecha']} · "
                         f"evaluado por {self.sesion['entrenador'] or '—'}")

        cp.encabezado(self, titulo, subtitulo,
                      acciones=[("Volver", self._volver, False)])

        self.cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cuerpo.pack(expand=True, fill="both", padx=28, pady=(0, 20))

        self._render()

    # ---------------- secciones ----------------

    def _render(self):
        if self.sesion is None:
            cp.vacio(self.cuerpo, "No se encontró la sesión solicitada.")
            return

        self._resumen()
        self._por_tecnica()
        self._errores()

    def _resumen(self):
        caja = cp.tarjeta(self.cuerpo, pady=(0, 14))
        fila = ctk.CTkFrame(caja, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=16)

        precision = self.sesion["precision"]
        abierta = self.sesion["hora_fin"] is None
        for etiqueta, valor, color in [
            ("Precisión de la sesión", cp.texto_precision(precision),
             cp.color_precision(precision)),
            ("Técnicas correctas", f"{self.sesion['aciertos']} de {self.sesion['evaluaciones']}",
             None),
            ("Inicio", cp.fecha_legible(self.sesion["hora_inicio"])[11:] or "—", None),
            ("Estado", "En curso" if abierta else "Cerrada",
             theme.ACENTO_AMARILLO if abierta else None),
        ]:
            cp.metrica(fila, etiqueta, valor, color).pack(side="left", padx=(0, 44))

    def _por_tecnica(self):
        ctk.CTkLabel(self.cuerpo, text="Puntos de control biomecánicos",
                     font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", pady=(6, 8))

        tecnicas = self.db.resumen_por_tecnica(self.sesion["id_atleta"],
                                               id_sesion=self.id_sesion)
        if not tecnicas:
            cp.vacio(self.cuerpo, "Esta sesión no dejó evaluaciones cerradas.",
                     "Puede haber terminado antes de que el atleta completara una técnica, "
                     "o el sistema no logró ver las articulaciones necesarias.")
            return

        for tecnica in tecnicas:
            caja = cp.tarjeta(self.cuerpo)
            ctk.CTkLabel(caja, text=cp.nombre_legible(tecnica["nombre_tecnica"]),
                         width=230, anchor="w", font=(theme.FUENTE, 12.5),
                         text_color=theme.TEXTO).pack(side="left", padx=4, pady=9)

            precision = tecnica["precision"]
            ctk.CTkLabel(caja, text=cp.texto_precision(precision), width=60, anchor="w",
                         font=(theme.FUENTE, 12.5, "bold"),
                         text_color=cp.color_precision(precision)).pack(side="left", padx=4)
            cp.barra_progreso(caja, precision, ancho=200).pack(side="left", padx=4)
            ctk.CTkLabel(caja, text=f"{tecnica['aciertos']} de {tecnica['evaluaciones']} correctas",
                         anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left", padx=(14, 4))

    def _errores(self):
        ctk.CTkLabel(self.cuerpo, text="Correcciones sugeridas",
                     font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", pady=(20, 2))
        ctk.CTkLabel(self.cuerpo,
                     text="Los errores que más se repitieron, en orden de frecuencia",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 8))

        errores = self.db.errores_frecuentes(self.id_sesion)
        if not errores:
            cp.vacio(self.cuerpo, "Sin errores registrados en esta sesión.",
                     "O bien todas las ejecuciones fueron correctas, o la sesión no llegó "
                     "a producir evaluaciones cerradas.")
            return

        for error in errores:
            caja = cp.tarjeta(self.cuerpo)
            ctk.CTkLabel(caja, text=f"{error['veces']}×", width=46, anchor="w",
                         font=(theme.FUENTE_MONO, 13, "bold"),
                         text_color=theme.ACENTO_ROJO).pack(side="left", padx=(14, 4), pady=10)

            textos = ctk.CTkFrame(caja, fg_color="transparent")
            textos.pack(side="left", anchor="w", padx=4)
            ctk.CTkLabel(textos, text=error["diagnostico"], anchor="w",
                         font=(theme.FUENTE, 12.5),
                         text_color=theme.TEXTO).pack(anchor="w")

            detalle = cp.nombre_legible(error["nombre_tecnica"])
            if error["angulo_medio"] is not None:
                detalle += f"  ·  ángulo medio registrado: {error['angulo_medio']:.0f}°"
            ctk.CTkLabel(textos, text=detalle, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(anchor="w")

    # ---------------- navegación ----------------

    def _volver(self):
        """Regresa al perfil del alumno, o al listado si la sesión no existe."""
        if self.sesion is None:
            self.master_app.on_abrir_historial()
        else:
            self.master_app.on_abrir_alumno(self.sesion["id_atleta"])
