"""
gui/ventanas.py — Que una ventana secundaria quede delante de la principal.

En Windows, una `CTkToplevel` recién creada aparece y al instante queda DETRÁS
de la ventana principal: CustomTkinter la configura con un retraso, la
principal recupera el foco y el sensei ve que «Registrar nuevo alumno» se abre
y desaparece. Lo observó Sebastián el 3-nov-2026, la primera vez que usó el
sistema en Windows. En macOS no ocurre.

`al_frente` lo corrige solo en Windows: declara la ventana como dependiente de
la principal (`transient`, que en Windows la mantiene siempre encima de su
dueña) y, cuando CustomTkinter termina de configurarla, la sube y le da el
foco. En otros sistemas no toca nada, para no cambiar lo que ya está
verificado en la Mac a días de la defensa.

No importa CustomTkinter ni Tk: recibe la ventana y el sistema, así que la
prueba corre en integración continua con un doble.
"""
import sys

# CustomTkinter termina de configurar la ventana en Windows con un `after` de
# 200 ms (el icono); subirla antes no sirve, porque ese paso la vuelve a hundir.
RETRASO_MS = 250


def al_frente(ventana, plataforma=None):
    """Deja `ventana` delante de su dueña en Windows. Devuelve si hizo algo."""
    plataforma = plataforma or sys.platform
    if not plataforma.startswith("win"):
        return False

    ventana.transient(ventana.master.winfo_toplevel())

    def subir():
        try:
            if ventana.winfo_exists():
                ventana.lift()
                ventana.focus_force()
        except Exception:  # cerrada entre tanto: no hay nada que subir
            pass

    ventana.after(RETRASO_MS, subir)
    return True
