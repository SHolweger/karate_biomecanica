import customtkinter as ctk

from gui import theme
from gui.validacion_umbrales import ValorInvalido, formatear_valor, interpretar_rango


# Nombres legibles. La base de datos guarda la clave técnica en minúsculas
# (así la consultan las reglas); el entrenador ve el nombre del dojo.
NOMBRE_TECNICA = {
    "tsuki": "Tsuki — golpe recto",
    "age_uke": "Age Uke — defensa alta",
    "heiko_dachi": "Heiko Dachi — postura natural",
    "kiba_dachi": "Kiba Dachi — postura de jinete",
    "zenkutsu_dachi": "Zenkutsu Dachi — postura adelantada",
    "kokutsu_dachi": "Kokutsu Dachi — postura atrasada",
    "mae_geri": "Mae Geri — patada frontal",
}

NOMBRE_ARTICULACION = {
    "codo": "Codo",
    "rodilla": "Rodilla",
    "rodilla_frontal": "Rodilla frontal",
    "rodilla_trasera": "Rodilla trasera",
    "rodilla_kime": "Rodilla en Kime",
    "velocidad_angular": "Velocidad angular",
}

FUENTE_LEGIBLE = {
    "literatura": "Literatura",
    "modelado_experto": "Modelado experto",
}

# Orden de presentación: golpes, defensas, posturas y patadas, que es como se
# enseñan. Sin esto el orden lo decidiría SQLite (el id de inserción), y al
# recalibrar un umbral su fila saltaría al final de la lista.
ORDEN = [
    ("tsuki", "codo"),
    ("age_uke", "codo"),
    ("heiko_dachi", "rodilla"),
    ("kiba_dachi", "rodilla"),
    ("zenkutsu_dachi", "rodilla_frontal"),
    ("zenkutsu_dachi", "rodilla_trasera"),
    ("kokutsu_dachi", "rodilla_frontal"),
    ("kokutsu_dachi", "rodilla_trasera"),
    ("mae_geri", "rodilla_kime"),
    ("mae_geri", "velocidad_angular"),
]


def etiqueta_umbral(tecnica, articulacion):
    """Nombre mostrado de un umbral, con respaldo si la clave no está mapeada."""
    return (f"{NOMBRE_TECNICA.get(tecnica, tecnica.replace('_', ' ').title())} · "
            f"{NOMBRE_ARTICULACION.get(articulacion, articulacion.replace('_', ' '))}")


class UmbralesScreen(ctk.CTkFrame):
    """
    Pantalla de calibración de los umbrales biomecánicos (RF-08).

    Cierra el requisito por el lado de la interfaz: la tabla `umbral_referencia`
    y el versionado ya existían, pero solo eran alcanzables desde Python. Aquí
    el entrenador los edita sin tocar el código fuente, que es exactamente lo
    que el Capítulo 3 promete cuando dice que el sistema migra de umbrales
    bibliográficos a umbrales de modelado experto.

    Tres decisiones que no son de presentación:

    1. **Restricción de acceso.** Solo se llega desde una sesión de entrenador
       autenticada, y cada versión guardada anota quién la firmó
       (`id_entrenador`). Sin entrenador la pantalla se abre en solo lectura.
    2. **Guardado todo-o-nada.** Si algún campo está mal, no se escribe
       ninguno. Un guardado parcial dejaría la mitad del criterio recalibrado
       y la otra mitad no, sin que nadie pueda saber cuál mitad.
    3. **Solo se escribe lo que cambió.** Cada guardado crea una versión nueva
       en la base de datos; reescribir los diez umbrales cada vez llenaría el
       historial de versiones idénticas y lo volvería inútil.

    Los cambios entran en vigor en la siguiente sesión de análisis: `LiveScreen`
    construye su `KarateRules` a partir de `cargar_umbrales_vigentes()` al
    abrirse. Recalibrar en medio de una medición cambiaría el criterio a mitad
    de la evaluación, que es justo lo que el versionado busca evitar.
    """

    def __init__(self, master, db, entrenador=None, app=None):
        super().__init__(master, fg_color=theme.FONDO)
        # `master` es el contenedor donde se dibuja esta pantalla; `app` es quien
        # resuelve la navegación. Desde que existe la barra lateral son objetos
        # distintos: el contenedor es el área de contenido, no la ventana.
        self.master_app = app if app is not None else master
        self.db = db
        self.entrenador = entrenador
        self.puede_editar = entrenador is not None

        self.campos = {}          # (tecnica, articulacion) -> {"min": StringVar, "max": StringVar}
        self.vigentes = {}        # (tecnica, articulacion) -> fila de umbral_referencia
        self.error_var = ctk.StringVar(value="")
        self.estado_var = ctk.StringVar(value="")
        self.ventana_historial = None

        self._construir_encabezado()

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(expand=True, fill="both", padx=28, pady=(0, 6))

        self._construir_pie()
        self._recargar()

    # ---------------- armado de la pantalla ----------------

    def _construir_encabezado(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=28, pady=(20, 4))

        titulos = ctk.CTkFrame(barra, fg_color="transparent")
        titulos.pack(side="left", anchor="w")
        ctk.CTkLabel(titulos, text="Calibración de umbrales", font=(theme.FUENTE, 20, "bold"),
                     text_color=theme.TEXTO).pack(anchor="w")
        ctk.CTkLabel(titulos, text="Criterios biomecánicos con los que el sistema evalúa cada técnica",
                     font=(theme.FUENTE, 12), text_color=theme.TEXTO_MUTED).pack(anchor="w")

        ctk.CTkButton(barra, text="Volver", fg_color="transparent", border_width=1,
                      border_color=theme.BORDE_CLARO, text_color=theme.TEXTO,
                      hover_color=theme.CARD_HOVER, width=110,
                      command=self._volver).pack(side="right")

        aviso = ("Recalibrar no borra el criterio anterior: se guarda una versión nueva y las "
                 "mediciones ya registradas conservan el umbral con el que fueron evaluadas.")
        if not self.puede_editar:
            aviso = "Solo lectura: se requiere una sesión de entrenador para recalibrar (RF-08)."
        ctk.CTkLabel(self, text=aviso, font=(theme.FUENTE, 11.5), justify="left",
                     text_color=theme.TEXTO_TENUE, wraplength=900).pack(padx=28, pady=(6, 12), anchor="w")

    def _construir_pie(self):
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.pack(fill="x", padx=28, pady=(0, 18))

        ctk.CTkLabel(pie, textvariable=self.error_var, text_color=theme.ACENTO_ROJO,
                     font=(theme.FUENTE, 11.5), justify="left", wraplength=600).pack(side="left")
        ctk.CTkLabel(pie, textvariable=self.estado_var, text_color=theme.ACENTO_VERDE,
                     font=(theme.FUENTE, 11.5)).pack(side="left", padx=(10, 0))

        if self.puede_editar:
            ctk.CTkButton(pie, text="Guardar cambios", fg_color=theme.ACENTO_ROJO,
                          hover_color=theme.ACENTO_ROJO_HOVER, width=170,
                          command=self._guardar_cambios).pack(side="right")
            ctk.CTkButton(pie, text="Descartar", fg_color="transparent", width=110,
                          text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                          command=self._recargar).pack(side="right", padx=(0, 8))

    def _encabezado_tabla(self):
        fila = ctk.CTkFrame(self.lista, fg_color="transparent")
        fila.pack(fill="x", pady=(0, 4))
        columnas = [("Técnica y articulación", 340), ("Mínimo", 90), ("Máximo", 90),
                    ("Unidad", 120), ("Fuente vigente", 150), ("", 90)]
        for texto, ancho in columnas:
            ctk.CTkLabel(fila, text=texto, width=ancho, anchor="w", font=(theme.FUENTE, 11, "bold"),
                         text_color=theme.TEXTO_TENUE).pack(side="left", padx=4)

    def _fila_umbral(self, clave, umbral):
        tecnica, articulacion = clave
        fila = ctk.CTkFrame(self.lista, fg_color=theme.CARD, border_color=theme.BORDE,
                            border_width=1, corner_radius=10)
        fila.pack(fill="x", pady=3)

        ctk.CTkLabel(fila, text=etiqueta_umbral(tecnica, articulacion), width=340, anchor="w",
                     font=(theme.FUENTE, 12.5), text_color=theme.TEXTO).pack(side="left", padx=4, pady=8)

        var_min = ctk.StringVar(value=formatear_valor(umbral["valor_min"]))
        var_max = ctk.StringVar(value=formatear_valor(umbral["valor_max"]))
        self.campos[clave] = {"min": var_min, "max": var_max}

        estado = "normal" if self.puede_editar else "disabled"
        ctk.CTkEntry(fila, textvariable=var_min, width=90, state=estado).pack(side="left", padx=4)
        ctk.CTkEntry(fila, textvariable=var_max, width=90, state=estado).pack(side="left", padx=4)

        ctk.CTkLabel(fila, text=umbral["unidad"], width=120, anchor="w", font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_MUTED).pack(side="left", padx=4)

        fuente = FUENTE_LEGIBLE.get(umbral["fuente"], umbral["fuente"])
        color = theme.ACENTO_VERDE if umbral["fuente"] == "modelado_experto" else theme.TEXTO_MUTED
        ctk.CTkLabel(fila, text=fuente, width=150, anchor="w", font=(theme.FUENTE, 11.5),
                     text_color=color).pack(side="left", padx=4)

        ctk.CTkButton(fila, text="Historial", width=90, fg_color="transparent",
                      text_color=theme.TEXTO_MUTED, hover_color=theme.CARD_HOVER,
                      font=(theme.FUENTE, 11.5),
                      command=lambda c=clave: self._abrir_historial(c)).pack(side="left", padx=4)

    # ---------------- datos ----------------

    def _recargar(self):
        """
        Relee los umbrales vigentes y redibuja la lista.

        Se usa tanto al abrir la pantalla como después de guardar y al
        descartar: en los tres casos lo que debe verse es el estado real de la
        base de datos, no lo que quedó escrito en los campos.
        """
        for w in self.lista.winfo_children():
            w.destroy()
        self.campos.clear()

        self.vigentes = self.db.cargar_umbrales_vigentes()
        if not self.vigentes:
            ctk.CTkLabel(self.lista, text="No hay umbrales cargados en la base de datos.",
                         font=(theme.FUENTE, 12.5), text_color=theme.TEXTO_MUTED).pack(pady=30)
            return

        self._encabezado_tabla()
        for clave in self._claves_ordenadas():
            self._fila_umbral(clave, self.vigentes[clave])

    def _claves_ordenadas(self):
        """Las conocidas en el orden de enseñanza; las demás detrás, alfabéticas."""
        conocidas = [c for c in ORDEN if c in self.vigentes]
        resto = sorted(c for c in self.vigentes if c not in ORDEN)
        return conocidas + resto

    def _leer_formulario(self):
        """
        Interpreta todos los campos y devuelve (cambios, problemas).

        `cambios` trae solo los umbrales cuyo valor difiere del vigente, ya
        convertidos a número. `problemas` trae un mensaje por cada campo mal
        escrito, con el nombre de la técnica al frente para que el entrenador
        sepa cuál fila corregir.
        """
        cambios, problemas = [], []

        for clave, entradas in self.campos.items():
            tecnica, articulacion = clave
            umbral = self.vigentes[clave]
            try:
                valor_min, valor_max = interpretar_rango(
                    entradas["min"].get(), entradas["max"].get(), umbral["unidad"])
            except ValorInvalido as error:
                problemas.append(f"{etiqueta_umbral(tecnica, articulacion)}: {error}")
                continue

            if (valor_min, valor_max) != (umbral["valor_min"], umbral["valor_max"]):
                cambios.append((tecnica, articulacion, valor_min, valor_max))

        return cambios, problemas

    def _guardar_cambios(self):
        """
        Escribe las recalibraciones y devuelve cuántas se aplicaron.

        Devolver el número no es para la interfaz —el usuario ve el mensaje de
        estado— sino para que las pruebas puedan afirmar sobre el efecto real
        del botón sin leer texto de pantalla.
        """
        if not self.puede_editar:
            self.error_var.set("Se requiere una sesión de entrenador para recalibrar.")
            return 0

        cambios, problemas = self._leer_formulario()

        if problemas:
            self.estado_var.set("")
            self.error_var.set(" · ".join(problemas))
            return 0

        if not cambios:
            self.error_var.set("")
            self.estado_var.set("No hay cambios que guardar.")
            return 0

        for tecnica, articulacion, valor_min, valor_max in cambios:
            self.db.actualizar_umbral(tecnica, articulacion, valor_min, valor_max,
                                      id_entrenador=self.entrenador["id_entrenador"],
                                      fuente="modelado_experto")

        self.error_var.set("")
        self.estado_var.set(
            f"{len(cambios)} umbral(es) recalibrado(s). Se aplican en la próxima sesión de análisis.")
        self._recargar()
        return len(cambios)

    # ---------------- historial ----------------

    def _abrir_historial(self, clave):
        """Versiones de un umbral, de la más reciente a la más antigua (solo lectura)."""
        if self.ventana_historial is not None:
            return

        tecnica, articulacion = clave
        self.ventana_historial = ctk.CTkToplevel(self)
        self.ventana_historial.title("Historial del umbral")
        self.ventana_historial.geometry("520x360")
        self.ventana_historial.configure(fg_color=theme.CARD)
        self.ventana_historial.protocol("WM_DELETE_WINDOW", self._cerrar_historial)

        ctk.CTkLabel(self.ventana_historial, text=etiqueta_umbral(tecnica, articulacion),
                     font=(theme.FUENTE, 15, "bold"), text_color=theme.TEXTO,
                     wraplength=460, justify="left").pack(padx=20, pady=(18, 10), anchor="w")

        contenedor = ctk.CTkScrollableFrame(self.ventana_historial, fg_color="transparent")
        contenedor.pack(expand=True, fill="both", padx=20, pady=(0, 18))

        for version in self.db.historial_umbral(tecnica, articulacion):
            marca = "vigente" if version["vigente"] else "reemplazado"
            color = theme.ACENTO_VERDE if version["vigente"] else theme.TEXTO_TENUE
            rango = f"{formatear_valor(version['valor_min'])} – {formatear_valor(version['valor_max'])}"
            fecha = str(version["fecha_modificacion"])[:16].replace("T", " ")
            fuente = FUENTE_LEGIBLE.get(version["fuente"], version["fuente"])

            linea = ctk.CTkFrame(contenedor, fg_color="transparent")
            linea.pack(fill="x", pady=3)
            ctk.CTkLabel(linea, text=f"v{version['id_umbral']}", width=50, anchor="w",
                         font=(theme.FUENTE_MONO, 11.5), text_color=theme.TEXTO_MUTED).pack(side="left")
            ctk.CTkLabel(linea, text=rango, width=120, anchor="w", font=(theme.FUENTE, 12),
                         text_color=theme.TEXTO).pack(side="left")
            ctk.CTkLabel(linea, text=fuente, width=130, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left")
            ctk.CTkLabel(linea, text=fecha, width=110, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=theme.TEXTO_MUTED).pack(side="left")
            ctk.CTkLabel(linea, text=marca, anchor="w", font=(theme.FUENTE, 11.5),
                         text_color=color).pack(side="left")

    def _cerrar_historial(self):
        if self.ventana_historial is not None:
            self.ventana_historial.destroy()
            self.ventana_historial = None

    # ---------------- navegación ----------------

    def _volver(self):
        self._cerrar_historial()
        self.master_app.on_volver_a_perfiles()
