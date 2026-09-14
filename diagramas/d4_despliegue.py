"""3.8.4 — Diagrama de despliegue físico (Edge Computing)."""
from _svg import (Lienzo, actor, TINTA, ACENTO, ACENTO_BG, GRIS, GRIS_BG, BANDA_BG, BLANCO)

W, H = 1250, 830
c = Lienzo(W, H, "Diagrama de despliegue físico — arquitectura Edge del Dojo")


def nodo(x, y, w, h, estereotipo, titulo, sub=None, planificado=False, fill="#f7f9fc"):
    col = GRIS if planificado else TINTA
    d = "6 4" if planificado else None
    # efecto 3D de nodo UML
    c.polilinea([(x, y), (x + 14, y - 14), (x + w + 14, y - 14), (x + w, y)],
                stroke=col, sw=1.6, dash=d, fill="#e8edf4")
    c.polilinea([(x + w, y), (x + w + 14, y - 14), (x + w + 14, y + h - 14), (x + w, y + h)],
                stroke=col, sw=1.6, dash=d, fill="#dde4ee")
    c.rect(x, y, w, h, fill=fill, stroke=col, sw=1.8, rx=0, dash=d)
    c.texto(x + w / 2, y + 22, estereotipo, size=11, anchor="middle", italic=True, fill=col)
    c.texto(x + w / 2, y + 42, titulo, size=13.5, anchor="middle", weight="bold",
            fill=TINTA if not planificado else GRIS)
    if sub:
        c.texto(x + w / 2, y + 60, sub, size=10.5, anchor="middle", fill="#7d8ba0", italic=True)


def artefacto(x, y, w, h, titulo, detalle, planificado=False):
    col = GRIS if planificado else ACENTO
    c.rect(x, y, w, h, fill=GRIS_BG if planificado else BLANCO, stroke=col, sw=1.5, rx=4,
           dash="5 4" if planificado else None)
    # icono de documento
    c.polilinea([(x + 12, y + 12), (x + 12, y + h - 12), (x + 30, y + h - 12), (x + 30, y + 20),
                 (x + 22, y + 12), (x + 12, y + 12)], stroke=col, sw=1.2)
    c.texto(x + 42, y + 24, titulo, size=12, weight="bold", fill=TINTA if not planificado else GRIS)
    c.texto(x + 42, y + 41, detalle, size=10.3, fill="#6b7a90")


# ---------------- nodo central: equipo del Dojo ----------------
nodo(500, 90, 520, 630, "«device»", "Equipo de cómputo del Dojo (Edge)",
     "Laptop / PC del entrenador — sin conexión a la nube")

c.rect(530, 175, 460, 400, fill=BLANCO, stroke=TINTA, sw=1.5, rx=6, dash="3 3")
c.texto(760, 196, "«executionEnvironment»  Python 3.11 + venv", size=11.5,
        anchor="middle", italic=True, fill=TINTA)

artefacto(550, 214, 420, 54, "gui/  —  App, LoginScreen, PerfilScreen, LiveScreen",
          "CustomTkinter · capa de presentación (RF-06, RNF-04)")
artefacto(550, 282, 420, 54, "vision/  +  pose_landmarker_full.task",
          "OpenCV · MediaPipe Pose — 33 landmarks (RF-01, RF-03)")
artefacto(550, 350, 420, 54, "biomechanics/  —  geometry, filters, renderer",
          "Ángulos articulares · filtro anti-jitter SMA (RNF-03)")
artefacto(550, 418, 420, 54, "expert_system/  —  analyzer, knowledge_base, fsm",
          "Motor de inferencia + base de conocimientos (RF-05)")
artefacto(550, 486, 420, 54, "persistence/  —  database, medicion_logger, reportes",
          "Acceso a datos y reportes matplotlib (RF-07)")

artefacto(530, 600, 240, 64, "karate_sistema.db", "SQLite embebido · un solo archivo local")
artefacto(790, 600, 200, 64, "evidencias/*.png", "Reportes de progreso generados")

# ---------------- dispositivos periféricos ----------------
nodo(70, 150, 290, 120, "«device»", "Cámara externa",
     "iPhone (Continuity) / webcam USB")
c.texto(215, 236, "≥ 60 fps de captura · 1080p", size=10.5, anchor="middle", fill="#7d8ba0")

nodo(70, 440, 290, 150, "«device»", "Módulos IMU vestibles", None, planificado=True)
c.texto(215, 520, "4 × BNO055 (9-DOF, fusión en chip)", size=10.5, anchor="middle", fill=GRIS)
c.texto(215, 538, "+ 2 × ESP32 (WiFi / Bluetooth)", size=10.5, anchor="middle", fill=GRIS)
c.texto(215, 562, "Sprint 4-5 — hardware en tránsito", size=10, anchor="middle",
        fill=GRIS, italic=True)

# ---------------- conexiones ----------------
c.linea(360, 210, 500, 210, stroke=TINTA, sw=1.8)
c.texto(430, 200, "«USB 3.0 / Continuity»", size=10.5, anchor="middle", italic=True)
c.texto(430, 228, "flujo de video RGB", size=10, anchor="middle", fill="#7d8ba0")

c.linea(360, 505, 500, 505, stroke=GRIS, sw=1.8, dash="6 4")
c.texto(430, 495, "«BLE / Serial»", size=10.5, anchor="middle", italic=True, fill=GRIS)
c.texto(430, 523, "tramas a 100 Hz (RF-02)", size=10, anchor="middle", fill=GRIS)

# entrenador
actor(c, 1130, 330, "Entrenador")
c.linea(1034, 356, 1108, 356, stroke=TINTA, sw=1.8)
c.texto(1071, 344, "monitor + GUI local", size=10, anchor="middle", italic=True)

# ---------------- nota RNF-02 ----------------
c.rect(70, 660, 380, 120, fill="#f2fbf4", stroke="#2e9e57", sw=1.4, rx=6)
c.texto(86, 684, "RNF-02 — Arquitectura local independiente", size=11.5,
        weight="bold", fill="#1e6b3a")
for i, ln in enumerate([
        "No existe nodo de servidor ni servicios en la nube.",
        "Inferencia y persistencia ocurren íntegramente en el",
        "equipo del Dojo: sin costos de API, sin dependencia de",
        "conectividad y sin que los datos biométricos salgan",
        "de las instalaciones de la Asociación (RNF-05)."]):
    c.texto(86, 706 + i * 15, ln, size=10.5, fill="#2c5c40")

# nube tachada
c.elipse(1120, 620, 62, 30, fill="#f4f6f9", stroke=GRIS, sw=1.4, dash="5 4")
c.texto(1120, 625, "Internet", size=11, anchor="middle", fill="#6b7a90")
c.linea(1072, 592, 1168, 648, stroke="#d0455a", sw=2.4)
c.linea(1168, 592, 1072, 648, stroke="#d0455a", sw=2.4)
c.texto(1120, 676, "no requerido", size=10, anchor="middle", fill="#d0455a", italic=True)

# ---------------- leyenda ----------------
c.rect(500, 745, 520, 42, fill=BLANCO, stroke="#dbe3ec", sw=1.2, rx=6)
c.rect(516, 756, 24, 18, fill=BLANCO, stroke=TINTA, sw=1.6)
c.texto(548, 770, "Desplegado y en uso", size=11.5)
c.rect(730, 756, 24, 18, fill=GRIS_BG, stroke=GRIS, sw=1.6, dash="4 3")
c.texto(762, 770, "Planificado (Sprint 4-5)", size=11.5, fill=GRIS)

c.guardar("3.8.4_diagrama_despliegue.svg")
print("3.8.4_diagrama_despliegue.svg")
