import mediapipe as mp

class PoseTracker:
    def __init__(self, model_path='pose_landmarker_full.task'):
        # Configuración inicial del motor de inferencia
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
        # Creamos la instancia del modelo que se mantendrá viva
        self.landmarker = PoseLandmarker.create_from_options(options)

    def process_frame(self, frame, timestamp_ms):
        # Transforma el frame de OpenCV al formato que entiende MediaPipe y extrae datos
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def close(self):
        # Cierra el modelo limpiamente
        self.landmarker.close()