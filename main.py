import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

# 1. EL "MAPA" DEL ESQUELETO (Biomecánica)
# Definimos manualmente qué articulación se une con cuál. 
# Ej: (11, 13) significa "unir Hombro Izquierdo(11) con Codo Izquierdo(13)"
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Brazos
    (11, 23), (12, 24), (23, 24),                     # Torso
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), # Piernas
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10)         # Rostro
]

# 2. Configuración del Modelo de IA
model_path = 'pose_landmarker_full.task'

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

# 3. Inicializar Cámara
cap = cv2.VideoCapture(2) # Usando Camo (2)

print("Iniciando motor biomecánico... Presiona 'q' para salir.")

with PoseLandmarker.create_from_options(options) as landmarker:
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1) # Efecto espejo
        h, w, _ = frame.shape

        timestamp_ms = int((time.time() - start_time) * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        pose_landmarker_result = landmarker.detect_for_video(mp_image, timestamp_ms)

        # 4. RENDERIZADO PROPIO DEL ESQUELETO
        if pose_landmarker_result.pose_landmarks:
            for landmark_list in pose_landmarker_result.pose_landmarks:
                
                # A. Dibujar los "Huesos" (Vectores entre articulaciones)
                for connection in POSE_CONNECTIONS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    
                    # Extraemos los datos 3D de los dos puntos a conectar
                    start_lm = landmark_list[start_idx]
                    end_lm = landmark_list[end_idx]
                    
                    # Transformamos las coordenadas de IA a Píxeles de pantalla
                    start_point = (int(start_lm.x * w), int(start_lm.y * h))
                    end_point = (int(end_lm.x * w), int(end_lm.y * h))
                    
                    # Trazamos la línea (Color Fucsia)
                    cv2.line(frame, start_point, end_point, (245, 66, 230), 2)

                # B. Dibujar las "Articulaciones" (Nodos)
                for lm in landmark_list:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    # Dibujamos el círculo (Color Naranja) sobre las líneas
                    cv2.circle(frame, (cx, cy), 4, (245, 117, 66), cv2.FILLED)

        cv2.imshow('Karate AI - Vision Directa', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()