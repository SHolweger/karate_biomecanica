"""
Pruebas de integración de persistence/database.py (SQLite).

Se ejecutan contra una base de datos real creada en un archivo temporal por
prueba (no contra un doble): interesa verificar el esquema, las claves
foráneas, el hash de contraseñas y la migración, cosas que un mock ocultaría.
"""
import hashlib
import sqlite3

import pytest

from persistence.database import Database

pytestmark = pytest.mark.integracion


# --------------------------------------------------------------------------
# Autenticación de entrenadores (RF-08)
# --------------------------------------------------------------------------

def test_primer_arranque_no_tiene_entrenadores(db):
    """Estado inicial: el sistema debe ofrecer crear la primera cuenta."""
    assert db.existe_algun_entrenador() is False


def test_registro_y_autenticacion_exitosa(db):
    db.crear_entrenador("Sebastian Holweger", "sholweger", "sholweger@dojo.gt", "clave123",
                        rol="principal")

    entrenador = db.autenticar_entrenador("sholweger", "clave123")

    assert db.existe_algun_entrenador() is True
    assert entrenador is not None
    assert entrenador["nombre"] == "Sebastian Holweger"
    assert entrenador["rol"] == "principal"


@pytest.mark.parametrize("usuario, password, motivo", [
    ("sholweger", "clave_incorrecta", "contraseña equivocada"),
    ("usuario_inexistente", "clave123", "usuario que no existe"),
    ("SHOLWEGER", "clave123", "usuario con distinta capitalización"),
    ("", "", "credenciales vacías"),
])
def test_credenciales_invalidas_no_dan_acceso(db, usuario, password, motivo):
    """Control de acceso: cualquier credencial que no coincida exactamente devuelve None."""
    db.crear_entrenador("Sebastian Holweger", "sholweger", "s@dojo.gt", "clave123")

    assert db.autenticar_entrenador(usuario, password) is None, f"dio acceso con {motivo}"


def test_la_contrasena_nunca_se_guarda_en_texto_plano(db):
    """
    RNF-05: en la tabla debe quedar el hash SHA-256, no la contraseña. Se
    consulta la fila cruda para comprobarlo, no la API que ya la oculta.
    """
    db.crear_entrenador("Sensei", "sensei", "s@dojo.gt", "MiClaveSecreta")

    fila = db.conn.execute("SELECT password_hash FROM entrenador WHERE usuario = 'sensei'").fetchone()

    assert fila["password_hash"] != "MiClaveSecreta"
    assert fila["password_hash"] == hashlib.sha256("MiClaveSecreta".encode()).hexdigest()
    assert len(fila["password_hash"]) == 64


def test_no_se_permiten_dos_entrenadores_con_el_mismo_usuario(db):
    """La restricción UNIQUE del esquema debe impedir usuarios duplicados."""
    db.crear_entrenador("Sensei Uno", "sensei", "uno@dojo.gt", "clave1")

    with pytest.raises(sqlite3.IntegrityError):
        db.crear_entrenador("Sensei Dos", "sensei", "dos@dojo.gt", "clave2")


def test_el_rol_por_defecto_es_sensei(db):
    db.crear_entrenador("Asistente", "asistente", "a@dojo.gt", "clave")

    assert db.autenticar_entrenador("asistente", "clave")["rol"] == "sensei"


# --------------------------------------------------------------------------
# Perfiles de atleta
# --------------------------------------------------------------------------

def test_los_atletas_se_listan_alfabeticamente(db):
    """La pantalla de perfiles muestra la lista ordenada por nombre."""
    for nombre in ("Diego Morales", "Ana Castillo", "Bruno Perez"):
        db.crear_atleta(nombre)

    nombres = [a["nombre"] for a in db.listar_atletas()]

    assert nombres == ["Ana Castillo", "Bruno Perez", "Diego Morales"]


def test_crear_atleta_devuelve_un_identificador_utilizable(db):
    id_atleta = db.crear_atleta("Ana Castillo", grado_cinturon="3er kyu")

    atleta = next(a for a in db.listar_atletas() if a["id_atleta"] == id_atleta)

    assert atleta["grado_cinturon"] == "3er kyu"
    assert atleta["fecha_registro"], "debe quedar registrada la fecha de alta"


def test_los_datos_opcionales_del_atleta_pueden_omitirse(db):
    """El sensei puede dar de alta a un alumno con solo el nombre."""
    id_atleta = db.crear_atleta("Alumno Nuevo")

    atleta = next(a for a in db.listar_atletas() if a["id_atleta"] == id_atleta)

    assert atleta["grado_cinturon"] is None
    assert atleta["fecha_nacimiento"] is None


# --------------------------------------------------------------------------
# Sesiones de entrenamiento
# --------------------------------------------------------------------------

def test_una_sesion_abierta_no_tiene_hora_de_fin(sesion_de_prueba):
    db, id_sesion, _, _ = sesion_de_prueba

    fila = db.conn.execute("SELECT * FROM sesion WHERE id_sesion = ?", (id_sesion,)).fetchone()

    assert fila["hora_inicio"] is not None
    assert fila["hora_fin"] is None


def test_cerrar_sesion_registra_la_hora_de_fin(sesion_de_prueba):
    """Permite calcular después la duración real del entrenamiento."""
    db, id_sesion, _, _ = sesion_de_prueba

    db.cerrar_sesion(id_sesion)

    fila = db.conn.execute("SELECT hora_fin FROM sesion WHERE id_sesion = ?", (id_sesion,)).fetchone()
    assert fila["hora_fin"] is not None


def test_la_sesion_queda_ligada_al_atleta_y_al_entrenador(sesion_de_prueba):
    """Trazabilidad: cada medición debe poder atribuirse a quién entrenó y con quién."""
    db, id_sesion, id_atleta, id_entrenador = sesion_de_prueba

    fila = db.conn.execute("SELECT * FROM sesion WHERE id_sesion = ?", (id_sesion,)).fetchone()

    assert fila["id_atleta"] == id_atleta
    assert fila["id_entrenador"] == id_entrenador


# --------------------------------------------------------------------------
# Mediciones e historial
# --------------------------------------------------------------------------

def test_guardar_y_recuperar_una_medicion(sesion_de_prueba):
    db, id_sesion, id_atleta, _ = sesion_de_prueba

    db.guardar_medicion(id_sesion, "Tsuki (brazo derecho)", 171.5, "TSUKI: EXCELENTE",
                        timestamp_ms=1500, correcto=True)

    historial = db.consultar_historial(id_atleta)
    assert len(historial) == 1
    assert historial[0]["nombre_tecnica"] == "Tsuki (brazo derecho)"
    assert historial[0]["angulo_promedio"] == pytest.approx(171.5)
    assert historial[0]["diagnostico"] == "TSUKI: EXCELENTE"


@pytest.mark.parametrize("correcto, almacenado", [(True, 1), (False, 0), (None, None)])
def test_el_veredicto_se_persiste_en_los_tres_estados(sesion_de_prueba, correcto, almacenado):
    """
    'correcto' es ternario a propósito: True/False son evaluaciones cerradas y
    None marca estados transitorios ("EN TRANSICION", "CARGA") que no deben
    contar como acierto ni como error en las estadísticas de progreso.
    """
    db, id_sesion, id_atleta, _ = sesion_de_prueba

    db.guardar_medicion(id_sesion, "Postura de piernas", 120.0, "diagnostico", 0, correcto=correcto)

    fila = db.conn.execute("SELECT correcto FROM tecnica_evaluada").fetchone()
    assert fila["correcto"] == almacenado


def test_el_historial_solo_devuelve_las_mediciones_del_atleta_consultado(db):
    """Aislamiento entre alumnos: el progreso de uno no puede filtrarse al de otro."""
    id_entrenador = db.crear_entrenador("Sensei", "sensei", "s@dojo.gt", "clave")
    id_ana = db.crear_atleta("Ana")
    id_bruno = db.crear_atleta("Bruno")

    sesion_ana = db.iniciar_sesion(id_ana, id_entrenador)
    sesion_bruno = db.iniciar_sesion(id_bruno, id_entrenador)
    db.guardar_medicion(sesion_ana, "Tsuki (brazo derecho)", 170.0, "TSUKI: EXCELENTE", 0, True)
    db.guardar_medicion(sesion_bruno, "Postura de piernas", 100.0, "POSTURA: FIRME", 0, True)

    historial_ana = db.consultar_historial(id_ana)

    assert len(historial_ana) == 1
    assert historial_ana[0]["nombre_tecnica"] == "Tsuki (brazo derecho)"


def test_un_atleta_sin_entrenamientos_tiene_historial_vacio(db):
    id_atleta = db.crear_atleta("Alumno Nuevo")

    assert db.consultar_historial(id_atleta) == []


def test_las_mediciones_sobreviven_al_cierre_de_la_aplicacion(ruta_db_temporal):
    """
    Persistencia real: se cierra la conexión y se reabre el archivo, igual que
    cuando el sensei cierra el programa y lo vuelve a abrir al día siguiente.
    """
    primera = Database(ruta_db_temporal)
    id_entrenador = primera.crear_entrenador("Sensei", "sensei", "s@dojo.gt", "clave")
    id_atleta = primera.crear_atleta("Ana")
    id_sesion = primera.iniciar_sesion(id_atleta, id_entrenador)
    primera.guardar_medicion(id_sesion, "Mae Geri (pierna izquierda)", 168.0,
                             "MAE GERI: KIME EXCELENTE", 900, True)
    primera.cerrar_sesion(id_sesion)
    primera.close()

    segunda = Database(ruta_db_temporal)
    try:
        historial = segunda.consultar_historial(id_atleta)
        assert len(historial) == 1
        assert historial[0]["diagnostico"] == "MAE GERI: KIME EXCELENTE"
        assert segunda.autenticar_entrenador("sensei", "clave") is not None
    finally:
        segunda.close()


# --------------------------------------------------------------------------
# Compatibilidad con bases de datos anteriores
# --------------------------------------------------------------------------

def test_migra_una_base_de_datos_creada_sin_la_columna_correcto(ruta_db_temporal):
    """
    Las bases anteriores a agosto de 2026 no tienen la columna 'correcto'.
    Abrirlas debe agregarla automáticamente y conservar los datos, sin que el
    sensei pierda el historial de sus alumnos.
    """
    antigua = sqlite3.connect(ruta_db_temporal)
    antigua.executescript("""
        CREATE TABLE tecnica_evaluada (
            id_medicion     INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sesion       INTEGER NOT NULL,
            nombre_tecnica  TEXT NOT NULL,
            timestamp_ms    INTEGER NOT NULL,
            angulo_promedio REAL,
            diagnostico     TEXT NOT NULL
        );
        INSERT INTO tecnica_evaluada (id_sesion, nombre_tecnica, timestamp_ms, angulo_promedio, diagnostico)
        VALUES (1, 'Tsuki (brazo derecho)', 500, 170.0, 'TSUKI: EXCELENTE');
    """)
    antigua.commit()
    antigua.close()

    migrada = Database(ruta_db_temporal)
    try:
        columnas = [f["name"] for f in migrada.conn.execute("PRAGMA table_info(tecnica_evaluada)")]
        fila = migrada.conn.execute("SELECT * FROM tecnica_evaluada").fetchone()

        assert "correcto" in columnas, "la migracion no agrego la columna"
        assert fila["diagnostico"] == "TSUKI: EXCELENTE", "la migracion perdio datos historicos"
        assert fila["correcto"] is None, "las filas antiguas quedan sin veredicto, no en False"
    finally:
        migrada.close()


def test_abrir_dos_veces_la_misma_base_no_duplica_el_esquema(ruta_db_temporal):
    """CREATE TABLE IF NOT EXISTS: reabrir la base no debe fallar ni borrar nada."""
    primera = Database(ruta_db_temporal)
    primera.crear_atleta("Ana")
    primera.close()

    segunda = Database(ruta_db_temporal)
    try:
        assert len(segunda.listar_atletas()) == 1
    finally:
        segunda.close()
