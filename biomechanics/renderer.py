import cv2

class SkeletonRenderer:
    def __init__(self):
        # El mapa anatómico del sistema
        self.POSE_CONNECTIONS = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Brazos
            (11, 23), (12, 24), (23, 24),                     # Torso
            (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), # Piernas
            (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10)         # Rostro
        ]

    def draw(self, frame, pose_landmarks):
        # Si no hay nadie en cámara, devolvemos el video intacto
        if not pose_landmarks:
            return frame

        h, w, _ = frame.shape
        
        for landmark_list in pose_landmarks:
            # A. Dibujamos los vectores (Huesos)
            for connection in self.POSE_CONNECTIONS:
                start_lm = landmark_list[connection[0]]
                end_lm = landmark_list[connection[1]]
                
                start_point = (int(start_lm.x * w), int(start_lm.y * h))
                end_point = (int(end_lm.x * w), int(end_lm.y * h))
                
                cv2.line(frame, start_point, end_point, (245, 66, 230), 2)

            # B. Dibujamos los nodos (Articulaciones)
            for lm in landmark_list:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 4, (245, 117, 66), cv2.FILLED)
        
        return frame
    
    def draw_diagnostics(self, frame, diagnostics_results):
        """
        Recibe los resultados del Analyzer y los pinta en la pantalla.
        """
        for res in diagnostics_results:
            # 1. Dibujar el texto principal arriba a la izquierda
            cv2.putText(frame, res['mensaje'], (20, res['y_offset']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, res['color'], 2)
            
            # 2. Dibujar el número de los grados junto a la articulación (si es visible)
            if res['angulo'] is not None:
                cv2.putText(frame, f"{int(res['angulo'])}", res['pos_angulo'], 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, res['color'], 2)
                
        return frame