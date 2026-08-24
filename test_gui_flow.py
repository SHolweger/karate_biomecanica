"""
test_gui_flow.py — Verificación de la GUI (CustomTkinter) sin cámara real.

No hay hardware disponible hasta la noche: se inyecta una cámara sintética
que genera un frame de prueba (un color sólido, no una persona real), para
verificar que el mecanismo de embeber video en Tkinter funciona de extremo
a extremo (Camera-like -> MediaPipe -> Renderer -> CTkImage), sin depender
de que MediaPipe detecte una pose real en el frame.

La ventana se mantiene oculta (app.withdraw()) durante la prueba, para no
interrumpir con una ventana visible al correr esto desde terminal.

Uso:
    ./venv/bin/python test_gui_flow.py
"""
import os
import tempfile
import numpy as np

from persistence.database import Database
from gui.app import App
from gui.login_screen import LoginScreen
from gui.perfil_screen import PerfilScreen
from gui.live_screen import LiveScreen


class CamaraSintetica:
    """Cámara falsa: devuelve un frame de prueba en vez de leer hardware real."""

    def get_frame(self):
        frame = np.zeros((480, 640, 3), dtype="uint8")
        frame[:, :, 1] = 120  # tinte verdoso, solo para confirmar que hay contenido real
        return frame

    def release(self):
        pass


def _db_temporal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    return Database(path), path


def test_login_crea_entrenador_y_avanza_a_perfiles():
    db, path = _db_temporal()
    try:
        app = App(db=db)
        app.withdraw()
        assert isinstance(app.pantalla_actual, LoginScreen)

        login = app.pantalla_actual
        login.nombre_var.set("Sebastián Holweger")
        login.usuario_var.set("sholweger")
        login.correo_var.set("s@dojo.com")
        login.password_var.set("clave123")
        login._crear_cuenta(rol="principal")

        assert app.entrenador is not None and app.entrenador["nombre"] == "Sebastián Holweger"
        assert isinstance(app.pantalla_actual, PerfilScreen), \
            f"esperaba PerfilScreen tras login, obtuve {type(app.pantalla_actual).__name__}"

        app.destroy()
    finally:
        db.close()
        os.remove(path)


def test_perfil_elegido_avanza_a_vivo_y_abre_sesion():
    db, path = _db_temporal()
    try:
        db.crear_entrenador("Sensei", "sensei", "s@dojo.com", "clave", rol="principal")
        entrenador = db.autenticar_entrenador("sensei", "clave")
        db.crear_atleta("Diego Morales", grado_cinturon="5º kyu")
        atleta = db.listar_atletas()[0]

        app = App(db=db)
        app.withdraw()
        app.on_login_exitoso(entrenador)
        assert isinstance(app.pantalla_actual, PerfilScreen)

        # Reemplazamos on_perfil_elegido momentáneamente para inyectar la cámara
        # sintética: LiveScreen usa cámara real por defecto (índice 2, igual que
        # main.py), y este archivo promete cero dependencia de hardware real.
        app.atleta = atleta
        app._mostrar(LiveScreen(app, db, entrenador, atleta, cam=CamaraSintetica()))

        assert isinstance(app.pantalla_actual, LiveScreen)
        assert app.pantalla_actual.id_sesion is not None

        app.pantalla_actual.cerrar()  # limpieza manual (normalmente la hace on_terminar_sesion)
        app.destroy()
    finally:
        db.close()
        os.remove(path)


def test_video_embebido_con_camara_sintetica():
    db, path = _db_temporal()
    try:
        db.crear_entrenador("Sensei", "sensei", "s@dojo.com", "clave", rol="principal")
        entrenador = db.autenticar_entrenador("sensei", "clave")
        db.crear_atleta("Diego Morales", grado_cinturon="5º kyu")
        atleta = db.listar_atletas()[0]

        app = App(db=db)
        app.withdraw()

        live = LiveScreen(app, db, entrenador, atleta, cam=CamaraSintetica())
        live.pack()
        live._actualizar_frame()  # una actualización manual (sin esperar los ms de after())

        assert live.video_label.image is not None, "el frame sintético debería haberse convertido a CTkImage"

        live.cerrar()
        fila = db.conn.execute(
            "SELECT hora_fin FROM sesion WHERE id_sesion = ?", (live.id_sesion,)
        ).fetchone()
        assert fila["hora_fin"] is not None, "cerrar() debería registrar la hora de fin de sesión"

        app.destroy()
    finally:
        db.close()
        os.remove(path)


if __name__ == "__main__":
    pruebas = [
        test_login_crea_entrenador_y_avanza_a_perfiles,
        test_perfil_elegido_avanza_a_vivo_y_abre_sesion,
        test_video_embebido_con_camara_sintetica,
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
        except Exception as e:
            print(f"ERROR - {prueba.__name__}: {type(e).__name__}: {e}")
            fallidas += 1

    print(f"\n{ok}/{len(pruebas)} pruebas pasaron.")
    if fallidas:
        raise SystemExit(1)
