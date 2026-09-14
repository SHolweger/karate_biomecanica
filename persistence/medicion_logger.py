NOMBRES_TECNICA = {
    "codo_izq": "Tsuki (brazo izquierdo)",
    "codo_der": "Tsuki (brazo derecho)",
    "postura": "Postura de piernas",
    "postura_der_numero": "Postura de piernas",
    "mae_geri_izq": "Mae Geri (pierna izquierda)",
    "mae_geri_der": "Mae Geri (pierna derecha)",
}


class MedicionLogger:
    """
    Envuelve Database.guardar_medicion() y solo persiste cuando el mensaje
    de diagnóstico de una categoría (ej. "codo_izq", "postura", "mae_geri_der")
    CAMBIA respecto al último guardado — evita llenar la base de datos con
    el mismo mensaje repetido ~30 veces por segundo mientras el usuario se
    mantiene quieto o sostiene la misma postura.
    """

    def __init__(self, db, id_sesion):
        self.db = db
        self.id_sesion = id_sesion
        self._ultimo_mensaje = {}  # categoria -> último mensaje ya guardado

    def registrar(self, diagnostico, timestamp_ms):
        """Recibe una lista de dicts de diagnóstico (el formato que ya arma TechniqueAnalyzer)."""
        for d in diagnostico:
            self._registrar_uno(d, timestamp_ms)

    def _registrar_uno(self, d, timestamp_ms):
        categoria = d.get("categoria")
        mensaje = d.get("mensaje")
        if not categoria or not mensaje:
            return  # sin categoría o mensaje vacío (ej. la segunda entrada de postura)

        if self._ultimo_mensaje.get(categoria) == mensaje:
            return  # sin cambios respecto a la última vez, no duplicar

        self._ultimo_mensaje[categoria] = mensaje
        nombre_tecnica = NOMBRES_TECNICA.get(categoria, categoria)
        self.db.guardar_medicion(self.id_sesion, nombre_tecnica, d.get("angulo"), mensaje, timestamp_ms,
                                  correcto=d.get("correcto"), id_umbral=d.get("id_umbral"))
