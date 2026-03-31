import cv2
import time

# Importamos nuestras propias clases
from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer

def main():
    print("Iniciando componentes del sistema experto...")
    
    # 1. Instanciamos los módulos
    cam = Camera(source=2)
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    
    start_time = time.time()
    print("Motor iniciado. Presiona 'q' para salir.")
    
    # 2. Bucle principal de procesamiento
    while True:
        frame = cam.get_frame()
        if frame is None:
            print("No se pudo capturar el frame.")
            break
            
        timestamp_ms = int((time.time() - start_time) * 1000)
        
        # Le pasamos la imagen a la IA
        result = tracker.process_frame(frame, timestamp_ms)
        
        # Le pasamos los datos de la IA al dibujante
        frame = renderer.draw(frame, result.pose_landmarks)
        
        # Mostramos el resultado final
        cv2.imshow('Karate AI - Vision Directa', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 3. Limpieza de memoria
    cam.release()
    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()