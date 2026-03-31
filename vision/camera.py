import cv2

class Camera:
    def __init__(self, source=1):
        # Inicializa la cámara (2 para Camo/iPhone, 0 para OBS o 1 Webcam integrada)
        self.cap = cv2.VideoCapture(source) 

    def get_frame(self):
        # Lee un cuadro y lo voltea (efecto espejo)
        ret, frame = self.cap.read() # Lee un cuadro de video
        if not ret: 
            return None
        return cv2.flip(frame, 0) # 1 para el efecto espejo, 0 para dejarlo normal

    def release(self):
        # Libera el hardware al terminar
        self.cap.release()