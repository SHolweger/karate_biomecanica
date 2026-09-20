"""
Escritura del video de una sesión (RF-01, RF-07).

Aquí vive lo que necesita códecs. Las decisiones —cómo se llama el archivo, a
qué velocidad se escribe, qué se le informa al sensei— están en
`vision/grabacion.py`, que no importa OpenCV y por eso se verifica en
integración continua.

El principio que gobierna este módulo
-------------------------------------
**Grabar nunca puede tumbar la sesión.**

Perder el video de una tarde en el dojo es malo. Perder las mediciones de esa
misma tarde porque el códec no estaba, el disco se llenó o la carpeta no se
pudo crear es peor, y es un riesgo real: se graba sobre el equipo de un dojo,
no sobre un servidor vigilado. Así que ningún fallo de escritura se propaga al
bucle de análisis. Se anota el motivo, se deja de grabar y la sesión sigue
midiendo —y al terminar, el sensei se entera de que no hay video y de por qué,
en vez de descubrirlo cuando vaya a buscarlo.
"""
import os

import cv2

from vision.grabacion import (FRAMES_PARA_ESTIMAR, describir_resultado, fps_estimado,
                              ruta_de_sesion)

# Códecs a intentar, en orden de preferencia.
#
# Se prueba más de uno porque la disponibilidad depende de cómo se compiló
# OpenCV en el equipo, y eso no se sabe hasta intentarlo: 'avc1' (H.264) da el
# archivo más pequeño y lo abre cualquier reproductor, pero falta en muchas
# instalaciones; 'mp4v' está casi siempre y produce archivos más grandes. Entre
# un video pesado y ningún video, pesado.
CODECS = ("avc1", "mp4v")


class GrabadorSesion:
    """
    Escribe el video crudo de una sesión de análisis.

    Se usa así, desde el bucle de video:

        grabador = GrabadorSesion(id_sesion, "Ana Gómez")
        ...
        grabador.escribir(frame_crudo, timestamp_ms)   # por cada fotograma
        ...
        resumen = grabador.cerrar()

    El fotograma que se le pasa debe ser el CRUDO, antes de dibujarle el
    esqueleto: el video anotado se regenera del crudo cuando se quiera, y el
    camino inverso no existe (ver el encabezado de vision/grabacion.py).
    """

    def __init__(self, id_sesion, nombre_alumno, cuando=None, directorio=None):
        from datetime import datetime

        self.ruta = ruta_de_sesion(
            id_sesion, nombre_alumno, cuando or datetime.now(),
            **({"directorio": directorio} if directorio else {}))

        self._escritor = None
        self._buffer = []        # fotogramas retenidos mientras se estima la velocidad
        self._marcas = []        # sus timestamps, para deducir los fps reales
        self._frames = 0
        self._fps = None
        self.error = None        # motivo por el que no se grabó, si no se grabó

    # ---------------- estado ----------------

    @property
    def grabando(self):
        """¿Se está escribiendo? Falso también cuando ya se renunció por un fallo."""
        return self.error is None

    @property
    def frames_escritos(self):
        return self._frames

    # ---------------- escritura ----------------

    def escribir(self, frame, timestamp_ms):
        """
        Agrega un fotograma. Nunca levanta: un fallo apaga la grabación, no la sesión.

        Los primeros fotogramas se retienen en memoria en vez de escribirse. No
        es una optimización: `cv2.VideoWriter` exige los fotogramas por segundo
        al crearse y no los puede cambiar después, y la velocidad real del bucle
        solo se conoce midiéndola. Se retienen doce —alrededor de un segundo de
        análisis— y con eso se abre el archivo y se vuelca lo retenido.
        """
        if frame is None or not self.grabando:
            return

        try:
            if self._escritor is None:
                self._buffer.append(frame.copy())
                self._marcas.append(timestamp_ms)
                if len(self._buffer) >= FRAMES_PARA_ESTIMAR:
                    self._abrir_y_volcar()
                return

            self._escritor.write(frame)
            self._frames += 1
        except Exception as e:                      # noqa: BLE001 — ver el encabezado
            self._renunciar(f"falló la escritura del video ({e})")

    def _abrir_y_volcar(self):
        """Crea el archivo con la velocidad ya medida y escribe lo retenido."""
        alto, ancho = self._buffer[0].shape[:2]
        self._fps = fps_estimado(self._marcas)

        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        escritor = None
        for codec in CODECS:
            candidato = cv2.VideoWriter(self.ruta, cv2.VideoWriter_fourcc(*codec),
                                        self._fps, (ancho, alto))
            if candidato.isOpened():
                escritor = candidato
                break
            candidato.release()

        if escritor is None:
            self._renunciar(
                "el equipo no tiene un códec de video disponible "
                f"(se intentó {' y '.join(CODECS)})")
            return

        self._escritor = escritor
        for retenido in self._buffer:
            self._escritor.write(retenido)
            self._frames += 1
        self._buffer.clear()

    def _renunciar(self, motivo):
        """Apaga la grabación conservando el motivo, y libera lo que haya abierto."""
        self.error = motivo
        self._buffer.clear()
        if self._escritor is not None:
            try:
                self._escritor.release()
            except Exception:                       # noqa: BLE001
                pass
            self._escritor = None

    # ---------------- cierre ----------------

    def cerrar(self):
        """
        Cierra el archivo y devuelve qué pasó, en una frase para el sensei.

        Una sesión más corta que el tramo de estimación termina sin que el
        archivo se haya abierto siquiera. Se abre aquí, con lo poco que haya:
        cinco segundos de video son poco, pero son más que ninguno, y un
        archivo que no existe se lee como un fallo del sistema.
        """
        if self._buffer and self._escritor is None and self.grabando:
            self._abrir_y_volcar()

        if self._escritor is not None:
            try:
                self._escritor.release()
            except Exception as e:                  # noqa: BLE001
                self._renunciar(f"falló el cierre del archivo de video ({e})")
            self._escritor = None

        if self.error:
            return f"No se grabó video de esta sesión: {self.error}."
        return describir_resultado(self.ruta, self._frames, self._fps or 0)

    @property
    def ruta_si_existe(self):
        """La ruta del video, o None si no llegó a escribirse ninguno."""
        if self.error or not self._frames:
            return None
        return self.ruta
