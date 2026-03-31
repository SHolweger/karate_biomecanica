import cv2
import time

# Importamos nuestros módulos
from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer
from biomechanics.geometry import BiomechanicsMath  # <-- Nueva importación

def main():
    print("Iniciando componentes del sistema experto...")
    
    cam = Camera(source=1) 
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    
    start_time = time.time()
    
    while True:
        frame = cam.get_frame()
        if frame is None: break
            
        timestamp_ms = int((time.time() - start_time) * 1000)
        h, w, _ = frame.shape  # Necesitamos las dimensiones para las coordenadas
        
        result = tracker.process_frame(frame, timestamp_ms)
        
        # 1. Dibujamos el esqueleto primero (capa base)
        frame = renderer.draw(frame, result.pose_landmarks)
        
        # 2. LÓGICA BIOMECÁNICA: Evaluando el brazo izquierdo
        if result.pose_landmarks:
            # Extraemos la primera persona detectada
            landmarks = result.pose_landmarks[0]
            
            # Transformamos las coordenadas normalizadas a píxeles
            hombro = (int(landmarks[11].x * w), int(landmarks[11].y * h))
            codo = (int(landmarks[13].x * w), int(landmarks[13].y * h))
            muneca = (int(landmarks[15].x * w), int(landmarks[15].y * h))
            
            # Calculamos el ángulo
            angulo_codo = BiomechanicsMath.calculate_angle(hombro, codo, muneca)
            
            # Lógica de Color Experta (Regla del Tsuki)
            # Un bloqueo o golpe sano no debe hiperextenderse a 180 exactos.
            if 160 <= angulo_codo <= 175:
                color_texto = (0, 255, 0)  # Verde: Técnica Correcta
                estado = "CORRECTO"
            else:
                color_texto = (0, 0, 255)  # Rojo: Técnica Incorrecta (Flexionado o Hiperextendido)
                estado = "INCORRECTO"
                
            # Mostramos el ángulo exacto flotando junto al codo
            cv2.putText(frame, f"{int(angulo_codo)}", (codo[0] + 20, codo[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_texto, 2)
            
            # Mostramos el estado en la esquina superior
            cv2.putText(frame, f"Tsuki Izquierdo: {estado}", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color_texto, 3)
        
        cv2.imshow('Karate AI - Vision Directa', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()