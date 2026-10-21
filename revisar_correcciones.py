"""
Qué le habría dicho el sistema al alumno, sobre una grabación, sin abrir la
interfaz.

Herramienta de diagnóstico, como `revisar_tsuki.py` y `comparar_2d_3d.py`. No
escribe en la base ni toca el sistema: recorre una grabación con el mismo
analizador de la pantalla en vivo y la misma lista de correcciones
(`gui/panel_vivo.FeedCorrecciones`, con la regla del sostenido), y escribe en
la terminal cada corrección en el segundo en que habría aparecido, traducida
como la lee el alumno y con el veredicto técnico al lado.

---------------------------------------------------------------------------
POR QUÉ EXISTE
---------------------------------------------------------------------------

El protocolo del 19-oct pedía pasar la Mae Geri y las tomas con errores a
propósito por la interfaz, una por una, con una base de datos aparte y una
captura de pantalla de cada reporte. Son seis videos, y la campaña del dojo
traerá más. Lo que se quería ver de esa sesión —qué corrección aparece, cuándo
y en qué palabras— no necesita la ventana: es la lista de correcciones, y esa
lista es lógica pura.

Lo que esta herramienta NO verifica, y por eso no sustituye a una prueba en la
interfaz: el dibujo del video, la técnica ideal, la articulación en rojo y el
reporte de sesión. Esas piezas se ven en la Mac.

Juzga con los umbrales de literatura (`UMBRALES_LITERATURA`), que son los que
siembra una base nueva: el mismo criterio que vería una sesión de prueba con
`SHOTOKAN_BD` apuntando a una base vacía.

Uso:

    python3 revisar_correcciones.py "grabacion.mp4"
    python3 revisar_correcciones.py "grabacion.mp4" --desde 3
"""
import argparse
import sys
from collections import Counter

from gui.coaching import traducir
from gui.panel_vivo import FeedCorrecciones

# Cómo se agrupan las categorías en el resumen final.
GRUPOS = {
    "postura": "Postura",
    "codo_izq": "Tsuki",
    "codo_der": "Tsuki",
    "mae_geri_izq": "Mae Geri",
    "mae_geri_der": "Mae Geri",
}


def correcciones_de(fotogramas):
    """
    Las correcciones que la lista en vivo habría anotado, en orden cronológico.

    `fotogramas` es un iterable de `(timestamp_ms, diagnosticos)`, donde
    `diagnosticos` es lo que devuelven juntos los tres análisis del fotograma.
    """
    lista = FeedCorrecciones(maximo=sys.maxsize)
    for timestamp_ms, diagnosticos in fotogramas:
        lista.registrar(diagnosticos, timestamp_ms)
    return list(reversed(lista.entradas))


def linea(entrada):
    """«00:12  ✗  Flexiona más la rodilla de adelante   [ZENKUTSU (...): ...]»."""
    instruccion, _ = traducir(entrada["mensaje"])
    marca = "✓" if entrada["correcto"] else "✗"
    return f"{entrada['tiempo']}  {marca}  {instruccion}   [{entrada['mensaje']}]"


def resumen(entradas):
    """Por técnica, cuántas correcciones aparecieron como correctas e incorrectas."""
    cuentas = Counter()
    for entrada in entradas:
        grupo = GRUPOS.get(entrada["categoria"], entrada["categoria"])
        cuentas[(grupo, bool(entrada["correcto"]))] += 1
    grupos = sorted({grupo for grupo, _ in cuentas})
    return [(grupo, cuentas[(grupo, True)], cuentas[(grupo, False)]) for grupo in grupos]


def informar(entradas, escribir=print):
    if not entradas:
        escribir("El sistema no habría mostrado ninguna corrección en esta grabación.")
        escribir("Ningún veredicto cerrado se sostuvo: o la técnica no se reconoció,")
        escribir("o la toma no permite medirla (revisa el plano con comparar_2d_3d.py).")
        return
    escribir("LO QUE HABRÍA LEÍDO EL ALUMNO, EN ORDEN")
    for entrada in entradas:
        escribir("  " + linea(entrada))
    escribir("")
    escribir("RESUMEN POR TÉCNICA")
    escribir(f"  {'técnica':<12}{'correctas':>11}{'incorrectas':>13}")
    for grupo, bien, mal in resumen(entradas):
        escribir(f"  {grupo:<12}{bien:>11}{mal:>13}")


def recorrer(fuente, desde_seg=0.0):
    """Los diagnósticos de cada fotograma, con el analizador de la pantalla en vivo."""
    from expert_system.analyzer import TechniqueAnalyzer
    from vision.camera import Camera
    from vision.tracker import PoseTracker

    camara = Camera(fuente, espejo=True)
    rastreador = PoseTracker()
    analizador = TechniqueAnalyzer(umbral_visibilidad=0.65)
    try:
        while True:
            fotograma = camara.get_frame()
            if fotograma is None:
                return
            marca = int(camara.marca_de_tiempo_ms())
            resultado = rastreador.process_frame(fotograma, marca)
            if marca < desde_seg * 1000 or not resultado.pose_landmarks:
                continue
            landmarks = resultado.pose_landmarks[0]
            alto, ancho = fotograma.shape[:2]
            yield marca, [analizador.analyze_tsuki(landmarks, ancho, alto, marca),
                          analizador.analyze_stance(landmarks, ancho, alto),
                          analizador.analyze_mae_geri(landmarks, ancho, alto, marca)]
    finally:
        camara.release()
        rastreador.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Qué correcciones habría mostrado el sistema sobre esta grabación. "
                    "Solo lectura: no escribe en la base de datos.")
    parser.add_argument("fuente", help="ruta de la grabación a analizar")
    parser.add_argument("--desde", type=float, default=0.0, metavar="SEG",
                        help="descarta los primeros segundos")
    args = parser.parse_args(argv)

    print(f"Revisando {args.fuente} con los umbrales de literatura")
    informar(correcciones_de(recorrer(args.fuente, desde_seg=args.desde)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
