"""
test_persistence.py — Verificación de la capa de persistencia (SQLite) sin cámara.

Ejercita persistence/database.py directamente con datos sintéticos: crear
entrenadores, autenticar, perfiles de atleta, sesiones y mediciones.

Uso:
    ./venv/bin/python test_persistence.py
"""
import os
import tempfile

from persistence.database import Database


def _db_temporal():
    """Crea una BD SQLite en un archivo temporal, aislada entre pruebas."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # Database la vuelve a crear desde cero
    return Database(path), path


def test_crear_y_autenticar_entrenador():
    db, path = _db_temporal()
    try:
        assert not db.existe_algun_entrenador()

        db.crear_entrenador("Sebastián Holweger", "sholweger", "sholwegerp@miumg.edu.gt", "clave123", rol="principal")
        assert db.existe_algun_entrenador()

        ok = db.autenticar_entrenador("sholweger", "clave123")
        assert ok is not None and ok["nombre"] == "Sebastián Holweger"

        assert db.autenticar_entrenador("sholweger", "clave_incorrecta") is None
        assert db.autenticar_entrenador("usuario_que_no_existe", "clave123") is None
    finally:
        db.close()
        os.remove(path)


def test_roles_como_catalogo():
    """El rol es un campo simple (catálogo), no una tabla de permisos — ver decisión con Sebastián."""
    db, path = _db_temporal()
    try:
        db.crear_entrenador("Sensei Principal", "principal", "p@dojo.com", "pass1", rol="principal")
        db.crear_entrenador("Sensei Asistente", "asistente", "a@dojo.com", "pass2", rol="sensei")

        principal = db.autenticar_entrenador("principal", "pass1")
        asistente = db.autenticar_entrenador("asistente", "pass2")
        assert principal["rol"] == "principal", f"rol inesperado: {principal['rol']}"
        assert asistente["rol"] == "sensei", f"rol inesperado: {asistente['rol']}"
    finally:
        db.close()
        os.remove(path)


def test_password_no_se_guarda_en_claro():
    """RNF-05: la contraseña debe almacenarse cifrada (hash), no en texto plano."""
    db, path = _db_temporal()
    try:
        db.crear_entrenador("Prueba", "prueba", "p@p.com", "mi_clave_secreta", rol="sensei")
        fila = db.conn.execute("SELECT password_hash FROM entrenador WHERE usuario = 'prueba'").fetchone()
        assert fila["password_hash"] != "mi_clave_secreta", "¡la contraseña se guardó en texto plano!"
        assert len(fila["password_hash"]) == 64, "el hash SHA-256 debería tener 64 caracteres hexadecimales"
    finally:
        db.close()
        os.remove(path)


def test_perfiles_de_atleta():
    db, path = _db_temporal()
    try:
        assert db.listar_atletas() == []

        db.crear_atleta("Diego Morales", grado_cinturon="5º kyu")
        db.crear_atleta("Ana Lucía Pérez", grado_cinturon="3º kyu")

        atletas = db.listar_atletas()
        assert len(atletas) == 2
        nombres = {a["nombre"] for a in atletas}
        assert nombres == {"Diego Morales", "Ana Lucía Pérez"}
    finally:
        db.close()
        os.remove(path)


def test_sesion_y_mediciones():
    db, path = _db_temporal()
    try:
        id_entrenador = db.crear_entrenador("Sensei", "sensei", "s@dojo.com", "clave", rol="principal")
        id_atleta = db.crear_atleta("Diego Morales", grado_cinturon="5º kyu")

        id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)

        db.guardar_medicion(id_sesion, "Gyaku Tsuki", 172.4, "TSUKI: EXCELENTE", timestamp_ms=1000)
        db.guardar_medicion(id_sesion, "Zenkutsu Dachi", 108.1, "POSTURA: FIRME", timestamp_ms=2000)
        db.guardar_medicion(id_sesion, "Mae Geri", 165.0, "MAE GERI: KIME EXCELENTE | HIKIASHI: CORRECTO", timestamp_ms=3000)

        db.cerrar_sesion(id_sesion)

        fila_sesion = db.conn.execute(
            "SELECT hora_fin FROM sesion WHERE id_sesion = ?", (id_sesion,)
        ).fetchone()
        assert fila_sesion["hora_fin"] is not None, "la sesión debería tener hora de cierre registrada"

        historial = db.consultar_historial(id_atleta)
        assert len(historial) == 3, f"esperaba 3 mediciones, obtuve {len(historial)}"
        tecnicas = {h["nombre_tecnica"] for h in historial}
        assert tecnicas == {"Gyaku Tsuki", "Zenkutsu Dachi", "Mae Geri"}
    finally:
        db.close()
        os.remove(path)


if __name__ == "__main__":
    pruebas = [
        test_crear_y_autenticar_entrenador,
        test_roles_como_catalogo,
        test_password_no_se_guarda_en_claro,
        test_perfiles_de_atleta,
        test_sesion_y_mediciones,
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
