"""
Pruebas del aviso de imagen detenida (RF-01).

El módulo bajo prueba no importa OpenCV, así que esto corre también en
integración continua. Lo que se verifica es la decisión, no el texto: cuándo
hay que hablar, cuándo hay que callarse y cuándo la frase tiene que mandar a
mirar el cable en vez de anunciar un final normal.

La costura —que la pantalla consulte esto y pinte el resultado— la verifica
`tests/e2e/test_gui_vivo.py`, porque lo que faltaba el 1-oct-2026 no era el
texto sino que alguien lo leyera.
"""
import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha
from vision.senal import (FIN_DE_GRABACION, SIN_IMAGEN, UMBRAL_SEGUNDOS,
                          aviso_de_senal)

pytestmark = pytest.mark.unitaria


# ---------------- cuándo callarse ----------------

@pytest.mark.parametrize("segundos", [0, 0.04, 0.5, UMBRAL_SEGUNDOS - 0.01])
def test_un_fotograma_perdido_no_merece_un_aviso(segundos):
    """
    A 24 fps un fotograma dura 40 ms. Avisar de eso sería ruido, y un aviso
    que salta ante lo normal se aprende a ignorar.
    """
    assert aviso_de_senal(segundos, fuente_es_grabacion=False) is None


def test_sin_dato_de_tiempo_no_se_inventa_un_aviso():
    """`None` es «no se ha perdido ningún fotograma todavía», no «cero segundos»."""
    assert aviso_de_senal(None, fuente_es_grabacion=False) is None


# ---------------- cuándo hablar ----------------

@ficha(
    id_caso="TC-AUTO-063",
    nombre="La imagen detenida se anuncia, y se distingue el fin de archivo de la cámara caída",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo=(
        "una imagen congelada muestra algo que ya no se está midiendo: la sesión "
        "sigue abierta y el último veredicto a la vista, de modo que el sensei "
        "corrige sobre una ejecución que terminó hace minutos"),
    componente="vision/senal.py (aviso_de_senal)",
    requisitos="RF-01",
    precondiciones="Ninguna. El módulo es puro y no abre cámara ni archivo",
    datos_entrada=(
        "Segundos de reloj sin fotograma: por debajo del umbral (0, 0,04, 0,5), "
        "en el umbral (1,5) y muy por encima (4, 30); para cada uno, fuente de "
        "cámara y fuente de grabación"),
    pasos=[
        Paso("Invocar aviso_de_senal por debajo del umbral",
             "assert aviso_de_senal(0.5, fuente_es_grabacion=False) is None"),
        Paso("Invocar aviso_de_senal por encima del umbral, con cámara",
             "assert aviso_de_senal(4.0, fuente_es_grabacion=False) != FIN_DE_GRABACION"),
        Paso("Comprobar que el aviso nombra los segundos detenidos",
             "assert '4' in aviso_de_senal(4.0, fuente_es_grabacion=False)"),
        Paso("Invocar aviso_de_senal por encima del umbral, con grabación",
             "assert aviso_de_senal(4.0, fuente_es_grabacion=True) == FIN_DE_GRABACION"),
        Paso("Volver a invocar con la imagen recuperada",
             "assert aviso_de_senal(0.0, fuente_es_grabacion=False) is None"),
    ],
    resultado_esperado="PASSED: el aviso aparece solo cuando corresponde y nombra la causa correcta",
)
def test_una_camara_detenida_manda_a_mirar_el_cable():
    aviso = aviso_de_senal(4.0, fuente_es_grabacion=False)
    assert aviso is not None
    assert aviso != FIN_DE_GRABACION


def test_el_aviso_de_camara_dice_cuanto_lleva_la_imagen_detenida():
    """
    No basta con decir que falta imagen: lo que el sensei necesita saber es
    cuánto lleva en pantalla algo que ya no se mide.
    """
    assert "4" in aviso_de_senal(4.0, fuente_es_grabacion=False)
    assert "30" in aviso_de_senal(30.7, fuente_es_grabacion=False)


def test_el_umbral_cuenta_como_alcanzado():
    """Un umbral que exige superarlo deja un caso sin definir justo en el borde."""
    assert aviso_de_senal(UMBRAL_SEGUNDOS, fuente_es_grabacion=False) is not None


# ---------------- la distinción que importa ----------------

def test_el_final_de_una_grabacion_no_se_anuncia_como_un_fallo():
    """
    De un archivo, quedarse sin fotogramas es el final normal del análisis.
    Decirlo con la frase de la cámara mandaría a revisar un cable que no existe.
    """
    assert aviso_de_senal(4.0, fuente_es_grabacion=True) == FIN_DE_GRABACION


def test_las_dos_situaciones_no_comparten_frase():
    """El mismo hecho técnico tiene dos lecturas opuestas; que se lean distinto."""
    de_camara = aviso_de_senal(10.0, fuente_es_grabacion=False)
    de_archivo = aviso_de_senal(10.0, fuente_es_grabacion=True)
    assert de_camara != de_archivo


def test_una_grabacion_por_debajo_del_umbral_tampoco_dice_nada():
    """Un hueco corto dentro de un archivo no es su final."""
    assert aviso_de_senal(0.5, fuente_es_grabacion=True) is None


# ---------------- el aviso se retira ----------------

def test_el_aviso_desaparece_cuando_la_imagen_vuelve():
    """
    Uno que se queda puesto después de resolverse el problema enseña a
    ignorarlo, y deja de servir cuando el problema es real.
    """
    assert aviso_de_senal(6.0, fuente_es_grabacion=False) is not None
    assert aviso_de_senal(0.0, fuente_es_grabacion=False) is None


# ---------------- el umbral es un parámetro ----------------

def test_el_umbral_se_puede_mover_sin_tocar_el_modulo():
    """
    Igual que los dos umbrales del Tsuki: se decide con datos, así que tiene
    que poder barrerse sin editar el código que lo usa.
    """
    assert aviso_de_senal(0.8, fuente_es_grabacion=False, umbral_s=0.5) is not None
    assert aviso_de_senal(0.8, fuente_es_grabacion=False, umbral_s=2.0) is None


def test_el_umbral_vigente_deja_fuera_un_fotograma_y_dentro_una_pausa_real():
    """
    Las dos cotas que justifican el número, comprobadas en vez de recordadas:
    40 ms es un fotograma a 24 fps; 2 s es cuando alguien ya dudó de la imagen.
    """
    assert 0.04 < UMBRAL_SEGUNDOS < 2.0


def test_la_frase_de_camara_tiene_hueco_para_los_segundos():
    """Una plantilla sin su marcador saldría literal en pantalla."""
    assert "{segundos}" in SIN_IMAGEN
