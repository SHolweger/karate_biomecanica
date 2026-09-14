"""
Pruebas de las consultas que alimentan el panel de inicio y de la ficha
completa del alumno (RF-07).

Son las cifras que un instructor ve al abrir el sistema, antes de tocar nada.
Por eso el criterio que recorre todo el módulo es el mismo que rige el resto de
los agregados: un dato que no existe se informa como inexistente, nunca como
cero. Un dojo sin mediciones no tiene 0 % de precisión — tiene una precisión que
todavía no se puede calcular, y presentarla como cero afirmaría que todo se
ejecuta mal.
"""
from datetime import datetime, timedelta

import pytest

from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.integracion


@pytest.fixture
def id_entrenador(db):
    """Entrenador principal ya registrado: toda sesión necesita quién la firme."""
    return db.crear_entrenador("Sensei Ejemplo", "sensei", "sensei@dojo.gt",
                               "clave123", rol="principal")


def _sesion_fechada(db, id_atleta, id_entrenador, dias_atras):
    """
    Crea una sesión con fecha desplazada hacia el pasado.

    `iniciar_sesion` siempre sella la fecha de hoy —es lo correcto en
    producción—, así que para ejercitar la ventana de actividad hay que
    reescribir la fecha después de crearla.
    """
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)
    fecha = (datetime.now() - timedelta(days=dias_atras)).date().isoformat()
    db.conn.execute("UPDATE sesion SET fecha = ? WHERE id_sesion = ?", (fecha, id_sesion))
    db.conn.commit()
    return id_sesion


# ---------------- ficha del alumno ----------------

def test_un_alumno_puede_inscribirse_solo_con_su_nombre(db):
    """
    El resto de los datos se completan después. Exigirlos pondría un trámite
    delante del entrenamiento, que es justo lo que el sistema debe evitar.
    """
    id_atleta = db.crear_atleta("Marta Similox")

    ficha_alumno = db.obtener_atleta(id_atleta)
    assert ficha_alumno["nombre"] == "Marta Similox"
    for campo in ("edad", "peso_kg", "color_cinta", "tiempo_entrenando", "notas"):
        assert ficha_alumno[campo] is None, f"{campo} no debería inventarse un valor"


def test_la_ficha_completa_se_guarda_y_se_recupera(db):
    id_atleta = db.crear_atleta(
        "Diego Morales", grado_cinturon="1er kyu", edad=16, peso_kg=62.5,
        color_cinta="Café", tiempo_entrenando="2 años",
        notas="Lesión previa de rodilla derecha; evitar Kiba Dachi prolongado.",
    )

    ficha_alumno = db.obtener_atleta(id_atleta)
    assert ficha_alumno["edad"] == 16
    assert ficha_alumno["peso_kg"] == 62.5
    assert ficha_alumno["color_cinta"] == "Café"
    assert ficha_alumno["tiempo_entrenando"] == "2 años"
    assert "rodilla derecha" in ficha_alumno["notas"]


def test_un_alumno_inexistente_devuelve_none_en_vez_de_reventar(db):
    assert db.obtener_atleta(9999) is None


def test_la_migracion_agrega_la_ficha_a_una_base_que_ya_tenia_alumnos(tmp_path):
    """
    El dojo actualiza el sistema sin perder el historial. Si la migración
    recreara la tabla, los alumnos ya inscritos y sus sesiones desaparecerían.
    """
    import sqlite3

    from persistence.database import Database

    ruta = tmp_path / "vieja.db"
    antigua = sqlite3.connect(ruta)
    antigua.executescript("""
        CREATE TABLE atleta (
            id_atleta        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre           TEXT NOT NULL,
            fecha_nacimiento TEXT,
            grado_cinturon   TEXT,
            fecha_registro   TEXT NOT NULL
        );
        INSERT INTO atleta (nombre, grado_cinturon, fecha_registro)
        VALUES ('Luis Garcia', '7o kyu', '2026-01-10T09:00:00');
    """)
    antigua.commit()
    antigua.close()

    db = Database(str(ruta))
    try:
        alumnos = db.listar_atletas()
        assert len(alumnos) == 1, "la migración no debe perder alumnos ya inscritos"
        assert alumnos[0]["nombre"] == "Luis Garcia"
        assert alumnos[0]["grado_cinturon"] == "7o kyu"
        assert alumnos[0]["edad"] is None, "la columna nueva debe existir y venir vacía"

        # Y la base migrada debe aceptar una ficha completa desde ya.
        nuevo = db.crear_atleta("Ana Lopez", edad=21, color_cinta="Negra")
        assert db.obtener_atleta(nuevo)["edad"] == 21
    finally:
        db.close()


# ---------------- métricas del dojo ----------------

def test_un_dojo_sin_actividad_no_reporta_cero_por_ciento(db):
    """
    Distinción central del panel: cero sesiones es un hecho; cero por ciento de
    precisión sería una afirmación falsa sobre cómo entrena el dojo.
    """
    db.crear_atleta("Marta Similox")

    metricas = db.metricas_dojo()

    assert metricas["sesiones"] == 0
    assert metricas["alumnos_activos"] == 0
    assert metricas["alumnos_inscritos"] == 1
    assert metricas["precision"] is None


@ficha(
    id_caso="TC-AUTO-029",
    nombre="El panel de inicio cuenta la actividad reciente del dojo y descarta la anterior "
           "a la ventana de siete días",
    tipo=TipoPrueba.INTEGRACION,
    prioridad=Prioridad.ALTA,
    justificacion_riesgo="es la primera cifra que el instructor ve al abrir el sistema y la que "
                         "usará para decidir cómo va la semana; si la ventana no filtra, el "
                         "número crece para siempre y deja de significar «actividad reciente», "
                         "convirtiendo el panel en un contador histórico disfrazado",
    componente="persistence/database.py (metricas_dojo)",
    requisitos="RF-07",
    precondiciones="Base de datos limpia con un entrenador y dos alumnos registrados",
    datos_entrada="Tres sesiones fechadas a 1, 3 y 20 días atrás; la de 20 días queda fuera de "
                  "la ventana de siete. Seis evaluaciones cerradas dentro de la ventana, cuatro "
                  "correctas",
    pasos=[
        Paso("Crear las tres sesiones y reescribir su fecha hacia el pasado",
             "assert las tres existen en la tabla `sesion`"),
        Paso("Registrar mediciones cerradas solo en las dos sesiones recientes",
             "assert se guardaron con `correcto` no nulo"),
        Paso("Invocar `metricas_dojo()` con la ventana por defecto",
             "assert metricas['sesiones'] == 2 (la de 20 días no cuenta)"),
        Paso("Comprobar alumnos activos y precisión",
             "assert metricas['alumnos_activos'] == 1 y metricas['precision'] == pytest.approx(66.67)"),
    ],
    resultado_esperado="PASSED. El panel refleja la actividad de los últimos siete días y la "
                       "precisión se calcula solo sobre evaluaciones cerradas de ese periodo.",
    evidencia="Reporte de consola de pytest.",
)
def test_la_ventana_de_actividad_deja_fuera_las_sesiones_viejas(db, id_entrenador):
    entrenador = id_entrenador
    diego = db.crear_atleta("Diego Morales")
    ana = db.crear_atleta("Ana Lopez")

    reciente = _sesion_fechada(db, diego, entrenador, dias_atras=1)
    tambien_reciente = _sesion_fechada(db, diego, entrenador, dias_atras=3)
    vieja = _sesion_fechada(db, ana, entrenador, dias_atras=20)

    for id_sesion, veredictos in [(reciente, [True, True, False]),
                                  (tambien_reciente, [True, True, False])]:
        for i, ok in enumerate(veredictos):
            db.guardar_medicion(id_sesion, "tsuki", 170.0, "TSUKI: EXCELENTE", i * 500, correcto=ok)
    db.guardar_medicion(vieja, "tsuki", 170.0, "TSUKI: EXCELENTE", 0, correcto=True)

    metricas = db.metricas_dojo()

    assert metricas["sesiones"] == 2, "la sesión de hace 20 días está fuera de la ventana"
    assert metricas["alumnos_activos"] == 1, "solo Diego entrenó en la ventana"
    assert metricas["alumnos_inscritos"] == 2, "Ana sigue inscrita aunque no haya entrenado"
    assert metricas["evaluaciones"] == 6
    assert metricas["aciertos"] == 4
    assert metricas["precision"] == pytest.approx(400 / 6)


def test_los_estados_transitorios_no_alteran_las_metricas_del_panel(db, id_entrenador):
    """
    Misma regla que el resto de los agregados: moverse frente a la cámara no es
    fallar. Un diagnóstico sin veredicto no entra en el porcentaje.
    """
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    db.guardar_medicion(id_sesion, "kokutsu_dachi", 160.0, "POSTURA: ESTABLE", 0, correcto=True)
    for i in range(8):
        db.guardar_medicion(id_sesion, "kokutsu_dachi", None, "EN TRANSICION...", i * 100)

    metricas = db.metricas_dojo()

    assert metricas["evaluaciones"] == 1
    assert metricas["precision"] == 100.0


# ---------------- sesiones recientes y técnicas practicadas ----------------

def test_las_sesiones_recientes_abarcan_a_todo_el_dojo(db, id_entrenador):
    """
    A diferencia de `listar_sesiones`, que es de un alumno, esta alimenta la
    vista de conjunto: el instructor quiere ver lo último que pasó en el tatami,
    sea de quien sea.
    """
    entrenador = id_entrenador
    diego = db.crear_atleta("Diego Morales")
    ana = db.crear_atleta("Ana Lopez")

    db.iniciar_sesion(diego, entrenador)
    ultima = db.iniciar_sesion(ana, entrenador)

    recientes = db.sesiones_recientes()

    assert [s["atleta"] for s in recientes] == ["Ana Lopez", "Diego Morales"], \
        "de la más reciente a la más antigua"
    assert recientes[0]["id_sesion"] == ultima


def test_las_sesiones_recientes_respetan_el_limite(db, id_entrenador):
    id_atleta = db.crear_atleta("Diego Morales")
    for _ in range(7):
        db.iniciar_sesion(id_atleta, id_entrenador)

    assert len(db.sesiones_recientes(limite=3)) == 3


def test_sin_sesiones_la_lista_viene_vacia_y_no_falla(db):
    assert db.sesiones_recientes() == []
    assert db.tecnicas_mas_practicadas() == []


def test_las_tecnicas_se_ordenan_por_cuanto_se_practican(db, id_entrenador):
    """
    El orden es por volumen y no por precisión: responde "qué se está
    trabajando", no "qué sale bien". La precisión viaja igual en cada fila,
    para que la pantalla pueda mostrar ambas cosas.
    """
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    for i in range(10):
        db.guardar_medicion(id_sesion, "tsuki", 170.0, "TSUKI: EXCELENTE", i, correcto=True)
    for i in range(4):
        db.guardar_medicion(id_sesion, "mae_geri", 165.0, "MAE GERI: SIN EXPLOSIVIDAD", i,
                            correcto=False)

    practicadas = db.tecnicas_mas_practicadas()

    assert [t["nombre_tecnica"] for t in practicadas] == ["tsuki", "mae_geri"]
    assert practicadas[0]["evaluaciones"] == 10
    assert practicadas[0]["precision"] == 100.0
    assert practicadas[1]["precision"] == 0.0, "cuatro intentos fallidos sí son un 0 % real"


def test_las_tecnicas_practicadas_pueden_acotarse_a_la_ventana_reciente(db, id_entrenador):
    entrenador = id_entrenador
    id_atleta = db.crear_atleta("Diego Morales")

    vieja = _sesion_fechada(db, id_atleta, entrenador, dias_atras=30)
    reciente = _sesion_fechada(db, id_atleta, entrenador, dias_atras=2)
    db.guardar_medicion(vieja, "age_uke", 130.0, "AGE UKE: EFECTIVO", 0, correcto=True)
    db.guardar_medicion(reciente, "tsuki", 170.0, "TSUKI: EXCELENTE", 0, correcto=True)

    assert {t["nombre_tecnica"] for t in db.tecnicas_mas_practicadas()} == {"age_uke", "tsuki"}
    assert [t["nombre_tecnica"] for t in db.tecnicas_mas_practicadas(dias=7)] == ["tsuki"]


# ---------------- señales de riesgo ----------------

def test_el_desempeno_se_separa_por_lado_del_cuerpo(db, id_entrenador):
    """
    El analizador antepone «IZQ - » y «DER - » a cada diagnóstico de brazo. Ese
    prefijo es lo que permite comparar lados sin agregar una columna: la
    información ya estaba guardada, solo no se leía.
    """
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    for i in range(10):
        db.guardar_medicion(id_sesion, "tsuki", 170.0, "IZQ - TSUKI: EXCELENTE", i,
                            correcto=i < 3)          # 30 % izquierdo
    for i in range(10):
        db.guardar_medicion(id_sesion, "tsuki", 170.0, "DER - TSUKI: EXCELENTE", i,
                            correcto=True)           # 100 % derecho

    por_lado = db.desempeno_por_lado(id_sesion)

    assert por_lado["izquierdo"]["evaluaciones"] == 10
    assert por_lado["izquierdo"]["precision"] == 30.0
    assert por_lado["derecho"]["precision"] == 100.0


def test_los_diagnosticos_sin_lado_no_se_atribuyen_a_ninguno(db, id_entrenador):
    """
    Las posturas se evalúan con las dos piernas a la vez y su diagnóstico no
    lleva prefijo. Contarlas en un lado inventaría una asimetría inexistente.
    """
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    for i in range(8):
        db.guardar_medicion(id_sesion, "kokutsu_dachi", 160.0, "POSTURA: ESTABLE", i,
                            correcto=True)

    por_lado = db.desempeno_por_lado(id_sesion)

    assert por_lado["izquierdo"]["evaluaciones"] == 0
    assert por_lado["derecho"]["evaluaciones"] == 0
    assert por_lado["izquierdo"]["precision"] is None


def test_se_cuentan_los_diagnosticos_que_contienen_un_fragmento(db, id_entrenador):
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    for i in range(4):
        db.guardar_medicion(id_sesion, "tsuki", 179.0,
                            "DER - TSUKI: HIPEREXTENDIDO (Peligro)", i, correcto=False)
    for i in range(16):
        db.guardar_medicion(id_sesion, "tsuki", 170.0, "DER - TSUKI: EXCELENTE", i,
                            correcto=True)
    # Un estado transitorio no debe contar en el total: no es una ejecución.
    db.guardar_medicion(id_sesion, "tsuki", None, "EN TRANSICION...", 99)

    conteo = db.contar_diagnosticos(id_sesion, "HIPEREXTENDIDO")

    assert conteo == {"veces": 4, "total": 20}


def test_una_sesion_sin_mediciones_devuelve_ceros_y_no_none(db, id_entrenador):
    """El análisis de riesgo espera números; un None ahí obligaría a comprobarlo en cada uso."""
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

    assert db.contar_diagnosticos(id_sesion, "HIPEREXTENDIDO") == {"veces": 0, "total": 0}
