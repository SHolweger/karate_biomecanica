"""
Utilidades mínimas para escribir SVG a mano (sin dependencias externas).

Se generan los diagramas del Capítulo 3 por script y no a mano en draw.io
para que puedan regenerarse cuando el código cambie: el diagrama sigue al
código, no al revés.
"""

# Paleta pensada para impresión en la tesis (fondo blanco, alto contraste).
TINTA      = "#1b2a4a"   # texto y bordes principales
ACENTO     = "#2563eb"   # azul: piezas YA implementadas
ACENTO_BG  = "#eef4ff"
GRIS       = "#8896ab"   # gris: piezas PLANIFICADAS (aún no codificadas)
GRIS_BG    = "#f7f9fc"
BANDA_BG   = "#f1f5f9"
BLANCO     = "#ffffff"
FUENTE     = "Arial, Helvetica, sans-serif"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Lienzo:
    def __init__(self, ancho, alto, titulo=""):
        self.w, self.h = ancho, alto
        self.titulo = titulo
        self.partes = []

    # ---------------- primitivas ----------------

    def rect(self, x, y, w, h, fill=BLANCO, stroke=TINTA, sw=1.6, rx=4, dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.partes.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{d}/>')

    def texto(self, x, y, s, size=13, anchor="start", weight="normal", fill=TINTA,
              italic=False, family=FUENTE):
        st = ' font-style="italic"' if italic else ""
        self.partes.append(
            f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{esc(s)}</text>')

    def linea(self, x1, y1, x2, y2, stroke=TINTA, sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}/>')

    def polilinea(self, pts, stroke=TINTA, sw=1.4, dash=None, fill="none"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.partes.append(
            f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round"{d}/>')

    def poligono(self, pts, fill=TINTA, stroke=TINTA, sw=1.4):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.partes.append(
            f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def elipse(self, cx, cy, rx, ry, fill=BLANCO, stroke=TINTA, sw=1.6, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.partes.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def circulo(self, cx, cy, r, fill=BLANCO, stroke=TINTA, sw=1.6):
        self.partes.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    # ---------------- puntas de flecha ----------------

    def punta_abierta(self, x, y, dx, dy, color=TINTA, largo=11, ancho=5):
        """V abierta (dependencia / asociación navegable). (dx,dy) = dirección de avance."""
        px, py = -dy, dx
        bx, by = x - dx * largo, y - dy * largo
        self.linea(bx + px * ancho, by + py * ancho, x, y, stroke=color, sw=1.6)
        self.linea(bx - px * ancho, by - py * ancho, x, y, stroke=color, sw=1.6)

    def punta_solida(self, x, y, dx, dy, color=TINTA, largo=12, ancho=5.5):
        px, py = -dy, dx
        bx, by = x - dx * largo, y - dy * largo
        self.poligono([(x, y), (bx + px * ancho, by + py * ancho), (bx - px * ancho, by - py * ancho)],
                      fill=color, stroke=color)

    def rombo(self, x, y, dx, dy, color=TINTA, relleno=True, largo=16, ancho=6):
        """Rombo de composición/agregación, dibujado en el extremo del 'dueño'."""
        px, py = -dy, dx
        m1x, m1y = x + dx * largo / 2, y + dy * largo / 2
        m2x, m2y = x + dx * largo, y + dy * largo
        self.poligono([(x, y), (m1x + px * ancho, m1y + py * ancho), (m2x, m2y),
                       (m1x - px * ancho, m1y - py * ancho)],
                      fill=color if relleno else BLANCO, stroke=color)

    # ---------------- conector orto ----------------

    def conector(self, pts, tipo="usa", color=TINTA, etiqueta=None, et_offset=(6, -6),
                 dueno_rombo=False):
        """
        tipo: 'usa' (línea sólida + punta abierta), 'dep' (punteada + punta abierta).
        dueno_rombo: dibuja rombo de composición en el PRIMER punto.
        """
        dash = "6 4" if tipo == "dep" else None
        self.polilinea(pts, stroke=color, sw=1.4, dash=dash)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        dx, dy = x2 - x1, y2 - y1
        n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        self.punta_abierta(x2, y2, dx / n, dy / n, color=color)
        if dueno_rombo:
            (ax, ay), (bx, by) = pts[0], pts[1]
            ddx, ddy = bx - ax, by - ay
            nn = max((ddx * ddx + ddy * ddy) ** 0.5, 1e-6)
            self.rombo(ax, ay, ddx / nn, ddy / nn, color=color)
        if etiqueta:
            mx, my = pts[len(pts) // 2]
            self.texto(mx + et_offset[0], my + et_offset[1], etiqueta, size=11,
                       fill=color, italic=True)

    # ---------------- salida ----------------

    def guardar(self, ruta):
        cuerpo = "\n  ".join(self.partes)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">\n'
               f'  <title>{esc(self.titulo)}</title>\n'
               f'  <rect width="{self.w}" height="{self.h}" fill="{BLANCO}"/>\n'
               f'  {cuerpo}\n</svg>\n')
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(svg)
        return ruta


# ---------------- componentes reutilizables ----------------

def actor(c, x, y, etiqueta, sub=None):
    """Monigote UML. (x,y) = centro de la cabeza."""
    c.circulo(x, y, 13, fill=BLANCO, stroke=TINTA, sw=1.8)
    c.linea(x, y + 13, x, y + 48, sw=1.8)
    c.linea(x - 20, y + 26, x + 20, y + 26, sw=1.8)
    c.linea(x, y + 48, x - 17, y + 76, sw=1.8)
    c.linea(x, y + 48, x + 17, y + 76, sw=1.8)
    c.texto(x, y + 96, etiqueta, size=14, anchor="middle", weight="bold")
    if sub:
        c.texto(x, y + 113, sub, size=11, anchor="middle", fill=GRIS, italic=True)


def caso_uso(c, cx, cy, lineas, rx=125, ry=34, planificado=False, tag=None):
    color = GRIS if planificado else ACENTO
    fondo = GRIS_BG if planificado else ACENTO_BG
    c.elipse(cx, cy, rx, ry, fill=fondo, stroke=color, sw=1.7,
             dash="6 4" if planificado else None)
    n = len(lineas)
    y0 = cy - (n - 1) * 8 + (0 if not tag else -6)
    for i, ln in enumerate(lineas):
        c.texto(cx, y0 + i * 16 + 5, ln, size=12.5, anchor="middle", fill=TINTA)
    if tag:
        c.texto(cx, cy + ry - 10, tag, size=10.5, anchor="middle",
                fill=color, weight="bold")
    return (cx, cy, rx, ry)


def caja_clase(c, x, y, w, nombre, atributos, metodos, estereotipo=None, planificado=False):
    """Caja UML de clase con 3 compartimentos. Devuelve (x, y, w, h)."""
    color = GRIS if planificado else ACENTO
    fondo = GRIS_BG if planificado else BLANCO
    h_nom = 30 + (14 if estereotipo else 0)
    h_at = 6 + 15 * len(atributos) + (4 if atributos else 0)
    h_me = 6 + 15 * len(metodos) + (4 if metodos else 0)
    h = h_nom + h_at + h_me
    c.rect(x, y, w, h, fill=fondo, stroke=color, sw=1.8,
           dash="6 4" if planificado else None)
    c.rect(x, y, w, h_nom, fill=ACENTO_BG if not planificado else "#eef1f6",
           stroke=color, sw=1.8, dash="6 4" if planificado else None)
    yy = y + 15
    if estereotipo:
        c.texto(x + w / 2, yy, estereotipo, size=10.5, anchor="middle", fill=color, italic=True)
        yy += 15
    c.texto(x + w / 2, yy + 5, nombre, size=13.5, anchor="middle", weight="bold",
            fill=TINTA if not planificado else GRIS)
    yy = y + h_nom
    c.linea(x, yy, x + w, yy, stroke=color, sw=1.2)
    ty = yy + 15
    for a in atributos:
        c.texto(x + 10, ty, a, size=11, fill=TINTA if not planificado else GRIS)
        ty += 15
    yy = y + h_nom + h_at
    c.linea(x, yy, x + w, yy, stroke=color, sw=1.2)
    ty = yy + 15
    for m in metodos:
        c.texto(x + 10, ty, m, size=11, fill=TINTA if not planificado else GRIS)
        ty += 15
    return (x, y, w, h)


def caja_entidad(c, x, y, w, nombre, filas, planificado=False):
    """Entidad del MER: cabecera + filas de atributos. filas = [(texto, marca)]."""
    color = GRIS if planificado else TINTA
    h_cab = 32
    h = h_cab + 21 * len(filas) + 8
    c.rect(x, y, w, h, fill=GRIS_BG if planificado else BLANCO, stroke=color, sw=1.8,
           dash="6 4" if planificado else None)
    c.rect(x, y, w, h_cab, fill=GRIS if planificado else TINTA, stroke=color, sw=1.8, rx=4)
    c.rect(x, y + h_cab - 8, w, 8, fill=GRIS if planificado else TINTA, stroke="none", sw=0, rx=0)
    c.texto(x + w / 2, y + 21, nombre, size=13, anchor="middle", weight="bold", fill=BLANCO)
    ty = y + h_cab + 16
    for texto_fila, marca in filas:
        if marca:
            c.texto(x + 10, ty, marca, size=10, weight="bold",
                    fill=ACENTO if marca in ("PK", "FK") else GRIS)
        c.texto(x + 42, ty, texto_fila, size=11.5, fill=TINTA if not planificado else "#5c6b80")
        ty += 21
    return (x, y, w, h)


def pata_gallo(c, x, y, dx, dy, muchos, color=TINTA):
    """Notación pata de gallo. (dx,dy): dirección de avance HACIA la entidad."""
    px, py = -dy, dx
    if muchos:
        bx, by = x - dx * 15, y - dy * 15
        for s in (-1, 0, 1):
            c.linea(bx, by, x + px * 9 * s, y + py * 9 * s, stroke=color, sw=1.5)
    else:
        bx, by = x - dx * 13, y - dy * 13
        c.linea(bx + px * 8, by + py * 8, bx - px * 8, by - py * 8, stroke=color, sw=1.8)
