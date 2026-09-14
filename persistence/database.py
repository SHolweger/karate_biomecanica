import sqlite3
import hashlib
from datetime import datetime, timedelta


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
                fecha_registro    TEXT NOT NULL,
                -- Ficha del alumno tal como la lleva el sensei. La edad se guarda
                -- como el numero que el instructor conoce y no como fecha de
                -- nacimiento, que en el dojo rara vez esta a mano; `fecha_registro`
                -- deja constancia de cuando se anoto, que es lo que la vuelve
                -- interpretable mas adelante.
                edad              INTEGER,
                peso_kg           REAL,
                color_cinta       TEXT,
                tiempo_entrenando TEXT,
                notas             TEXT
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

            -- Preferencias del equipo donde corre el sistema (fuente de video,
            -- por ejemplo). Van en la base y no en un archivo de configuracion
            -- aparte porque el sistema ya es local por diseno (RNF-02) y asi
            -- todo el estado del dojo vive en un solo archivo respaldable.
            CREATE TABLE IF NOT EXISTS configuracion (
                clave  TEXT PRIMARY KEY,
                valor  TEXT
            );
        """)
        self._migrar_columnas()
        self.conn.commit()

    # Columnas que se agregaron despues de que ya existian bases de datos con
    # informacion real. El CREATE TABLE de arriba solo aplica a bases nuevas, y
    # SQLite no soporta "ADD COLUMN IF NOT EXISTS".
    #
    # Migrar en vez de recrear la tabla es lo que permite que el dojo actualice
    # el sistema sin perder el historial de entrenamiento ya registrado.
    COLUMNAS_MIGRADAS = {
        "tecnica_evaluada": {
            "correcto": "INTEGER",          # 13-ago-2026
            "id_umbral": "INTEGER",         # 26-ago-2026
        },
        "atleta": {
            "edad": "INTEGER",              # 14-sep-2026, ficha del alumno
            "peso_kg": "REAL",
            "color_cinta": "TEXT",
            "tiempo_entrenando": "TEXT",
            "notas": "TEXT",
        },
    }

    def _migrar_columnas(self):
        """Agrega las columnas que falten, sin tocar los datos existentes."""
        for tabla, columnas_esperadas in self.COLUMNAS_MIGRADAS.items():
            presentes = {fila["name"] for fila in self.conn.execute(f"PRAGMA table_info({tabla})")}
            for nombre, tipo in columnas_esperadas.items():
                if nombre not in presentes:
                    self.conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}")

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

    def listar_entrenadores(self):
        """
        Senseis registrados, para el selector de perfil.

        Nunca devuelve `password_hash`: la pantalla que muestra esta lista no
        necesita el hash para nada, y no sacarlo de la capa de datos evita que
        termine, por descuido, en un widget o en un registro de depuracion.
        """
        filas = self.conn.execute(
            "SELECT id_entrenador, nombre, usuario, correo, rol, fecha_registro "
            "FROM entrenador ORDER BY nombre"
        ).fetchall()
        return [dict(f) for f in filas]

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

    def crear_atleta(self, nombre, fecha_nacimiento=None, grado_cinturon=None,
                     edad=None, peso_kg=None, color_cinta=None,
                     tiempo_entrenando=None, notas=None):
        """
        Inscribe a un alumno. Solo el nombre es obligatorio.

        Todo lo demas es opcional a proposito: en el dojo un alumno se apunta el
        primer dia y los datos se completan despues. Exigir peso o grado para
        poder medir a alguien pondria un tramite delante del entrenamiento.
        """
        cursor = self.conn.execute(
            "INSERT INTO atleta (nombre, fecha_nacimiento, grado_cinturon, fecha_registro, "
            "edad, peso_kg, color_cinta, tiempo_entrenando, notas) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nombre, fecha_nacimiento, grado_cinturon, datetime.now().isoformat(),
             edad, peso_kg, color_cinta, tiempo_entrenando, notas),
        )
        self.conn.commit()
        return cursor.lastrowid

    def obtener_atleta(self, id_atleta):
        """Ficha completa de un alumno, o None si no existe."""
        fila = self.conn.execute(
            "SELECT * FROM atleta WHERE id_atleta = ?", (id_atleta,)
        ).fetchone()
        return None if fila is None else dict(fila)

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

    def corregir_umbrales_de_literatura(self, correcciones):
        """
        Aplica una corrección bibliográfica a umbrales que nadie recalibró.

        `sembrar_umbrales` es idempotente y no toca lo ya existente, que es lo
        correcto para no pisar el trabajo del entrenador — pero significa que
        corregir un valor equivocado en el código no llega a las bases que ya
        estaban sembradas. Este método cubre ese caso.

        Solo se corrige un umbral cuya fuente vigente siga siendo 'literatura':
        si un instructor ya lo ajustó con su criterio ('modelado_experto'), su
        decisión manda sobre la del libro y no se toca. La corrección crea una
        versión nueva, de modo que las mediciones anteriores conservan el umbral
        con el que fueron evaluadas.

        Formato de 'correcciones': {(tecnica, articulacion): (min, max)}.
        Devuelve la lista de claves efectivamente corregidas.
        """
        corregidos = []
        for (tecnica, articulacion), (v_min, v_max) in correcciones.items():
            fila = self.conn.execute(
                "SELECT * FROM umbral_referencia "
                "WHERE nombre_tecnica = ? AND articulacion = ? AND vigente = 1",
                (tecnica, articulacion),
            ).fetchone()

            if fila is None or fila["fuente"] != "literatura":
                continue
            if (fila["valor_min"], fila["valor_max"]) == (v_min, v_max):
                continue  # ya está corregido; no se versiona por gusto

            self.actualizar_umbral(tecnica, articulacion, v_min, v_max,
                                   id_entrenador=None, fuente="literatura")
            corregidos.append((tecnica, articulacion))

        return corregidos

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

    # ---------------- Consultas agregadas para los reportes ----------------
    #
    # Viven aquí y no en la capa de presentación por una razón concreta: son la
    # respuesta a preguntas del dojo ("¿cómo viene este alumno?", "¿qué técnica
    # se le dificulta?"), no detalles de cómo se dibuja una pantalla. Calcularlas
    # en SQL además evita traer a memoria miles de mediciones para promediarlas
    # en Python.
    #
    # Regla común a todas: solo cuentan las evaluaciones CERRADAS. Un diagnóstico
    # con `correcto` nulo es un estado transitorio ("EN TRANSICION", "MAE GERI:
    # CARGA") o una articulación no visible; incluirlos hundiría el porcentaje
    # de un alumno por el simple hecho de haberse movido frente a la cámara.

    def resumen_atletas(self):
        """
        Un renglón por atleta con lo que el sensei necesita ver de un vistazo:
        cuántas sesiones lleva, cuándo entrenó por última vez, cuántas técnicas
        se le evaluaron y qué porcentaje resultó correcto.

        Incluye a los atletas que aún no tienen mediciones, con precisión None:
        un alumno recién inscrito debe aparecer en la lista, no desaparecer.
        """
        filas = self.conn.execute("""
            SELECT a.id_atleta,
                   a.nombre,
                   a.grado_cinturon,
                   COUNT(DISTINCT s.id_sesion)                      AS sesiones,
                   MAX(s.fecha)                                     AS ultima_fecha,
                   COUNT(t.id_medicion)                             AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM atleta a
            LEFT JOIN sesion s ON s.id_atleta = a.id_atleta
            LEFT JOIN tecnica_evaluada t
                   ON t.id_sesion = s.id_sesion AND t.correcto IS NOT NULL
            GROUP BY a.id_atleta
            ORDER BY a.nombre
        """).fetchall()
        return [self._con_precision(dict(f)) for f in filas]

    def listar_sesiones(self, id_atleta):
        """Sesiones de un atleta, de la más reciente a la más antigua."""
        filas = self.conn.execute("""
            SELECT s.id_sesion,
                   s.fecha,
                   s.hora_inicio,
                   s.hora_fin,
                   e.nombre                                         AS entrenador,
                   COUNT(t.id_medicion)                             AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM sesion s
            LEFT JOIN entrenador e ON e.id_entrenador = s.id_entrenador
            LEFT JOIN tecnica_evaluada t
                   ON t.id_sesion = s.id_sesion AND t.correcto IS NOT NULL
            WHERE s.id_atleta = ?
            GROUP BY s.id_sesion
            ORDER BY s.id_sesion DESC
        """, (id_atleta,)).fetchall()
        return [self._con_precision(dict(f)) for f in filas]

    def resumen_por_tecnica(self, id_atleta, id_sesion=None):
        """
        Desempeño por técnica, de la más floja a la más sólida — que es el
        orden en que un instructor quiere leerlo: primero lo que hay que
        corregir. Con `id_sesion` se acota a una sola sesión.
        """
        condicion = "s.id_atleta = ?"
        parametros = [id_atleta]
        if id_sesion is not None:
            condicion += " AND s.id_sesion = ?"
            parametros.append(id_sesion)

        filas = self.conn.execute(f"""
            SELECT t.nombre_tecnica,
                   COUNT(*)                                         AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos,
                   AVG(t.angulo_promedio)                           AS angulo_medio
            FROM tecnica_evaluada t
            JOIN sesion s ON s.id_sesion = t.id_sesion
            WHERE {condicion} AND t.correcto IS NOT NULL
            GROUP BY t.nombre_tecnica
        """, parametros).fetchall()

        resumen = [self._con_precision(dict(f)) for f in filas]
        return sorted(resumen, key=lambda r: r["precision"])

    def detalle_sesion(self, id_sesion):
        """
        Cabecera de una sesión: atleta, entrenador, fecha y su precisión global.
        Devuelve None si la sesión no existe.
        """
        fila = self.conn.execute("""
            SELECT s.id_sesion, s.fecha, s.hora_inicio, s.hora_fin,
                   a.id_atleta, a.nombre AS atleta, a.grado_cinturon,
                   e.nombre AS entrenador,
                   COUNT(t.id_medicion)                             AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM sesion s
            JOIN atleta a ON a.id_atleta = s.id_atleta
            LEFT JOIN entrenador e ON e.id_entrenador = s.id_entrenador
            LEFT JOIN tecnica_evaluada t
                   ON t.id_sesion = s.id_sesion AND t.correcto IS NOT NULL
            WHERE s.id_sesion = ?
            GROUP BY s.id_sesion
        """, (id_sesion,)).fetchone()

        return None if fila is None or fila["id_sesion"] is None else self._con_precision(dict(fila))

    def errores_frecuentes(self, id_sesion, limite=6):
        """
        Los diagnósticos incorrectos más repetidos de una sesión.

        Es lo que convierte un porcentaje en una corrección accionable: saber
        que el alumno acertó el 60 % no dice qué practicar; saber que falló
        catorce veces por hiperextender el codo, sí.
        """
        filas = self.conn.execute("""
            SELECT t.nombre_tecnica, t.diagnostico,
                   COUNT(*)               AS veces,
                   AVG(t.angulo_promedio) AS angulo_medio
            FROM tecnica_evaluada t
            WHERE t.id_sesion = ? AND t.correcto = 0
            GROUP BY t.nombre_tecnica, t.diagnostico
            ORDER BY veces DESC
            LIMIT ?
        """, (id_sesion, limite)).fetchall()
        return [dict(f) for f in filas]

    # ---------------- Consultas del panel de inicio ----------------

    # Ventana de actividad del dojo. Siete dias y no "la semana calendario"
    # porque un lunes por la manana la semana calendario esta casi vacia y el
    # panel diria que el dojo no entrena, cuando lo que pasa es que el corte
    # acaba de ocurrir.
    DIAS_ACTIVIDAD = 7

    def metricas_dojo(self, dias=DIAS_ACTIVIDAD):
        """
        Las cifras de cabecera del panel: cuanto se entreno en la ventana
        reciente y con que precision.

        `alumnos_activos` cuenta a quienes efectivamente entrenaron en esos
        dias, no a los inscritos: son preguntas distintas y confundirlas haria
        que el numero nunca bajara aunque el dojo se vaciara.
        """
        corte = self._fecha_corte(dias)
        fila = self.conn.execute("""
            SELECT COUNT(DISTINCT s.id_sesion)                      AS sesiones,
                   COUNT(DISTINCT s.id_atleta)                      AS alumnos_activos,
                   COUNT(t.id_medicion)                             AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM sesion s
            LEFT JOIN tecnica_evaluada t
                   ON t.id_sesion = s.id_sesion AND t.correcto IS NOT NULL
            WHERE s.fecha >= ?
        """, (corte,)).fetchone()

        metricas = self._con_precision(dict(fila))
        metricas["dias"] = dias
        metricas["alumnos_inscritos"] = self.conn.execute(
            "SELECT COUNT(*) AS n FROM atleta").fetchone()["n"]
        return metricas

    def sesiones_recientes(self, limite=5):
        """Ultimas sesiones del dojo completo, sin importar de que alumno."""
        filas = self.conn.execute("""
            SELECT s.id_sesion, s.fecha, s.hora_inicio, s.hora_fin,
                   a.id_atleta, a.nombre AS atleta, a.grado_cinturon, a.color_cinta,
                   COUNT(t.id_medicion)                             AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM sesion s
            JOIN atleta a ON a.id_atleta = s.id_atleta
            LEFT JOIN tecnica_evaluada t
                   ON t.id_sesion = s.id_sesion AND t.correcto IS NOT NULL
            GROUP BY s.id_sesion
            ORDER BY s.id_sesion DESC
            LIMIT ?
        """, (limite,)).fetchall()
        return [self._con_precision(dict(f)) for f in filas]

    def tecnicas_mas_practicadas(self, limite=6, dias=None):
        """
        Que se esta trabajando en el dojo, por volumen de evaluaciones.

        Sin `dias` abarca todo el historial. El orden es por cantidad y no por
        precision a proposito: responde "que se practica", no "que sale bien".
        """
        condicion = "t.correcto IS NOT NULL"
        parametros = []
        if dias is not None:
            condicion += " AND s.fecha >= ?"
            parametros.append(self._fecha_corte(dias))
        parametros.append(limite)

        filas = self.conn.execute(f"""
            SELECT t.nombre_tecnica,
                   COUNT(*)                                         AS evaluaciones,
                   SUM(CASE WHEN t.correcto = 1 THEN 1 ELSE 0 END)  AS aciertos
            FROM tecnica_evaluada t
            JOIN sesion s ON s.id_sesion = t.id_sesion
            WHERE {condicion}
            GROUP BY t.nombre_tecnica
            ORDER BY evaluaciones DESC
            LIMIT ?
        """, parametros).fetchall()
        return [self._con_precision(dict(f)) for f in filas]

    @staticmethod
    def _fecha_corte(dias):
        """Fecha ISO de hace `dias`, para comparar con `sesion.fecha`."""
        return (datetime.now() - timedelta(days=dias)).date().isoformat()

    @staticmethod
    def _con_precision(fila):
        """
        Agrega el porcentaje de acierto a partir de `evaluaciones` y `aciertos`.

        Sin evaluaciones cerradas la precisión es None, no 0: un alumno que
        todavía no ha sido medido no tiene un 0 % de acierto, tiene un dato
        inexistente, y mostrarlo como cero sería una afirmación falsa.
        """
        total = fila.get("evaluaciones") or 0
        aciertos = fila.get("aciertos") or 0
        fila["evaluaciones"] = total
        fila["aciertos"] = aciertos
        fila["precision"] = None if total == 0 else aciertos / total * 100
        return fila

    # ---------------- Configuración del equipo ----------------

    def leer_config(self, clave, por_defecto=None):
        """Valor guardado para 'clave', o 'por_defecto' si nunca se configuró."""
        fila = self.conn.execute(
            "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
        ).fetchone()
        return por_defecto if fila is None else fila["valor"]

    def guardar_config(self, clave, valor):
        """Escribe o reemplaza una preferencia. El valor se guarda como texto."""
        self.conn.execute(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, None if valor is None else str(valor)),
        )
        self.conn.commit()

    # ---------------- Umbrales: historial ----------------

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
