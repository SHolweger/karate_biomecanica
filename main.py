import mediapipe as mp
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from mediapipe.framework.formats import landmark_pb2
#from mediapipe.tasks.python.vision.pose_landmarker import landmark_pb2

# 1. Configuración del Modelo
model_path = 'pose_landmarker_full.task'

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 2. Configurar las opciones
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

# 3. Inicializar Cámara
cap = cv2.VideoCapture(2) # Prueba 0 = OBS, 1 = Camo o 2 = FaceTime

print("Iniciando motor biomecánico... Presiona 'q' para salir.")

with PoseLandmarker.create_from_options(options) as landmarker:
    print("Motor iniciado. Si no ves la ventana, revisa los permisos de cámara de macOS.")
    
    # Usaremos el tiempo de inicio para calcular los milisegundos transcurridos
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: 
            print("No se pudo capturar el frame.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # CALCULAMOS EL TIMESTAMP MANUALMENTE
        # (Tiempo actual - Tiempo de inicio) convertido a milisegundos
        timestamp_ms = int((time.time() - start_time) * 1000)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        # Enviamos el timestamp que calculamos nosotros
        pose_landmarker_result = landmarker.detect_for_video(mp_image, timestamp_ms)

        if pose_landmarker_result.pose_landmarks:
            for landmark_list in pose_landmarker_result.pose_landmarks:
                for lm in landmark_list:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (245, 117, 66), cv2.FILLED)

        cv2.imshow('Karate AI - Vision Directa', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()