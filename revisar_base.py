"""
Qué hay dentro de la base de datos, antes de apartarla.

Herramienta de solo lectura. Abre la base en modo `ro` de SQLite, así que no
puede escribir aunque se quisiera: se usa justo antes de empezar con datos
limpios, y una herramienta que toca lo que viene a describir no sirve para eso.

---------------------------------------------------------------------------
PARA QUÉ
---------------------------------------------------------------------------

El 30-sep-2026 se descubrió que `analyze_tsuki` juzgaba el codo en cada
fotograma, sin comprobar antes que hubiera un golpe (ver expert_system/tsuki.py).
Todo lo medido hasta ese día lleva, por tanto, filas de Tsuki producidas por
brazos que no golpeaban, y la precisión que el sistema calcula sobre ese
historial no describe la técnica de nadie.

Antes de apartar esa base conviene dejar constancia de CUÁNTO la afecta. No es
curiosidad: la sección de validación de la tesis sostiene que los defectos
importantes aparecieron al contrastar el sistema con uso real y no con pruebas
automatizadas, y una cifra concreta sostiene ese argumento mucho mejor que la
descripción del defecto.

---------------------------------------------------------------------------
QUÉ PUEDE Y QUÉ NO PUEDE AFIRMAR
---------------------------------------------------------------------------

**No puede** separar fila por fila los Tsuki reales de los inventados. El código
viejo no registraba si hubo golpe —ese era justamente el defecto—, así que esa
distinción no está en los datos y ninguna consulta la recupera.

**Sí puede** contar una firma que solo produce un brazo en reposo: veredictos
OPUESTOS —«EXCELENTE» e «HIPEREXTENDIDO»— separados por menos de
`VENTANA_ALTERNANCIA_MS`. Un brazo quieto cerca de 175° cruza el límite del
rango de un fotograma al siguiente, y `MedicionLogger` escribe en cada cruce.
Dos golpes reales no pueden dar veredictos opuestos con esa separación: un
Tsuki dura 150-250 ms y el más rápido de los encadenados no baja de ~300 ms
entre impactos.

La cifra es, pues, una **cota inferior** de la contaminación: cuenta los casos
inequívocos y deja fuera los que no puede distinguir. Conviene citarla así.
"""
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import rutas

# Separación por debajo de la cual dos veredictos OPUESTOS del mismo brazo no
# pueden venir de dos golpes distintos. El fotograma del bucle real ronda los
# 33-40 ms; el Tsuki encadenado más rápido no baja de unos 300 ms entre
# impactos. 150 ms deja un margen amplio a favor de NO contar de más.
VENTANA_ALTERNANCIA_MS = 150

EXCELENTE = "TSUKI: EXCELENTE"
HIPEREXTENDIDO = "TSUKI: HIPEREXTENDIDO"


# ---------------------------------------------------------------------------
# Lógica pura: recibe filas, no toca SQLite. Por eso la verifica CI.
# ---------------------------------------------------------------------------

def resumen_por_tecnica(filas):
    """
    Cuántas mediciones y cuántos veredictos cerrados hay de cada técnica.

    `filas` son diccionarios con `nombre_tecnica`, `diagnostico`, `correcto` y
    `timestamp_ms`. La precisión se calcula solo sobre `correcto is not None`,
    igual que las consultas agregadas del sistema: un estado transitorio no es
    un fallo.
    """
    resumen = defaultdict(lambda: {"total": 0, "cerradas": 0, "correctas": 0})
    for fila in filas:
        entrada = resumen[fila["nombre_tecnica"]]
        entrada["total"] += 1
        if fila["correcto"] is not None:
            entrada["cerradas"] += 1
            entrada["correctas"] += 1 if fila["correcto"] else 0

    for entrada in resumen.values():
        entrada["precision"] = (None if entrada["cerradas"] == 0
                                else 100.0 * entrada["correctas"] / entrada["cerradas"])
    return dict(resumen)


def alternancias_rapidas(filas, ventana_ms=VENTANA_ALTERNANCIA_MS):
    """
    Veredictos opuestos del mismo brazo separados por menos de `ventana_ms`.

    Es la firma de un brazo en reposo cruzando el límite de 175°, y no puede
    producirla ninguna secuencia de golpes reales. Devuelve cuántas filas
    participan en esas alternancias, que es la cota inferior de contaminación.

    Se agrupa por (sesión, técnica) porque dos brazos distintos, o dos sesiones,
    pueden tener marcas de tiempo cercanas sin relación entre sí. El brazo
    izquierdo y el derecho se registran además con la MISMA marca, porque salen
    del mismo fotograma: compararlos entre sí daría una alternancia falsa en
    cada fotograma de cualquier sesión.

    Cuenta FILAS DISTINTAS implicadas, no parejas. En una tanda alternante cada
    fila participa en dos parejas —la anterior y la siguiente— así que sumar
    dos por pareja contaba casi el doble de filas de las que hay. Se vio al
    contrastar contra una base real: daba el 190 % del total.
    """
    por_grupo = defaultdict(list)
    for fila in filas:
        if fila["correcto"] is None:
            continue
        por_grupo[(fila["id_sesion"], fila["nombre_tecnica"])].append(fila)

    implicadas = 0
    for grupo in por_grupo.values():
        grupo.sort(key=lambda f: f["timestamp_ms"])
        posiciones = set()
        for i, (anterior, siguiente) in enumerate(zip(grupo, grupo[1:])):
            if siguiente["timestamp_ms"] - anterior["timestamp_ms"] >= ventana_ms:
                continue
            veredictos = {_clase(anterior["diagnostico"]), _clase(siguiente["diagnostico"])}
            if veredictos == {EXCELENTE, HIPEREXTENDIDO}:
                posiciones.update((i, i + 1))
        implicadas += len(posiciones)
    return implicadas


def _clase(diagnostico):
    """El veredicto sin el prefijo de lado que antepone el analizador."""
    texto = diagnostico or ""
    if EXCELENTE in texto:
        return EXCELENTE
    if HIPEREXTENDIDO in texto:
        return HIPEREXTENDIDO
    return texto


def es_tsuki(nombre_tecnica):
    return "Tsuki" in (nombre_tecnica or "")


# ---------------------------------------------------------------------------
# Lectura y presentación
# ---------------------------------------------------------------------------

def leer(ruta):
    """Abre la base en SOLO LECTURA y devuelve las mediciones."""
    conexion = sqlite3.connect(f"file:{Path(ruta).as_uri()[7:]}?mode=ro", uri=True)
    conexion.row_factory = sqlite3.Row
    try:
        filas = conexion.execute(
            "SELECT id_sesion, nombre_tecnica, timestamp_ms, diagnostico, correcto "
            "FROM tecnica_evaluada").fetchall()
    finally:
        conexion.close()
    return [dict(f) for f in filas]


def informar(filas, salida=sys.stdout):
    def escribir(texto=""):
        print(texto, file=salida)

    if not filas:
        escribir("La base no tiene mediciones.")
        return

    resumen = resumen_por_tecnica(filas)
    escribir(f"MEDICIONES REGISTRADAS: {len(filas)}")
    escribir()
    escribir(f"{'Tecnica':32} {'filas':>7} {'cerradas':>9} {'precision':>10}")
    escribir("-" * 61)
    for nombre in sorted(resumen):
        d = resumen[nombre]
        precision = "     -" if d["precision"] is None else f"{d['precision']:8.1f} %"
        escribir(f"{nombre:32} {d['total']:7} {d['cerradas']:9} {precision:>10}")

    tsuki = [f for f in filas if es_tsuki(f["nombre_tecnica"])]
    cerradas = sum(1 for f in filas if f["correcto"] is not None)
    cerradas_tsuki = sum(1 for f in tsuki if f["correcto"] is not None)

    escribir()
    escribir("CUANTO DE ESTO ES TSUKI")
    escribir(f"  {len(tsuki)} de {len(filas)} filas "
             f"({100.0 * len(tsuki) / len(filas):.1f} %)")
    if cerradas:
        escribir(f"  {cerradas_tsuki} de {cerradas} veredictos cerrados "
                 f"({100.0 * cerradas_tsuki / cerradas:.1f} %)")

    implicadas = alternancias_rapidas(filas)
    escribir()
    escribir("CONTAMINACION DEMOSTRABLE (cota inferior)")
    if implicadas == 0:
        escribir("  Ninguna alternancia rapida. Eso NO significa que no haya filas")
        escribir("  inventadas: solo que no las hay de la clase que se puede probar.")
    else:
        escribir(f"  {implicadas} filas participan en veredictos OPUESTOS separados por")
        escribir(f"  menos de {VENTANA_ALTERNANCIA_MS} ms, que es la firma de un brazo en reposo")
        escribir(f"  cruzando el limite de 175 grados. Son el {100.0 * implicadas / len(filas):.1f} %")
        escribir("  del total, y es una COTA INFERIOR: el codigo viejo no registraba")
        escribir("  si hubo golpe, asi que el resto no se puede clasificar.")


def main(argumentos=None):
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    ruta = argumentos[0] if argumentos else rutas.base_de_datos()

    if not Path(ruta).is_file():
        print(f"No hay base de datos en {ruta}", file=sys.stderr)
        return 1

    print(f"Base: {ruta}\n")
    informar(leer(ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
