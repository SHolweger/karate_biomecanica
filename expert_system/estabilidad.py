"""
Una postura se registra cuando se sostiene, no cuando asoma.

Medido el 19-oct-2026 sobre una sesión real de Sebastián (`s10`, 107 s a
11 fps, analizada con el sistema tal como corrió en vivo): de 101 veredictos de
postura que se escribieron en la base, **56 duraron menos de 0,2 s** —dos
fotogramas— y **75 menos de 0,5 s**. La precisión que el sistema calculaba con
ellos era del **26 %**; contando solo los que duraron medio segundo o más, del
**58 %**.

Dos causas, las dos ajenas a la técnica:

- **El temblor sobre un límite del rango.** De pie, las rodillas rondan los
  165°, que es justo el mínimo del Heiko Dachi, y cada cruce alternaba
  «CORRECTO» y «DEMASIADO FLEXIONADO». `MedicionLogger` escribe cuando el
  mensaje cambia, así que cada cruce era una fila.
- **Las transiciones.** Al pasar de una postura a otra, el cuerpo atraviesa
  durante uno o dos fotogramas ángulos que el clasificador reconoce como Kiba,
  Kokutsu o Zenkutsu, y esas posturas de paso se registraban como evaluadas.

Es el mismo tipo de fallo que el del Tsuki del 30-sep: **no falla, inventa**.
Un alumno de pie y quieto sacaba alrededor de un 50 % de precisión por puro
temblor.

La regla: en la categoría `postura`, un mensaje solo se da por bueno cuando se
ha mantenido **sin cambiar** durante `SOSTENIDO_MINIMO_MS`. El valor, 0,5 s, lo
fijó Sebastián: en kihon una postura se sostiene bastante más que eso —el
protocolo de grabación pide 3 a 4 s— y un parpadeo de temblor o de transición
dura uno o dos fotogramas.

Lo que **no** cambia:

- **Lo que se ve en el video** y las métricas de la tira inferior: siguen al
  fotograma, como antes. Esto decide qué se REGISTRA y qué entra a la lista de
  correcciones, no qué se dibuja.
- **El Tsuki y la Mae Geri**: ya emiten un veredicto por golpe, con máquinas de
  estados que juzgan una transición. Sostenerlos medio segundo más perdería
  justo el Kime.

Un efecto que conviene saber: un parpadeo entre dos tramos de la MISMA postura
ya no parte el tramo en dos. «CORRECTO», 0,2 s de «DEMASIADO FLEXIONADO» y
«CORRECTO» otra vez es una sola evaluación, que es lo que fue.

Módulo puro: corre en CI.
"""

# Cuánto tiene que mantenerse un mensaje de postura para registrarse. A 11 fps,
# unos seis fotogramas; a 30 fps, quince.
SOSTENIDO_MINIMO_MS = 500

# Categorías que describen un ESTADO del cuerpo y por eso parpadean con el
# temblor. Las de golpes y patadas no: sus máquinas ya juzgan una transición.
CATEGORIAS_DE_ESTADO = ("postura",)


class Estabilizador:
    """
    Dice si el mensaje de una categoría lleva sostenido el tiempo mínimo.

    Hay que consultarlo en CADA fotograma, también cuando el mensaje no ha
    cambiado: es lo que le permite medir cuánto dura. El tiempo es el del video
    (`Camera.marca_de_tiempo_ms`), no el reloj, por el mismo motivo que la
    velocidad del Kime: sobre una grabación, el reloj mediría cuánto tarda este
    equipo en analizar.
    """

    def __init__(self, minimo_ms=SOSTENIDO_MINIMO_MS):
        self.minimo_ms = minimo_ms
        self._candidato = {}  # categoría -> (mensaje, desde_ms)

    def sostenido(self, categoria, mensaje, t_ms):
        if categoria not in CATEGORIAS_DE_ESTADO:
            return True
        candidato = self._candidato.get(categoria)
        if candidato is None or candidato[0] != mensaje:
            self._candidato[categoria] = (mensaje, t_ms)
            return self.minimo_ms <= 0
        return t_ms - candidato[1] >= self.minimo_ms
