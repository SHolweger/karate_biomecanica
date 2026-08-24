"""
test_reportes.py — Verificación de las gráficas de progreso, sin cámara.

Uso:
    ./venv/bin/python test_reportes.py
"""
import os
import tempfile

from persistence.database import Database
from persistence.reportes import generar_reporte_progreso


def _sesion_temporal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    db = Database(path)
    id_entrenador = db.crear_entrenador("Sensei", "sensei", "s@dojo.com", "clave", rol="principal")
    id_atleta = db.crear_atleta("Diego Morales", grado_cinturon="5º kyu")
    return db, path, id_atleta, id_entrenador


def test_sin_datos_evaluados_no_genera_grafica():
    """Si nunca se guardó un diagnóstico con correcto=True/False, no debe intentar graficar."""
    db, path, id_atleta, id_entrenador = _sesion_temporal()
    try:
        id_sesion = db.iniciar_sesion(id_atleta, id_entrenador)
        # Solo un mensaje transitorio, sin evaluación cerrada (correcto=None)
        db.guardar_medicion(id_sesion, "Postura de piernas", 150.0, "MOVIENDOSE: EN TRANSICION...",
                             timestamp_ms=0, correcto=None)
        db.cerrar_sesion(id_sesion)

        ruta = generar_reporte_progreso(db, id_atleta, "Diego Morales", carpeta=tempfile.mkdtemp())
        assert ruta is None, f"esperaba None (sin datos evaluados), obtuve {ruta}"
    finally:
        db.close()
        os.remove(path)


def test_genera_grafica_con_datos_reales():
    """Con datos evaluados de 2 sesiones y 2 técnicas, debe generar un PNG real."""
    db, path, id_atleta, id_entrenador = _sesion_temporal()
    carpeta = tempfile.mkdtemp()
    try:
        # Sesión 1: 3 de 4 correctos = 75%
        id_sesion1 = db.iniciar_sesion(id_atleta, id_entrenador)
        db.guardar_medicion(id_sesion1, "Tsuki (brazo derecho)", 172.0, "TSUKI: EXCELENTE", 0, correcto=True)
        db.guardar_medicion(id_sesion1, "Tsuki (brazo derecho)", 150.0, "TSUKI: FLEXIONADO", 1000, correcto=False)
        db.guardar_medicion(id_sesion1, "Postura de piernas", 110.0, "ZENKUTSU: FIRME", 2000, correcto=True)
        db.guardar_medicion(id_sesion1, "Postura de piernas", 112.0, "ZENKUTSU: FIRME", 3000, correcto=True)
        db.cerrar_sesion(id_sesion1)

        # Sesión 2: 2 de 2 correctos = 100%
        id_sesion2 = db.iniciar_sesion(id_atleta, id_entrenador)
        db.guardar_medicion(id_sesion2, "Tsuki (brazo derecho)", 170.0, "TSUKI: EXCELENTE", 0, correcto=True)
        db.guardar_medicion(id_sesion2, "Postura de piernas", 108.0, "ZENKUTSU: FIRME", 1000, correcto=True)
        db.cerrar_sesion(id_sesion2)

        ruta = generar_reporte_progreso(db, id_atleta, "Diego Morales", carpeta=carpeta)
        assert ruta is not None, "esperaba una ruta de PNG generada"
        assert os.path.isfile(ruta), f"el archivo {ruta} debería existir"
        assert os.path.getsize(ruta) > 0, "el PNG generado no debería estar vacío"
    finally:
        db.close()
        os.remove(path)


if __name__ == "__main__":
    pruebas = [
        test_sin_datos_evaluados_no_genera_grafica,
        test_genera_grafica_con_datos_reales,
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
