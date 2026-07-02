from collections import deque

class MovingAverageFilter:
    """
    Filtro de Media Móvil Simple (SMA) - Anti-Jitter.
    Suaviza una señal 1D (ej. el ángulo de una articulación) promediando
    las últimas 'window' mediciones. Elimina el temblor visual que produce
    el ruido natural de MediaPipe (ej. saltos de 170° a 174° en estático).
    """
    def __init__(self, window=5):
        # deque con maxlen actúa como buffer circular: al llegar la medición
        # número 6, la más vieja se descarta automáticamente.
        self.buffer = deque(maxlen=window)

    def update(self, value):
        """Agrega una nueva medición y devuelve el promedio suavizado."""
        self.buffer.append(value)
        return sum(self.buffer) / len(self.buffer)

    def reset(self):
        """
        Vacía el historial. Se llama cuando la articulación se oculta,
        para que al reaparecer no se promedie con valores obsoletos.
        """
        self.buffer.clear()
