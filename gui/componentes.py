"""
Piezas visuales reutilizables de la interfaz.

Las pantallas de historial, alumno, reporte y técnicas comparten la misma
estructura —barra de título con acciones, tarjetas, filas de datos, indicadores
de precisión—, y repetir ese andamiaje en cada archivo haría que corregir un
detalle visual obligara a tocar cuatro lugares. Aquí vive una sola vez.

Solo se ocupa de presentación: ninguna función consulta la base de datos ni
decide reglas. Lo que reciben ya viene calculado por la capa de persistencia.
"""
import customtkinter as ctk

from gui import theme

# Umbrales de color para la precisión. No son criterios biomecánicos —esos
# viven en la base de conocimientos—, sino la convención visual con que el
# sensei lee un porcentaje de un vistazo.
PRECISION_BUENA = 75.0
PRECISION_REGULAR = 50.0


def color_precision(porcentaje):
    """Verde / ámbar / rojo según qué tan sólida viene una técnica."""
    if porcentaje is None:
        return theme.TEXTO_TENUE
    if porcentaje >= PRECISION_BUENA:
        return theme.ACENTO_VERDE
    if porcentaje >= PRECISION_REGULAR:
        return theme.ACENTO_AMARILLO
    return theme.ACENTO_ROJO


def texto_precision(porcentaje):
    """
    Porcentaje legible, o un guion cuando no hay datos.

    La distinción importa: "sin datos" y "0 %" son cosas distintas y confundirlas
    le diría al instructor que un alumno falla todo cuando en realidad nunca ha
    sido medido.
    """
    return "—" if porcentaje is None else f"{porcentaje:.0f} %"


def nombre_legible(clave):
    """Convierte `mae_geri` en `Mae Geri` para mostrarlo en pantalla."""
    return str(clave).replace("_", " ").title()


def fecha_legible(marca):
    """Recorta una marca de tiempo ISO a 'AAAA-MM-DD HH:MM'."""
    if not marca:
        return "—"
    return str(marca)[:16].replace("T", " ")


def encabezado(padre, titulo, subtitulo, acciones=()):
    """
    Barra superior estándar: título, subtítulo y botones a la derecha.

    `acciones` es una lista de (etiqueta, comando, destacado). El destacado se
    reserva para la acción principal de la pantalla; el resto van discretos para
    no competir con ella.
    """
    barra = ctk.CTkFrame(padre, fg_color="transparent")
    barra.pack(fill="x", padx=28, pady=(20, 10))

    textos = ctk.CTkFrame(barra, fg_color="transparent")
    textos.pack(side="left", anchor="w")
    ctk.CTkLabel(textos, text=titulo, font=(theme.FUENTE, 20, "bold"),
                 text_color=theme.TEXTO).pack(anchor="w")
    ctk.CTkLabel(textos, text=subtitulo, font=(theme.FUENTE, 12),
                 text_color=theme.TEXTO_MUTED).pack(anchor="w")

    for etiqueta, comando, destacado in reversed(list(acciones)):
        if destacado:
            ctk.CTkButton(barra, text=etiqueta, fg_color=theme.ACENTO_ROJO,
                          hover_color=theme.ACENTO_ROJO_HOVER, width=150,
                          command=comando).pack(side="right", padx=(8, 0))
        else:
            ctk.CTkButton(barra, text=etiqueta, fg_color="transparent", border_width=1,
                          border_color=theme.BORDE_CLARO, text_color=theme.TEXTO,
                          hover_color=theme.CARD_HOVER, width=130,
                          command=comando).pack(side="right", padx=(8, 0))
    return barra


def tarjeta(padre, **empaque):
    """Contenedor con el borde y el fondo de tarjeta del sistema visual."""
    caja = ctk.CTkFrame(padre, fg_color=theme.CARD, border_color=theme.BORDE,
                        border_width=1, corner_radius=10)
    caja.pack(fill="x", **({"pady": 3} | empaque))
    return caja


def vacio(padre, mensaje, detalle=None):
    """
    Estado vacío explicado.

    Una lista en blanco deja al usuario sin saber si el sistema falló o si
    todavía no hay nada; el texto convierte el silencio en información.
    """
    caja = ctk.CTkFrame(padre, fg_color="transparent")
    caja.pack(fill="x", pady=30)
    ctk.CTkLabel(caja, text=mensaje, font=(theme.FUENTE, 13),
                 text_color=theme.TEXTO_MUTED).pack()
    if detalle:
        ctk.CTkLabel(caja, text=detalle, font=(theme.FUENTE, 11.5),
                     text_color=theme.TEXTO_TENUE, wraplength=560,
                     justify="center").pack(pady=(4, 0))
    return caja


def barra_progreso(padre, porcentaje, ancho=180):
    """
    Barra horizontal proporcional a la precisión.

    Codifica el mismo dato dos veces —longitud y color— a propósito: la longitud
    permite comparar técnicas entre sí de un vistazo y el color da el veredicto
    sin tener que leer el número.
    """
    canal = ctk.CTkFrame(padre, fg_color=theme.BORDE, height=8, width=ancho,
                         corner_radius=4)
    canal.pack_propagate(False)
    if porcentaje is not None and porcentaje > 0:
        relleno = ctk.CTkFrame(canal, fg_color=color_precision(porcentaje),
                               height=8, corner_radius=4)
        relleno.place(relx=0, rely=0, relwidth=min(porcentaje, 100) / 100, relheight=1)
    return canal


def metrica(padre, etiqueta, valor, color=None):
    """Par etiqueta/valor para las cabeceras de resumen."""
    caja = ctk.CTkFrame(padre, fg_color="transparent")
    ctk.CTkLabel(caja, text=etiqueta.upper(), font=(theme.FUENTE, 10),
                 text_color=theme.TEXTO_TENUE).pack(anchor="w")
    ctk.CTkLabel(caja, text=valor, font=(theme.FUENTE, 19, "bold"),
                 text_color=color or theme.TEXTO).pack(anchor="w")
    return caja
