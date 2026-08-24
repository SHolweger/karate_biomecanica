"""
reportes.py — Gráficas de progreso de un atleta a partir de su historial real
en la base de datos (RF-07). Genera evidencia visual para la tesis, en el
mismo espíritu que test_antijitter.py: consulta datos reales, calcula
métricas simples y guarda un PNG en evidencias/.
"""
import os
from datetime import datetime

AZUL = "#2a78d6"     # mismo acento usado en las gráficas de anti-jitter, por consistencia
GRIS_TEXTO = "#333333"
GRIS_MUTED = "#8a94a6"


def _porcentaje_correcto(filas):
    """% de diagnósticos correctos entre los que sí fueron evaluaciones cerradas (correcto no es None)."""
    evaluados = [f for f in filas if f["correcto"] is not None]
    if not evaluados:
        return None
    aciertos = sum(1 for f in evaluados if f["correcto"])
    return aciertos / len(evaluados) * 100


def generar_reporte_progreso(db, id_atleta, nombre_atleta, carpeta="evidencias"):
    """
    Genera dos gráficas a partir de db.consultar_historial(id_atleta):
      1. % de precisión por sesión (progreso en el tiempo)
      2. % de precisión por técnica (en qué se le dificulta más)
    Guarda un PNG combinado en `carpeta` y devuelve la ruta, o None si no
    hay datos evaluados todavía (todo "EN TRANSICION"/oculto, sin correcto).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    historial = db.consultar_historial(id_atleta)
    evaluados = [f for f in historial if f["correcto"] is not None]
    if not evaluados:
        return None

    # ---- Métrica 1: % correcto por sesión, en orden cronológico ----
    por_sesion = {}
    for f in evaluados:
        por_sesion.setdefault(f["id_sesion"], []).append(f)
    sesiones_ordenadas = sorted(por_sesion.keys())
    etiquetas_sesion = [f"Sesión {i + 1}" for i in range(len(sesiones_ordenadas))]
    porcentajes_sesion = [_porcentaje_correcto(por_sesion[s]) for s in sesiones_ordenadas]

    # ---- Métrica 2: % correcto por técnica ----
    por_tecnica = {}
    for f in evaluados:
        por_tecnica.setdefault(f["nombre_tecnica"], []).append(f)
    tecnicas_ordenadas = sorted(por_tecnica.keys(), key=lambda t: _porcentaje_correcto(por_tecnica[t]))
    porcentajes_tecnica = [_porcentaje_correcto(por_tecnica[t]) for t in tecnicas_ordenadas]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Progreso de {nombre_atleta}", fontsize=14, color=GRIS_TEXTO)

    # Gráfica 1: precisión por sesión (barras verticales, una sola serie -> un solo tono)
    barras1 = ax1.bar(etiquetas_sesion, porcentajes_sesion, color=AZUL, width=0.55)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Precisión (%)")
    ax1.set_title("Precisión por sesión", fontsize=11, color=GRIS_TEXTO)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.grid(axis="y", alpha=0.25, linewidth=0.5)
    for barra, pct in zip(barras1, porcentajes_sesion):
        ax1.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 2,
                  f"{pct:.0f}%", ha="center", fontsize=9, color=GRIS_TEXTO)

    # Gráfica 2: precisión por técnica (barras horizontales, ordenadas de menor a mayor)
    barras2 = ax2.barh(tecnicas_ordenadas, porcentajes_tecnica, color=AZUL, height=0.55)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Precisión (%)")
    ax2.set_title("Precisión por técnica", fontsize=11, color=GRIS_TEXTO)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="x", alpha=0.25, linewidth=0.5)
    for barra, pct in zip(barras2, porcentajes_tecnica):
        ax2.text(barra.get_width() + 1.5, barra.get_y() + barra.get_height() / 2,
                  f"{pct:.0f}%", va="center", fontsize=9, color=GRIS_TEXTO)

    fig.tight_layout()
    os.makedirs(carpeta, exist_ok=True)
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(carpeta, f"progreso_atleta{id_atleta}_{sello}.png")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta
