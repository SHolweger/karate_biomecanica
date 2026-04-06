import cv2
import time

# Importamos nuestros módulos (Nuestra Arquitectura Modular)
from vision.camera import Camera
from vision.tracker import PoseTracker
from biomechanics.renderer import SkeletonRenderer
from expert_system.analyzer import TechniqueAnalyzer

def main():
    print("Iniciando componentes del sistema experto...")
    
    # 1. Inicialización de Objetos
    cam = Camera(source=2)  
    tracker = PoseTracker(model_path='pose_landmarker_full.task')
    renderer = SkeletonRenderer()
    analyzer = TechniqueAnalyzer(umbral_visibilidad=0.65)
    
    start_time = time.time()
    
    # 2. Bucle Principal
    while True:
        frame = cam.get_frame()
        if frame is None: break
            
        timestamp_ms = int((time.time() - start_time) * 1000)
        h, w, _ = frame.shape
        
        # A. Visión: Extraer el esqueleto
        result = tracker.process_frame(frame, timestamp_ms)
        
        # B. Renderizado Base: Dibujar líneas y nodos
        frame = renderer.draw(frame, result.pose_landmarks)
        
        # C. Inteligencia: Analizar y mostrar diagnósticos
        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            
            # Le pedimos al analista que evalúe ambos brazos
            diagnostico_tsuki = analyzer.analyze_tsuki(landmarks, w, h)
            
            # Le pedimos al dibujante que ponga los resultados en pantalla
            frame = renderer.draw_diagnostics(frame, diagnostico_tsuki)
        
        # D. Salida: Mostrar ventana
        cv2.imshow('Karate AI - Vision Directa', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 3. Limpieza
    cam.release()
    tracker.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()