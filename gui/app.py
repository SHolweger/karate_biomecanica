import os
import sys

# Permite ejecutar este archivo directamente (python gui/app.py) sin importar
# desde qué carpeta se invoque: al correr un script, Python solo agrega SU
# PROPIA carpeta (gui/) a las rutas de búsqueda, no la raíz del proyecto —
# por eso "from persistence.database import Database" fallaba. Esta línea
# agrega la raíz del proyecto explícitamente, antes de los demás imports.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk

from persistence.database import Database
from expert_system.knowledge_base import CORRECCIONES_LITERATURA, UMBRALES_LITERATURA
from gui import theme
from gui.barra_lateral import BarraLateral
from gui.login_screen import LoginScreen
from gui.perfil_screen import PerfilScreen
from gui.inicio_screen import InicioScreen
from gui.live_screen import LiveScreen
from gui.umbrales_screen import UmbralesScreen
from gui.camara_screen import CamaraScreen
from gui.historial_screen import HistorialScreen
from gui.alumno_screen import AlumnoScreen
from gui.reporte_screen import ReporteScreen
from gui.tecnicas_screen import TecnicasScreen


class App(ctk.CTk):
    """
    Orquesta la navegación del sistema.

    La ventana se divide en dos: una barra lateral permanente con las secciones
    y un área de contenido que cambia. Antes cada pantalla ocupaba la ventana
    entera y las opciones colgaban de la selección de perfiles, de modo que para
    consultar el progreso de un alumno había que pasar por "¿quién entrena hoy?"
    — mezclando elegir a quién medir con administrar el sistema.

    Dos excepciones deliberadas al marco: el acceso, porque antes de
    autenticarse no hay nada que navegar; y el análisis en vivo, que ocupa la
    ventana completa para dar al video todo el espacio disponible y evitar que
    alguien cambie de sección con una sesión de medición abierta.

    No reemplaza a `python main.py --consola` — es la misma cadena de análisis
    (Camera/PoseTracker/SkeletonRenderer/TechniqueAnalyzer) con otra
    presentación.
    """

    def __init__(self, db=None):
        super().__init__()
        self.title("Shotokan AI — Sistema Experto de Biomecánica")
        self.geometry("1000x680")
        self.configure(fg_color=theme.FONDO)
        ctk.set_appearance_mode("dark")

        self.db = db if db is not None else Database()
        # Siembra idempotente de los umbrales biomecanicos (RF-08): si el
        # entrenador ya recalibro alguno, su version vigente no se toca.
        self.db.sembrar_umbrales(UMBRALES_LITERATURA)
        # Corrige valores bibliográficos equivocados en bases ya sembradas, sin
        # tocar los que un entrenador haya recalibrado con su propio criterio.
        self.db.corregir_umbrales_de_literatura(CORRECCIONES_LITERATURA)
        self.entrenador = None
        self.atleta = None
        self.pantalla_actual = None
        self.barra = None
        self.contenido = None

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        self._mostrar(LoginScreen(self, self.db))

    # ---------------- marco de la ventana ----------------

    def _montar_marco(self, seccion):
        """
        Crea la barra lateral y el área de contenido si todavía no existen, y
        marca la sección activa. Reutilizar la barra en vez de reconstruirla en
        cada navegación es lo que evita el parpadeo al cambiar de sección.
        """
        if self.barra is None:
            self.barra = BarraLateral(self, self._navegar, self.entrenador, seccion)
            self.barra.pack(side="left", fill="y")
            self.contenido = ctk.CTkFrame(self, fg_color=theme.FONDO, corner_radius=0)
            self.contenido.pack(side="left", expand=True, fill="both")
        else:
            self.barra.marcar(seccion)

    def _desmontar_marco(self):
        """Devuelve la ventana a pantalla completa (acceso y análisis en vivo)."""
        if self.barra is not None:
            self.barra.destroy()
            self.contenido.destroy()
            self.barra = None
            self.contenido = None

    def _mostrar(self, pantalla):
        """Pantalla a ventana completa, sin barra lateral."""
        self._limpiar_pantalla()
        self._desmontar_marco()
        self.pantalla_actual = pantalla
        self.pantalla_actual.pack(expand=True, fill="both")

    def _mostrar_en_marco(self, constructor, seccion):
        """
        Pantalla dentro del marco con barra lateral.

        Recibe un constructor y no una pantalla ya creada porque el área de
        contenido debe existir antes de instanciarla: es su contenedor padre.
        """
        self._limpiar_pantalla()
        self._montar_marco(seccion)
        self.pantalla_actual = constructor(self.contenido)
        self.pantalla_actual.pack(expand=True, fill="both")

    def _limpiar_pantalla(self):
        """
        Retira la pantalla vigente.

        Si es el análisis en vivo hay que cerrarla antes de destruirla: destruir
        el widget no libera la cámara ni sella la hora de fin de la sesión, y esa
        sesión quedaría abierta para siempre en la base — contaminando los
        promedios de todo lo que venga después.
        """
        if self.pantalla_actual is not None:
            if isinstance(self.pantalla_actual, LiveScreen):
                self.pantalla_actual.cerrar()
            self.pantalla_actual.pack_forget()
            self.pantalla_actual.destroy()
            self.pantalla_actual = None

    def _navegar(self, seccion):
        """Traduce la sección elegida en la barra a la pantalla que corresponde."""
        destinos = {
            "inicio": self.on_abrir_inicio,
            "vivo": self.on_abrir_vivo,
            "perfiles": self.on_cambiar_perfil,
            "historial": self.on_abrir_historial,
            "tecnicas": self.on_abrir_tecnicas,
            "umbrales": self.on_abrir_umbrales,
            "camara": self.on_abrir_camara,
            "salir": self.on_cerrar_sesion_entrenador,
        }
        destinos[seccion]()

    # ---------------- navegación ----------------

    def on_login_exitoso(self, entrenador):
        """
        Entra al sistema. El destino es el panel de inicio y no una selección de
        alumno: quién entrena se decide dentro del análisis en vivo, cuando ya se
        va a medir.
        """
        self.entrenador = entrenador
        self.on_abrir_inicio()

    def on_cambiar_perfil(self):
        """
        Selección del sensei que opera el sistema.

        Va a ventana completa y sin barra lateral porque durante ese momento no
        hay una identidad activa que respalde las secciones: la barra mostraría
        opciones firmadas por un sensei que se está a punto de dejar de ser.
        """
        self._mostrar(PerfilScreen(self, self.db, self.entrenador, app=self))

    def on_cerrar_sesion_entrenador(self):
        """Vuelve al acceso. La barra desaparece: sin entrenador no hay qué navegar."""
        self.entrenador = None
        self.atleta = None
        self._mostrar(LoginScreen(self, self.db))

    def on_abrir_inicio(self):
        self._mostrar_en_marco(
            lambda padre: InicioScreen(padre, self.db, self.entrenador, app=self), "inicio")

    def on_abrir_vivo(self, atleta=None):
        """
        Análisis en vivo (RF-01, RF-03, RF-05, RF-06).

        Conserva la barra lateral: durante una clase el instructor necesita poder
        consultar un umbral o el historial sin perder de vista dónde está. Que
        salir de aquí cierre la sesión correctamente lo garantiza
        `_limpiar_pantalla`, no la ausencia de navegación.
        """
        self.atleta = atleta if atleta is not None else self.atleta
        self._mostrar_en_marco(
            lambda padre: LiveScreen(padre, self.db, self.entrenador, self.atleta, app=self),
            "vivo")

    # Nombre anterior de `on_abrir_vivo`. La selección de perfiles ya no elige
    # alumno, pero la pantalla de alumnos sigue necesitando "medir a este".
    def on_perfil_elegido(self, atleta):
        self.on_abrir_vivo(atleta)

    def on_terminar_sesion(self):
        if isinstance(self.pantalla_actual, LiveScreen):
            self.pantalla_actual.cerrar()
        self.on_abrir_inicio()

    def on_abrir_umbrales(self):
        """
        Calibración de umbrales (RF-08). Requiere sesión de entrenador iniciada:
        es esa sesión la que queda firmando cada versión de umbral guardada.
        """
        # Queda marcada la sección "Técnicas": la calibración salió de la barra
        # porque recalibrar es algo que se hace SOBRE una técnica, y se llega
        # desde la biblioteca, donde el criterio vigente está a la vista.
        self._mostrar_en_marco(
            lambda padre: UmbralesScreen(padre, self.db, self.entrenador, app=self),
            "tecnicas")

    def on_abrir_camara(self):
        """
        Fuente de video (RF-01). Vive fuera de la pantalla en vivo a propósito:
        cambiar de cámara a mitad de una medición interrumpiría la sesión que se
        está registrando.
        """
        self._mostrar_en_marco(
            lambda padre: CamaraScreen(padre, self.db, app=self), "camara")

    # ---- Historial y reportes (RF-07) ----
    # La navegación es jerárquica: alumnos -> un alumno -> una de sus sesiones.
    # Las tres viven en la sección "historial" de la barra, de modo que bajar al
    # detalle no hace perder de vista dónde se está.

    def on_abrir_historial(self):
        self._mostrar_en_marco(
            lambda padre: HistorialScreen(padre, self.db, self.entrenador, app=self),
            "historial")

    def on_abrir_alumno(self, id_atleta):
        self._mostrar_en_marco(
            lambda padre: AlumnoScreen(padre, self.db, id_atleta, self.entrenador, app=self),
            "historial")

    def on_abrir_reporte(self, id_sesion):
        self._mostrar_en_marco(
            lambda padre: ReporteScreen(padre, self.db, id_sesion, self.entrenador, app=self),
            "historial")

    def on_abrir_tecnicas(self):
        self._mostrar_en_marco(
            lambda padre: TecnicasScreen(padre, self.db, self.entrenador, app=self),
            "tecnicas")

    def on_volver_a_perfiles(self):
        """Nombre histórico del regreso tras una medición; hoy lleva al inicio."""
        self.on_abrir_inicio()

    def _al_cerrar(self):
        """
        Cierre ordenado: libera la cámara, cierra la base y detiene el ciclo de
        eventos ANTES de destruir la ventana.

        El `quit()` no es decorativo. CustomTkinter mantiene un vigilante de
        escala de pantalla (ScalingTracker) que se reprograma solo con `after`;
        si la ventana se destruye con el ciclo de eventos todavía corriendo, esa
        llamada pendiente se dispara contra una ventana que ya no existe y
        termina en:

            _tkinter.TclError: can't invoke "winfo" command:
            application has been destroyed

        No rompe nada —ocurre al salir— pero deja una traza en la terminal que
        parece un fallo del sistema. Detener el ciclo primero impide que esa
        llamada llegue a ejecutarse.
        """
        if isinstance(self.pantalla_actual, LiveScreen):
            self.pantalla_actual.cerrar()
        self.db.close()
        self.quit()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
