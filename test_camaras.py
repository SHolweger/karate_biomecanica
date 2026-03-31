import cv2

def escanear_camaras():
    print("Buscando cámaras conectadas a la Mac...")
    for i in range(5): # Probamos los primeros 5 índices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"[EXITO] Cámara encontrada en el índice: {i}")
                cv2.imshow(f"Prueba de Camara {i} (Presiona cualquier tecla para cerrar)", frame)
                cv2.waitKey(0) # Espera a que presiones una tecla para probar la siguiente
                cv2.destroyWindow(f"Prueba de Camara {i}")
            cap.release()
        else:
            print(f"[FALLO] No hay cámara en el índice: {i}")

escanear_camaras()