"""
fakes.py — Dobles de prueba (test doubles) del proyecto.

El sistema depende de hardware (cámara) y de un modelo de visión por
computadora (MediaPipe) que no están disponibles en un servidor de
integración continua. Estos dobles reemplazan esas dependencias por
objetos sintéticos con el MISMO contrato, para que la lógica de negocio
(geometría, reglas de karate, máquina de estados, persistencia) sea
verificable sin cámara, sin GPU y sin una persona frente al lente.
"""
import math

import numpy as np

# MediaPipe Pose entrega 33 puntos anatómicos por persona detectada.
NUM_LANDMARKS = 33

# Índices oficiales de MediaPipe usados por el sistema experto.
HOMBRO_DER, HOMBRO_IZQ = 11, 12
CODO_DER, CODO_IZQ = 13, 14
MUNECA_DER, MUNECA_IZQ = 15, 16
CADERA_DER, CADERA_IZQ = 23, 24
RODILLA_DER, RODILLA_IZQ = 25, 26
TOBILLO_DER, TOBILLO_IZQ = 27, 28

# OJO — MODO ESPEJO: el analizador invierte los lados a propósito (el video se
# voltea horizontalmente para que el karateka se vea como en un espejo). Por eso
# lo que en pantalla es el brazo "IZQ" se calcula con los índices 12/14/16, que
# en la nomenclatura de MediaPipe son el lado derecho anatómico. Estos alias
# nombran los índices tal como los usa el analizador, para que las pruebas se
# lean igual que el código bajo prueba.
BRAZO_IZQ_VISUAL = (HOMBRO_IZQ, CODO_IZQ, MUNECA_IZQ)      # 12, 14, 16
BRAZO_DER_VISUAL = (HOMBRO_DER, CODO_DER, MUNECA_DER)      # 11, 13, 15
PIERNA_IZQ_VISUAL = (CADERA_IZQ, RODILLA_IZQ, TOBILLO_IZQ)  # 24, 26, 28
PIERNA_DER_VISUAL = (CADERA_DER, RODILLA_DER, TOBILLO_DER)  # 23, 25, 27


class LandmarkFalso:
    """
    Réplica mínima de un landmark de MediaPipe.

    El sistema solo consume cuatro atributos (x, y normalizados 0-1,
    profundidad z y visibility 0-1), así que reproducirlos es suficiente
    para que analyzer.py no distinga este objeto del real.
    """

    __slots__ = ("x", "y", "z", "visibility")

    def __init__(self, x=0.5, y=0.5, z=0.0, visibility=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility

    def __repr__(self):
        return f"LandmarkFalso(x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f}, vis={self.visibility:.2f})"


def _colocar_articulacion(landmarks, indices, vertice, angulo_grados,
                          longitud=0.15, orientacion_grados=-90.0, visibilidad=1.0):
    """
    Coloca los tres puntos de una articulación de modo que el ángulo interno
    medido en el vértice sea exactamente `angulo_grados`.

    El segmento proximal (ej. hombro->codo) se dibuja en la dirección
    `orientacion_grados` y el distal (codo->muñeca) se rota ese ángulo, así
    que la prueba declara el ángulo que quiere probar en vez de "adivinar"
    coordenadas.
    """
    idx_a, idx_b, idx_c = indices
    vx, vy = vertice

    rad_a = math.radians(orientacion_grados)
    rad_c = math.radians(orientacion_grados + angulo_grados)

    landmarks[idx_b] = LandmarkFalso(vx, vy, visibility=visibilidad)
    landmarks[idx_a] = LandmarkFalso(vx + longitud * math.cos(rad_a),
                                     vy + longitud * math.sin(rad_a),
                                     visibility=visibilidad)
    landmarks[idx_c] = LandmarkFalso(vx + longitud * math.cos(rad_c),
                                     vy + longitud * math.sin(rad_c),
                                     visibility=visibilidad)
    return landmarks


def _trasladar_extremidad(landmarks, indices, dy):
    """
    Desplaza verticalmente los tres puntos de una extremidad completa.

    Una traslación rígida NO altera el ángulo interno de la articulación, así
    que permite elevar la pierna (como en una patada) manteniendo exactamente
    el ángulo de rodilla que la prueba declaró. Mover solo el tobillo, en
    cambio, cambiaría el ángulo sin querer.
    """
    for indice in indices:
        landmarks[indice].y += dy
    return landmarks


def pose_sintetica(angulo_codo_izq=175.0, angulo_codo_der=175.0,
                   angulo_rodilla_izq=175.0, angulo_rodilla_der=175.0,
                   visibilidad=1.0, visibilidad_brazos=None, visibilidad_piernas=None,
                   z_tobillo_izq=0.0, z_tobillo_der=0.0,
                   y_tobillo_izq=None, y_tobillo_der=None):
    """
    Construye una lista de 33 landmarks que representa una pose con los
    ángulos articulares pedidos. Es el equivalente sintético de "una persona
    parada frente a la cámara haciendo exactamente esta técnica".

    z_tobillo_izq / z_tobillo_der controlan la profundidad de los tobillos,
    que es como el analizador decide qué pierna va adelante (la guardia).
    """
    vis_brazos = visibilidad if visibilidad_brazos is None else visibilidad_brazos
    vis_piernas = visibilidad if visibilidad_piernas is None else visibilidad_piernas

    landmarks = [LandmarkFalso(0.5, 0.5, visibility=visibilidad) for _ in range(NUM_LANDMARKS)]

    _colocar_articulacion(landmarks, BRAZO_IZQ_VISUAL, (0.62, 0.40), angulo_codo_izq,
                          visibilidad=vis_brazos)
    _colocar_articulacion(landmarks, BRAZO_DER_VISUAL, (0.38, 0.40), angulo_codo_der,
                          visibilidad=vis_brazos)
    _colocar_articulacion(landmarks, PIERNA_IZQ_VISUAL, (0.58, 0.70), angulo_rodilla_izq,
                          visibilidad=vis_piernas)
    _colocar_articulacion(landmarks, PIERNA_DER_VISUAL, (0.42, 0.70), angulo_rodilla_der,
                          visibilidad=vis_piernas)

    # Altura del tobillo (pie en el suelo ~0.9, pie en el aire ~0.5): la pierna
    # entera se traslada para preservar el ángulo de rodilla pedido.
    if y_tobillo_izq is not None:
        _trasladar_extremidad(landmarks, PIERNA_IZQ_VISUAL, y_tobillo_izq - landmarks[TOBILLO_IZQ].y)
    if y_tobillo_der is not None:
        _trasladar_extremidad(landmarks, PIERNA_DER_VISUAL, y_tobillo_der - landmarks[TOBILLO_DER].y)

    landmarks[TOBILLO_IZQ].z = z_tobillo_izq
    landmarks[TOBILLO_DER].z = z_tobillo_der
    return landmarks


class CamaraSintetica:
    """
    Cámara falsa: cumple el contrato de vision.camera.Camera (get_frame /
    release) devolviendo un frame generado en memoria. Permite ejercitar la
    GUI y el pipeline de video sin hardware conectado.
    """

    def __init__(self, ancho=640, alto=480, frames_disponibles=None):
        self.ancho = ancho
        self.alto = alto
        self.frames_entregados = 0
        self.liberada = False
        # None = flujo infinito; un entero simula que el video se corta.
        self.frames_disponibles = frames_disponibles

    def get_frame(self):
        if self.frames_disponibles is not None and self.frames_entregados >= self.frames_disponibles:
            return None  # mismo contrato que la cámara real cuando falla la lectura
        self.frames_entregados += 1
        frame = np.zeros((self.alto, self.ancho, 3), dtype=np.uint8)
        frame[:, :, 1] = 120  # tinte verdoso: confirma que el frame trae contenido real
        return frame

    def release(self):
        self.liberada = True
