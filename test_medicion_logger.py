"""
test_medicion_logger.py — Verificación de MedicionLogger sin cámara.

Comprueba la regla central: solo se guarda en la base de datos cuando el
mensaje de una categoría CAMBIA respecto al anterior, no en cada frame.

Uso:
    ./venv/bin/python test_medicion_logger.py
"""
import os
import tempfile

from persistence.database import Database
from persistence.medicion_logger import MedicionLogger


def _sesion_temporal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    db = Database(path)
    id_entrenador = db.crear_entrenador("Sensei", "sensei", "s@dojo.com", "clave", rol="principal")
    id_atleta = db.crear_atleta("Diego Morales")
    id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)
    return db, path, id_sesion


def test_no_duplica_el_mismo_mensaje():
    """30 frames seguidos con el mismo mensaje deben producir 1 sola fila, no 30."""
    db, path, id_sesion = _sesion_temporal()
    try:
        logger = MedicionLogger(db, id_sesion)
        diagnostico = [{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE",
                         "angulo": 172.0, "color": (0, 255, 0)}]

        for t in range(30):
            logger.registrar(diagnostico, timestamp_ms=t * 33)

        filas = db.conn.execute(
            "SELECT COUNT(*) AS n FROM tecnica_evaluada WHERE id_sesion = ?", (id_sesion,)
        ).fetchone()
        assert filas["n"] == 1, f"esperaba 1 fila (sin duplicados), obtuve {filas['n']}"
    finally:
        db.close()
        os.remove(path)


def test_guarda_cuando_el_mensaje_cambia():
    """Si el mensaje cambia varias veces, cada cambio real debe generar una fila nueva."""
    db, path, id_sesion = _sesion_temporal()
    try:
        logger = MedicionLogger(db, id_sesion)
        secuencia = [
            "IZQ - TSUKI: FLEXIONADO",
            "IZQ - TSUKI: FLEXIONADO",  # repetido, no debe duplicar
            "IZQ - TSUKI: EXCELENTE",   # cambio real
            "IZQ - TSUKI: EXCELENTE",   # repetido
            "IZQ - TSUKI: HIPEREXTENDIDO (Peligro)",  # cambio real
        ]
        for t, msg in enumerate(secuencia):
            logger.registrar([{"categoria": "codo_izq", "mensaje": msg, "angulo": 170.0,
                                "color": (0, 255, 0)}], timestamp_ms=t * 33)

        historial = db.consultar_historial(
            db.conn.execute("SELECT id_atleta FROM sesion WHERE id_sesion = ?", (id_sesion,)).fetchone()["id_atleta"]
        )
        assert len(historial) == 3, f"esperaba 3 cambios reales guardados, obtuve {len(historial)}"
    finally:
        db.close()
        os.remove(path)


def test_ignora_mensajes_vacios_o_sin_categoria():
    """La segunda entrada de analyze_stance (mensaje vacío) no debe guardarse."""
    db, path, id_sesion = _sesion_temporal()
    try:
        logger = MedicionLogger(db, id_sesion)
        diagnostico = [
            {"categoria": "postura", "mensaje": "ZENKUTSU (DER ADELANTE): POSTURA: FIRME",
             "angulo": 110.0, "color": (0, 255, 0)},
            {"categoria": "postura_der_numero", "mensaje": "", "angulo": 172.0, "color": (0, 255, 0)},
        ]
        logger.registrar(diagnostico, timestamp_ms=0)

        filas = db.conn.execute(
            "SELECT COUNT(*) AS n FROM tecnica_evaluada WHERE id_sesion = ?", (id_sesion,)
        ).fetchone()
        assert filas["n"] == 1, f"esperaba 1 fila (la segunda entrada vacía se ignora), obtuve {filas['n']}"
    finally:
        db.close()
        os.remove(path)


def test_categorias_independientes_no_se_pisan():
    """Un cambio en 'codo_izq' no debe afectar el registro de 'codo_der' ni viceversa."""
    db, path, id_sesion = _sesion_temporal()
    try:
        logger = MedicionLogger(db, id_sesion)
        logger.registrar([{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE",
                            "angulo": 170.0, "color": (0, 255, 0)}], timestamp_ms=0)
        logger.registrar([{"categoria": "codo_der", "mensaje": "DER - TSUKI: EXCELENTE",
                            "angulo": 170.0, "color": (0, 255, 0)}], timestamp_ms=33)
        # Repetir "codo_izq" con el MISMO mensaje no debe duplicar, aunque "codo_der" ya se guardó.
        logger.registrar([{"categoria": "codo_izq", "mensaje": "IZQ - TSUKI: EXCELENTE",
                            "angulo": 170.0, "color": (0, 255, 0)}], timestamp_ms=66)

        filas = db.conn.execute(
            "SELECT COUNT(*) AS n FROM tecnica_evaluada WHERE id_sesion = ?", (id_sesion,)
        ).fetchone()
        assert filas["n"] == 2, f"esperaba 2 filas (una por categoría), obtuve {filas['n']}"
    finally:
        db.close()
        os.remove(path)


if __name__ == "__main__":
    pruebas = [
        test_no_duplica_el_mismo_mensaje,
        test_guarda_cuando_el_mensaje_cambia,
        test_ignora_mensajes_vacios_o_sin_categoria,
        test_categorias_independientes_no_se_pisan,
    ]

    ok, fallidas = 0, 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"PASS - {prueba.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"FAIL - {prueba.__name__}: {e}")
            fallidas += 1

    print(f"\n{ok}/{len(pruebas)} pruebas pasaron.")
    if fallidas:
        raise SystemExit(1)
