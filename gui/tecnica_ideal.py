"""
La figura de la técnica ideal, dibujada con el criterio vigente.

El prototipo `.dc.html` mostraba un panel «Técnica ideal» que gustó mucho, pero
el muñeco era el mismo para todas las técnicas: una interpolación fija entre dos
poses de puñetazo. Con «Técnica ideal · Mae-geri» en el título, la figura
lanzaba un golpe de puño. Era decoración.

Aquí la figura **se calcula**, no se dibuja a mano:

- Cada articulación que juzga la regla se coloca en el **centro de su rango
  vigente**. Si el cuerpo técnico recalibra el Zenkutsu desde la interfaz, la
  figura cambia sola, porque sale del mismo `KarateRules` que juzga al alumno.
  Es la misma decisión de «los umbrales son datos» aplicada a la presentación.
- Los segmentos tienen proporciones antropométricas fijas (fracciones de la
  estatura, tablas de Drillis y Contini). Ninguno se estira para que el ángulo
  cuadre: el ángulo se obtiene resolviendo el triángulo cadera-rodilla-tobillo.
- Se dibuja **en el plano en que se filma la técnica**: de perfil las
  sagitales, de frente Heiko y Kiba. Es la regla del protocolo de cámara, y la
  figura la enseña sin necesidad de explicarla.

Y una consecuencia que se verifica en las pruebas: medida con la misma función
con que se mide al alumno (`BiomechanicsMath.calculate_angle`), la figura da
los ángulos del criterio, el clasificador la reconoce como la técnica que dice
ser y la regla la aprueba. La guía no puede enseñar algo que el propio sistema
reprobaría.

Lo que la figura **no** muestra, a propósito: rotación de cadera, giro del
puño, velocidad o reparto del peso. El sistema no los mide, y una guía que los
dibujara prometería una corrección que nadie va a hacer. Lo que no se juzga se
dibuja en una postura neutra y sin resaltar.

Coordenadas: fracciones de la estatura, con `y` hacia ABAJO como en la imagen.
El suelo está en `y = 1`. Este módulo no importa CustomTkinter, así que corre
en integración continua; la pantalla solo traza lo que aquí se calcula.
"""
import math
from dataclasses import dataclass

from expert_system.knowledge_base import KarateRules

# Longitudes de segmento en fracciones de la estatura (Drillis y Contini, 1966).
MUSLO = 0.245
PIERNA = 0.246
BRAZO = 0.186
ANTEBRAZO = 0.146
TRONCO = 0.288           # de la línea de caderas a la de hombros
CUELLO = 0.05
RADIO_CABEZA = 0.06
ALTURA_TOBILLO = 0.04
ANCHO_CADERAS = 0.18     # entre articulaciones de cadera, vista de frente
ANCHO_HOMBROS = 0.26
PIE = 0.10

# Qué fracción de la distancia cadera-tobillo baja en vertical la cadera en una
# postura de paso largo. Fija la longitud de la postura sin estirar ningún
# segmento: con 0,92, un Zenkutsu de rangos de literatura mide unos 0,49
# estaturas de largo, cerca de dos anchos de hombros.
CAIDA_DE_CADERA = 0.92

# Separación de los pies en Kiba Dachi: unos dos anchos de hombros.
APERTURA_KIBA = 0.26     # del centro a cada tobillo

# Carga de la Mae Geri que se dibuja. No sale de un rango de la base de
# conocimiento —la regla no juzga la carga—, sino del umbral con que la
# máquina de estados la detecta: tiene que quedar holgadamente por debajo. La
# carga real medida el 12-ago-2026 llegó a 52–55°.
CARGA_MAE_GERI = 55.0

PERFIL = "de perfil"
FRENTE = "de frente"

NOMBRES = {
    "heiko_dachi": "Heiko Dachi",
    "kiba_dachi": "Kiba Dachi",
    "zenkutsu_dachi": "Zenkutsu Dachi",
    "kokutsu_dachi": "Kokutsu Dachi",
    "tsuki": "Tsuki",
    "mae_geri": "Mae Geri",
}

PLANO = {
    "heiko_dachi": FRENTE,
    "kiba_dachi": FRENTE,
    "zenkutsu_dachi": PERFIL,
    "kokutsu_dachi": PERFIL,
    "tsuki": PERFIL,
    "mae_geri": PERFIL,
}

# Huesos que se trazan, por nombre de punto. Los dos juegos solo difieren en
# cómo se llaman los lados: de perfil importa cuál va adelante; de frente, cuál
# queda a cada lado de la pantalla.
SEGMENTOS_PERFIL = (
    ("cuello", "cabeza"), ("cuello", "pelvis"),
    ("cuello", "codo_a"), ("codo_a", "muneca_a"),
    ("cuello", "codo_b"), ("codo_b", "muneca_b"),
    ("pelvis", "rodilla_del"), ("rodilla_del", "tobillo_del"), ("tobillo_del", "pie_del"),
    ("pelvis", "rodilla_tras"), ("rodilla_tras", "tobillo_tras"), ("tobillo_tras", "pie_tras"),
)
SEGMENTOS_FRENTE = (
    ("cuello", "cabeza"), ("cuello", "pelvis"),
    ("hombro_izq", "hombro_der"), ("cadera_izq", "cadera_der"),
    ("hombro_izq", "codo_izq"), ("codo_izq", "muneca_izq"),
    ("hombro_der", "codo_der"), ("codo_der", "muneca_der"),
    ("cadera_izq", "rodilla_izq"), ("rodilla_izq", "tobillo_izq"),
    ("cadera_der", "rodilla_der"), ("rodilla_der", "tobillo_der"),
)


@dataclass(frozen=True)
class Articulacion:
    """Una articulación que la regla juzga: dónde está, contra qué rango y qué ángulo se dibujó."""
    vertice: str
    extremos: tuple          # (punto, punto): el ángulo es el de vertice entre ellos
    etiqueta: str
    rango: tuple             # (mínimo, máximo) del criterio vigente
    angulo: float            # el que se dibujó


@dataclass(frozen=True)
class Fase:
    nombre: str
    puntos: dict
    segmentos: tuple
    juzgadas: tuple          # de Articulacion


@dataclass(frozen=True)
class Figura:
    tecnica: str
    nombre: str
    plano: str
    fases: tuple


# ----------------------------------------------------------------- geometría

def _hipotenusa(angulo_rodilla):
    """Distancia cadera-tobillo con la rodilla a ese ángulo interno (ley del coseno)."""
    c = math.cos(math.radians(angulo_rodilla))
    return math.sqrt(MUSLO ** 2 + PIERNA ** 2 - 2 * MUSLO * PIERNA * c)


def _rodilla(cadera, tobillo, hacia):
    """
    Dónde queda la rodilla entre una cadera y un tobillo ya colocados.

    Es la intersección de dos circunferencias —una de radio MUSLO alrededor de
    la cadera y otra de radio PIERNA alrededor del tobillo— y tiene dos
    soluciones. `hacia` elige la del lado al que se dobla la rodilla: +1 hacia
    +x, -1 hacia -x. Anatómicamente la rodilla flexionada apunta adelante, y de
    frente en Kiba apunta hacia afuera.
    """
    (x0, y0), (x1, y1) = cadera, tobillo
    d = math.hypot(x1 - x0, y1 - y0)
    a = (MUSLO ** 2 - PIERNA ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(MUSLO ** 2 - a ** 2, 0.0))
    mx, my = x0 + a * (x1 - x0) / d, y0 + a * (y1 - y0) / d
    ox, oy = -(y1 - y0) / d * h, (x1 - x0) / d * h
    candidatas = ((mx + ox, my + oy), (mx - ox, my - oy))
    return max(candidatas, key=lambda p: p[0] * hacia)


def _brazo(hombro, angulo_brazo, angulo_codo, flexion):
    """
    Codo y muñeca desde el hombro.

    `angulo_brazo` es la dirección del brazo en grados (0 = hacia +x, 90 = hacia
    abajo, con y hacia abajo). `angulo_codo` es el ángulo interno del codo y
    `flexion` el sentido en que se dobla (+1 o -1).
    """
    rad = math.radians(angulo_brazo)
    codo = (hombro[0] + BRAZO * math.cos(rad), hombro[1] + BRAZO * math.sin(rad))
    giro = math.radians(angulo_brazo + flexion * (180.0 - angulo_codo))
    muneca = (codo[0] + ANTEBRAZO * math.cos(giro), codo[1] + ANTEBRAZO * math.sin(giro))
    return codo, muneca


def _tronco(pelvis):
    """Cuello y cabeza sobre la pelvis, con el tronco erguido."""
    cuello = (pelvis[0], pelvis[1] - TRONCO)
    cabeza = (pelvis[0], cuello[1] - CUELLO - RADIO_CABEZA)
    return cuello, cabeza


def _suelo():
    return 1.0 - ALTURA_TOBILLO


def _centro(rango):
    minimo, maximo = rango
    return minimo if maximo is None else (minimo + maximo) / 2.0


# ------------------------------------------------------------ las posturas

def _postura_de_paso(delantera, trasera):
    """
    Zenkutsu y Kokutsu: las dos son la misma construcción con otros ángulos.

    Los dos tobillos van al suelo y la cadera baja una fracción fija de la
    distancia cadera-tobillo más corta. El resto lo dicta la geometría.
    """
    d_del, d_tras = _hipotenusa(delantera), _hipotenusa(trasera)
    caida = CAIDA_DE_CADERA * min(d_del, d_tras)
    suelo = _suelo()
    pelvis = (0.0, suelo - caida)
    tobillo_del = (math.sqrt(d_del ** 2 - caida ** 2), suelo)
    tobillo_tras = (-math.sqrt(d_tras ** 2 - caida ** 2), suelo)
    cuello, cabeza = _tronco(pelvis)
    codo_a, muneca_a = _brazo(cuello, 80.0, 165.0, -1)
    codo_b, muneca_b = _brazo(cuello, 95.0, 165.0, -1)
    return {
        "pelvis": pelvis, "cuello": cuello, "cabeza": cabeza,
        "codo_a": codo_a, "muneca_a": muneca_a,
        "codo_b": codo_b, "muneca_b": muneca_b,
        "rodilla_del": _rodilla(pelvis, tobillo_del, +1), "tobillo_del": tobillo_del,
        "pie_del": (tobillo_del[0] + PIE, 1.0),
        "rodilla_tras": _rodilla(pelvis, tobillo_tras, +1), "tobillo_tras": tobillo_tras,
        "pie_tras": (tobillo_tras[0] + PIE * 0.6, 1.0),
    }


def _postura_de_frente(rodilla, apertura):
    """Heiko y Kiba, vistas de frente. Las rodillas se abren hacia afuera."""
    d = _hipotenusa(rodilla)
    lateral = apertura - ANCHO_CADERAS / 2
    caida = math.sqrt(d ** 2 - lateral ** 2)
    suelo = _suelo()
    pelvis = (0.0, suelo - caida)
    cad_izq, cad_der = (-ANCHO_CADERAS / 2, pelvis[1]), (ANCHO_CADERAS / 2, pelvis[1])
    tob_izq, tob_der = (-apertura, suelo), (apertura, suelo)
    cuello, cabeza = _tronco(pelvis)
    hom_izq, hom_der = (-ANCHO_HOMBROS / 2, cuello[1]), (ANCHO_HOMBROS / 2, cuello[1])
    codo_izq, muneca_izq = _brazo(hom_izq, 95.0, 170.0, +1)
    codo_der, muneca_der = _brazo(hom_der, 85.0, 170.0, -1)
    return {
        "pelvis": pelvis, "cuello": cuello, "cabeza": cabeza,
        "hombro_izq": hom_izq, "hombro_der": hom_der,
        "codo_izq": codo_izq, "muneca_izq": muneca_izq,
        "codo_der": codo_der, "muneca_der": muneca_der,
        "cadera_izq": cad_izq, "cadera_der": cad_der,
        "rodilla_izq": _rodilla(cad_izq, tob_izq, -1), "tobillo_izq": tob_izq,
        "rodilla_der": _rodilla(cad_der, tob_der, +1), "tobillo_der": tob_der,
    }


def _de_pie_de_perfil():
    """
    De pie y de perfil, piernas rectas: la base del Tsuki y de la Mae Geri.

    Los pies se separan un poco para que las dos piernas no se tapen en el
    dibujo; la cadera baja lo justo para que cada pierna conserve su largo.
    """
    suelo, paso = _suelo(), 0.02
    largo = MUSLO + PIERNA
    pelvis = (0.0, suelo - math.sqrt(largo ** 2 - paso ** 2))
    cuello, cabeza = _tronco(pelvis)
    puntos = {"pelvis": pelvis, "cuello": cuello, "cabeza": cabeza}
    for lado, x in (("del", paso), ("tras", -paso)):
        tobillo = (x, suelo)
        puntos[f"rodilla_{lado}"] = (pelvis[0] + (tobillo[0] - pelvis[0]) * MUSLO / largo,
                                     pelvis[1] + (tobillo[1] - pelvis[1]) * MUSLO / largo)
        puntos[f"tobillo_{lado}"] = tobillo
        puntos[f"pie_{lado}"] = (x + PIE, 1.0)
    return puntos


# ------------------------------------------------------------ cada técnica

def _rodillas_de_perfil(tecnica, reglas):
    rango_del = reglas.rango(tecnica, "rodilla_frontal")
    rango_tras = reglas.rango(tecnica, "rodilla_trasera")
    del_, tras = _centro(rango_del), _centro(rango_tras)
    puntos = _postura_de_paso(del_, tras)
    juzgadas = (
        Articulacion("rodilla_del", ("pelvis", "tobillo_del"), "Rodilla delantera", rango_del, del_),
        Articulacion("rodilla_tras", ("pelvis", "tobillo_tras"), "Rodilla trasera", rango_tras, tras),
    )
    return (Fase(NOMBRES[tecnica], puntos, SEGMENTOS_PERFIL, juzgadas),)


def _rodillas_de_frente(tecnica, reglas, apertura):
    rango = reglas.rango(tecnica, "rodilla")
    angulo = _centro(rango)
    puntos = _postura_de_frente(angulo, apertura)
    juzgadas = (
        Articulacion("rodilla_izq", ("cadera_izq", "tobillo_izq"), "Rodilla", rango, angulo),
        Articulacion("rodilla_der", ("cadera_der", "tobillo_der"), "Rodilla", rango, angulo),
    )
    return (Fase(NOMBRES[tecnica], puntos, SEGMENTOS_FRENTE, juzgadas),)


def _hikite(cuello, pelvis):
    """El brazo recogido, con el puño junto a la cadera: de ahí sale el golpe."""
    puno = (pelvis[0] + 0.03, pelvis[1] - 0.04)
    d = math.hypot(puno[0] - cuello[0], puno[1] - cuello[1])
    angulo_codo = math.degrees(math.acos(
        (BRAZO ** 2 + ANTEBRAZO ** 2 - d ** 2) / (2 * BRAZO * ANTEBRAZO)))
    # El brazo baja hacia atrás; el ángulo de salida se ajusta para que el puño
    # caiga exactamente junto a la cadera.
    direccion = math.degrees(math.atan2(puno[1] - cuello[1], puno[0] - cuello[0]))
    alfa = math.degrees(math.asin(ANTEBRAZO * math.sin(math.radians(angulo_codo)) / d))
    codo, muneca = _brazo(cuello, direccion + alfa, angulo_codo, -1)
    return codo, muneca, angulo_codo


def _tsuki(reglas):
    rango = reglas.rango("tsuki", "codo")
    kime = _centro(rango)
    base = _de_pie_de_perfil()
    cuello, pelvis = base["cuello"], base["pelvis"]
    codo_h, muneca_h, angulo_hikite = _hikite(cuello, pelvis)

    salida = dict(base, codo_a=codo_h, muneca_a=muneca_h, codo_b=codo_h, muneca_b=muneca_h)
    codo_k, muneca_k = _brazo(cuello, 5.0, kime, -1)
    golpe = dict(base, codo_a=codo_k, muneca_a=muneca_k, codo_b=codo_h, muneca_b=muneca_h)

    def codo(angulo):
        return (Articulacion("codo_a", ("cuello", "muneca_a"), "Codo", rango, angulo),)

    return (
        Fase("Hikite", salida, SEGMENTOS_PERFIL, codo(angulo_hikite)),
        Fase("Kime", golpe, SEGMENTOS_PERFIL, codo(kime)),
    )


def _mae_geri(reglas):
    rango = reglas.rango("mae_geri", "rodilla_kime")
    kime = _centro(rango)
    base = _de_pie_de_perfil()
    pelvis, cuello = base["pelvis"], base["cuello"]
    guardia = {}
    guardia["codo_a"], guardia["muneca_a"] = _brazo(cuello, 70.0, 90.0, -1)
    guardia["codo_b"], guardia["muneca_b"] = _brazo(cuello, 100.0, 80.0, -1)

    # Muslo horizontal hacia adelante, rodilla a la altura de la cadera.
    rodilla = (pelvis[0] + MUSLO, pelvis[1])

    def pierna(angulo):
        # Desde la rodilla, el vector hacia la cadera apunta a -x; la pierna se
        # abre `angulo` grados respecto de él, doblándose hacia abajo.
        giro = math.radians(180.0 - angulo)
        return (rodilla[0] + PIERNA * math.cos(giro), rodilla[1] + PIERNA * math.sin(giro))

    def fase(nombre, angulo):
        tobillo = pierna(angulo)
        puntos = dict(base, **guardia, rodilla_del=rodilla, tobillo_del=tobillo,
                      pie_del=(tobillo[0] + PIE * 0.5, tobillo[1] + 0.02))
        juzgada = Articulacion("rodilla_del", ("pelvis", "tobillo_del"),
                               "Rodilla", rango, angulo)
        return Fase(nombre, puntos, SEGMENTOS_PERFIL, (juzgada,))

    return (fase("Carga", CARGA_MAE_GERI), fase("Kime", kime),
            fase("Hikiashi", CARGA_MAE_GERI))


def figura(tecnica, reglas=None):
    """
    La figura ideal de una técnica, con el criterio que la juzga.

    `reglas` es el `KarateRules` vigente; sin él se usan los rangos de
    literatura. Pasar el de la sesión hace que la figura siga a una
    recalibración del cuerpo técnico.
    """
    reglas = reglas or KarateRules()
    if tecnica in ("zenkutsu_dachi", "kokutsu_dachi"):
        fases = _rodillas_de_perfil(tecnica, reglas)
    elif tecnica == "heiko_dachi":
        fases = _rodillas_de_frente(tecnica, reglas, ANCHO_CADERAS / 2)
    elif tecnica == "kiba_dachi":
        fases = _rodillas_de_frente(tecnica, reglas, APERTURA_KIBA)
    elif tecnica == "tsuki":
        fases = _tsuki(reglas)
    elif tecnica == "mae_geri":
        fases = _mae_geri(reglas)
    else:
        raise KeyError(f"No hay figura ideal para '{tecnica}'")
    return Figura(tecnica, NOMBRES[tecnica], PLANO[tecnica], fases)


def texto_rango(rango):
    """«90–115°», o «≥ 160°» si el criterio no tiene máximo."""
    minimo, maximo = rango
    if maximo is None:
        return f"≥ {minimo:.0f}°"
    return f"{minimo:.0f}–{maximo:.0f}°"


TECNICAS = tuple(NOMBRES)
