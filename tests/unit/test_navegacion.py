"""
Pruebas unitarias del mapa de navegación (RNF-04).

El requisito dice que el ciclo de uso se resuelve en tres pulsaciones o menos.
Estaba asociado a un caso E2E que comprueba que se abre una sesión de análisis,
lo cual no es lo mismo: esa prueba pasaría igual si llegar a la pantalla
costara siete clics. Aquí se cuenta.

Corren en las unitarias —y por tanto también en integración continua, sin
entorno gráfico— porque `gui/navegacion.py` no importa CustomTkinter. Que la
declaración corresponda con los botones que la aplicación dibuja de verdad lo
verifica `tests/e2e/test_navegacion_rnf04.py`.
"""
import pytest

from gui import navegacion
from gui.navegacion import MAXIMO_PULSACIONES, Paso, RUTAS, Ruta
from reporte.plantilla import Paso as PasoFicha, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@ficha(
    id_caso="TC-AUTO-037",
    nombre="Ninguna tarea principal del sistema cuesta más de tres pulsaciones",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es la verificación directa del RNF-04; sin ella el requisito se "
                         "daba por cumplido sin haber contado nunca las pulsaciones reales",
    componente="gui/navegacion.py (RUTAS, exceden_el_limite)",
    requisitos="RNF-04",
    precondiciones="Ninguna: el mapa de navegación es un módulo sin dependencias gráficas",
    datos_entrada="Las nueve rutas declaradas en `gui.navegacion.RUTAS`, cada una con la "
                  "secuencia de controles que hay que pulsar desde el panel de inicio",
    pasos=[
        PasoFicha("Contar los pasos de cada ruta declarada",
                  "Cada ruta tiene entre 1 y 3 pasos"),
        PasoFicha("Invocar `exceden_el_limite(RUTAS, limite=3)`",
                  "assert resultado == [] (ninguna tarea supera el límite)"),
        PasoFicha("Invocar el mismo verificador sobre una ruta artificial de cuatro pasos",
                  "assert la ruta aparece en el resultado: el verificador sí detecta un "
                  "incumplimiento, de modo que el resultado vacío anterior no es vacuo"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_ninguna_tarea_pasa_de_tres_pulsaciones():
    excedidas = navegacion.exceden_el_limite(RUTAS, limite=MAXIMO_PULSACIONES)

    assert excedidas == [], (
        f"el RNF-04 admite {MAXIMO_PULSACIONES} pulsaciones y estas tareas piden más: "
        f"{excedidas}")


def test_el_verificador_detecta_una_ruta_demasiado_larga():
    """
    Sin esta prueba la anterior podría pasar por estar mal escrita —por ejemplo,
    si `exceden_el_limite` devolviera siempre una lista vacía— y el RNF-04
    quedaría 'verificado' por un comprobador que no comprueba nada.
    """
    larga = Ruta("inventada", "Tarea imaginaria de cuatro pasos", "InicioScreen",
                 tuple(Paso("boton", f"Paso {i}") for i in range(4)))

    excedidas = navegacion.exceden_el_limite([larga], limite=MAXIMO_PULSACIONES)

    assert excedidas == [("Tarea imaginaria de cuatro pasos", 4)]


def test_cada_ruta_llega_a_una_pantalla_del_sistema():
    for ruta in RUTAS:
        assert ruta.destino.endswith("Screen"), \
            f"la ruta '{ruta.clave}' no declara a qué pantalla llega"


def test_las_claves_de_ruta_no_se_repiten():
    claves = [r.clave for r in RUTAS]

    assert len(claves) == len(set(claves)), f"hay claves repetidas en RUTAS: {claves}"


def test_ninguna_ruta_esta_vacia():
    for ruta in RUTAS:
        assert navegacion.pulsaciones(ruta) >= 1, \
            f"la ruta '{ruta.clave}' no declara ninguna pulsación"


def test_cada_paso_declara_un_tipo_de_control_conocido():
    for ruta in RUTAS:
        for paso in ruta.pasos:
            assert paso.control in navegacion.CONTROLES, \
                f"'{paso.control}' no es un control de la interfaz ({navegacion.CONTROLES})"


def test_las_etiquetas_variables_estan_declaradas():
    """
    Una etiqueta entre llaves es un dato del dojo (el nombre de un alumno, el de
    un sensei) que la prueba de interfaz sustituye por el valor real. Si se cuela
    una marca no declarada, la sustitución la dejaría pasar tal cual y el
    recorrido buscaría un botón llamado literalmente '{algo}'.
    """
    for ruta in RUTAS:
        for paso in ruta.pasos:
            if paso.etiqueta.startswith("{"):
                assert paso.etiqueta in navegacion.ETIQUETAS_VARIABLES, \
                    f"la ruta '{ruta.clave}' usa la marca {paso.etiqueta}, que no está declarada"


def test_toda_ruta_arranca_en_un_control_del_panel_de_inicio():
    """
    Las rutas se cuentan desde el panel de inicio, que es donde el sensei queda
    tras autenticarse. Su primer paso solo puede ser una sección de la barra
    lateral, una acción de la propia pantalla de inicio o el control de cambio
    de perfil del pie de la barra.
    """
    alcanzables = set(navegacion.etiquetas_de_seccion())
    alcanzables.update(navegacion.CONTROLES_DE_INICIO)
    alcanzables.add("{cambiar perfil}")

    for ruta in RUTAS:
        primero = ruta.pasos[0].etiqueta
        assert primero in alcanzables, \
            f"la ruta '{ruta.clave}' empieza en '{primero}', que no está en el panel de inicio"


def test_la_calibracion_no_es_una_seccion_de_la_barra():
    """
    Recalibrar se hace SOBRE una técnica y se llega desde la biblioteca, donde el
    criterio vigente está a la vista. Como sección suelta invitaba a abrir una
    tabla de diez umbrales sin recordar cuál se quería tocar.
    """
    assert "umbrales" not in [clave for clave, _ in navegacion.SECCIONES]
    assert navegacion.ruta("calibrar").pasos[0].etiqueta == "Técnicas"


def test_elegir_sensei_no_es_una_seccion_de_la_barra():
    """
    El perfil identifica a quién opera el sistema, no un lugar al que se va. Por
    eso cuelga de la identidad activa, en el pie, y no de la lista de secciones.
    """
    assert "perfiles" not in [clave for clave, _ in navegacion.SECCIONES]
    assert navegacion.ruta("sensei").pasos[0].etiqueta == "{cambiar perfil}"


def test_el_texto_de_cambiar_perfil_refleja_el_rol():
    assert navegacion.etiqueta_cambiar_perfil("principal") == "Principal · cambiar perfil"
    assert navegacion.etiqueta_cambiar_perfil("sensei") == "Sensei · cambiar perfil"


def test_sin_rol_el_control_dice_sensei():
    """Un entrenador dado de alta sin rol no debe dejar el pie de la barra en blanco."""
    assert navegacion.etiqueta_cambiar_perfil(None) == "Sensei · cambiar perfil"
    assert navegacion.etiqueta_cambiar_perfil("") == "Sensei · cambiar perfil"


def test_pedir_una_ruta_inexistente_falla_con_su_nombre():
    with pytest.raises(KeyError, match="inexistente"):
        navegacion.ruta("inexistente")
