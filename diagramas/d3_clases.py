"""3.8.3 — Diagrama de clases, organizado por las capas del Capítulo 3."""
from _svg import (Lienzo, caja_clase, TINTA, ACENTO, ACENTO_BG, GRIS, GRIS_BG, BANDA_BG, BLANCO)

W, H = 1440, 1600
c = Lienzo(W, H, "Diagrama de clases — Sistema experto de análisis biomecánico")

BANDAS = [
    (60,   330, "CAPA DE PRESENTACIÓN (GUI)", "Cap. 3 — capa de interfaz gráfica de usuario"),
    (400,  610, "CAPA DE ADQUISICIÓN DE DATOS", "Cap. 3 — captura óptica e ingesta inercial"),
    (680,  890, "CAPA DE PROCESAMIENTO BIOMECÁNICO Y FUSIÓN", "Cap. 3 — sincronización temporal y fusión sensorial"),
    (960, 1210, "CAPA DE INFERENCIA (SISTEMA EXPERTO)", "Cap. 3 — motor heurístico y base de conocimientos"),
    (1280,1530, "CAPA DE PERSISTENCIA", "RF-07 — SQLite embebido, local (RNF-02)"),
]
for y0, y1, titulo, sub in BANDAS:
    c.rect(60, y0, 1350, y1 - y0, fill=BANDA_BG, stroke="#dbe3ec", sw=1.2, rx=8)
    c.texto(76, y0 + 22, titulo, size=11.5, weight="bold", fill="#5b6a80")
    c.texto(76 + len(titulo) * 6.9 + 18, y0 + 22, sub, size=10, fill="#93a1b5", italic=True)

# ---------------- CAPA A: presentación ----------------
app = caja_clase(c, 70, 100, 230, "App", [
    "- db : Database", "- entrenador : dict", "- atleta : dict", "- pantalla_actual"],
    ["+ _mostrar(pantalla)", "+ on_login_exitoso(e)", "+ on_perfil_elegido(a)", "+ on_terminar_sesion()"],
    estereotipo="«CTk» gui/app.py")

login = caja_clase(c, 350, 100, 230, "LoginScreen", ["- db : Database"],
    ["+ _intentar_login()", "+ _crear_cuenta(rol)"], estereotipo="«CTkFrame»")

perfil = caja_clase(c, 630, 100, 230, "PerfilScreen", ["- db : Database"],
    ["+ _elegir(atleta)", "+ _abrir_form_nuevo()"], estereotipo="«CTkFrame»")

live = caja_clase(c, 910, 100, 250, "LiveScreen", [
    "- cam : Camera", "- tracker : PoseTracker", "- renderer : SkeletonRenderer",
    "- analyzer : TechniqueAnalyzer", "- logger : MedicionLogger"],
    ["+ _actualizar_frame()", "+ cerrar()"], estereotipo="«CTkFrame»")

consola = caja_clase(c, 1190, 100, 215, "main + cli_auth", [],
    ["+ main()", "+ login_o_registro(db)", "+ elegir_o_crear_perfil(db)"],
    estereotipo="«módulo» vía consola")

# ---------------- CAPA B: adquisición ----------------
cam = caja_clase(c, 70, 440, 250, "Camera", ["- cap : cv2.VideoCapture"],
    ["+ get_frame()", "+ release()"], estereotipo="vision/camera.py")

track = caja_clase(c, 360, 440, 270, "PoseTracker", ["- landmarker : PoseLandmarker"],
    ["+ process_frame(frame, ts_ms)", "+ close()"], estereotipo="vision/tracker.py")

imu = caja_clase(c, 670, 440, 250, "ImuReceiver", ["- puerto_serial", "- buffer : deque"],
    ["+ leer_trama()", "+ cerrar()"], estereotipo="RF-02 — planificado", planificado=True)

# ---------------- CAPA C: procesamiento biomecánico ----------------
geo = caja_clase(c, 70, 720, 250, "BiomechanicsMath", [],
    ["+ calculate_angle(a, b, c)  «static»"], estereotipo="biomechanics/geometry.py")

filt = caja_clase(c, 360, 720, 250, "MovingAverageFilter", ["- buffer : deque"],
    ["+ update(value)", "+ reset()"], estereotipo="RNF-03 — anti-jitter")

rend = caja_clase(c, 650, 720, 250, "SkeletonRenderer", ["- POSE_CONNECTIONS : list"],
    ["+ draw(frame, landmarks)", "+ draw_diagnostics(frame, r)"], estereotipo="RF-06")

fus = caja_clase(c, 940, 720, 250, "SensorFusion", [],
    ["+ alinear(ts_video, ts_imu)", "+ cuaternion_a_angulo(q)"],
    estereotipo="RF-04 — planificado", planificado=True)

# ---------------- CAPA D: inferencia ----------------
analy = caja_clase(c, 200, 1000, 310, "TechniqueAnalyzer", [
    "- umbral : float", "- filtros : dict<str, MovingAverageFilter>",
    "- maquinas_patada : dict<str, MaeGeriSM>"],
    ["+ analyze_tsuki(lm, w, h)", "+ analyze_stance(lm, w, h)",
     "+ analyze_mae_geri(lm, w, h, ts)"], estereotipo="motor de inferencia (RF-05)")

fsm = caja_clase(c, 550, 1000, 310, "MaeGeriStateMachine", [
    "- estado : str", "- velocidad_pico : float", "- filtro_angulo : MovingAverageFilter"],
    ["+ update(vis, ang, ankle_y, ts)", "+ reset()"],
    estereotipo="cinemática dinámica — 4 fases")

reglas = caja_clase(c, 900, 1000, 330, "KarateRules", [],
    ["+ evaluate_tsuki(ang)  «static»", "+ evaluate_heiko_dachi(ang)",
     "+ evaluate_kiba_dachi(i, d)", "+ evaluate_zenkutsu_dachi(f, t)",
     "+ evaluate_kokutsu_dachi(f, t)", "+ evaluate_mae_geri(ang, vel)",
     "+ evaluate_hikiashi(recogido)", "+ evaluate_age_uke(ang)"],
    estereotipo="base de conocimientos (RF-05)")

# ---------------- CAPA E: persistencia ----------------
bd = caja_clase(c, 70, 1320, 320, "Database", ["- conn : sqlite3.Connection"],
    ["+ autenticar_entrenador(u, p)", "+ crear_atleta(...)",
     "+ iniciar_sesion(...) / cerrar_sesion(id)", "+ guardar_medicion(...)",
     "+ consultar_historial(id_atleta)"], estereotipo="RF-07 / RF-08")

mlog = caja_clase(c, 440, 1320, 280, "MedicionLogger", ["- _ultimo_mensaje : dict"],
    ["+ registrar(diagnostico, ts_ms)"], estereotipo="anti-duplicados")

rep = caja_clase(c, 780, 1320, 300, "reportes", [],
    ["+ generar_reporte_progreso(db, id)"], estereotipo="«módulo» matplotlib")

# ================= RELACIONES =================
# Los puntos de anclaje se toman del borde REAL de cada caja (caja_clase
# devuelve su alto calculado), no de una estimación.
BUS = 1300   # canal vertical para las dependencias de LiveScreen

def borde_inf(caja):   return caja[1] + caja[3]
def borde_der(caja):   return caja[0] + caja[2]

# App ◆— pantallas (composición)
c.conector([(borde_der(app), 144), (login[0], 144)], dueno_rombo=True, color=ACENTO)
c.conector([(185, borde_inf(app)), (185, 300), (745, 300), (745, borde_inf(perfil))],
           dueno_rombo=True, color=ACENTO)
c.conector([(215, borde_inf(app)), (215, 316), (890, 316), (890, 180), (live[0], 180)],
           dueno_rombo=True, color=ACENTO)

# LiveScreen ⟶ pipeline (bus vertical a la derecha, un canal por destino)
for destino_x, destino_y, canal_y in [(195, cam[1], 360), (495, track[1], 382),
                                      (775, rend[1], 645), (355, analy[1], 925),
                                      (580, mlog[1], 1245)]:
    c.conector([(1035, borde_inf(live)), (1035, 292), (BUS, 292), (BUS, canal_y),
                (destino_x, canal_y), (destino_x, destino_y)], color=ACENTO)

# App ⇢ Database: App crea la instancia y la inyecta a todas las pantallas
c.conector([(app[0], 200), (28, 200), (28, 1390), (bd[0], 1390)], tipo="dep", color=ACENTO)
c.texto(34, 800, "usa / inyecta", size=10.5, fill=ACENTO, italic=True)

# TechniqueAnalyzer
c.conector([(280, analy[1]), (280, 930), (450, 930), (450, borde_inf(filt))],
           dueno_rombo=True, color=ACENTO, etiqueta="5")
c.conector([(borde_der(analy), 1070), (fsm[0], 1070)], dueno_rombo=True, color=ACENTO,
           etiqueta="2", et_offset=(-24, -10))
c.conector([(235, analy[1]), (235, 950), (195, 950), (195, borde_inf(geo))],
           tipo="dep", color=ACENTO)
c.conector([(450, borde_inf(analy)), (450, 1192), (1065, 1192), (1065, borde_inf(reglas))],
           tipo="dep", color=ACENTO)

# MaeGeriStateMachine
c.conector([(700, fsm[1]), (700, 902), (485, 902), (485, borde_inf(filt))],
           dueno_rombo=True, color=ACENTO)
c.conector([(borde_der(fsm), 1055), (reglas[0], 1055)], tipo="dep", color=ACENTO)

# Persistencia
c.conector([(mlog[0], 1365), (borde_der(bd), 1365)], color=ACENTO)
c.conector([(930, borde_inf(rep)), (930, 1502), (230, 1502), (230, borde_inf(bd))],
           tipo="dep", color=ACENTO)

# Cadena IMU (planificada)
c.conector([(795, borde_inf(imu)), (795, 648), (1065, 648), (1065, fus[1])],
           tipo="dep", color=GRIS)
c.conector([(1065, borde_inf(fus)), (1065, 958), (400, 958), (400, analy[1])],
           tipo="dep", color=GRIS)

# ---------------- notas ----------------
def nota(x, y, w, lineas, titulo, color="#c9a227", bg="#fffdf2", tinta="#5a4a10"):
    h = 26 + 14 * len(lineas)
    c.rect(x, y, w, h, fill=bg, stroke=color, sw=1.3, rx=6)
    c.polilinea([(x + w - 18, y), (x + w, y), (x + w, y + 18)], stroke=color, sw=1.3)
    c.texto(x + 12, y + 18, titulo, size=11, weight="bold", fill=tinta)
    for i, ln in enumerate(lineas):
        c.texto(x + 12, y + 36 + i * 14, ln, size=10.3, fill=tinta)

nota(1190, 232, 215, [
    "Vía alterna por consola: instancia",
    "directamente Camera, PoseTracker,",
    "SkeletonRenderer, TechniqueAnalyzer,",
    "Database y MedicionLogger — el mismo",
    "pipeline que LiveScreen, sin GUI.",
], "main.py")
c.linea(1297, borde_inf(consola), 1297, 232, stroke="#c9a227", sw=1.3, dash="4 3")

nota(960, 428, 290, [
    "TechniqueAnalyzer responde «¿qué hay AHORA?»;",
    "MaeGeriStateMachine responde «¿en qué FASE de",
    "un evento de varios frames estamos?». Por eso",
    "son clases separadas y no una sola.",
], "Separación de responsabilidades")

# ---------------- leyenda ----------------
c.rect(60, 1545, 690, 45, fill=BLANCO, stroke="#dbe3ec", sw=1.2, rx=6)
c.rect(78, 1558, 26, 18, fill=BLANCO, stroke=ACENTO, sw=1.8)
c.texto(114, 1572, "Implementado y verificado (git log)", size=11.5)
c.rect(360, 1558, 26, 18, fill=GRIS_BG, stroke=GRIS, sw=1.8, dash="4 3")
c.texto(396, 1572, "Planificado (Sprint 4-5, depende del IMU)", size=11.5, fill=GRIS)

c.guardar("3.8.3_diagrama_clases.svg")
print("3.8.3_diagrama_clases.svg")
