"""
Si la cámara está puesta donde hace falta, y qué decir cuando no.

Vive en `vision/` junto a `fuentes.py` porque responde una pregunta sobre la
captura, no sobre la técnica: ¿esta toma permite medir lo que se va a medir?
No importa MediaPipe ni OpenCV —solo lee el atributo `visibility` de los
puntos y unos pocos números—, de modo que la integración continua puede
verificarlo sin cámara.

---------------------------------------------------------------------------
POR QUÉ HACE FALTA (medido, no supuesto)
---------------------------------------------------------------------------

El sistema falla **en silencio** ante una toma mal puesta, y de dos maneras
distintas que el instructor no puede distinguir mirando la pantalla:

1. **Articulación fuera de cuadro.** Sobre una grabación con el ejecutante de
   cuerpo entero, la visibilidad media de las rodillas es de 0,95–0,98; con un
   encuadre malo cae a 0,00. La separación es limpia, así que basta un umbral.

2. **Plano equivocado.** Este es el que no se ve venir. Los ángulos se calculan
   sobre la proyección 2D, y la proyección arrastra todo ángulo hacia 90°
   cuanto más apunte el segmento a la cámara. Medido sobre 637 fotogramas de
   Zenkutsu Dachi grabados de frente: la postura **no se reconoció ni una sola
   vez**. De perfil, el 40,5 %. No es que acierte menos de frente: es ciego.

El segundo caso es el que justifica este módulo. Las articulaciones se ven
perfectamente, la visibilidad es alta, el esqueleto se dibuja bien y el sistema
mide números que no guardan relación con el cuerpo real. Nada en la pantalla lo
delata. En una campaña de recolección eso significa volver del dojo con datos
inservibles y enterarse al analizarlos.

---------------------------------------------------------------------------
LO QUE ESTE MÓDULO **NO** HACE
---------------------------------------------------------------------------

No condiciona el aviso a la técnica detectada, y no es un descuido. Reconocer
la técnica es justamente lo que falla cuando el plano está mal, así que
esperar a saber qué se está ejecutando para avisar de que no se puede saber
sería circular. El aviso de plano es **informativo y permanente**: dice para
qué sirve la posición actual de la cámara, y el instructor —que sí sabe qué va
a pedir— decide.

Tampoco usa la puntuación de visibilidad como garantía de que un ángulo sea
correcto. Medido el 29-sep-2026: la pierna peor medida de una grabación marcaba
0,958 de visibilidad media. El estimador infiere las articulaciones ocluidas
sin bajar esa cifra, de modo que sirve para saber si algo está **en cuadro**,
no para saber si está **bien medido**.
"""

# Mismo umbral que emplea `TechniqueAnalyzer` para decidir si una articulación
# cuenta. Se repite aquí como valor por defecto y no se importa de allá para no
# atar este módulo al sistema experto, pero si uno cambia debe cambiar el otro.
VISIBILIDAD_MINIMA = 0.65

# Cortes de orientación, los mismos que usa `comparar_2d_3d.py` al desglosar
# por ángulo de cámara, para que el aviso y la medición hablen de lo mismo.
ORIENTACION_FRONTAL = 0.80
ORIENTACION_PERFIL = 0.50

# Índices de MediaPipe Pose agrupados por parte del cuerpo, con el nombre que
# el instructor usaría. El orden importa: es el de gravedad con que se avisa.
GRUPOS = [
    ("piernas", "las piernas", (23, 24, 25, 26, 27, 28)),
    ("brazos", "los brazos", (11, 12, 13, 14, 15, 16)),
]

NIVEL_ALTO, NIVEL_MEDIO, NIVEL_INFO = "alto", "medio", "info"

SIN_PERSONA = "No se detecta a nadie en cuadro."

# Para qué sirve cada posición de cámara. Sale de la medición del 29-sep sobre
# Zenkutsu Dachi (0,0 % de frente contra 40,5 % de perfil) y del principio que
# la explica: cada técnica se mide en el plano en que ocurre.
PLANO = {
    "frontal": "Cámara de frente: sirve para Heiko Dachi y Kiba Dachi. "
               "Zenkutsu, Kokutsu, Tsuki y Mae Geri necesitan perfil.",
    "perfil": "Cámara de perfil: sirve para Zenkutsu, Kokutsu, Tsuki y Mae Geri. "
              "Heiko Dachi y Kiba Dachi se miden mejor de frente.",
    "oblicuo": "Cámara en diagonal: ninguna técnica se mide bien así. "
               "Colócala de frente o de perfil.",
}


def visibilidades_por_grupo(landmarks):
    """
    La visibilidad del punto PEOR visto de cada grupo.

    Se toma el mínimo y no el promedio porque una rodilla fuera de cuadro
    invalida la medición de esa pierna aunque la cadera y el tobillo se vean
    perfectamente: el ángulo necesita los tres puntos. Un promedio la
    escondería detrás de los otros dos.
    """
    return {clave: min(landmarks[i].visibility for i in indices)
            for clave, _etiqueta, indices in GRUPOS}


def clasificar_plano(orientacion):
    """De 1,0 (de frente) a 0,0 (de perfil), a la etiqueta del plano."""
    if orientacion is None:
        return None
    if orientacion > ORIENTACION_FRONTAL:
        return "frontal"
    if orientacion < ORIENTACION_PERFIL:
        return "perfil"
    return "oblicuo"


def evaluar(landmarks=None, orientacion=None, umbral=VISIBILIDAD_MINIMA):
    """
    Los avisos que merece esta toma, del más grave al más leve.

    Cada aviso es un dict con `nivel` y `mensaje`. La lista vacía significa que
    la toma está bien **para lo que el módulo puede comprobar**, que no es lo
    mismo que garantizar que la medición sea correcta: ver el encabezado.

    `landmarks` en None representa un fotograma sin pose detectada, que es un
    caso distinto de «hay pose y no se le ven las piernas» y merece otro texto.
    """
    avisos = []

    if landmarks is None:
        avisos.append({"nivel": NIVEL_ALTO, "mensaje": SIN_PERSONA})
    else:
        por_grupo = visibilidades_por_grupo(landmarks)
        etiquetas = {clave: etiqueta for clave, etiqueta, _ in GRUPOS}
        fuera = [etiquetas[clave] for clave, _e, _i in GRUPOS
                 if por_grupo[clave] <= umbral]
        if fuera:
            # Todos los grupos se nombran en plural ("las piernas", "los
            # brazos"), así que el verbo no cambia con la cantidad.
            avisos.append({
                "nivel": NIVEL_ALTO,
                "mensaje": f"No se ven {' ni '.join(fuera)}. Aleja la cámara o "
                           f"inclínala hasta que el cuerpo entre completo.",
            })

    plano = clasificar_plano(orientacion)
    if plano is not None:
        avisos.append({
            "nivel": NIVEL_MEDIO if plano == "oblicuo" else NIVEL_INFO,
            "mensaje": PLANO[plano],
        })

    return avisos
