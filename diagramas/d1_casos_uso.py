"""3.8.1 — Diagrama de casos de uso."""
from _svg import (Lienzo, actor, caso_uso, TINTA, ACENTO, GRIS, GRIS_BG, BANDA_BG, BLANCO)

W, H = 1180, 800
c = Lienzo(W, H, "Diagrama de casos de uso — Sistema experto de análisis biomecánico")

# ---- frontera del sistema ----
c.rect(210, 55, 700, 700, fill="#fbfcfe", stroke=TINTA, sw=2, rx=8)
c.texto(560, 82, "Sistema Experto de Análisis Biomecánico (Edge — equipo del Dojo)",
        size=13.5, anchor="middle", weight="bold")

XA, XB = 400, 750           # columna de casos primarios / incluidos
RA, RB = 120, 112

# ---- casos de uso primarios ----
uc_auth   = caso_uso(c, XA, 140, ["Autenticarse en", "el sistema"], rx=RA, tag="RF-08")
uc_perf   = caso_uso(c, XA, 222, ["Gestionar perfiles", "de deportistas"], rx=RA, tag="RF-07")
uc_ini    = caso_uso(c, XA, 304, ["Iniciar sesión", "de evaluación"], rx=RA, tag="RF-07")
uc_ana    = caso_uso(c, XA, 430, ["Analizar técnica", "en tiempo real"], rx=RA, ry=40, tag="RF-01 / RF-05")
uc_hist   = caso_uso(c, XA, 585, ["Consultar historial y", "generar reporte de progreso"], rx=RA, tag="RF-07")
uc_umb    = caso_uso(c, XA, 682, ["Editar umbrales", "biomecánicos"], rx=RA, tag="RF-08", planificado=True)

# ---- casos incluidos ----
uc_pose   = caso_uso(c, XB, 300, ["Estimar pose:", "33 landmarks"], rx=RB, tag="RF-03")
uc_jit    = caso_uso(c, XB, 382, ["Aplicar filtro", "anti-jitter"], rx=RB, tag="RNF-03")
uc_reglas = caso_uso(c, XB, 464, ["Evaluar contra base", "de conocimientos"], rx=RB, tag="RF-05")
uc_bd     = caso_uso(c, XB, 546, ["Registrar medición", "en base de datos"], rx=RB, tag="RF-07")
uc_imu    = caso_uso(c, XB, 640, ["Ingerir telemetría", "inercial (100 Hz)"], rx=RB, tag="RF-02", planificado=True)
uc_fus    = caso_uso(c, XB, 715, ["Fusionar visión", "+ IMU"], rx=RB, tag="RF-04", planificado=True)

# ---- actores ----
actor(c, 95, 250, "Entrenador", "(actor primario)")
actor(c, 95, 600, "Deportista", "(actor secundario)")
actor(c, 1080, 600, "Módulos IMU", "(sistema externo)")

# ---- asociaciones actor <-> caso de uso ----
for cy in (140, 222, 304, 430):
    c.linea(120, 300, XA - RA, cy, stroke=TINTA, sw=1.3)
for cy in (585, 682):
    c.linea(120, 312, XA - RA, cy, stroke=TINTA, sw=1.3)
c.linea(120, 650, XA - RA, 445, stroke=TINTA, sw=1.3)          # Deportista -> analizar
c.linea(1055, 650, XB + RB, 640, stroke=GRIS, sw=1.3, dash="6 4")  # IMU -> ingerir

# ---- «include» desde "Analizar técnica" ----
for (cx, cy, rx, ry), plan in [(uc_pose, False), (uc_jit, False), (uc_reglas, False),
                               (uc_bd, False), (uc_fus, True)]:
    col = GRIS if plan else ACENTO
    c.conector([(XA + RA - 8, 430), (cx - rx, cy)], tipo="dep", color=col)
    mx, my = (XA + RA - 8 + cx - rx) / 2, (430 + cy) / 2
    c.texto(mx, my - 5, "«include»", size=10, anchor="middle", fill=col, italic=True)

# «include» de autenticarse: se rutea por fuera de los óvalos (izquierda) para
# no cruzar texto. Solo se dibujan los dos casos que realmente exigen credenciales.
c.conector([(XA - RA, 304), (252, 304), (252, 148), (XA - RA + 4, 145)], tipo="dep", color=ACENTO)
c.texto(256, 245, "«include»", size=10, fill=ACENTO, italic=True)
c.conector([(XA - RA + 30, 682), (228, 682), (228, 132), (XA - RA + 6, 130)], tipo="dep", color=GRIS)
c.texto(232, 480, "«include»", size=10, fill=GRIS, italic=True)

# «extend»: la retroalimentación en pantalla extiende el análisis
uc_feed = caso_uso(c, XB, 175, ["Visualizar diagnóstico", "y esqueleto en pantalla"], rx=RB, tag="RF-06")
c.conector([(XB - RB + 20, 209), (XA + RA - 20, 400)], tipo="dep", color=ACENTO)
c.texto(600, 300, "«extend»", size=10, anchor="middle", fill=ACENTO, italic=True)

# ---- leyenda ----
c.rect(210, 768, 700, 0.1, stroke="none", sw=0)
c.elipse(255, 782, 22, 10, fill="#eef4ff", stroke=ACENTO, sw=1.5)
c.texto(288, 786, "Implementado y verificado", size=11.5)
c.elipse(500, 782, 22, 10, fill=GRIS_BG, stroke=GRIS, sw=1.5, dash="6 4")
c.texto(533, 786, "Planificado (Sprint 4-5)", size=11.5, fill=GRIS)

c.guardar("3.8.1_diagrama_casos_uso.svg")
print("3.8.1_diagrama_casos_uso.svg")
