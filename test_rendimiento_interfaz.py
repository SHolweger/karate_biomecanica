"""
test_rendimiento_interfaz.py — RNF-01 y RF-01 sobre la interfaz real.

`test_rendimiento.py` mide el encadenamiento de análisis con una ventana de
OpenCV. Esa ventana es de depuración y **no es la que se usa en el dojo**: en
una medición del 27-sep se llevó 20,5 de los 45,4 ms por fotograma, más que la
estimación de pose. Quitarla subió la tasa de 22,0 a 44,1 fps.

Ninguna de esas dos cifras describe el producto. La interfaz real hace cosas que
aquella medición no incluye:

  * convierte el fotograma a imagen de CustomTkinter y lo escala al hueco;
  * refresca las cuatro métricas articulares y, cuando cambia, el panel de
    correcciones — widgets de Tk, no píxeles de OpenCV;
  * escribe las mediciones en SQLite;
  * graba el video crudo de la sesión, si está activada la grabación.

Este script abre la pantalla de análisis en vivo de verdad, con un monitor
inyectado, la deja correr N fotogramas y emite la misma evidencia que
`test_rendimiento.py` — CSV, gráfica y veredicto— para que ambas cifras sean
comparables.

Uso:
    python3 test_rendimiento_interfaz.py [fuente] [n_fotogramas]

    fuente        índice de cámara, cámara IP o ruta de un video. Sin este
                  argumento se usa la que quedó configurada en la aplicación
    n_fotogramas  cuántos medir antes de cortar. Default: 300

Sobre una grabación conviene que empiece con el ejecutante ya colocado: los
primeros segundos de un video casero son la persona caminando hacia su sitio.
"""
import sys

from biomechanics.metrics import PerformanceMonitor
from test_rendimiento import fuente_por_defecto, reportar

# Las mismas etapas que marca `gui/live_screen.py`, en su orden. `grabacion`,
# `persistencia` y `panel` no existen en la medición de consola: son
# precisamente lo que este script viene a poner sobre la mesa.
ETAPAS_INTERFAZ = ["captura", "grabacion", "estimacion_pose", "analisis",
                   "renderizado", "persistencia", "panel", "despliegue"]


def medir_interfaz(fuente, n_fotogramas):
    """Abre la aplicación real, mide N fotogramas de análisis y la cierra."""
    import customtkinter as ctk

    from gui.app import App
    from gui.live_screen import LiveScreen
    from persistence.database import Database
    from vision.camera import Camera

    db = Database()
    entrenadores = db.listar_entrenadores()
    atletas = db.listar_atletas()
    if not entrenadores or not atletas:
        print("Hace falta al menos un sensei y un alumno registrados.")
        print("Créalos desde la interfaz gráfica antes de medir.")
        db.close()
        return None

    entrenador, atleta = entrenadores[0], atletas[0]
    print(f"Midiendo con {entrenador['nombre']} y {atleta['nombre']}.")

    monitor = PerformanceMonitor(descartar_iniciales=5)
    app = App(db=db)
    app.entrenador = entrenador

    # La cámara se construye aquí para poder apuntarla a la fuente pedida sin
    # tocar la configuración guardada del equipo: medir no debe dejar la
    # aplicación apuntando a otro sitio del que estaba.
    cam = Camera(fuente)
    app._limpiar_pantalla()
    app._montar_marco("vivo")
    pantalla = LiveScreen(app.contenido, db, entrenador, atleta,
                          cam=cam, app=app, monitor=monitor)
    app.pantalla_actual = pantalla
    pantalla.pack(expand=True, fill="both")

    print(f"Midiendo {n_fotogramas} fotogramas sobre la interfaz real...")

    def vigilar():
        if len(monitor.totales) >= n_fotogramas or not pantalla._activo:
            app.quit()
            return
        app.after(200, vigilar)

    app.after(200, vigilar)
    app.mainloop()

    pantalla.cerrar()
    app.destroy()
    db.close()
    return monitor


if __name__ == "__main__":
    fuente = sys.argv[1] if len(sys.argv) > 1 else fuente_por_defecto()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    monitor = medir_interfaz(fuente, n)
    if monitor is not None:
        print("\n(Medición sobre la INTERFAZ REAL, no sobre la ventana de OpenCV.)")
        reportar(monitor, etapas=ETAPAS_INTERFAZ)
