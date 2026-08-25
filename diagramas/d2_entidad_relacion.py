"""3.8.2 — Diagrama entidad-relación (SQLite local)."""
from _svg import (Lienzo, caja_entidad, pata_gallo, TINTA, ACENTO, GRIS, GRIS_BG, BLANCO)

W, H = 1330, 985
c = Lienzo(W, H, "Diagrama entidad-relación — base de datos local SQLite")

# ------------- entidades -------------
ent = caja_entidad(c, 70, 110, 280, "ENTRENADOR", [
    ("id_entrenador : INTEGER", "PK"),
    ("nombre : TEXT", ""),
    ("usuario : TEXT  (UNIQUE)", ""),
    ("correo : TEXT", ""),
    ("password_hash : TEXT", ""),
    ("rol : TEXT", ""),
    ("fecha_registro : TEXT", ""),
])

atl = caja_entidad(c, 520, 110, 270, "ATLETA", [
    ("id_atleta : INTEGER", "PK"),
    ("nombre : TEXT", ""),
    ("fecha_nacimiento : TEXT", ""),
    ("grado_cinturon : TEXT", ""),
    ("fecha_registro : TEXT", ""),
])

umb = caja_entidad(c, 950, 110, 320, "UMBRAL_REFERENCIA", [
    ("id_umbral : INTEGER", "PK"),
    ("id_entrenador : INTEGER", "FK"),
    ("nombre_tecnica : TEXT", ""),
    ("articulacion : TEXT", ""),
    ("valor_min : REAL", ""),
    ("valor_max : REAL", ""),
    ("fuente : TEXT", ""),
    ("fecha_modificacion : TEXT", ""),
], planificado=True)

ses = caja_entidad(c, 400, 420, 290, "SESION", [
    ("id_sesion : INTEGER", "PK"),
    ("id_atleta : INTEGER", "FK"),
    ("id_entrenador : INTEGER", "FK"),
    ("fecha : TEXT", ""),
    ("hora_inicio : TEXT", ""),
    ("hora_fin : TEXT", ""),
])

tec = caja_entidad(c, 385, 700, 320, "TECNICA_EVALUADA", [
    ("id_medicion : INTEGER", "PK"),
    ("id_sesion : INTEGER", "FK"),
    ("id_umbral : INTEGER", "FK"),
    ("nombre_tecnica : TEXT", ""),
    ("timestamp_ms : INTEGER", ""),
    ("angulo_promedio : REAL", ""),
    ("velocidad_pico : REAL", ""),
    ("diagnostico : TEXT", ""),
    ("correcto : INTEGER", ""),
])

# ------------- relaciones -------------
# ENTRENADOR (1) ---< SESION (N)   "supervisa"
c.polilinea([(350, 230), (375, 230), (375, 480), (400, 480)], stroke=TINTA, sw=1.5)
pata_gallo(c, 350, 230, -1, 0, muchos=False)
pata_gallo(c, 400, 480, 1, 0, muchos=True)
c.texto(378, 355, "supervisa", size=11.5, italic=True, fill=TINTA)
c.texto(358, 218, "1", size=11, weight="bold", fill=ACENTO)
c.texto(378, 503, "N", size=11, weight="bold", fill=ACENTO)

# ATLETA (1) ---< SESION (N)   "participa en"
c.linea(655, 249, 655, 420, stroke=TINTA, sw=1.5)
pata_gallo(c, 655, 249, 0, -1, muchos=False)
pata_gallo(c, 655, 420, 0, 1, muchos=True)
c.texto(665, 340, "participa en", size=11.5, italic=True, fill=TINTA)
c.texto(636, 268, "1", size=11, weight="bold", fill=ACENTO)
c.texto(636, 414, "N", size=11, weight="bold", fill=ACENTO)

# SESION (1) ---< TECNICA_EVALUADA (N)   "contiene"
c.linea(545, 566, 545, 700, stroke=TINTA, sw=1.5)
pata_gallo(c, 545, 566, 0, -1, muchos=False)
pata_gallo(c, 545, 700, 0, 1, muchos=True)
c.texto(555, 640, "contiene", size=11.5, italic=True, fill=TINTA)
c.texto(526, 588, "1", size=11, weight="bold", fill=ACENTO)
c.texto(526, 694, "N", size=11, weight="bold", fill=ACENTO)

# UMBRAL_REFERENCIA (1) ---< TECNICA_EVALUADA (N)   "evaluada contra"  [propuesto]
c.polilinea([(1115, 300), (1115, 810), (705, 810)], stroke=GRIS, sw=1.5, dash="6 4")
pata_gallo(c, 1115, 300, 0, -1, muchos=False, color=GRIS)
pata_gallo(c, 705, 810, -1, 0, muchos=True, color=GRIS)
c.texto(900, 800, "evaluada contra", size=11.5, italic=True, fill=GRIS)
c.texto(1095, 322, "1", size=11, weight="bold", fill=GRIS)
c.texto(718, 830, "N", size=11, weight="bold", fill=GRIS)

# ENTRENADOR (1) ---< UMBRAL_REFERENCIA (N)   "calibra / modifica" [propuesto, RF-08]
c.polilinea([(210, 110), (210, 62), (1000, 62), (1000, 110)], stroke=GRIS, sw=1.5, dash="6 4")
pata_gallo(c, 210, 110, 0, 1, muchos=False, color=GRIS)
pata_gallo(c, 1000, 110, 0, 1, muchos=True, color=GRIS)
c.texto(610, 52, "calibra / modifica   (RF-08 — solo entrenadores autorizados)",
        size=11.5, anchor="middle", italic=True, fill=GRIS)

# ------------- nota sobre 'fuente' -------------
c.rect(70, 700, 265, 150, fill="#fffdf2", stroke="#c9a227", sw=1.4, rx=6)
c.polilinea([(315, 700), (335, 700), (335, 720)], stroke="#c9a227", sw=1.4)
c.texto(84, 724, "Nota — UMBRAL_REFERENCIA.fuente", size=11.5, weight="bold", fill="#7a6412")
for i, ln in enumerate([
        "Toma dos valores:",
        "  • 'literatura'  → umbral inicial tomado de",
        "     la bibliografía Shotokan (estado actual).",
        "  • 'modelado_experto' → umbral promediado",
        "     de ejecuciones de cinturones negros.",
        "Permite reemplazar umbrales sin cambiar el",
        "modelo de datos (ver 'Estrategia de recolección",
        "inicial de datos', Capítulo 3).", ]):
    c.texto(84, 744 + i * 14, ln, size=10.5, fill="#5a4a10")

# ------------- leyenda -------------
c.rect(950, 862, 320, 90, fill="#fbfcfe", stroke=TINTA, sw=1.2, rx=6)
c.texto(965, 884, "Leyenda", size=11.5, weight="bold")
c.rect(968, 894, 22, 13, fill=BLANCO, stroke=TINTA, sw=1.6)
c.texto(1000, 905, "Tabla implementada y en uso", size=10.5)
c.rect(968, 918, 22, 13, fill=GRIS_BG, stroke=GRIS, sw=1.6, dash="4 3")
c.texto(1000, 929, "Tabla propuesta (cierra RF-08)", size=10.5, fill=GRIS)

# columnas nuevas en TECNICA_EVALUADA
c.texto(390, 950, "Columnas propuestas en TECNICA_EVALUADA:  id_umbral (FK)  y  velocidad_pico.",
        size=10.5, fill=GRIS, italic=True)

c.guardar("3.8.2_diagrama_entidad_relacion.svg")
print("3.8.2_diagrama_entidad_relacion.svg")
