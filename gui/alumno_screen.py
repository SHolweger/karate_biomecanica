import customtkinter as ctk

from gui import componentes as cp
from gui import theme
from persistence.reportes import generar_reporte_progreso


class AlumnoScreen(ctk.CTkFrame):
    """
    Perfil de un alumno (RF-07).

    Reúne las tres preguntas que un instructor se hace sobre un atleta concreto:
    cómo viene en conjunto, qué técnicas domina y cuáles no, y qué pasó en cada
    sesión. Desde aquí también se genera la gráfica de progreso, que hasta ahora
    existía como módulo pero no era alcanzable desde la aplicación.

    La lista de técnicas se ordena de la más floja a la más sólida a propósito:
    lo primero que se lee debe ser lo que hay que corregir, no lo que ya salió
    bien.
    """

    SESIONES_EN_GRAFICA = 8
    ALTO_GRAFICA = 150

    def __init__(self, master, db, id_atleta, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación. Desde que existe la barra lateral son objetos
        # distintos: el contenedor es el área de contenido, no la ventana.
        self.master_app = app if app is not None else master
        self.db = db
        self.id_atleta = id_atleta
        self.entrenador = entrenador
        self.estado_var = ctk.StringVar(value="")

        self.atleta = next((a for a in db.resumen_atletas()
                            if a["id_atleta"] == id_atleta), None)
        nombre = self.atleta["nombre"] if self.atleta else "Alumno"
        grado = (self.atleta or {}).get("grado_cinturon") or "sin grado registrado"

        cp.encabezado(
            self, nombre, f"{grado} · historial de entrenamiento",
            acciones=[("Volver", self._volver, False),
                      ("Generar reporte", self.generar_reporte, True)],
        )

        self.cuerpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cuerpo.pack(expand=True, fill="both", padx=28, pady=(0, 4))

        ctk.CTkLabel(self, textvariable=self.estado_var, font=(theme.FUENTE, 11.5),
                     text_color=theme.ACENTO_VERDE, wraplength=900,
                     justify="left").pack(anchor="w", padx=28, pady=(0, 16))

        self.recargar()

    # ---------------- secciones ----------------

    def recargar(self):
        for w in self.cuerpo.winfo_children():
            w.destroy()

        if self.atleta is None:
            cp.vacio(self.cuerpo, "No se encontró el alumno.")
            return

        self._resumen()
        self._evolucion()
        self._tecnicas()
        self._sesiones()

    def _evolucion(self):
        """
        Precisión de las últimas sesiones, en orden cronológico.

        Es la pregunta que ni el promedio global ni el desglose por técnica
        responden: ¿está mejorando? Un alumno con 70 % de precisión que viene de
        55 % y uno que viene de 85 % tienen el mismo número y situaciones
        opuestas, y es la segunda la que obliga al instructor a intervenir.

        Se dibuja con barras propias en vez de matplotlib: la gráfica de
        `persistence/reportes.py` sigue existiendo para el expediente en PNG,
        pero incrustar una imagen aquí obligaría a regenerarla en cada recarga y
        desentonaría con el resto de la interfaz.
        """
        # De la más antigua a la más reciente: una evolución se lee hacia la
        # derecha. `listar_sesiones` las devuelve al revés, para la tabla.
        sesiones = [s for s in reversed(self.db.listar_sesiones(self.id_atleta))
                    if s["precision"] is not None][-self.SESIONES_EN_GRAFICA:]

        ctk.CTkLabel(self.cuerpo, text="Precisión por sesión",
                     font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", pady=(6, 2))

        if len(sesiones) < 2:
            cp.vacio(self.cuerpo, "Aún no hay suficientes sesiones para ver una evolución.",
                     "Hacen falta al menos dos sesiones con evaluaciones cerradas.")
            return

        ctk.CTkLabel(self.cuerpo,
                     text=f"Últimas {len(sesiones)} sesiones, de la más antigua a la más reciente",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 8))

        caja = cp.tarjeta(self.cuerpo, pady=(0, 14))
        grafica = ctk.CTkFrame(caja, fg_color="transparent", height=self.ALTO_GRAFICA + 52)
        grafica.pack(fill="x", padx=20, pady=16)
        grafica.pack_propagate(False)

        for posicion, sesion in enumerate(sesiones):
            self._columna(grafica, sesion, ultima=posicion == len(sesiones) - 1)

    def _columna(self, padre, sesion, ultima):
        columna = ctk.CTkFrame(padre, fg_color="transparent")
        columna.pack(side="left", expand=True, fill="both", padx=5)

        precision = sesion["precision"]
        ctk.CTkLabel(columna, text=cp.texto_precision(precision), font=(theme.FUENTE, 10.5),
                     text_color=theme.TEXTO_MUTED).pack()

        # La barra se mide contra el 100 % y no contra el máximo del alumno: la
        # escala tiene que ser la misma entre alumnos para poder compararlos, y
        # un eje que se reajusta solo haría que un 40 % se viera alto.
        canal = ctk.CTkFrame(columna, fg_color="transparent", height=self.ALTO_GRAFICA)
        canal.pack(fill="x")
        canal.pack_propagate(False)
        relleno = ctk.CTkFrame(canal, fg_color=cp.color_precision(precision), corner_radius=4)
        relleno.place(relx=0, rely=1.0, anchor="sw", relwidth=1,
                      relheight=max(precision, 1) / 100)
        if not ultima:
            # La sesión más reciente va a color pleno; las anteriores, atenuadas,
            # para que el ojo caiga primero en dónde está hoy el alumno.
            relleno.configure(fg_color=theme.BORDE_CLARO)

        ctk.CTkLabel(columna, text=(sesion["fecha"] or "")[5:], font=(theme.FUENTE, 9.5),
                     text_color=theme.TEXTO_TENUE).pack(pady=(6, 0))

    def _resumen(self):
        caja = cp.tarjeta(self.cuerpo, pady=(0, 14))
        fila = ctk.CTkFrame(caja, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=16)

        precision = self.atleta["precision"]
        for etiqueta, valor, color in [
            ("Precisión global", cp.texto_precision(precision), cp.color_precision(precision)),
            ("Sesiones", str(self.atleta["sesiones"]), None),
            ("Técnicas evaluadas", str(self.atleta["evaluaciones"]), None),
            ("Última sesión", self.atleta["ultima_fecha"] or "—", None),
        ]:
            cp.metrica(fila, etiqueta, valor, color).pack(side="left", padx=(0, 46))

    def _tecnicas(self):
        ctk.CTkLabel(self.cuerpo, text="Dominio por técnica",
                     font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", pady=(6, 2))
        ctk.CTkLabel(self.cuerpo, text="De la que más se le dificulta a la que mejor ejecuta",
                     font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(anchor="w", pady=(0, 8))

        tecnicas = self.db.resumen_por_tecnica(self.id_atleta)
        if not tecnicas:
            cp.vacio(self.cuerpo, "Todavía no hay técnicas evaluadas.",
                     "Las evaluaciones se registran automáticamente durante el análisis en vivo.")
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

            detalle = f"{tecnica['aciertos']} de {tecnica['evaluaciones']} correctas"
            if tecnica["angulo_medio"] is not None:
                detalle += f"  ·  ángulo medio {tecnica['angulo_medio']:.0f}°"
            ctk.CTkLabel(caja, text=detalle, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left", padx=(14, 4))

    def _sesiones(self):
        ctk.CTkLabel(self.cuerpo, text="Sesiones registradas",
                     font=(theme.FUENTE, 15, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w", pady=(20, 8))

        sesiones = self.db.listar_sesiones(self.id_atleta)
        if not sesiones:
            cp.vacio(self.cuerpo, "Este alumno todavía no tiene sesiones.",
                     "Se crean al abrir el análisis en vivo con su perfil.")
            return

        for sesion in sesiones:
            caja = cp.tarjeta(self.cuerpo)
            ctk.CTkLabel(caja, text=sesion["fecha"], width=110, anchor="w",
                         font=(theme.FUENTE, 12.5, "bold"),
                         text_color=theme.TEXTO).pack(side="left", padx=4, pady=9)
            ctk.CTkLabel(caja, text=cp.fecha_legible(sesion["hora_inicio"])[11:] or "—",
                         width=60, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)

            abierta = sesion["hora_fin"] is None
            ctk.CTkLabel(caja, text="en curso" if abierta else "cerrada", width=80, anchor="w",
                         font=(theme.FUENTE, 11.5),
                         text_color=theme.ACENTO_AMARILLO if abierta else theme.TEXTO_TENUE
                         ).pack(side="left", padx=4)

            ctk.CTkLabel(caja, text=sesion["entrenador"] or "—", width=150, anchor="w",
                         font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)
            ctk.CTkLabel(caja, text=f"{sesion['evaluaciones']} evaluaciones", width=130,
                         anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)

            precision = sesion["precision"]
            ctk.CTkLabel(caja, text=cp.texto_precision(precision), width=60, anchor="w",
                         font=(theme.FUENTE, 12.5, "bold"),
                         text_color=cp.color_precision(precision)).pack(side="left", padx=4)

            ctk.CTkButton(caja, text="Ver reporte", width=110, fg_color="transparent",
                          text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                          font=(theme.FUENTE, 11.5),
                          command=lambda s=sesion: self._abrir_reporte(s["id_sesion"])
                          ).pack(side="left", padx=4)

    # ---------------- acciones ----------------

    def generar_reporte(self):
        """
        Produce la gráfica de progreso del atleta y devuelve la ruta del archivo.

        Es la única vía por la que `reportes.py` es alcanzable desde la
        aplicación: hasta ahora el módulo funcionaba y estaba probado, pero
        ningún usuario podía invocarlo.
        """
        ruta = generar_reporte_progreso(self.db, self.id_atleta, self.atleta["nombre"])
        if ruta is None:
            self.estado_var.set(
                "Todavía no hay evaluaciones cerradas para graficar. "
                "Registra al menos una sesión de análisis con este alumno.")
        else:
            self.estado_var.set(f"Reporte de progreso generado: {ruta}")
        return ruta

    def _abrir_reporte(self, id_sesion):
        self.master_app.on_abrir_reporte(id_sesion)

    def _volver(self):
        self.master_app.on_abrir_historial()
