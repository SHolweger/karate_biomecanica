"""
El análisis por lotes de los videos del dojo (TC-AUTO-085).

Corre en CI porque lo que decide —qué cuenta como evaluación, a qué técnica y
deportista se suma, qué se le entrega al sensei— es lógica pura. Lo que se fija
aquí es que cuente con el registrador REAL de la base y no con una copia de su
regla: si la herramienta contara distinto que una sesión, sus cifras no
servirían para el indicador (a) del 6.10.
"""
import ast
import inspect

import pytest

import analizar_lote as al
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria

ZEN_BIEN = "ZENKUTSU (DER ADELANTE): POSTURA: FIRME"
HEIKO_BIEN = "POSTURA NATURAL: HEIKO DACHI: CORRECTO"
KIBA_ALTO = "KIBA DACHI: POSTURA: FLEXIONA MAS LAS RODILLAS"
MOVIENDOSE = "MOVIENDOSE: EN TRANSICION..."
TECNICA_DE = {ZEN_BIEN: "zenkutsu_dachi", HEIKO_BIEN: "heiko_dachi", KIBA_ALTO: "kiba_dachi"}


def _postura(mensaje, correcto):
    return [[], [{"categoria": "postura", "mensaje": mensaje, "correcto": correcto,
                  "tecnica": TECNICA_DE.get(mensaje)}], []]


def _tramo(desde_ms, hasta_ms, diagnosticos, orientacion=0.2, paso_ms=50):
    return [(t, diagnosticos, orientacion) for t in range(desde_ms, hasta_ms, paso_ms)]


def _segmento(tecnica="zenkutsu_dachi", repeticiones=2, deportista="D1", **extra):
    base = {"fila": 2, "archivo": "zen.mp4", "deportista": deportista, "tecnica": tecnica,
            "orientacion": "perfil", "vestimenta": "karategi", "repeticiones": repeticiones,
            "desde": None, "hasta": None, "espejado": False}
    base.update(extra)
    return base


def _dos_zenkutsu_con_heiko_en_medio():
    return (_tramo(0, 1000, _postura(ZEN_BIEN, True))
            + _tramo(1000, 1300, _postura(MOVIENDOSE, None))
            + _tramo(1300, 2300, _postura(HEIKO_BIEN, True))
            + _tramo(2300, 2500, _postura(KIBA_ALTO, False))      # parpadeo de paso
            + _tramo(2500, 3000, _postura(HEIKO_BIEN, True))
            + _tramo(3000, 4000, _postura(ZEN_BIEN, True))
            + _tramo(4000, 4500, None, None))                      # sin pose


@ficha(
    id_caso="TC-AUTO-085",
    nombre="El análisis por lotes cuenta las evaluaciones como las registraría una sesión "
           "y las suma al deportista y la técnica del tramo",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="los videos del dojo del 24-oct dan el indicador (a) del 6.10 y las "
                         "cifras de la defensa. Si la herramienta contara con una regla propia, "
                         "dos repeticiones, un parpadeo de transición o el Heiko entre "
                         "repeticiones se contarían distinto que en una sesión real, y la "
                         "cifra no describiría al sistema",
    componente="analizar_lote.py (contar, fila_de_segmento, agregar)",
    requisitos="RF-05, RF-07",
    precondiciones="Ninguna: diagnósticos escritos a mano, sin cámara ni MediaPipe",
    datos_entrada="Dos Zenkutsu correctos con un Heiko en medio, un parpadeo de Kiba de 0,2 s, "
                  "una transición y medio segundo sin pose",
    pasos=[
        Paso("Contar el tramo con el registrador de la base",
             "assert dos Zenkutsu y un Heiko; ni el parpadeo ni la transición cuentan"),
        Paso("Resumir el tramo de Zenkutsu",
             "assert 2 evaluaciones propias, el Heiko aparte y la pose al 88,9 %"),
        Paso("Agregar por deportista y técnica",
             "assert el Heiko de descanso no se suma al indicador"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_cuenta_como_una_sesion_y_suma_al_tramo():
    conteo = al.contar(_dos_zenkutsu_con_heiko_en_medio())

    assert [e["tecnica"] for e in conteo["evaluaciones"]] == [
        "zenkutsu_dachi", "heiko_dachi", "zenkutsu_dachi"]
    assert {e["lado"] for e in conteo["evaluaciones"] if e["tecnica"] == "zenkutsu_dachi"} == {"der"}
    assert (conteo["fotogramas"], conteo["con_pose"]) == (90, 80)

    fila = al.fila_de_segmento(_segmento(), conteo)
    assert (fila["evaluaciones"], fila["correctas"], fila["incorrectas"]) == (2, 2, 0)
    assert fila["reconocida"] == "sí"
    assert fila["otras_tecnicas"] == "Heiko Dachi: 1"
    assert fila["pose_detectada"] == "88,9 %"

    [agregada] = al.agregar([(_segmento(), conteo)])
    assert (agregada["tecnica"], agregada["evaluaciones"], agregada["repeticiones_ejecutadas"]) == (
        "Zenkutsu Dachi", 2, 2)


def test_el_tsuki_se_cuenta_por_brazo():
    golpe = [[{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE", "correcto": True,
               "tecnica": "tsuki"}], [], []]
    reposo = [[{"categoria": "codo_izq", "mensaje": "IZQ - SIN TSUKI: BRAZO EN REPOSO",
                "correcto": None}], [], []]
    fotogramas = [(0, golpe, 0.2), (40, reposo, 0.2), (80, golpe, 0.2)]

    evaluaciones = al.contar(fotogramas)["evaluaciones"]

    # El reposo en medio separa los dos golpes, como en la base.
    assert [(e["tecnica"], e["lado"]) for e in evaluaciones] == [("tsuki", "izq")] * 2


def test_sin_evaluaciones_el_porcentaje_es_un_guion():
    conteo = al.contar(_tramo(0, 2000, _postura(MOVIENDOSE, None)))
    [fila] = al.agregar([(_segmento(), conteo)])
    assert fila["porcentaje_correctas"] == "—"
    assert fila["tramos_sin_reconocer"] == 1


def test_un_tramo_combinado_se_informa_aparte():
    conteo = al.contar(_dos_zenkutsu_con_heiko_en_medio())
    filas = al.agregar([(_segmento(tecnica=None, repeticiones=None), conteo)])
    assert {(f["tecnica"], f["contexto"], f["evaluaciones"]) for f in filas} == {
        ("Zenkutsu Dachi", "combinada", 2), ("Heiko Dachi", "combinada", 1)}


def test_el_inventario_se_lee_como_lo_guarda_excel(tmp_path):
    (tmp_path / "zen.mp4").write_bytes(b"")
    ruta = tmp_path / "inventario.csv"
    ruta.write_text(
        "archivo;deportista;tecnica;orientacion;vestimenta;repeticiones;desde;hasta;espejado;notas\n"
        "zen.mp4;D1;Zenkutsu Dachi;Perfil;karategi;5;0:12;1:03,5;;\n"
        "zen.mp4;D2;Mae-Geri;perfil;casual;3;70;80;Sí;\n"
        "zen.mp4;D3;ura zuki;perfil;;3;;;;\n"
        "falta.mp4;D4;tsuki;perfil;;dos;;;;\n"
        "zen.mp4;;;;;;;;;sin clasificar\n",
        encoding="utf-8-sig")

    segmentos, errores = al.leer_inventario(ruta, tmp_path)

    assert [(s["deportista"], s["tecnica"], s["desde"], s["hasta"]) for s in segmentos] == [
        ("D1", "zenkutsu_dachi", 12.0, 63.5), ("D2", "mae_geri", 70.0, 80.0)]
    assert segmentos[1]["espejado"] is True
    assert errores[0].startswith("fila 4 (zen.mp4): técnica «ura zuki» desconocida")
    assert "fila 5" in errores[1] and "no es un número" in errores[1] and "no está" in errores[1]


def test_la_plantilla_conserva_lo_escrito_y_suma_lo_nuevo(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"")
    (tmp_path / "dia2").mkdir()
    (tmp_path / "dia2" / "b.MOV").write_bytes(b"")
    (tmp_path / "resultados_20261102_1000").mkdir()
    (tmp_path / "resultados_20261102_1000" / "c.mp4").write_bytes(b"")
    (tmp_path / "notas.txt").write_text("no es video")

    assert al.escribir_plantilla(tmp_path) == 2
    ruta = tmp_path / "inventario.csv"
    texto = ruta.read_text(encoding="utf-8-sig").replace("a.mp4,,", "a.mp4,D1,")
    ruta.write_text(texto, encoding="utf-8-sig")
    (tmp_path / "d.mp4").write_bytes(b"")

    assert al.escribir_plantilla(tmp_path) == 1
    filas = al._leer_csv(ruta)
    assert [(f["archivo"], f["deportista"]) for f in filas] == [
        ("a.mp4", "D1"), ("dia2/b.MOV", ""), ("d.mp4", "")]


def test_la_planilla_del_sensei_no_trae_el_veredicto_del_sistema():
    filas = al.filas_de_rubrica([_segmento(repeticiones=3, desde=12.0, hasta=40.0),
                                 _segmento(tecnica=None, repeticiones=None)])
    assert [f["codigo"] for f in filas] == ["S01-R1", "S01-R2", "S01-R3", "S02-R1"]
    assert filas[0]["desde"] == "0:12,0"
    assert not {"correcto", "veredicto", "evaluaciones"} & set(al.COLUMNAS_RUBRICA)


def test_avisa_cuando_la_toma_no_sigue_el_protocolo():
    conteo = {"fotogramas": 10, "con_pose": 5, "orientacion": 0.95, "evaluaciones": []}

    avisos = al.advertencias(_segmento(orientacion="frontal"), conteo)
    assert "declarado frontal; el protocolo pide perfil" in avisos
    assert "la toma se midió frontal; el protocolo pide perfil" in avisos
    assert "pose detectada en solo 50,0 %" in avisos
    assert any("Kokutsu" in a for a in al.advertencias(_segmento(tecnica="kokutsu_dachi"), conteo))


def test_importarla_no_exige_camara_ni_mediapipe():
    """Lo que necesita hardware se importa dentro de `recorrer`, no arriba."""
    arbol = ast.parse(inspect.getsource(al))
    arriba = {nodo.module for nodo in arbol.body if isinstance(nodo, ast.ImportFrom)}
    assert not arriba & {"vision.camera", "vision.tracker", "expert_system.analyzer"}


# ---------------------------------------------------------------------------
# --registrar: los videos re-analizados entran a la base con su fecha
# ---------------------------------------------------------------------------

import datetime as _dt


def _con_fecha(fecha, deportista="D1", archivo="zen.mp4", **extra):
    return _segmento(deportista=deportista, archivo=archivo, fecha=_dt.date.fromisoformat(fecha), **extra)


@pytest.fixture
def sensei(db):
    db.crear_entrenador("Sensei Prueba", "sensei", "s@d.gt", "clave123", rol="principal")
    return db.autenticar_entrenador("sensei", "clave123")["id_entrenador"]


@ficha(
    id_caso="TC-AUTO-087",
    nombre="Un video re-analizado entra a la base como una sesión con su fecha de grabación, "
           "sin duplicarse y en orden en la gráfica de evolución",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="los videos del dojo se re-analizan días después de grabarse y son la "
                         "única fuente de la evolución de cada alumno. Con la fecha de hoy, todo "
                         "el entrenamiento caería en un solo día; registrado dos veces, la "
                         "precisión contaría doble; y la gráfica ordenaba por orden de registro, "
                         "así que importar un video viejo después de uno nuevo la desordenaba",
    componente="analizar_lote.py (registrar); persistence/database.py (iniciar_sesion, "
               "listar_sesiones, importacion_video)",
    requisitos="RF-07, RF-05",
    precondiciones="Base SQLite temporal con un sensei; diagnósticos escritos a mano",
    datos_entrada="Dos videos de D1 (3-nov y, importado después, 24-oct) y uno de D2",
    pasos=[
        Paso("Registrar el video del 3-nov y después el del 24-oct",
             "assert cada sesión lleva su fecha de grabación y la gráfica los ordena por fecha"),
        Paso("Contar las filas escritas",
             "assert son las mismas que la interfaz habría escrito, con su criterio"),
        Paso("Volver a registrar lo mismo",
             "assert no se crea ninguna sesión nueva"),
        Paso("Registrar un alumno que no existe",
             "assert queda inscrito con el nombre del inventario"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz gráfica",
    evidencia="Reporte de consola de pytest y documento de casos generado con "
              "`--reporte-formal`.",
)
def test_registra_cada_video_con_su_fecha_y_sin_duplicar(db, sensei, tmp_path):
    conteo = al.contar(_dos_zenkutsu_con_heiko_en_medio())
    nuevo = [(_con_fecha("2026-11-03", archivo="b.mp4"), conteo)]
    viejo = [(_con_fecha("2026-10-24", archivo="a.mp4"), conteo)]
    otro = [(_con_fecha("2026-10-24", deportista="D2", archivo="a.mp4"), conteo)]

    assert al.registrar(db, sensei, nuevo, tmp_path, escribir=lambda _: None) == 1
    assert al.registrar(db, sensei, viejo + otro, tmp_path, escribir=lambda _: None) == 2

    [d1] = [a for a in db.listar_atletas() if a["nombre"] == "D1"]
    sesiones = db.listar_sesiones(d1["id_atleta"])
    assert [s["fecha"] for s in sesiones] == ["2026-11-03", "2026-10-24"], \
        "la gráfica se arma con esta lista: tiene que ir por fecha, no por orden de registro"
    assert sesiones[0]["evaluaciones"] == 3
    assert {a["nombre"] for a in db.listar_atletas()} == {"D1", "D2"}

    filas = db.conn.execute("SELECT COUNT(*) FROM tecnica_evaluada").fetchone()[0]
    assert filas == 3 * len(conteo["registro"])

    assert al.registrar(db, sensei, nuevo + viejo + otro, tmp_path, escribir=lambda _: None) == 0
    assert db.conn.execute("SELECT COUNT(*) FROM sesion").fetchone()[0] == 3


def test_los_tramos_de_un_video_son_una_sola_sesion(db, sensei, tmp_path):
    conteo = al.contar(_dos_zenkutsu_con_heiko_en_medio())
    tramos = [(_con_fecha("2026-10-24", desde=40.0, hasta=60.0), conteo),
              (_con_fecha("2026-10-24", tecnica="heiko_dachi", desde=0.0, hasta=6.0), conteo)]

    assert al.registrar(db, sensei, tramos, tmp_path, escribir=lambda _: None) == 1

    [sesion] = db.conn.execute("SELECT fecha, hora_inicio, hora_fin, ruta_video FROM sesion").fetchall()
    assert sesion["fecha"] == "2026-10-24"
    assert sesion["hora_inicio"] == "2026-10-24T00:00:00"
    assert sesion["hora_fin"] == "2026-10-24T00:00:08.900000"   # dos tramos de 4,45 s
    assert sesion["ruta_video"].endswith("zen.mp4")


def test_sin_fecha_no_se_registra_y_lo_dice(db, sensei, tmp_path):
    avisos = []
    sin_fecha = [(_segmento(fecha=None), al.contar(_dos_zenkutsu_con_heiko_en_medio()))]
    assert al.registrar(db, sensei, sin_fecha, tmp_path, escribir=avisos.append) == 0
    assert "sin fecha de grabación" in avisos[0]


def test_la_fecha_sale_de_la_columna_o_de_la_carpeta():
    assert al.leer_fecha("2026-11-03") == _dt.date(2026, 11, 3)
    assert al.leer_fecha("3/11/2026") == _dt.date(2026, 11, 3)
    assert al.leer_fecha("", "dojo/2026-10-24/clip.mp4") == _dt.date(2026, 10, 24)
    assert al.leer_fecha("", "clip.mp4") is None
    with pytest.raises(ValueError):
        al.leer_fecha("ayer")
