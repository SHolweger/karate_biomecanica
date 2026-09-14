"""
Instrumentación de rendimiento del pipeline.

Mide dos magnitudes que la tesis exige por separado y que NO son lo mismo:

  * Tiempo de cómputo por fotograma (RNF-01, < 500 ms): cuánto tarda el
    sistema desde que recibe el fotograma hasta que el diagnóstico quedó
    desplegado. Es trabajo de CPU y no depende del periférico.

  * Tasa de fotogramas sostenida (RF-01, >= 30 fps de procesamiento):
    cuántos fotogramas completos procesa el sistema por segundo en operación
    real. Incluye la espera de la cámara, por lo que nunca puede superar la
    tasa que el periférico entrega.

Se usa time.perf_counter() y no time.time(): es un reloj monotónico de alta
resolución, diseñado para medir intervalos, que no se altera si el reloj del
sistema se ajusta a mitad de la medición.
"""
import math
import time


class PerformanceMonitor:
    """
    Cronómetro por etapas del pipeline.

    No conoce el pipeline: recibe el nombre de cada etapa y mide el intervalo
    entre marcas consecutivas. Eso permite instrumentar cualquier secuencia
    sin acoplar la medición a los módulos medidos.

    El parámetro 'reloj' existe para poder inyectar un reloj simulado en las
    pruebas y verificar la aritmética sin depender del tiempo real.
    """

    def __init__(self, descartar_iniciales=5, reloj=time.perf_counter):
        # Los primeros fotogramas incluyen la carga diferida del modelo de
        # inferencia y la reserva de buffers; no representan el régimen
        # estable de operación, así que se excluyen de las estadísticas
        # (pero SÍ se conservan en el registro crudo).
        self.descartar_iniciales = descartar_iniciales
        self._reloj = reloj

        self.etapas = {}        # nombre -> [ms por fotograma]
        self.totales = []       # ms de cómputo por fotograma completo
        self.instantes = []     # marca de inicio de cada fotograma

        self._t_frame = None
        self._t_etapa = None

    # ---------------- captura de medidas ----------------

    def iniciar_frame(self):
        ahora = self._reloj()
        self.instantes.append(ahora)
        self._t_frame = ahora
        self._t_etapa = ahora

    def marcar(self, etapa):
        """Cierra la etapa en curso y la registra bajo el nombre indicado."""
        if self._t_etapa is None:
            raise RuntimeError("marcar() llamado sin un iniciar_frame() previo")
        ahora = self._reloj()
        self.etapas.setdefault(etapa, []).append((ahora - self._t_etapa) * 1000.0)
        self._t_etapa = ahora

    def cerrar_frame(self):
        if self._t_frame is None:
            raise RuntimeError("cerrar_frame() llamado sin un iniciar_frame() previo")
        self.totales.append((self._reloj() - self._t_frame) * 1000.0)
        self._t_frame = None
        self._t_etapa = None

    # ---------------- estadística ----------------

    @staticmethod
    def _estadisticas(valores):
        """
        Devuelve media, mediana, percentil 95 y máximo.

        Se reporta el percentil 95 y no solo la media porque el RNF-01 describe
        una experiencia de uso: un promedio bajo puede ocultar picos que el
        entrenador sí percibe. El percentil se calcula por rango más cercano.
        """
        if not valores:
            return None
        orden = sorted(valores)
        n = len(orden)
        mediana = orden[n // 2] if n % 2 else (orden[n // 2 - 1] + orden[n // 2]) / 2.0
        return {
            "n": n,
            "media": sum(orden) / n,
            "mediana": mediana,
            "p95": orden[min(n - 1, math.ceil(0.95 * n) - 1)],
            "max": orden[-1],
        }

    def _estables(self, serie):
        """Descarta los fotogramas iniciales de calentamiento."""
        return serie[self.descartar_iniciales:]

    def resumen_etapas(self):
        return {nombre: self._estadisticas(self._estables(v))
                for nombre, v in self.etapas.items()}

    def resumen_total(self):
        return self._estadisticas(self._estables(self.totales))

    def resumen_fps(self):
        """
        Tasa sostenida, calculada sobre el tiempo transcurrido entre inicios
        de fotograma consecutivos (no sobre el tiempo de cómputo).
        """
        inst = self._estables(self.instantes)
        if len(inst) < 2:
            return None
        intervalos = [b - a for a, b in zip(inst, inst[1:])]
        medio = sum(intervalos) / len(intervalos)
        return {
            "medio": 1.0 / medio if medio else 0.0,
            "minimo": 1.0 / max(intervalos) if max(intervalos) else 0.0,
            "fotogramas": len(inst),
            "duracion_s": inst[-1] - inst[0],
        }
