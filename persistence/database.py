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
                id_umbral         INTEGER,
                FOREIGN KEY (id_sesion) REFERENCES sesion(id_sesion),
                FOREIGN KEY (id_umbral) REFERENCES umbral_referencia(id_umbral)
            );

            -- Umbrales biomecanicos como DATOS y no como constantes de codigo
            -- (RF-08). Recalibrar NO reescribe la fila: se marca la anterior
            -- como no vigente y se inserta una version nueva, de modo que las
            -- mediciones historicas sigan apuntando al umbral que las juzgo.
            CREATE TABLE IF NOT EXISTS umbral_referencia (
                id_umbral          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_tecnica     TEXT NOT NULL,
                articulacion       TEXT NOT NULL,
                valor_min          REAL NOT NULL,
                valor_max          REAL,
                unidad             TEXT NOT NULL DEFAULT 'grados',
                fuente             TEXT NOT NULL DEFAULT 'literatura',
                vigente            INTEGER NOT NULL DEFAULT 1,
                id_entrenador      INTEGER,
                fecha_modificacion TEXT NOT NULL,
                FOREIGN KEY (id_entrenador) REFERENCES entrenador(id_entrenador)
            );

            -- Solo puede haber UN umbral vigente por tecnica y articulacion.
            -- El indice parcial deja convivir las versiones historicas.
            CREATE UNIQUE INDEX IF NOT EXISTS idx_umbral_vigente
                ON umbral_referencia (nombre_tecnica, articulacion)
                WHERE vigente = 1;
        """)
        self._migrar_columnas()
        self.conn.commit()

    # Columnas que se agregaron a 'tecnica_evaluada' despues de que ya existian
    # bases de datos con informacion real. El CREATE TABLE de arriba solo aplica
    # a bases nuevas, y SQLite no soporta "ADD COLUMN IF NOT EXISTS".
    COLUMNAS_MIGRADAS = {
        "correcto": "INTEGER",    # 13-ago-2026
        "id_umbral": "INTEGER",   # 26-ago-2026
    }

    def _migrar_columnas(self):
        """Agrega las columnas que falten, sin tocar los datos existentes."""
        columnas = {fila["name"] for fila in self.conn.execute("PRAGMA table_info(tecnica_evaluada)")}
        for nombre, tipo in self.COLUMNAS_MIGRADAS.items():
            if nombre not in columnas:
                self.conn.execute(f"ALTER TABLE tecnica_evaluada ADD COLUMN {nombre} {tipo}")

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

    def guardar_medicion(self, id_sesion, nombre_tecnica, angulo_promedio, diagnostico, timestamp_ms,
                         correcto=None, id_umbral=None):
        # correcto: True/False si el diagnóstico es una evaluación cerrada
        # (ej. "TSUKI: EXCELENTE"), None si es un estado transitorio sin
        # calificar (ej. "EN TRANSICION...", "MAE GERI: CARGA").
        # id_umbral: version del umbral que emitio este diagnostico. Sin el,
        # recalibrar dejaria el historial sin criterio verificable.
        self.conn.execute(
            "INSERT INTO tecnica_evaluada (id_sesion, nombre_tecnica, timestamp_ms, angulo_promedio, "
            "diagnostico, correcto, id_umbral) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_sesion, nombre_tecnica, timestamp_ms, angulo_promedio, diagnostico,
             None if correcto is None else int(correcto), id_umbral),
        )
        self.conn.commit()

    def consultar_historial(self, id_atleta):
        filas = self.conn.execute(
            """SELECT s.id_sesion, s.fecha, t.nombre_tecnica, t.angulo_promedio, t.diagnostico,
                      t.correcto, t.id_umbral
               FROM sesion s JOIN tecnica_evaluada t ON t.id_sesion = s.id_sesion
               WHERE s.id_atleta = ?
               ORDER BY s.fecha DESC""",
            (id_atleta,),
        ).fetchall()
        return [dict(f) for f in filas]

    # ---------------- Umbrales biomecánicos (RF-08) ----------------

    def sembrar_umbrales(self, por_defecto):
        """
        Carga los umbrales iniciales si aún no existen. Idempotente: al arrancar
        con una base ya sembrada no duplica ni sobrescribe nada, de modo que una
        recalibración hecha por el entrenador sobrevive a reinicios del sistema.

        'por_defecto' llega como parámetro y no se importa desde la base de
        conocimientos: la capa de persistencia no debe depender de la capa de
        inferencia. Formato: {(tecnica, articulacion): (min, max, unidad)}.
        """
        ahora = datetime.now().isoformat()
        nuevos = 0
        for (tecnica, articulacion), (v_min, v_max, unidad) in por_defecto.items():
            existe = self.conn.execute(
                "SELECT 1 FROM umbral_referencia "
                "WHERE nombre_tecnica = ? AND articulacion = ? AND vigente = 1",
                (tecnica, articulacion),
            ).fetchone()
            if existe:
                continue
            self.conn.execute(
                "INSERT INTO umbral_referencia (nombre_tecnica, articulacion, valor_min, valor_max, "
                "unidad, fuente, vigente, fecha_modificacion) VALUES (?, ?, ?, ?, ?, 'literatura', 1, ?)",
                (tecnica, articulacion, v_min, v_max, unidad, ahora),
            )
            nuevos += 1
        self.conn.commit()
        return nuevos

    def cargar_umbrales_vigentes(self):
        """
        Devuelve los umbrales en curso, indexados por (tecnica, articulacion).
        Es lo que la base de conocimientos consulta al arrancar.
        """
        filas = self.conn.execute(
            "SELECT * FROM umbral_referencia WHERE vigente = 1"
        ).fetchall()
        return {(f["nombre_tecnica"], f["articulacion"]): dict(f) for f in filas}

    def actualizar_umbral(self, nombre_tecnica, articulacion, valor_min, valor_max,
                          id_entrenador, fuente="modelado_experto"):
        """
        Recalibra un umbral creando una VERSIÓN NUEVA en vez de sobrescribir la
        anterior. La fila previa se marca como no vigente pero permanece, porque
        las mediciones históricas la referencian por 'id_umbral': sin eso, un
        cambio de criterio rompería en silencio la comparabilidad de los reportes
        de progreso. Devuelve el id de la versión nueva.
        """
        if valor_max is not None and valor_max < valor_min:
            raise ValueError("El valor máximo no puede ser menor que el mínimo")

        anterior = self.conn.execute(
            "SELECT * FROM umbral_referencia "
            "WHERE nombre_tecnica = ? AND articulacion = ? AND vigente = 1",
            (nombre_tecnica, articulacion),
        ).fetchone()
        unidad = anterior["unidad"] if anterior else "grados"

        # Se retira la vigencia ANTES de insertar: el índice parcial único
        # impide que dos versiones de la misma articulación estén vigentes.
        if anterior:
            self.conn.execute(
                "UPDATE umbral_referencia SET vigente = 0 WHERE id_umbral = ?",
                (anterior["id_umbral"],),
            )

        cursor = self.conn.execute(
            "INSERT INTO umbral_referencia (nombre_tecnica, articulacion, valor_min, valor_max, "
            "unidad, fuente, vigente, id_entrenador, fecha_modificacion) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (nombre_tecnica, articulacion, valor_min, valor_max, unidad, fuente,
             id_entrenador, datetime.now().isoformat()),
        )
        self.conn.commit()
        return cursor.lastrowid

    def historial_umbral(self, nombre_tecnica, articulacion):
        """Todas las versiones de un umbral, de la más reciente a la más antigua."""
        filas = self.conn.execute(
            "SELECT * FROM umbral_referencia WHERE nombre_tecnica = ? AND articulacion = ? "
            "ORDER BY id_umbral DESC",
            (nombre_tecnica, articulacion),
        ).fetchall()
        return [dict(f) for f in filas]

    def close(self):
        self.conn.close()
