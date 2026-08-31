"""
Pruebas de integración de persistence/cli_auth.py (acceso por consola, RF-08).

Es una interfaz interactiva: pide datos con input() y getpass(). Para
automatizarla se sustituyen esas dos funciones por un guion de respuestas
predefinidas (monkeypatch), que es el equivalente en consola de "escribir en
los campos y pulsar el botón". Así el flujo completo de login queda cubierto
sin una persona tecleando.
"""
import builtins

import pytest

from persistence import cli_auth

pytestmark = pytest.mark.integracion


@pytest.fixture
def teclado(monkeypatch):
    """
    Simula a la persona frente al teclado: se le carga la lista de respuestas
    y las va entregando en orden a input() y getpass().
    """
    def cargar(*respuestas):
        pendientes = list(respuestas)

        def responder(_prompt=""):
            assert pendientes, "el programa pidió más datos de los que la prueba previó"
            return pendientes.pop(0)

        monkeypatch.setattr(builtins, "input", responder)
        monkeypatch.setattr(cli_auth.getpass, "getpass", responder)
        return pendientes

    return cargar


def test_el_primer_uso_registra_al_entrenador_principal(db, teclado, capsys):
    """
    Sin entrenadores en la base, el sistema no pide credenciales: guía al
    usuario a crear la primera cuenta y lo deja autenticado.
    """
    teclado("Sebastian Holweger", "sholweger", "sholweger@dojo.gt", "clave123")

    entrenador = cli_auth.login_o_registro(db)

    assert entrenador["nombre"] == "Sebastian Holweger"
    assert entrenador["rol"] == "principal", "la cuenta inicial debe ser la del sensei principal"
    assert db.autenticar_entrenador("sholweger", "clave123") is not None


def test_login_exitoso_de_un_entrenador_existente(db, teclado):
    db.crear_entrenador("Sensei Ejemplo", "sensei", "s@dojo.gt", "clave123", rol="principal")
    teclado("sensei", "clave123")

    entrenador = cli_auth.login_o_registro(db)

    assert entrenador["usuario"] == "sensei"


def test_reintento_tras_una_contrasena_equivocada(db, teclado):
    """
    Camino de recuperación: credencial mala -> el usuario elige reintentar ->
    entra. El bucle debe volver a pedir los datos, no abortar el programa.
    """
    db.crear_entrenador("Sensei Ejemplo", "sensei", "s@dojo.gt", "clave123")
    teclado("sensei", "mala", "r",          # primer intento fallido, reintenta
            "sensei", "clave123")           # segundo intento correcto

    entrenador = cli_auth.login_o_registro(db)

    assert entrenador["usuario"] == "sensei"


def test_tras_fallar_puede_crear_una_cuenta_de_sensei_asistente(db, teclado):
    """La cuenta creada desde el camino alterno es 'sensei', no 'principal'."""
    db.crear_entrenador("Sensei Principal", "principal", "p@dojo.gt", "clave123", rol="principal")
    teclado("desconocido", "mala", "n",                              # falla y elige crear cuenta
            "Ana Castillo", "acastillo", "ana@dojo.gt", "clave456")  # datos de la cuenta nueva

    entrenador = cli_auth.login_o_registro(db)

    assert entrenador["usuario"] == "acastillo"
    assert entrenador["rol"] == "sensei"


def test_elegir_un_perfil_existente_de_la_lista(db, teclado):
    """Selección estilo Netflix: se lista a los alumnos y se elige por número."""
    db.crear_atleta("Ana Castillo")
    db.crear_atleta("Diego Morales")
    teclado("2")  # la lista va ordenada alfabéticamente: 1=Ana, 2=Diego

    atleta = cli_auth.elegir_o_crear_perfil(db)

    assert atleta["nombre"] == "Diego Morales"


def test_crear_un_perfil_nuevo_desde_la_lista(db, teclado):
    """La última opción siempre es "agregar perfil", esté vacía o llena la lista."""
    db.crear_atleta("Ana Castillo")
    teclado("2", "Bruno Perez", "8o kyu")

    atleta = cli_auth.elegir_o_crear_perfil(db)

    assert atleta["nombre"] == "Bruno Perez"
    assert atleta["grado_cinturon"] == "8o kyu"
    assert atleta["id_atleta"] is not None
    assert [a["nombre"] for a in db.listar_atletas()] == ["Ana Castillo", "Bruno Perez"]


def test_el_grado_del_cinturon_es_opcional(db, teclado):
    """Enter en blanco debe guardar NULL, no una cadena vacía."""
    teclado("1", "Alumno Nuevo", "")

    atleta = cli_auth.elegir_o_crear_perfil(db)

    assert atleta["grado_cinturon"] is None


@pytest.mark.parametrize("entrada_invalida, motivo", [
    ("abc", "texto en vez de número"),
    ("0", "número fuera de rango por abajo"),
    ("99", "número fuera de rango por arriba"),
])
def test_una_opcion_invalida_vuelve_a_preguntar(db, teclado, entrada_invalida, motivo):
    """Robustez de entrada: no debe reventar ni elegir un perfil al azar."""
    db.crear_atleta("Ana Castillo")
    teclado(entrada_invalida, "1")

    atleta = cli_auth.elegir_o_crear_perfil(db)

    assert atleta["nombre"] == "Ana Castillo", f"no se recuperó de: {motivo}"
