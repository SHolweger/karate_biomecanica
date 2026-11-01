"""
Los videos del dojo, analizados por lotes: qué evaluó el sistema, por
deportista y por técnica, sin abrir la interfaz video por video.

Herramienta de consola, como `revisar_correcciones.py`, y como ella NO escribe
en la base: recorre cada grabación con el mismo analizador de la pantalla en
vivo y cuenta las evaluaciones con la MISMA regla con que `MedicionLogger` las
escribe en una sesión (medio segundo sostenido en la postura, una fila cada vez
que el diagnóstico cambia). Lo que aquí sale como «evaluaciones» es, por tanto,
lo que la base habría registrado si cada tramo se hubiera analizado desde la
interfaz.

---------------------------------------------------------------------------
POR QUÉ EXISTE
---------------------------------------------------------------------------

El 6.10 de la tesis separa dos indicadores: (a) el funcionamiento del sistema
sobre material real —ejecuciones grabadas, reconocidas, evaluadas, correctas e
incorrectas, por técnica y deportista— y (b) la concordancia con el sensei. El
(a) sale entero de los videos del 24-oct; el (b) necesita que el sensei
califique cada repetición sin ver antes el veredicto del sistema. Esta
herramienta produce lo primero y la planilla para lo segundo.

---------------------------------------------------------------------------
CÓMO SE USA: TRES PASOS
---------------------------------------------------------------------------

1. Inventario. Lista los videos de la carpeta en `inventario.csv`:

       python3 analizar_lote.py ~/Movies/dojo_24oct --plantilla

   Ábrelo en Excel o Numbers y completa una fila por video (o varias, si un
   video tiene tramos de técnicas distintas: copia la fila y pon `desde` y
   `hasta`). Columnas:

   - deportista: un CÓDIGO, no el nombre (D1, D2, D3, D4; SH para ti).
   - tecnica: heiko, kiba, zenkutsu, kokutsu, tsuki, mae_geri o combinada.
   - orientacion: frente, perfil o 45.
   - vestimenta: karategi o casual.
   - repeticiones: cuántas ejecutó de verdad, contadas viendo el video.
   - desde / hasta: segundos del tramo («83», «83,5» o «1:23»). Vacíos = todo.
   - espejado: «si» solo si se grabó con la cámara frontal del teléfono con el
     espejo activado. Lo normal es dejarlo vacío.

   Si luego agregas videos, vuelve a correr `--plantilla`: añade los nuevos y
   conserva lo que ya escribiste.

2. Planilla del sensei, antes de analizar nada:

       python3 analizar_lote.py ~/Movies/dojo_24oct --rubrica

   Una fila por repetición declarada, sin ningún veredicto del sistema. El
   sensei llena lado, valoración (correcta, incorrecta o no evaluable) y motivo.

3. Análisis:

       python3 analizar_lote.py ~/Movies/dojo_24oct

   Escribe en `resultados_AAAAMMDD_HHMM/` dentro de la misma carpeta:

   - segmentos.csv: una fila por tramo del inventario.
   - deportista_tecnica.csv: el indicador (a) del 6.10.
   - evaluaciones.csv: cada veredicto cerrado, en su segundo, con lo que leería
     el alumno. Es lo que se contrasta con la planilla del sensei.
   - resumen.txt: lo mismo que imprime en la terminal.

---------------------------------------------------------------------------
LO QUE CONVIENE SABER AL LEER LOS NÚMEROS
---------------------------------------------------------------------------

- Juzga con los umbrales de literatura, los que siembra una base nueva.
- Dos repeticiones seguidas de la misma postura con el mismo veredicto, sin
  pasar por otra cosa en medio, son UNA evaluación: así escribe la base. Por eso
  el protocolo pide volver a Heiko Dachi entre repeticiones.
- En un tramo de una técnica, las otras posturas que aparezcan —el Heiko entre
  repeticiones, sobre todo— se informan en `segmentos.csv` pero no cuentan para
  el indicador: no son lo que se pidió ejecutar.
- «Izquierda» y «derecha» son las del sistema, que analiza en modo espejo, igual
  que la pantalla en vivo.
- Sin evaluaciones, el porcentaje de correctas es un guion, nunca 0 %.
"""
import argparse
import csv
import datetime
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from expert_system.guardia import orientacion_frente_a_camara
from gui.coaching import traducir
from persistence.medicion_logger import MedicionLogger
from vision.encuadre import clasificar_plano

EXTENSIONES_DE_VIDEO = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
INVENTARIO = "inventario.csv"
RUBRICA = "rubrica_sensei.csv"

COLUMNAS_INVENTARIO = ["archivo", "deportista", "tecnica", "orientacion", "vestimenta",
                       "repeticiones", "desde", "hasta", "espejado", "notas"]
COLUMNAS_RUBRICA = ["codigo", "archivo", "deportista", "tecnica", "desde", "hasta",
                    "repeticion", "lado", "valoracion", "motivo"]

# Lo que se escribe en la columna `tecnica` -> la clave con que el motor la juzga.
# `combinada` es un tramo con varias técnicas, sin una esperada.
TECNICAS = {
    "heiko": "heiko_dachi",
    "kiba": "kiba_dachi",
    "zenkutsu": "zenkutsu_dachi",
    "kokutsu": "kokutsu_dachi",
    "tsuki": "tsuki",
    "mae_geri": "mae_geri",
    "combinada": None,
}
NOMBRES = {
    "heiko_dachi": "Heiko Dachi", "kiba_dachi": "Kiba Dachi",
    "zenkutsu_dachi": "Zenkutsu Dachi", "kokutsu_dachi": "Kokutsu Dachi",
    "tsuki": "Tsuki", "mae_geri": "Mae Geri", None: "Combinada",
}

# El protocolo de cámara (Tabla 6.5): cada técnica, perpendicular a su plano.
# El Kokutsu no tiene toma válida con una sola cámara, y por eso no está.
PLANO_DEL_PROTOCOLO = {
    "heiko_dachi": "frontal", "kiba_dachi": "frontal",
    "zenkutsu_dachi": "perfil", "tsuki": "perfil", "mae_geri": "perfil",
}
ORIENTACIONES = {"frente": "frontal", "frontal": "frontal", "perfil": "perfil",
                 "lateral": "perfil", "45": "oblicuo", "oblicuo": "oblicuo", "oblicua": "oblicuo"}

# Por debajo de esto, el video dice más del encuadre que de la técnica.
POSE_MINIMA = 0.80


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------

def _simplificar(texto):
    """«Zenkutsu Dachi» -> «zenkutsu»; «Mae-Geri» -> «mae_geri»; «Sí» -> «si»."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                         if unicodedata.category(c) != "Mn")
    plano = sin_tildes.strip().lower().replace("-", " ").replace("°", "")
    plano = "_".join(plano.split())
    return plano.removesuffix("_dachi")


def leer_segundos(texto):
    """«83», «83,5», «83.5» o «1:23» a segundos. Vacío -> None."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if ":" in texto:
        minutos, segundos = texto.split(":", 1)
        return int(minutos) * 60 + float(segundos.replace(",", "."))
    return float(texto.replace(",", "."))


def buscar_videos(carpeta):
    """Los videos bajo la carpeta, como rutas relativas, sin las carpetas de resultados."""
    carpeta = Path(carpeta)
    videos = []
    for ruta in carpeta.rglob("*"):
        relativa = ruta.relative_to(carpeta)
        if any(parte.startswith((".", "resultados_")) for parte in relativa.parts):
            continue
        if ruta.is_file() and ruta.suffix.lower() in EXTENSIONES_DE_VIDEO:
            videos.append(relativa.as_posix())
    return sorted(videos)


def _leer_csv(ruta):
    """Filas de un CSV escrito por Excel o Numbers, con coma o punto y coma."""
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        texto = f.read()
    primera = texto.splitlines()[0] if texto else ""
    separador = ";" if primera.count(";") > primera.count(",") else ","
    return list(csv.DictReader(texto.splitlines(), delimiter=separador))


def _escribir_csv(ruta, columnas, filas):
    # El BOM es lo que hace que Excel abra las tildes bien (ver plan_de_pruebas.py).
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila.get(c, "") for c in columnas})


def escribir_plantilla(carpeta, ruta_inventario=None):
    """
    Crea el inventario o le añade los videos nuevos. Nunca borra lo escrito.

    Devuelve cuántas filas nuevas añadió.
    """
    ruta = Path(ruta_inventario or Path(carpeta) / INVENTARIO)
    existentes = _leer_csv(ruta) if ruta.exists() else []
    ya_listados = {(fila.get("archivo") or "").strip() for fila in existentes}
    nuevas = [{"archivo": video} for video in buscar_videos(carpeta) if video not in ya_listados]
    columnas = list(COLUMNAS_INVENTARIO)
    for fila in existentes:
        columnas += [c for c in fila if c and c not in columnas]
    _escribir_csv(ruta, columnas, existentes + nuevas)
    return len(nuevas)


def leer_inventario(ruta, carpeta=None):
    """
    Los tramos del inventario, validados. Devuelve (segmentos, errores).

    Una fila con errores no se analiza, pero las demás sí: un inventario a medio
    llenar no debería impedir ver lo que ya está listo. Las filas sin técnica
    se saltan sin error: son videos que aún no se han clasificado.
    """
    segmentos, errores = [], []
    for numero, fila in enumerate(_leer_csv(ruta), start=2):
        archivo = (fila.get("archivo") or "").strip()
        clave_tecnica = _simplificar(fila.get("tecnica"))
        if not archivo or not clave_tecnica:
            continue
        problemas = []
        if clave_tecnica not in TECNICAS:
            problemas.append(f"técnica «{fila.get('tecnica')}» desconocida "
                             f"(usa {', '.join(TECNICAS)})")
        orientacion = _simplificar(fila.get("orientacion"))
        if orientacion and orientacion not in ORIENTACIONES:
            problemas.append(f"orientación «{fila.get('orientacion')}» desconocida (frente, perfil o 45)")
        repeticiones = (fila.get("repeticiones") or "").strip()
        if repeticiones and not repeticiones.isdigit():
            problemas.append(f"repeticiones «{repeticiones}» no es un número entero")
        try:
            desde, hasta = leer_segundos(fila.get("desde")), leer_segundos(fila.get("hasta"))
        except ValueError:
            desde = hasta = None
            problemas.append("desde/hasta no se entienden (usa 83, 83,5 o 1:23)")
        if desde is not None and hasta is not None and hasta <= desde:
            problemas.append("hasta debe ser mayor que desde")
        if carpeta is not None and not (Path(carpeta) / archivo).exists():
            problemas.append("el archivo no está en la carpeta")
        if problemas:
            errores.append(f"fila {numero} ({archivo}): " + "; ".join(problemas))
            continue
        segmentos.append({
            "fila": numero,
            "archivo": archivo,
            "deportista": (fila.get("deportista") or "").strip() or "sin código",
            "tecnica": TECNICAS[clave_tecnica],
            "orientacion": ORIENTACIONES.get(orientacion),
            "vestimenta": (fila.get("vestimenta") or "").strip(),
            "repeticiones": int(repeticiones) if repeticiones else None,
            "desde": desde,
            "hasta": hasta,
            "espejado": _simplificar(fila.get("espejado")) in ("si", "s", "x", "1"),
        })
    return segmentos, errores


def filas_de_rubrica(segmentos):
    """
    Una fila por repetición declarada, sin ningún veredicto del sistema.

    El sensei tiene que calificar SIN ver lo que dijo el programa (6.8): si la
    planilla lo trajera, la concordancia que se midiera después no sería
    independiente.
    """
    filas = []
    for indice, segmento in enumerate(segmentos, start=1):
        cuantas = segmento["repeticiones"] or 1
        for repeticion in range(1, cuantas + 1):
            filas.append({
                "codigo": f"S{indice:02d}-R{repeticion}",
                "archivo": segmento["archivo"],
                "deportista": segmento["deportista"],
                "tecnica": NOMBRES[segmento["tecnica"]],
                "desde": formatear_segundos(segmento["desde"]),
                "hasta": formatear_segundos(segmento["hasta"]),
                "repeticion": repeticion if segmento["repeticiones"] else "",
            })
    return filas


# ---------------------------------------------------------------------------
# Conteo: lógica pura, alimentada por fotogramas
# ---------------------------------------------------------------------------

class _BaseEnMemoria:
    """
    Recibe lo que `MedicionLogger` mandaría a SQLite y lo guarda en una lista.

    Usar el registrador real y no una copia de su regla es lo que hace que
    «evaluaciones» signifique aquí exactamente lo mismo que en una sesión.
    """

    def __init__(self):
        self.filas = []

    def guardar_medicion(self, id_sesion, nombre_tecnica, angulo_promedio, diagnostico,
                         timestamp_ms, correcto=None, tecnica_clave=None, **_):
        self.filas.append({"nombre": nombre_tecnica, "mensaje": diagnostico,
                           "timestamp_ms": timestamp_ms, "correcto": correcto,
                           "tecnica_clave": tecnica_clave})


def _tecnica_y_lado(fila):
    """De una fila registrada, qué técnica se juzgó y de qué lado."""
    nombre, mensaje = fila["nombre"], fila["mensaje"]
    if nombre.startswith("Tsuki"):
        return "tsuki", "izq" if "izquierdo" in nombre else "der"
    if nombre.startswith("Mae Geri"):
        return "mae_geri", "izq" if "izquierda" in nombre else "der"
    lado = "izq" if "IZQ ADELANTE" in mensaje else "der" if "DER ADELANTE" in mensaje else ""
    return fila["tecnica_clave"], lado


def contar(fotogramas):
    """
    Lo que el sistema habría registrado en un tramo.

    `fotogramas` es un iterable de `(timestamp_ms, diagnosticos, orientacion)`;
    `diagnosticos` es None en los fotogramas sin pose detectada.
    """
    base = _BaseEnMemoria()
    registrador = MedicionLogger(base, id_sesion=None)
    total = con_pose = 0
    orientaciones = []
    for timestamp_ms, diagnosticos, orientacion in fotogramas:
        total += 1
        if diagnosticos is None:
            continue
        con_pose += 1
        if orientacion is not None:
            orientaciones.append(orientacion)
        for diagnostico in diagnosticos:
            registrador.registrar(diagnostico if isinstance(diagnostico, list) else [diagnostico],
                                  timestamp_ms)

    evaluaciones = []
    for fila in base.filas:
        if fila["correcto"] is None:
            continue
        tecnica, lado = _tecnica_y_lado(fila)
        evaluaciones.append({"timestamp_ms": fila["timestamp_ms"], "tecnica": tecnica,
                             "lado": lado, "correcto": fila["correcto"],
                             "mensaje": fila["mensaje"]})
    return {
        "fotogramas": total,
        "con_pose": con_pose,
        "orientacion": statistics.median(orientaciones) if orientaciones else None,
        "evaluaciones": evaluaciones,
    }


def advertencias(segmento, conteo):
    """Lo que hace dudar de un tramo antes de leer sus números."""
    avisos = []
    tecnica = segmento["tecnica"]
    if tecnica == "kokutsu_dachi":
        avisos.append("Kokutsu: no se mide de forma fiable con una cámara (Tabla 6.5)")
    plano = PLANO_DEL_PROTOCOLO.get(tecnica)
    if plano and segmento["orientacion"] and segmento["orientacion"] != plano:
        avisos.append(f"declarado {segmento['orientacion']}; el protocolo pide {plano}")
    medido = clasificar_plano(conteo["orientacion"])
    if plano and medido and medido != plano:
        avisos.append(f"la toma se midió {medido}; el protocolo pide {plano}")
    if conteo["fotogramas"] and conteo["con_pose"] / conteo["fotogramas"] < POSE_MINIMA:
        avisos.append(f"pose detectada en solo {_porcentaje(conteo['con_pose'], conteo['fotogramas'])}")
    if conteo["fotogramas"] == 0:
        avisos.append("el tramo no tiene fotogramas: revisa desde/hasta")
    return avisos


def fila_de_segmento(segmento, conteo):
    """La fila de `segmentos.csv`."""
    propias = [e for e in conteo["evaluaciones"] if e["tecnica"] == segmento["tecnica"]]
    otras = Counter(e["tecnica"] for e in conteo["evaluaciones"]
                    if e["tecnica"] != segmento["tecnica"])
    reconocida = ("" if segmento["tecnica"] is None
                  else "sí" if propias else "no")
    return {
        "archivo": segmento["archivo"],
        "deportista": segmento["deportista"],
        "tecnica": NOMBRES[segmento["tecnica"]],
        "orientacion_declarada": segmento["orientacion"] or "",
        "orientacion_medida": clasificar_plano(conteo["orientacion"]) or "",
        "vestimenta": segmento["vestimenta"],
        "desde": formatear_segundos(segmento["desde"]),
        "hasta": formatear_segundos(segmento["hasta"]),
        "fotogramas": conteo["fotogramas"],
        "pose_detectada": _porcentaje(conteo["con_pose"], conteo["fotogramas"]),
        "repeticiones_ejecutadas": segmento["repeticiones"] if segmento["repeticiones"] else "",
        "reconocida": reconocida,
        "evaluaciones": len(propias) if segmento["tecnica"] else len(conteo["evaluaciones"]),
        "correctas": sum(1 for e in propias if e["correcto"]),
        "incorrectas": sum(1 for e in propias if not e["correcto"]),
        "otras_tecnicas": "; ".join(f"{NOMBRES.get(t, t)}: {n}" for t, n in sorted(otras.items(), key=str)),
        "advertencias": "; ".join(advertencias(segmento, conteo)),
    }


def agregar(resultados):
    """
    El indicador (a) del 6.10, por deportista y técnica.

    `resultados` es una lista de `(segmento, conteo)`. En un tramo aislado solo
    cuenta la técnica que se pidió; en uno combinado cuentan todas, por
    separado, y se marcan como tales para no mezclar las dos situaciones.
    """
    tabla = defaultdict(lambda: {"tramos": 0, "ejecutadas": 0, "con_repeticiones": 0,
                                 "evaluaciones": 0, "correctas": 0, "sin_reconocer": 0})
    for segmento, conteo in resultados:
        if segmento["tecnica"] is None:
            por_tecnica = defaultdict(list)
            for e in conteo["evaluaciones"]:
                por_tecnica[e["tecnica"]].append(e)
            for tecnica, evaluaciones in por_tecnica.items():
                celda = tabla[(segmento["deportista"], tecnica, "combinada")]
                celda["tramos"] += 1
                celda["evaluaciones"] += len(evaluaciones)
                celda["correctas"] += sum(1 for e in evaluaciones if e["correcto"])
            continue
        celda = tabla[(segmento["deportista"], segmento["tecnica"], "aislada")]
        propias = [e for e in conteo["evaluaciones"] if e["tecnica"] == segmento["tecnica"]]
        celda["tramos"] += 1
        if segmento["repeticiones"]:
            celda["ejecutadas"] += segmento["repeticiones"]
            celda["con_repeticiones"] += 1
        celda["evaluaciones"] += len(propias)
        celda["correctas"] += sum(1 for e in propias if e["correcto"])
        celda["sin_reconocer"] += 0 if propias else 1

    filas = []
    for (deportista, tecnica, contexto), celda in sorted(tabla.items(), key=str):
        filas.append({
            "deportista": deportista,
            "tecnica": NOMBRES.get(tecnica, tecnica),
            "contexto": contexto,
            "tramos": celda["tramos"],
            "repeticiones_ejecutadas": (celda["ejecutadas"] if celda["con_repeticiones"] else ""),
            "evaluaciones": celda["evaluaciones"],
            "correctas": celda["correctas"],
            "incorrectas": celda["evaluaciones"] - celda["correctas"],
            "porcentaje_correctas": _porcentaje(celda["correctas"], celda["evaluaciones"]),
            "tramos_sin_reconocer": celda["sin_reconocer"] if contexto == "aislada" else "",
        })
    return filas


def filas_de_evaluaciones(resultados):
    """Cada veredicto cerrado, en su segundo del video, con lo que leería el alumno."""
    filas = []
    for segmento, conteo in resultados:
        for e in conteo["evaluaciones"]:
            filas.append({
                "archivo": segmento["archivo"],
                "deportista": segmento["deportista"],
                "tecnica_del_tramo": NOMBRES[segmento["tecnica"]],
                "segundo": formatear_segundos(e["timestamp_ms"] / 1000),
                "tecnica_evaluada": NOMBRES.get(e["tecnica"], e["tecnica"]),
                "lado": e["lado"],
                "correcto": "sí" if e["correcto"] else "no",
                "lo_que_lee_el_alumno": traducir(e["mensaje"])[0],
                "veredicto_tecnico": e["mensaje"],
            })
    return filas


def _porcentaje(parte, total):
    # Sin denominador no hay porcentaje: un guion, nunca 0 % (ver CLAUDE.md).
    return f"{100 * parte / total:.1f} %".replace(".", ",") if total else "—"


def formatear_segundos(segundos):
    """83,4 -> «1:23,4». None -> vacío."""
    if segundos is None:
        return ""
    minutos, resto = divmod(max(0.0, segundos), 60)
    return f"{int(minutos)}:{resto:04.1f}".replace(".", ",")


def resumen(filas_agregadas, filas_segmentos, errores=()):
    """Las líneas del resumen de la terminal y de `resumen.txt`."""
    lineas = ["INDICADOR (a): LO QUE EVALUÓ EL SISTEMA, POR DEPORTISTA Y TÉCNICA", ""]
    encabezado = f"  {'deportista':<11}{'técnica':<16}{'tramo':<10}{'ejecut.':>8}{'evalua.':>8}{'bien':>6}{'mal':>5}{'% bien':>9}"
    lineas.append(encabezado)
    for fila in filas_agregadas:
        lineas.append(f"  {fila['deportista']:<11}{fila['tecnica']:<16}{fila['contexto']:<10}"
                      f"{fila['repeticiones_ejecutadas']!s:>8}{fila['evaluaciones']:>8}"
                      f"{fila['correctas']:>6}{fila['incorrectas']:>5}{fila['porcentaje_correctas']:>9}")
    avisos = [f for f in filas_segmentos if f["advertencias"]]
    if avisos:
        lineas += ["", "TRAMOS CON ADVERTENCIAS"]
        lineas += [f"  {f['archivo']} [{f['desde'] or 'inicio'}–{f['hasta'] or 'fin'}]: {f['advertencias']}"
                   for f in avisos]
    if errores:
        lineas += ["", "FILAS DEL INVENTARIO QUE NO SE ANALIZARON"] + [f"  {e}" for e in errores]
    lineas += ["",
               "«ejecut.» son las repeticiones que declaraste; «evalua.», lo que la base habría",
               "registrado. Dos repeticiones seguidas sin volver a otra postura cuentan como una."]
    return lineas


# ---------------------------------------------------------------------------
# Lo que necesita OpenCV y MediaPipe: se importa dentro, como en las demás herramientas
# ---------------------------------------------------------------------------

def recorrer(ruta, desde_s=None, hasta_s=None, espejado=False):
    """`(timestamp_ms, diagnosticos, orientacion)` de cada fotograma del tramo."""
    from expert_system.analyzer import TechniqueAnalyzer
    from vision.camera import Camera
    from vision.tracker import PoseTracker

    # La pantalla en vivo voltea los archivos; un video ya espejado se deja como está.
    camara = Camera(str(ruta), espejo=not espejado)
    rastreador = PoseTracker()
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65)
    desde_ms = (desde_s or 0) * 1000
    hasta_ms = None if hasta_s is None else hasta_s * 1000
    try:
        while True:
            fotograma = camara.get_frame()
            if fotograma is None:
                return
            marca = int(camara.marca_de_tiempo_ms())
            if marca < desde_ms:
                continue
            if hasta_ms is not None and marca > hasta_ms:
                return
            resultado = rastreador.process_frame(fotograma, marca)
            if not resultado.pose_landmarks:
                yield marca, None, None
                continue
            landmarks = resultado.pose_landmarks[0]
            alto, ancho = fotograma.shape[:2]
            orientacion = orientacion_frente_a_camara((landmarks[24].x, landmarks[24].z),
                                                      (landmarks[23].x, landmarks[23].z))
            yield marca, [analizador.analyze_tsuki(landmarks, ancho, alto, marca),
                          analizador.analyze_stance(landmarks, ancho, alto),
                          analizador.analyze_mae_geri(landmarks, ancho, alto, marca)], orientacion
    finally:
        camara.release()
        rastreador.close()


def analizar(carpeta, segmentos, escribir=print):
    """Recorre cada tramo y devuelve `[(segmento, conteo)]`."""
    resultados = []
    for indice, segmento in enumerate(segmentos, start=1):
        tramo = (f" [{formatear_segundos(segmento['desde']) or 'inicio'}–"
                 f"{formatear_segundos(segmento['hasta']) or 'fin'}]")
        escribir(f"  {indice}/{len(segmentos)}  {segmento['archivo']}{tramo}  "
                 f"{segmento['deportista']} · {NOMBRES[segmento['tecnica']]}")
        inicio = datetime.datetime.now()
        conteo = contar(recorrer(Path(carpeta) / segmento["archivo"], segmento["desde"],
                                 segmento["hasta"], segmento["espejado"]))
        segundos = (datetime.datetime.now() - inicio).total_seconds()
        escribir(f"         {conteo['fotogramas']} fotogramas en {segundos:.0f} s; "
                 f"{len(conteo['evaluaciones'])} evaluaciones")
        resultados.append((segmento, conteo))
    return resultados


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Analiza por lotes los videos de una carpeta, según su inventario. "
                    "Solo lectura: no escribe en la base de datos.")
    parser.add_argument("carpeta", help="carpeta con los videos")
    parser.add_argument("--inventario", help=f"ruta del inventario (por omisión, {INVENTARIO} en la carpeta)")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--plantilla", action="store_true",
                      help="crea el inventario, o le añade los videos nuevos")
    modo.add_argument("--rubrica", action="store_true",
                      help="crea la planilla del sensei, una fila por repetición")
    args = parser.parse_args(argv)

    carpeta = Path(args.carpeta).expanduser()
    if not carpeta.is_dir():
        print(f"No existe la carpeta {carpeta}")
        return 1
    ruta_inventario = Path(args.inventario).expanduser() if args.inventario else carpeta / INVENTARIO

    if args.plantilla:
        nuevas = escribir_plantilla(carpeta, ruta_inventario)
        print(f"{ruta_inventario}: {nuevas} video(s) nuevo(s) añadido(s).")
        print("Complétalo en Excel o Numbers y guárdalo como CSV con el mismo nombre.")
        return 0

    if not ruta_inventario.exists():
        print(f"No hay inventario en {ruta_inventario}. Créalo con --plantilla.")
        return 1
    segmentos, errores = leer_inventario(ruta_inventario, carpeta)
    for error in errores:
        print(f"  ! {error}")
    if not segmentos:
        print("El inventario no tiene ninguna fila con técnica: no hay nada que analizar.")
        return 1

    if args.rubrica:
        destino = carpeta / RUBRICA
        filas = filas_de_rubrica(segmentos)
        _escribir_csv(destino, COLUMNAS_RUBRICA, filas)
        print(f"{destino}: {len(filas)} fila(s) para el sensei.")
        print("Llena lado (izq/der), valoracion (correcta, incorrecta o no evaluable) y motivo,")
        print("viendo cada repetición SIN consultar antes lo que dijo el sistema.")
        return 0

    print(f"Analizando {len(segmentos)} tramo(s) de {carpeta} con los umbrales de literatura")
    resultados = analizar(carpeta, segmentos)

    salida = carpeta / f"resultados_{datetime.datetime.now():%Y%m%d_%H%M}"
    salida.mkdir(exist_ok=True)
    filas_segmentos = [fila_de_segmento(s, c) for s, c in resultados]
    filas_agregadas = agregar(resultados)
    _escribir_csv(salida / "segmentos.csv", list(filas_segmentos[0]), filas_segmentos)
    if filas_agregadas:
        _escribir_csv(salida / "deportista_tecnica.csv", list(filas_agregadas[0]), filas_agregadas)
    filas_eval = filas_de_evaluaciones(resultados)
    if filas_eval:
        _escribir_csv(salida / "evaluaciones.csv", list(filas_eval[0]), filas_eval)
    lineas = resumen(filas_agregadas, filas_segmentos, errores)
    (salida / "resumen.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print()
    print("\n".join(lineas))
    print(f"\nResultados en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
