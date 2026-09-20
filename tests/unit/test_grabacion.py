"""
Pruebas de las reglas de grabación de sesión (RF-01, RF-07).

El módulo bajo prueba no importa OpenCV, así que todo esto corre también en
integración continua, donde no hay cámara ni códecs. Lo que se verifica son las
tres decisiones que, mal tomadas, arruinan una toma de datos en el dojo: cómo se
llama el archivo, a qué velocidad se escribe y qué se le informa al sensei.
"""
from datetime import datetime

import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from vision.grabacion import (FPS_POR_DEFECTO, describir_resultado, directorio_configurado,
                              fps_estimado, grabacion_activada, nombre_de_archivo,
                              nombre_visible, parte_de_nombre, ruta_de_sesion)

pytestmark = pytest.mark.unitaria

CUANDO = datetime(2026, 10, 3, 18, 5, 42)


# ---------------- el nombre del archivo ----------------

def test_el_archivo_empieza_por_la_fecha_para_que_el_listado_quede_cronologico():
    nombre = nombre_de_archivo(14, "Ana Gómez", CUANDO)
    assert nombre.startswith("20261003_180542_")


def test_el_archivo_conserva_el_nombre_del_alumno():
    """En el dojo, 'sesion_014.mp4' obliga a abrir el sistema para saber de quién es."""
    assert "ana_gomez" in nombre_de_archivo(14, "Ana Gómez", CUANDO)


def test_el_archivo_termina_con_el_id_de_sesion_que_lo_ata_a_la_base():
    assert nombre_de_archivo(14, "Ana Gómez", CUANDO).endswith("_s14.mp4")


@pytest.mark.parametrize("entrada, esperado", [
    ("José Pérez", "jose_perez"),
    ("Ana  María   Gómez", "ana_maria_gomez"),
    ("O'Brien-Smith", "o_brien_smith"),
    ("Ah Sún", "ah_sun"),
    ("   ", "sin_alumno"),
    ("", "sin_alumno"),
    (None, "sin_alumno"),
])
def test_un_nombre_real_no_rompe_la_ruta(entrada, esperado):
    """Tildes, apóstrofos y espacios de un nombre real rompen rutas y copias."""
    assert parte_de_nombre(entrada) == esperado


def test_un_nombre_larguisimo_se_recorta_sin_dejar_guion_colgando():
    fragmento = parte_de_nombre("Maria Fernanda de los Angeles Rodriguez")
    assert len(fragmento) <= 24
    assert not fragmento.endswith("_")


def test_la_ruta_va_bajo_la_carpeta_de_grabaciones_y_no_bajo_evidencias():
    """Un video de sesión pesa cientos de MB: no entra al repositorio."""
    ruta = ruta_de_sesion(14, "Ana Gómez", CUANDO)
    assert ruta.startswith("grabaciones/")


def test_la_carpeta_se_puede_cambiar(tmp_path):
    ruta = ruta_de_sesion(14, "Ana", CUANDO, directorio=str(tmp_path))
    assert ruta.startswith(str(tmp_path))


# ---------------- la velocidad de escritura ----------------

@ficha(
    id_caso="TC-AUTO-041",
    nombre="La velocidad de grabación se deduce del análisis real y no de la que declara la cámara",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "el bucle corre a la velocidad que permite la estimación de pose, no a la de captura; "
        "declarar 30 fps sobre un flujo real de 10 produce un video que se reproduce al triple "
        "y deja de coincidir con los tiempos de las mediciones guardadas"
    ),
    componente="vision/grabacion.py (fps_estimado)",
    requisitos="RF-01",
    precondiciones="Ninguna. El módulo no importa OpenCV",
    datos_entrada="Once marcas de tiempo separadas 100 ms: [0, 100, ..., 1000]",
    pasos=[
        Paso("Invocar fps_estimado() con las marcas observadas",
             "Se miden los intervalos, no los fotogramas"),
        Paso("Comparar contra la velocidad real del flujo",
             "assert fps == 10.0, no 11.0 ni la nominal de la cámara"),
    ],
    resultado_esperado="10.0 fps: diez intervalos de 100 ms entre once fotogramas",
)
def test_la_velocidad_se_mide_por_intervalos_no_por_fotogramas():
    marcas = [i * 100 for i in range(11)]   # 11 fotogramas, 10 intervalos, 1 segundo

    assert fps_estimado(marcas) == 10.0


def test_el_costo_del_primer_fotograma_no_hunde_la_estimacion():
    """
    El primer fotograma incluye la carga del modelo de pose y tarda mucho más.
    Como solo marca el inicio del conteo, no debe contar como un intervalo.
    """
    marcas = [0, 800, 900, 1000, 1100, 1200]   # 800 ms de arranque, luego 100 ms

    # Los cinco intervalos suman 1200 ms -> 4.17 fps. Sin el arranque serían 10,
    # pero afirmar 10 seria mentir sobre lo que el video realmente contiene:
    # el fotograma lento tambien esta grabado y tambien ocupa su lugar.
    assert fps_estimado(marcas) == pytest.approx(4.17, abs=0.01)


@pytest.mark.parametrize("marcas", [
    [],
    [0],
    [500, 500],       # dos marcas iguales: intervalo cero
    [1000, 0],        # marcas al reves
])
def test_sin_informacion_suficiente_se_usa_un_valor_razonable(marcas):
    """Un valor por defecto desincroniza un poco; un valor absurdo hace el video invisible."""
    assert fps_estimado(marcas) == FPS_POR_DEFECTO


def test_una_estimacion_absurdamente_alta_se_descarta():
    marcas = [0, 1, 2, 3]   # 1000 fps: una pausa del sistema, no una grabación
    assert fps_estimado(marcas) == FPS_POR_DEFECTO


def test_una_estimacion_absurdamente_baja_se_descarta():
    marcas = [0, 600_000]   # un fotograma cada diez minutos
    assert fps_estimado(marcas) == FPS_POR_DEFECTO


# ---------------- lo que se le dice al sensei ----------------

def test_el_resumen_dice_cuanto_dura_el_video_y_a_que_velocidad():
    texto = describir_resultado("grabaciones/20261003_180542_ana_gomez_s14.mp4",
                                frames=300, fps=10.0)

    assert "20261003_180542_ana_gomez_s14.mp4" in texto
    assert "300 fotogramas" in texto
    assert "30 s" in texto
    assert "10 fps" in texto


def test_sin_grabacion_se_dice_explicitamente_y_no_se_calla():
    """La interfaz no muestra lo que el sistema no midió, pero tampoco lo omite."""
    assert describir_resultado(None, frames=0, fps=0) == "No se grabó video de esta sesión."
    assert describir_resultado("x.mp4", frames=0, fps=10) == "No se grabó video de esta sesión."


# ---------------- preferencias del equipo ----------------

def test_la_grabacion_viene_activada_por_defecto():
    """Un sistema que silenciosamente no graba defrauda a quien creyó registrar la clase."""
    assert grabacion_activada(None) is True
    assert grabacion_activada("") is True


@pytest.mark.parametrize("guardado", ["0", "false", "False", "no", "NO", "off", " off "])
def test_la_grabacion_se_puede_apagar(guardado):
    """
    Filmar a un menor requiere el consentimiento de quien lo tiene a cargo, y en
    un dojo se entrena con menores. Apagada, la sesión se mide igual.
    """
    assert grabacion_activada(guardado) is False


@pytest.mark.parametrize("guardado", ["1", "true", "si", "on", "cualquier cosa"])
def test_cualquier_otro_valor_deja_la_grabacion_activada(guardado):
    assert grabacion_activada(guardado) is True


def test_sin_carpeta_configurada_se_usa_la_de_por_defecto():
    assert directorio_configurado(None) == "grabaciones"
    assert directorio_configurado("   ") == "grabaciones"


def test_la_carpeta_configurada_manda():
    """En el dojo puede ser un disco externo, no el disco del equipo."""
    assert directorio_configurado("/Volumes/DojoUSB/videos") == "/Volumes/DojoUSB/videos"


# ---------------- cómo se nombra el video en el reporte ----------------

def test_el_reporte_muestra_el_nombre_del_archivo_no_la_ruta_completa():
    """La ruta de un disco externo ocupa media pantalla y no aporta nada."""
    assert nombre_visible("/Volumes/DojoUSB/videos/20261003_180542_ana_gomez_s14.mp4") \
        == "20261003_180542_ana_gomez_s14.mp4"


@pytest.mark.parametrize("vacio", [None, "", "   "])
def test_sin_video_el_reporte_declara_la_ausencia_en_vez_de_callarla(vacio):
    """
    Omitir la línea dejaría sin saber si la sesión no se grabó o si el reporte
    no lo menciona, y esa diferencia importa al ir a buscar el archivo.
    """
    assert nombre_visible(vacio) == "Sin video"
