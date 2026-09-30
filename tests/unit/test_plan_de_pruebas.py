"""
Pruebas del generador del plan de pruebas.

Tiene algo de circular —una prueba que verifica el documento que la incluye—
pero la parte que importa no lo es: lo que se protege es que el plan **describa
lo que de verdad se ejecuta**. Un plan con un comando que no corre, o al que le
faltan justo los casos de interfaz, es peor que no tener plan: se entrega, se
firma y nadie descubre el hueco hasta que hay que demostrar una prueba.
"""
import csv
import subprocess
import shlex

import pytest

from plan_de_pruebas import (COLUMNAS_A_LLENAR, comando, escribir_csv,
                             leer_casos, necesita_pantalla)
from reporte.plantilla import Paso, Prioridad, TipoPrueba, ficha

pytestmark = pytest.mark.unitaria


@ficha(
    id_caso="TC-AUTO-062",
    nombre="El plan de pruebas recoge todos los casos y sus comandos ejecutan",
    tipo=TipoPrueba.UNITARIA,
    prioridad=Prioridad.MEDIA,
    justificacion_riesgo="el plan es un entregable que se firma y se presenta, y su "
                         "utilidad depende de dos cosas que nada mas vigila: que no "
                         "falte ningun caso y que el comando de cada fila ejecute de "
                         "verdad. Los diez modulos de tests/e2e/ se omiten solos sin "
                         "entorno grafico, asi que un plan generado importando los "
                         "modulos saldria SIN los casos de interfaz --justo los que hay "
                         "que ejecutar a mano delante de alguien--. Por eso el generador "
                         "lee el arbol sintactico y no importa nada, y por eso esto se "
                         "verifica",
    componente="plan_de_pruebas.py",
    requisitos="RNF-03",
    precondiciones="Ninguna: el generador no importa los modulos de prueba, los lee",
    datos_entrada="Los archivos test_*.py del repositorio",
    pasos=[
        Paso("Leer los casos con ficha del arbol sintactico",
             "assert aparecen tambien los de tests/e2e/, que este entorno no puede "
             "importar"),
        Paso("Comprobar que los identificadores son unicos y sin huecos",
             "assert la serie TC-AUTO-NNN es correlativa: un hueco significa una "
             "ficha borrada sin renumerar"),
        Paso("Ejecutar el comando generado para un caso concreto",
             "assert pytest lo recoge y lo ejecuta, en vez de fallar por una ruta "
             "mal armada"),
    ],
    resultado_esperado="PASSED en los dos entornos, con y sin interfaz grafica",
    evidencia="Reporte de consola de pytest y el propio `docs/plan_de_pruebas.md`.",
)
def test_el_plan_recoge_todos_los_casos_y_sus_comandos_ejecutan(tmp_path):
    casos = leer_casos()

    assert any(necesita_pantalla(c) for c in casos), (
        "faltan los casos de tests/e2e/: son los que este entorno no puede importar, "
        "y son justamente los que el plan tiene que listar para ejecutarlos a mano")

    identificadores = [c.id for c in casos]
    assert len(identificadores) == len(set(identificadores)), "hay IDs repetidos"
    numeros = sorted(int(i.rsplit("-", 1)[1]) for i in identificadores)
    assert numeros == list(range(1, len(numeros) + 1)), \
        f"la serie tiene huecos: {set(range(1, numeros[-1] + 1)) - set(numeros)}"

    # Un comando de verdad, ejecutado de verdad. Se elige uno que no necesite
    # pantalla para que esto corra en los dos entornos.
    sin_pantalla = next(c for c in casos if not necesita_pantalla(c))
    resultado = subprocess.run(shlex.split(comando(sin_pantalla)),
                               capture_output=True, text=True)
    assert resultado.returncode == 0, (
        f"el comando del plan no ejecuta:\n{comando(sin_pantalla)}\n{resultado.stdout[-800:]}")


def test_las_columnas_de_planificacion_salen_vacias(tmp_path):
    """
    Se llenan al planificar y al ejecutar. Rellenarlas con algo inventado
    convertiría el plan en el registro de unas pruebas que nadie corrió, que es
    exactamente lo que un plan de pruebas no puede ser.
    """
    destino = tmp_path / "plan.csv"
    escribir_csv(leer_casos(), destino)

    with open(destino, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))

    assert filas, "el plan salió vacío"
    for columna in COLUMNAS_A_LLENAR:
        assert all(fila[columna] == "" for fila in filas), columna


def test_cada_caso_declara_el_entorno_que_necesita():
    """
    Es lo que decide si una prueba se puede planificar en integración continua
    o hace falta sentarse delante de un equipo con cámara. Sin esa columna, el
    plan promete fechas que no se pueden cumplir en un servidor.
    """
    casos = leer_casos()
    e2e = [c for c in casos if c.archivo.startswith("tests/e2e/")]

    assert e2e, "sin casos de interfaz, esta distinción no protegería de nada"
    assert all(necesita_pantalla(c) for c in e2e)
    assert not any(necesita_pantalla(c) for c in casos
                   if c.archivo.startswith("tests/unit/"))
