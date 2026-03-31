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