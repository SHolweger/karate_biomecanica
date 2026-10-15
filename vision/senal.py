"""
Aviso de imagen detenida (RF-01).

Por qué existe
--------------
Cuando la fuente dejaba de entregar fotogramas, el bucle de `live_screen`
anotaba el motivo en `_motivo_detencion`, aumentaba `_sin_fotograma` y **se
reprogramaba igual**. Ninguna de las dos variables se leía desde la interfaz:
sus únicos lectores eran las dos últimas líneas de `test_rendimiento_interfaz.py`.
Un contador que se incrementa y nadie consulta es peor que no tenerlo, porque al
leer el código parece que hay una guarda donde no la hay.

Lo que veía el sensei era la última imagen congelada, indefinidamente, con la
sesión abierta y el último veredicto todavía a la vista. En un dojo eso no es
hipotético: alguien tropieza con el cable del USB, o el teléfono que hace de
cámara IP pierde la red. Y contradice el criterio que gobierna toda la
presentación del sistema —la interfaz no muestra lo que el sistema no mide—,
porque una imagen congelada **muestra algo que ya no se está midiendo**.

Dos situaciones que no son la misma
-----------------------------------
De una **grabación**, quedarse sin fotogramas significa que el archivo se acabó:
es el final normal del análisis y no hay nada que revisar. De una **cámara**,
significa que hay que ir a mirar el cable. El mismo hecho técnico —`get_frame()`
devuelve `None`— tiene dos lecturas opuestas, y decirlas igual obligaría al
sensei a averiguar cuál es.

Se mide en segundos, no en fotogramas
-------------------------------------
El bucle corre a la velocidad de MediaPipe, no a la de la cámara, así que
«treinta fotogramas perdidos» dura cosas distintas en dos equipos: en la Mac de
Sebastián, alrededor de un segundo; en el contenedor de desarrollo, el doble.
Contar fotogramas haría que el aviso apareciera antes o después según dónde
corra, que es justo lo que no queremos de una guarda.

El umbral son **1,5 s**: holgadamente por encima de un fotograma perdido
—40 ms a 24 fps— y por debajo de lo que tarda alguien en dudar de lo que está
viendo.

El aviso se retira solo
-----------------------
En cuanto vuelve a llegar imagen, `aviso_de_senal` devuelve `None` y el texto
desaparece. Un aviso que se queda puesto después de que el problema se resolvió
enseña a ignorarlo, y entonces deja de servir cuando el problema es real.

Este módulo no importa OpenCV
-----------------------------
Aquí viven solo las decisiones —cuándo avisar y con qué frase—, por el mismo
motivo que `vision/grabacion.py` vive separado de `vision/grabador.py`: así se
verifican en integración continua, donde no hay cámara ni códecs. TC-AUTO-063.
"""

# Cuánto tiene que llevar la imagen sin avanzar antes de decir nada.
#
# Por debajo de esto el silencio es correcto: un fotograma suelto se pierde sin
# consecuencia y avisarlo sería ruido. El valor no sale de una medición sino de
# dos cotas que lo encierran —un fotograma dura 40 ms a 24 fps, y nadie duda de
# una imagen quieta en menos de dos segundos—, así que cualquier número entre
# ambas sirve; este es el centro.
UMBRAL_SEGUNDOS = 1.5

# El final de un archivo no es un fallo, y la frase no debe sonar a uno.
FIN_DE_GRABACION = "■ La grabación terminó"

# Para una cámara sí lo es, y la frase tiene que mandar a mirar el cable. Lleva
# los segundos porque lo que importa no es que falte imagen, sino cuánto lleva
# en pantalla algo que ya no se está midiendo.
SIN_IMAGEN = "⚠ Sin imagen: lo que se ve lleva {segundos} s detenido"


def aviso_de_senal(segundos_sin_imagen, fuente_es_grabacion=False,
                   umbral_s=UMBRAL_SEGUNDOS):
    """
    Qué decir sobre una imagen que dejó de avanzar, o `None` si no hay nada.

    `segundos_sin_imagen` es tiempo de reloj desde el último fotograma que sí
    llegó. Cero —o cualquier valor por debajo del umbral— significa que no hay
    nada que avisar, y entonces devuelve `None`: es la misma convención de
    abstención que usa `expert_system/guardia.py`, y obliga a quien llama a
    decidir explícitamente qué hacer con el caso «todo va bien» en vez de
    pintar una cadena vacía por descuido.

    El umbral es un parámetro para que las pruebas no dependan del valor
    vigente y para poder barrerlo si alguna vez se discute, igual que los dos
    umbrales de `TsukiStateMachine`.
    """
    if segundos_sin_imagen is None or segundos_sin_imagen < umbral_s:
        return None
    if fuente_es_grabacion:
        return FIN_DE_GRABACION
    return SIN_IMAGEN.format(segundos=int(segundos_sin_imagen))
