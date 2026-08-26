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
from expert_system.knowledge_base import UMBRALES_LITERATURA
from gui import theme
from gui.login_screen import LoginScreen
from gui.perfil_screen import PerfilScreen
from gui.live_screen import LiveScreen


class App(ctk.CTk):
    """
    Orquesta la navegación entre pantallas (Login -> Perfil -> Análisis en
    vivo), replicando el flujo estilo Netflix del mockup de referencia
    (login de entrenador + selección de perfil sin contraseña).

    No reemplaza a main.py — es una vía alterna y más visual hacia el mismo
    sistema experto (mismo Camera/PoseTracker/SkeletonRenderer/TechniqueAnalyzer).
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
        self.entrenador = None
        self.atleta = None
        self.pantalla_actual = None

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        self._mostrar(LoginScreen(self, self.db))

    def _mostrar(self, pantalla):
        if self.pantalla_actual is not None:
            self.pantalla_actual.pack_forget()
            self.pantalla_actual.destroy()
        self.pantalla_actual = pantalla
        self.pantalla_actual.pack(expand=True, fill="both")

    def on_login_exitoso(self, entrenador):
        self.entrenador = entrenador
        self._mostrar(PerfilScreen(self, self.db, entrenador))

    def on_perfil_elegido(self, atleta):
        self.atleta = atleta
        self._mostrar(LiveScreen(self, self.db, self.entrenador, atleta))

    def on_terminar_sesion(self):
        if isinstance(self.pantalla_actual, LiveScreen):
            self.pantalla_actual.cerrar()
        self._mostrar(PerfilScreen(self, self.db, self.entrenador))

    def _al_cerrar(self):
        if isinstance(self.pantalla_actual, LiveScreen):
            self.pantalla_actual.cerrar()
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
