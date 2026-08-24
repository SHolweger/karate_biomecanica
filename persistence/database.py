import sqlite3
import hashlib
from datetime import datetime


class Database:
    """
    Acceso a la base de datos local del sistema (SQLite, RF-07).
    Un solo archivo, sin servidor: apropiado para un sistema de un solo
    dojo corriendo en un solo equipo (Edge Computing, ver RNF-02).
    """

    def __init__(self, db_path="karate_sistema.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre, ej. fila["nombre"]
        self._crear_tablas()

    def _crear_tablas(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS entrenador (
                id_entrenador   INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre          TEXT NOT NULL,
                usuario         TEXT NOT NULL UNIQUE,
                correo          TEXT,
                password_hash   TEXT NOT NULL,
                rol             TEXT NOT NULL DEFAULT 'sensei',
                fecha_registro  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS atleta (
                id_atleta         INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre            TEXT NOT NULL,
                fecha_nacimiento  TEXT,
                grado_cinturon    TEXT,
                fecha_registro    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sesion (
                id_sesion       INTEGER PRIMARY KEY AUTOINCREMENT,
                id_atleta       INTEGER NOT NULL,
                id_entrenador   INTEGER NOT NULL,
                fecha           TEXT NOT NULL,
                hora_inicio     TEXT NOT NULL,
                hora_fin        TEXT,
                FOREIGN KEY (id_atleta) REFERENCES atleta(id_atleta),
                FOREIGN KEY (id_entrenador) REFERENCES entrenador(id_entrenador)
            );

            CREATE TABLE IF NOT EXISTS tecnica_evaluada (
                id_medicion       INTEGER PRIMARY KEY AUTOINCREMENT,
                id_sesion         INTEGER NOT NULL,
                nombre_tecnica    TEXT NOT NULL,
                timestamp_ms      INTEGER NOT NULL,
                angulo_promedio   REAL,
                diagnostico       TEXT NOT NULL,
                correcto          INTEGER,
                FOREIGN KEY (id_sesion) REFERENCES sesion(id_sesion)
            );
        """)
        self._migrar_columna_correcto()
        self.conn.commit()

    def _migrar_columna_correcto(self):
        """
        Agrega la columna 'correcto' a bases de datos creadas antes del
        13-ago-2026 (no la tenían). SQLite no soporta "ADD COLUMN IF NOT
        EXISTS", así que se verifica manualmente antes de intentarlo —
        el CREATE TABLE de arriba solo aplica a bases de datos nuevas.
        """
        columnas = [fila["name"] for fila in self.conn.execute("PRAGMA table_info(tecnica_evaluada)")]
        if "correcto" not in columnas:
            self.conn.execute("ALTER TABLE tecnica_evaluada ADD COLUMN correcto INTEGER")

    @staticmethod
    def _hash_password(password):
        # Cifrado básico (RNF-05): suficiente para un prototipo de un solo
        # dojo en un equipo local, no es un esquema de seguridad bancario.
        return hashlib.sha256(password.encode()).hexdigest()

    # ---------------- Entrenadores (autenticación, RF-08) ----------------

    def existe_algun_entrenador(self):
        fila = self.conn.execute("SELECT COUNT(*) AS n FROM entrenador").fetchone()
        return fila["n"] > 0

    def crear_entrenador(self, nombre, usuario, correo, password, rol="sensei"):
        cursor = self.conn.execute(
            "INSERT INTO entrenador (nombre, usuario, correo, password_hash, rol, fecha_registro) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, usuario, correo, self._hash_password(password), rol, datetime.now().isoformat()),
        )
        self.conn.commit()
        return cursor.lastrowid

    def autenticar_entrenador(self, usuario, password):
        """Devuelve el entrenador (dict) si usuario/password son correctos, o None."""
        fila = self.conn.execute(
            "SELECT * FROM entrenador WHERE usuario = ?", (usuario,)
        ).fetchone()
        if fila is None or fila["password_hash"] != self._hash_password(password):
            return None
        return dict(fila)

    # ---------------- Atletas (perfiles, estilo Netflix) ----------------

    def listar_atletas(self):
        filas = self.conn.execute("SELECT * FROM atleta ORDER BY nombre").fetchall()
        return [dict(f) for f in filas]

    def crear_atleta(self, nombre, fecha_nacimiento=None, grado_cinturon=None):
        cursor = self.conn.execute(
            "INSERT INTO atleta (nombre, fecha_nacimiento, grado_cinturon, fecha_registro) "
            "VALUES (?, ?, ?, ?)",
            (nombre, fecha_nacimiento, grado_cinturon, datetime.now().isoformat()),
        )
        self.conn.commit()
        return cursor.lastrowid

    # ---------------- Sesiones de entrenamiento ----------------

    def iniciar_sesion(self, id_atleta, id_entrenador):
        ahora = datetime.now()
        cursor = self.conn.execute(
            "INSERT INTO sesion (id_atleta, id_entrenador, fecha, hora_inicio) VALUES (?, ?, ?, ?)",
            (id_atleta, id_entrenador, ahora.date().isoformat(), ahora.isoformat()),
        )
        self.conn.commit()
        return cursor.lastrowid

    def cerrar_sesion(self, id_sesion):
        self.conn.execute(
            "UPDATE sesion SET hora_fin = ? WHERE id_sesion = ?",
            (datetime.now().isoformat(), id_sesion),
        )
        self.conn.commit()

    # ---------------- Mediciones de técnicas ----------------

    def guardar_medicion(self, id_sesion, nombre_tecnica, angulo_promedio, diagnostico, timestamp_ms, correcto=None):
        # correcto: True/False si el diagnóstico es una evaluación cerrada
        # (ej. "TSUKI: EXCELENTE"), None si es un estado transitorio sin
        # calificar (ej. "EN TRANSICION...", "MAE GERI: CARGA").
        self.conn.execute(
            "INSERT INTO tecnica_evaluada (id_sesion, nombre_tecnica, timestamp_ms, angulo_promedio, diagnostico, correcto) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_sesion, nombre_tecnica, timestamp_ms, angulo_promedio, diagnostico,
             None if correcto is None else int(correcto)),
        )
        self.conn.commit()

    def consultar_historial(self, id_atleta):
        filas = self.conn.execute(
            """SELECT s.id_sesion, s.fecha, t.nombre_tecnica, t.angulo_promedio, t.diagnostico, t.correcto
               FROM sesion s JOIN tecnica_evaluada t ON t.id_sesion = s.id_sesion
               WHERE s.id_atleta = ?
               ORDER BY s.fecha DESC""",
            (id_atleta,),
        ).fetchall()
        return [dict(f) for f in filas]

    def close(self):
        self.conn.close()
