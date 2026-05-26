import cv2

class Camera:
    def __init__(self, source=0):
        # Inicializa la cámara (2 para Camo/iPhone, 0 para OBS o 1 Webcam integrada)
        self.cap = cv2.VideoCapture(source) 

    def get_frame(self):
        # Lee un cuadro y lo voltea (efecto espejo)
        ret, frame = self.cap.read() # Lee un cuadro de video
        if not ret: 
            return None
        return cv2.flip(frame, 1) #el cv2.flip sirve como espejo = 0 para no espejar, 1 para espejar horizontalmente, -1 para espejar ambos ejes
        #return frame # Devuelve el cuadro sin espejear

    def release(self):
        # Libera el hardware al terminar
        self.cap.release()