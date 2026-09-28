import math

class BiomechanicsMath:
    @staticmethod
    def calculate_angle(point_a, point_b, point_c):
        """
        Calcula el ángulo interno en grados entre tres puntos 2D.
        point_b es el vértice (ej. el codo o la rodilla).
        """
        x1, y1 = point_a
        x2, y2 = point_b
        x3, y3 = point_c
        
        # Calculamos el ángulo en radianes y lo convertimos a grados
        radians = math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
        angle = abs(radians * 180.0 / math.pi)
        
        # El rango de movimiento de una articulación humana (ángulo interno)
        # se evalúa entre 0 y 180 grados.
        if angle > 180.0:
            angle = 360.0 - angle

        return angle

    @staticmethod
    def calculate_angle_3d(point_a, point_b, point_c):
        """
        El mismo ángulo interno, pero sobre tres puntos 3D `(x, y, z)`.

        Existe porque `calculate_angle` descarta la profundidad, y eso tiene un
        coste medido: **la proyección 2D arrastra todo ángulo hacia 90°**, tanto
        más cuanto más apunte el segmento a la cámara. Medido el 28-sep-2026
        sobre un codo real de 175°, según el giro del plano de la técnica
        respecto del sensor:

            giro    0°   ->  175°      giro   75°  ->  161°
            giro   45°   ->  173°      giro   90°  ->   90°

        A 90° de giro —una técnica lanzada de frente a la cámara— *cualquier*
        ángulo real mide 90°, y por eso un tsuki perfecto grabado de frente se
        informa como flexionado.

        MediaPipe ya entrega coordenadas 3D en `pose_world_landmarks`, del mismo
        paso de inferencia que las de imagen, así que su coste ya está pagado.
        Esta función es lo que permite **medir** si usarlas mejora el análisis
        en vez de suponerlo: ver `comparar_2d_3d.py`. Mientras esa comparación
        no se haga sobre grabaciones reales, el sistema sigue midiendo en 2D.

        Se calcula con el producto escalar y no con `atan2` porque en tres
        dimensiones no hay un signo de giro que recuperar: el ángulo entre dos
        vectores ya es el interno, entre 0 y 180. Devuelve 0.0 si algún
        segmento tiene longitud nula, que es el caso degenerado de dos
        articulaciones estimadas en el mismo punto.
        """
        ba = [a - b for a, b in zip(point_a, point_b)]
        bc = [c - b for c, b in zip(point_c, point_b)]

        norma_ba = math.sqrt(sum(v * v for v in ba))
        norma_bc = math.sqrt(sum(v * v for v in bc))
        if norma_ba == 0.0 or norma_bc == 0.0:
            return 0.0

        coseno = sum(u * v for u, v in zip(ba, bc)) / (norma_ba * norma_bc)
        # El redondeo de punto flotante puede sacar el coseno de [-1, 1] y
        # hacer que acos lance ValueError justo en los ángulos extremos (0° y
        # 180°), que son precisamente los del Kime.
        return math.degrees(math.acos(max(-1.0, min(1.0, coseno))))