# Shotokan AI — notas para trabajar en este repositorio

Sistema experto de análisis biomecánico con visión artificial y sensores
inerciales para la Asociación Departamental de Karate Do de Sacatepéquez.
Proyecto de graduación de Sebastián Holweger (Ing. en Sistemas, Universidad
Mariano Gálvez). Se trabaja **en español**.

**Fechas que mandan:** el sistema debe estar 100 % funcional el **31 de octubre
de 2026**; la defensa ante la terna, con demostración en vivo, es el **9 de
noviembre de 2026**.

---

## Cómo se ejecuta

```bash
python3 main.py              # interfaz gráfica
python3 main.py --consola    # el encadenamiento sin GUI, por terminal
python3 main.py --consola --fuente "grabacion.mp4"   # analiza un video y lo registra
python3 diagnostico_video.py "grabacion.mp4"         # por qué no se detecta pose
python3 comparar_2d_3d.py "grabacion.mp4" --esperado zenkutsu_dachi   # ¿2D o 3D?
python3 revisar_base.py                              # qué hay en la base (solo lectura)
python3 revisar_tsuki.py "grabacion.mp4" --golpes 8  # ¿a qué velocidad son los Tsuki?
python3 plan_de_pruebas.py                           # regenera docs/plan_de_pruebas.{csv,md}
python3 -m pytest -q         # suite completa
```

En la Mac de Sebastián **`python` a secas no existe**; siempre `python3`.

## Arquitectura

Cinco capas, y la separación es deliberada:

```
vision/         captura y resolución de la fuente de video
biomechanics/   geometría, filtros, dibujado del esqueleto
expert_system/  reglas, clasificador de posturas, máquina de estados, riesgos
persistence/    SQLite, umbrales versionados, consultas agregadas
gui/            presentación (10 pantallas + módulos de lógica pura)
```

El motor de reglas opera sobre **magnitudes cinemáticas puras** (ángulos,
velocidades angulares) sin saber de dónde vienen. Eso es lo que permitió avanzar
sin los sensores inerciales, y no debe romperse.

---

## Decisiones ya tomadas — no volver a discutirlas sin motivo nuevo

**La interfaz no muestra lo que el sistema no mide.** Es el criterio que
gobierna toda la presentación:

- Sin evaluaciones cerradas, la precisión es `None` y se dibuja como guion.
  **Nunca 0 %**: un alumno sin medir no falla el 100 % de sus técnicas.
- Los sensores IMU se declaran ausentes («Sin sensores IMU»), no se muestran en
  cero ni se omiten. Un cero se lee como «hay sensores y ninguno responde».
- El veredicto es **Correcto / Incorrecto / «—»**, no un puntaje 0–100. Las
  reglas evalúan contra un rango angular; un número continuo fingiría una
  precisión que el dato no tiene.
- No se muestran rotación de cadera, velocidad del puño en m/s ni balance. La
  cámara da píxeles, no metros.

**El perfil es del sensei, no del alumno.** Corregido el 14-sep-2026. El perfil
identifica a *quién opera* el sistema y firma cada medición; el alumno es *a
quién se mide* y se inscribe desde la sección de alumnos. Elegir perfil pide
contraseña (RNF-05) — Sebastián dejó esa decisión «pendiente» pero por ahora se
queda así.

**Los umbrales son datos versionados, no constantes** (RF-08). Recalibrar no
reescribe: marca la versión anterior como no vigente e inserta una nueva. Cada
medición guarda el `id_umbral` que la juzgó, o el historial quedaría sin
criterio verificable.

**El veredicto es ternario** (`correcto` = True / False / NULL). NULL es estado
transitorio o articulación no visible. Todas las consultas agregadas filtran por
`correcto IS NOT NULL`.

**Una medición se guarda con qué la juzgó, no solo con su veredicto**
(19-sep-2026). Además del `id_umbral`, la fila lleva `tecnica_clave` y los
argumentos exactos que consumió la regla (`angulo_regla_1`, `angulo_regla_2`).
Eso es lo que permite contestar «¿qué cambiaría si corrijo este umbral?» sin
volver al dojo — `expert_system/reevaluacion.py`. Ese módulo **no escribe**:
re-juzgar en el lugar borraría la evidencia de qué criterio regía al medir. El
Mae Geri queda fuera a propósito: su veredicto usa la velocidad angular pico,
que la fila no guarda. Las mediciones anteriores al 19-sep quedan fuera del
informe, y `cobertura_reevaluable()` lo dice, para que «no cambia ninguna» no
se lea como garantía cuando la muestra es de cuatro filas.

**El impacto de recalibrar se ve ANTES de guardar** (19-sep-2026). El botón
«Ver impacto en el historial» de `gui/umbrales_screen.py` contrasta lo escrito
en el formulario contra lo ya medido y responde «3 de 5 mediciones cambiarían
de veredicto». Contrasta el **criterio completo** que quedaría, no solo el
campo editado: un Kokutsu se juzga por dos rodillas y mirar una sola daría un
número tranquilizador y falso. No escribe nada. La redacción vive en
`gui/impacto_umbrales.py` (puro, corre en CI) y ninguna frase afirma que el
criterio nuevo sea el correcto — eso lo fija el cuerpo técnico, no el programa.

**El tiempo de una grabación lo dicta el video, no el reloj de pared**
(20-sep-2026). `Camera.marca_de_tiempo_ms()` devuelve la posición dentro del
archivo cuando la fuente es una grabación, y el reloj transcurrido cuando es
una cámara en vivo. Importa porque la velocidad angular del Kime se deriva de
ese intervalo: sobre un archivo el reloj mide cuánto tarda *este equipo* en
analizar, no cuánto duró la ejecución, así que la **misma grabación daría
veredictos distintos en dos computadoras** — y eso destruye justo la propiedad
por la que `vision/fuentes.py` acepta archivos (entrada idéntica en cada
corrida, luego toda diferencia viene del código).

Dos detalles que costaron un intento cada uno:

- La posición se consulta **después** de `read()`. Este backend la informa con
  un fotograma de retraso: consultada antes, el primero y el segundo declaran
  ambos el milisegundo cero.
- **MediaPipe exige marcas estrictamente crecientes** («Input timestamp must be
  monotonically increasing») y **aborta** si no. Cuando el contenedor repite una
  posición se rellena con la duración nominal de un fotograma —que es el
  intervalo real— y no con un epsilon, que dispararía la velocidad de ese
  fotograma. Sin esto, una grabación larga pierde el trabajo a mitad de camino.

**Cifras medidas el 20-sep** (no recordadas): la estimación de pose cuesta
**~10 ms por fotograma** y es prácticamente independiente de la resolución de
entrada —MediaPipe reescala al tamaño de su modelo—, de 640×360 a 1920×1080.
La cifra de «~100 ms por fotograma» que este archivo citaba en la sección de
`update()` no coincide con lo medido; conviene revisarla antes de usarla en la
tesis.

Los dobles de cámara de las pruebas cumplen el mismo contrato con un intervalo
declarado, no con el reloj, para que las pruebas no dependan de la velocidad
del equipo.

**Se graba el fotograma crudo, nunca el anotado** (19-sep-2026). El video con
esqueleto se regenera del crudo; al revés no. Grabar el anotado dejaría las
conclusiones de hoy cocidas en la evidencia. La velocidad de escritura **se
mide**, no se asume: el bucle corre a la velocidad de MediaPipe (~10 fps), no
a la de la cámara, y por eso `GrabadorSesion` retiene los primeros 12
fotogramas para estimarla antes de abrir el archivo. **Un fallo de grabación
jamás tumba la sesión**: se apaga la grabación, se anota el motivo y se sigue
midiendo. La grabación se puede apagar por equipo (`grabar_sesiones` en
`configuracion`) porque en un dojo se entrena con menores.

**La guardia puede abstenerse, y tiene que poder** (28-sep-2026). Zenkutsu y
Kokutsu son, para el clasificador, **la misma postura con las piernas
intercambiadas**: lo único que las distingue es cuál va adelante. Eso se
decidía con `z_diff = tobillo_izq.z - tobillo_der.z` y un `if z_diff < 0`, sin
zona muerta, de modo que un ruido de 0,0001 decidía igual que una separación
real. Y como las dos posturas son simétricas, equivocarse no daba «no
reconocido» sino **la otra postura con veredicto positivo**. Reproducido con la
misma geometría corporal, cambiando solo el signo de Z:

```
Z correcta  ->  ZENKUTSU (IZQ ADELANTE): POSTURA: FIRME   correcto=True
Z invertida ->  KOKUTSU  (DER ADELANTE): POSTURA: ESTABLE correcto=True
```

Esa fila entraba a la base con la técnica equivocada y contaminaba el historial
y la gráfica de evolución del alumno. Es el único defecto conocido que
**corrompe datos** en vez de limitarse a fallar. Lo encontró una prueba en vivo
de Sebastián, no la suite.

`expert_system/guardia.py` (puro, corre en CI) lo corrige con dos cambios:

- La separación de los tobillos se proyecta sobre el **eje sagital del cuerpo**,
  deducido de la línea de caderas, en vez de mirar el eje Z de la cámara. Así la
  decisión usa el eje que mejor la informa: **X cuando la toma es de perfil** —la
  magnitud más fiable de MediaPipe, y justo la toma que estas posturas
  requieren—, Z cuando es frontal. Antes se usaba siempre el peor dato
  disponible.
- Por debajo de **medio ancho de cadera** de separación, devuelve `None`. El
  umbral se expresa en anchos de cadera de la propia persona, no en unidades de
  MediaPipe, para que no dependa de la resolución ni de la distancia al sensor.
  El valor sale de la definición de las posturas —un Zenkutsu tiene por
  construcción un pie claramente adelantado—, pero **conviene contrastarlo
  contra grabaciones reales antes de fijarlo en la tesis**.

Con `guardia is None`, las ramas de Zenkutsu y Kokutsu no se pueden tomar y el
sistema informa «GUARDIA INDEFINIDA», que es distinto de «EN TRANSICION»: el
ejecutante no se está moviendo, es la toma la que no permite decidir. Heiko y
Kiba no dependen de la guardia y siguen evaluándose — es exactamente lo que
Sebastián observó en el dojo: esas dos salían perfectas mientras Zenkutsu
fallaba.

**Y el signo del eje estuvo invertido un día** (29-sep-2026). La primera
versión dedujo el sentido de «adelante» de `tests/helpers/fakes.py`, que
colocaba el landmark 24 —la cadera DERECHA anatómica— en x=0,58, la mitad
derecha de la pantalla. MediaPipe lo pone en la izquierda: medido sobre
grabación real, cadera 24 en **x=0,461** y cadera 23 en **x=0,579**. El doble
espejaba el cuerpo entero, y como el código y las pruebas compartían el mismo
supuesto falso, **las 764 pruebas confirmaban el error en vez de encontrarlo**.
El sentido correcto sale de la anatomía y no del doble: con el eje vertical de
la imagen hacia abajo, `izquierda = arriba × adelante`, y despejando queda
`adelante ∝ (-hz, hx)`.

Lo delató una grabación real, no la suite: sobre 3190 fotogramas de Zenkutsu,
0,0 % de aciertos y **20,0 % al invertir la guardia**. Corregido el doble, el
signo viejo rompe siete pruebas, entre ellas la que dice
`'IZQ ADELANTE' in 'KOKUTSU (DER ADELANTE)'`.

La lección general, que vale más que el arreglo: **un doble de prueba que no
reproduce el convenio de los datos reales no verifica, ratifica**. Cualquier
doble nuevo tiene que declarar de dónde salen sus cifras, y hay una guarda
—`test_el_doble_de_prueba_coloca_el_cuerpo_como_lo_hace_mediapipe`— que fija
esta en concreto.

**Lo que la abstención NO arregla:** si la toma es frontal y MediaPipe estima
la profundidad con el signo cambiado de forma sostenida, la proyección saldrá
grande y con el sentido incorrecto. El remedio de ese caso es de protocolo, no
numérico. Ver el punto siguiente.

**Un Tsuki es una transición, no un estado** (30-sep-2026). `analyze_tsuki`
juzgaba el codo en CADA fotograma en que el brazo se viera, sin preguntar antes
si había un golpe. Como el rango de evaluación del Tsuki es 160–175° y un brazo
colgando al costado mide entre 160 y 180°, el sistema calificaba de Tsuki a
alguien que estaba de pie sin hacer nada. Medido sobre tres segundos de brazo
quieto a 175 ± 2°:

| | filas de Tsuki en la base |
|---|---|
| código viejo | **90** (45 «EXCELENTE» y 45 «HIPEREXTENDIDO (Peligro)») |
| código nuevo | 0 |

Por brazo, y son tres segundos. El temblor natural cruza el límite de 175° una
y otra vez, y `MedicionLogger` escribe en cada cruce porque el mensaje cambia.

Es el mismo tipo de fallo que el de la guardia: **no falla, inventa**. Esas
filas entran con `tecnica="tsuki"` y veredicto cerrado, así que contaminan la
precisión del alumno, su gráfica de evolución y el conteo de errores
frecuentes. Y `expert_system/riesgos.py` cuenta hiperextensiones para advertir
de bloqueo articular: bastaba estar de pie con los brazos estirados para que el
reporte de prevención de lesiones recomendara corregir el Kime.

Lo encontró otra prueba en vivo de Sebastián, no la suite —y esta vez ni
siquiera hizo falta buscarlo: estaba escrito en la pantalla de la captura, «IZQ
- TSUKI: EXCELENTE» con los brazos abajo—. El Mae Geri nunca tuvo el problema
porque su máquina de estados solo califica al cerrar el Kime, y la postura
aprendió a abstenerse el 28-sep. **El Tsuki era la única técnica que juzgaba un
estado en vez de una transición.**

`expert_system/tsuki.py` (puro, corre en CI) lo corrige con una máquina de
estados por brazo, REPOSO → EXTENDIENDO → RECOGIENDO, que emite **un veredicto
por golpe** en el instante en que la extensión se detiene —que es la definición
del Kime—. El criterio es un RECORRIDO y no un umbral: el ángulo tiene que
subir `RECORRIDO_MINIMO` (35°) sobre el mínimo de la ventana de tiempo reciente
(`VENTANA_RECORRIDO_MS`, 500 ms) **y estar en el máximo de esa ventana**. Lo
segundo no es un adorno: sin ello, el brazo seguía estando muy por encima del
mínimo *mientras volvía* del golpe, y la máquina detectaba un segundo golpe en
la recogida del primero.

Los dos números equivalen a exigir **70°/s**, y esa es la cifra que hay que
poder defender.

**Y la justificación que aquí se dio era de literatura, no medida** (corregido
el 30-sep-2026). Decía «un Tsuki extiende unos 125° en 150–250 ms, entre 500 y
800°/s», y sobre grabación real eso no aparece por ningún lado:

| | P50 | P75 | P90 | P95 | P99 |
|---|---|---|---|---|---|
| codo izquierdo | 20,9 | 48,1 | 91,3 | 129,3 | **189,0** |
| codo derecho | 12,3 | 35,4 | 79,0 | 129,2 | **234,0** |

(°/s, sobre los 2911 fotogramas de «Zenkusu dachi.mp4»). **Ni el 1 % de los
fotogramas supera los 234°/s.** Los cuatro golpes que el sistema reconoce en
esa grabación van de **44 a 318°/s**, no de 500 a 800.

La hipótesis de que el filtro de media móvil deprimiera la cifra **está
descartada por medición**: sobre una rampa sintética pierde un 20 % en un golpe
de 150 ms y **0 %** de 200 ms en adelante. Las velocidades son las que son.

Queda por decidir si eso describe el Tsuki o describe ese video —una grabación
de prueba de posturas, no un entrenamiento a velocidad de combate—, y la
respuesta cambia dónde va el umbral. **No citar 500–800°/s en la tesis: no está
verificado contra nada.**

**ABIERTO: el umbral de 70°/s deja fuera el Tsuki lento** (30-sep-2026,
observado en vivo). El par (recorrido, ventana) ES un umbral de velocidad, y
una ejecución deliberadamente lenta no llega. Este archivo y el módulo llegaron
a decir que «una ejecución lenta frente al espejo sigue siendo un Tsuki»; con
este criterio, **no**. La frase describía mal su propio umbral.

La tensión es real y no está resuelta: `expert_system/riesgos.py` recomienda
literalmente «trabajar el Tsuki a velocidad media frente al espejo». Un sistema
que recomienda practicar despacio y luego no mide cuando se practica despacio se
contradice. Bajar el umbral reabre los falsos positivos que el módulo existe
para cerrar.

**Se decide con datos, no con criterio.** Los dos umbrales son parámetros del
constructor de `TsukiStateMachine`, y `revisar_tsuki.py` (raíz) los barre sobre
una grabación real: lista cada golpe reconocido con su marca de tiempo, de qué
ángulo salió y a qué velocidad, imprime los percentiles de velocidad angular del
codo y contrasta lo reconocido contra lo ejecutado (`--golpes N`).

**Primera corrida, 30-sep-2026**, sobre «Zenkusu dachi.mp4» (2911 fotogramas):

| recorrido | 500 ms | 750 ms | 1000 ms |
|---|---|---|---|
| 20° | 12 | 15 | 17 |
| 25° | 7 | 8 | 10 |
| 30° | 7 | 7 | 8 |
| **35° (vigente)** | **4** | 6 | 7 |
| 40° | 4 | 4 | 5 |

Cuatro golpes con el criterio vigente; diecisiete con el más permisivo. **Falta
el dato que decide: cuántos Tsuki hay de verdad en ese video.** Sin él, la tabla
no dice si cuatro son pocos — por eso existe `--golpes N`, y por eso la
herramienta lo dice en vez de elegir por su cuenta.

Dos cosas que esa corrida sí deja claras:

- **El brazo derecho se pierde en el 33 % de los fotogramas** (952 de 2911,
  contra 394 del izquierdo). El Hikite oculta el codo, y eso —no el umbral—
  puede ser lo que explique que solo se le reconozca un golpe.
- Un golpe a **44,2°/s durante 1382 ms** se clasificó «HIPEREXTENDIDO
  (Peligro)» con un pico de 179,5°, en el segundo **40,92**. **CONFIRMADO
  falso positivo**: Sebastián abrió el video ahí y lo que hace es estirar el
  brazo y sostenerlo unos tres segundos, sin golpear. La abstención no cierra
  el caso que motivó el módulo — solo lo hizo mucho más raro.

**Tres situaciones distintas que hoy se confunden en una** (30-sep-2026, a
raíz de una pregunta de Sebastián: «¿qué pasa si el Tsuki tiene baja potencia,
lo detecta o marca que debe ser más potente?»). Hoy el sistema las trata igual
—no dice nada—, y son casos que pedirían respuestas opuestas:

| Lo que ocurre | Lo que el sistema hace | Lo que debería |
|---|---|---|
| Se golpea con potencia | Lo juzga | ✔ |
| Se golpea flojo, pero se golpea | **Silencio** | Decirlo: es lo que el alumno tiene que corregir |
| Se estira el brazo sin golpear | **Silencio** (y antes, un veredicto falso) | ✔ |

El segundo caso es el problema: un Tsuki lento es **una ejecución mejorable,
no la ausencia de ejecución**, y callarse es justo lo contrario de lo que un
sistema de corrección técnica debe hacer.

Y conviene decir una cosa con claridad en la tesis: **el sistema no mide
potencia**. La cámara da píxeles, no newtons. Lo que mide es velocidad angular
del codo, que se relaciona con la potencia pero no es ella — afirmar lo
contrario sería del mismo tipo que las cifras en m/s que este archivo ya
prohíbe mostrar.

La salida que se perfila, **sin decidir todavía**: un segundo umbral por debajo
del actual. Entre los dos, el golpe se reconoce y se informa como lento; por
debajo del segundo, sigue sin haber golpe. Eso convierte un umbral en una
banda, y necesita las dos cifras medidas sobre una grabación donde se sepa qué
se ejecutó — la de esta noche.

Lo que el criterio **no** puede distinguir, en ningún caso, es un Tsuki de
cualquier otra extensión rápida del codo; conviene decirlo en la tesis en vez
de insinuar que reconoce la técnica por su forma.

Tres errores míos en la propia herramienta, los tres encontrados **al ejecutarla**
y no al leerla, y los dos en la única cifra para la que existe: informaba el
golpe «de 90,7° a 172° a 411°/s» cuando salió de 50° a 616°/s —tomaba como
inicio el fotograma en que la máquina se enteró, no el Hikite—, y al corregir
eso pasó a 205°/s, porque la duración se tragaba los cientos de milisegundos
que el puño llevaba parado. Ahora mide desde el último instante en que el codo
seguía abajo hasta aquel en que la extensión llegó más arriba, con **la
resolución del muestreo**: a 30 fps, ±33 ms sobre una extensión de 200.

El tercero lo delató la grabación real: **ningún golpe salía del Hikite**, sino
de 81°, 94°, 105° y 118°. Buscaba el arranque dentro de la ventana de
detección, y esa dura lo que necesita DETECTAR, no lo que dura el golpe: cuando
la máquina dispara, el fondo de la flexión ya salió de la ventana. Detectar y
medir son dos cosas. Ahora el arranque se busca hacia atrás por la serie
completa, hasta el fondo de la flexión y de ahí al último instante que siga en
él. Lo fija `test_el_arranque_no_lo_recorta_la_ventana_de_deteccion`.

Efecto secundario que conviene aprovechar: «evaluaciones cerradas» pasa a
significar **repeticiones**, que es lo que siempre debió significar.

**Verificado en su Mac el 30-sep, en vivo y sobre grabación**, que era el
pendiente declarado: las pruebas cubrían que el golpe se detecta, pero no con
MediaPipe real. Contrastado contra las capturas de esa misma mañana:

| Situación | Antes | Después |
|---|---|---|
| De pie, brazos abajo (codos 168°/173°) | «IZQ - TSUKI: EXCELENTE / DER - TSUKI: EXCELENTE» | «SIN TSUKI: BRAZO EN REPOSO» |
| En transición (codo 179°) | «TSUKI: HIPEREXTENDIDO (peligro)», veredicto **Incorrecto** | «SIN TSUKI», veredicto por la postura |
| Rascándose la cabeza ante la cámara | *(habría calificado)* | «SIN TSUKI: BRAZO EN REPOSO» |
| **Zenkutsu de perfil con Tsuki real** | — | «Kime correcto (izquierdo)» a los 00:21, y «Extiende más el brazo» a los 00:17 |

Dos veredictos de Tsuki en veintiún segundos, espaciados, en vez de uno por
fotograma. El panel de correcciones de esa misma sesión tenía por la mañana
cuatro entradas de Tsuki en los dos primeros segundos, **con el ejecutante
quieto**.

**Un efecto de diseño que conviene tener presente el 9 de noviembre:** sostener
el brazo extendido más de `VENTANA_RECORRIDO_MS` devuelve el aviso a «SIN
TSUKI». Es correcto —el golpe terminó, y su veredicto queda fechado en el panel
de correcciones— pero en una demostración, donde la postura se sostiene para
que la terna la vea, el texto del brazo desaparece del video mientras la
postura sigue en pantalla. Decidir antes de la defensa si eso se explica o se
cambia.

**Y deja el historial anterior inservible para calcular precisión.** Todo lo
medido antes del 30-sep lleva filas de Tsuki producidas por brazos que no
golpeaban, y no se pueden separar fila por fila: el código viejo no registraba
si hubo golpe, que era justamente el defecto. `revisar_base.py` (raíz, **solo
lectura**, abre SQLite en modo `ro`) cuantifica lo que sí se puede demostrar:
veredictos OPUESTOS del mismo brazo separados por menos de 150 ms, que es la
firma de un brazo quieto cruzando el límite de 175° y no la puede producir
ninguna secuencia de golpes reales —un Tsuki dura 150-250 ms y el encadenado
más rápido no baja de ~300 ms—. Es una **cota inferior**, y conviene citarla
así en la tesis.

Contrastado de extremo a extremo contra una base construida con el código
viejo (seis segundos de pie más cuatro Tsukis reales y doce filas de postura):
marca 360 de 376 filas, deja fuera los cuatro golpes y las doce posturas.

La primera versión informó **«190,4 % del total»**, porque sumaba dos filas por
cada pareja y en una tanda alternante cada fila participa en dos. Lo delató
correr la herramienta contra una base real; las pruebas unitarias con
`> 0` no podían verlo. Lo fija ahora `test_la_cuenta_nunca_supera_el_total_de_
filas`.

**Apartar la base se hace renombrando, no borrando.** El historial contaminado
sigue siendo evidencia de la tesis —sostiene con números el argumento de la
sección de validación— y borrarlo no se deshace. Al renombrar
`karate_sistema.db`, la base nueva nace en la carpeta de datos del sistema
(`~/Library/Application Support/ShotokanAI/`), porque ya no hay ninguna junto
al código: ver la excepción de `rutas.py`.

**Los ángulos son 2D y eso tiene un coste medible** (28-sep-2026).
`calculate_angle` usa solo `(x, y)`. Cuando el plano de la técnica no es
paralelo al sensor, el ángulo proyectado no es el real, y **la proyección
arrastra todo ángulo hacia 90°**:

| giro | real 90° | real 120° | real 160° | real 175° |
|---|---|---|---|---|
| 0° | 90,0 | 120,0 | 160,0 | 175,0 |
| 45° | 90,0 | 112,2 | 152,8 | 172,9 |
| 75° | 90,0 | 98,5 | 125,4 | 161,3 |
| 90° | 90,0 | 90,0 | 90,0 | 90,0 |

A 90° de giro —técnica lanzada de frente a la cámara— *cualquier* ángulo real
mide 90°. Por eso un tsuki perfecto de 175° se reporta **«TSUKI: FLEXIONADO»**
cuando se graba de frente: no es que no se detecte, es que se mide con un
número sin relación con el codo real, y la visibilidad sigue alta, así que
ninguna guarda lo atrapa.

**Consecuencia de protocolo, y es un hallazgo de tesis, no un defecto:** cada
técnica se filma perpendicular a su plano.

| Técnica | Plano | Cámara |
|---|---|---|
| Heiko Dachi, Kiba Dachi | frontal | **de frente** |
| Zenkutsu, Kokutsu, Tsuki, Mae Geri | sagital | **de perfil** |

**Y está medido, no razonado** (29-sep-2026, 3190 fotogramas de Zenkutsu
Dachi grabados desde tres ángulos en la misma sesión):

| Ángulo de cámara | fotogramas | acierto 2D | acierto 3D |
|---|---|---|---|
| de frente | 1156 | **0,0 %** | 0,0 % |
| a 45° | 411 | 8,8 % | 11,7 % |
| de perfil | 1623 | **37,2 %** | 41,8 % |

De frente el sistema **no reconoce el Zenkutsu ni una sola vez**. No es que
acierte menos: es ciego a esa postura desde esa cámara. Y el gradiente es
monótono, lo que descarta la hipótesis de que los 45° fueran el punto dulce
por compensar la oclusión de la pierna lejana con menos escorzo: el escorzo
domina y el perfil gana.

Esta tabla es el protocolo de grabación de la campaña del dojo. Sin ella,
los datos que se recojan de Zenkutsu, Kokutsu, Tsuki y Mae Geri filmados de
frente serían inservibles y no habría tiempo de repetir la campaña.

La tabla se confirmó en la interfaz el 30-sep: el mismo video que de frente
daba «HEIKO DACHI» sobre un Zenkutsu, de perfil da **«ZENKUTSU (DER ADELANTE):
POSTURA: FIRME»**, con la rodilla delantera en 106° y la trasera en 168°. La
guardia acierta y el veredicto es el que corresponde.

`guardia.orientacion_frente_a_camara()` mide esto (0 = de perfil, 1 = de
frente) y desde el 29-sep **alimenta el aviso de encuadre** de la pantalla en
vivo (`vision/encuadre.py`, puro, corre en CI). **Verificado el 30-sep**: el
aviso cambia solo al girar la toma, de «Cámara de frente: sirve para Heiko
Dachi y Kiba Dachi» a «Cámara de perfil: sirve para Zenkutsu, Kokutsu, Tsuki y
Mae Geri». El aviso es informativo y
permanente, no condicionado a la técnica detectada: reconocer la técnica es
justamente lo que falla cuando el plano está mal, así que esperar a saberla
para avisar sería circular.

**MediaPipe ya calcula coordenadas 3D y se están descartando** (28-sep-2026).
`vision/tracker.py` devuelve el resultado completo, pero `live_screen.py` y
`main.py` usan solo `result.pose_landmarks`. `result.pose_world_landmarks`
—coordenadas en metros relativas al centro de las caderas— sale del mismo paso
de inferencia, así que su coste ya está pagado. Calcular los ángulos ahí
atacaría a la vez la guardia y el arrastre hacia 90°. **No está comprobado que
funcione mejor**: la Z de un modelo monocular es estimada. Hay que medirlo
contra las grabaciones antes de afirmarlo.

**El modelo y la base de datos no comparten ubicación, y es a propósito**
(30-sep-2026). Las dos rutas eran relativas —`'pose_landmarker_full.task'` en
seis módulos y `'karate_sistema.db'` en uno—, y una ruta relativa se resuelve
contra el **directorio de trabajo**. Eso funciona mientras se lance
`python3 main.py` desde la carpeta del proyecto, y deja de funcionar al
empaquetar: un `.command` abierto con doble clic arranca en la carpeta personal
del usuario, y PyInstaller descomprime sus datos en una carpeta temporal
distinta en cada arranque. `rutas.py` (raíz, puro, corre en CI) las resuelve:

- **El modelo es parte del programa**: se instala con él, no cambia, y en un
  ejecutable congelado vive dentro del paquete, que es de solo lectura. Si
  falta, se lanza `ModeloNoEncontrado` nombrando el archivo y la carpeta donde
  se buscó, en vez de dejar que MediaPipe informe un error que no lo menciona.
- **La base de datos es del usuario**: se escribe en cada sesión y tiene que
  sobrevivir a reinstalar. Dentro del paquete, la siguiente versión la borraría
  con todas las mediciones, así que va a la carpeta de datos del sistema
  (`~/Library/Application Support/ShotokanAI` en macOS).

**Con una excepción que evita perder el historial:** si ya existe una base
junto al código, se sigue usando esa. Todo el desarrollo escribió en
`karate_sistema.db` dentro del repositorio —no está versionada, vive solo en la
Mac de Sebastián— y moverla en silencio dejaría el historial huérfano sin que
nada avisara hasta ver la lista de alumnos vacía. Migrar es decisión suya.

`SHOTOKAN_MODELO` y `SHOTOKAN_BD` mandan sobre todo lo demás: sirven para las
pruebas, para una base compartida en el dojo y para mover los datos sin tocar
el código.

**El aviso de grabación dice lo que pasa, no lo que se configuró**
(30-sep-2026). Es la única pieza del sistema dedicada al **consentimiento** —
existe para que nadie descubra después que lo filmaron, y en el dojo se entrena
con menores—, y se resolvía una sola vez al construir la pantalla, leyendo solo
el interruptor del equipo. Tres situaciones distintas, un solo texto:

| Situación real | Anunciaba | Anuncia ahora |
|---|---|---|
| Sin alumno: ni cámara ni sesión | ● Grabando | ○ Se grabará al comenzar |
| Grabando de verdad | ● Grabando | ● Grabando |
| **El grabador renunció a mitad** | ● Grabando | ⚠ Grabación detenida |
| Apagada en el equipo | ○ Solo midiendo | ○ Solo midiendo |

El primero se vio en una captura de Sebastián con la base recién estrenada:
cero alumnos, recuadro de video en negro y el punto rojo encendido. **El
tercero es el grave**: la decisión de que un fallo de grabación nunca tumbe la
sesión —se anota el motivo, se deja de grabar y se sigue midiendo— tiene como
reverso que la sesión entera transcurre anunciando que graba, y el sensei se
entera al ir a buscar el video. Un punto rojo que a veces no significa nada es
peor que no tener punto rojo.

`vision/grabacion.estado_en_vivo()` (puro, corre en CI) lo decide con lo que el
sistema sabe: si la fuente es un archivo, si está configurada, si hay sesión y
si el grabador sigue activo. `grabador_activo` es ternario a propósito: `None`
es «no hay grabador que consultar», que no es lo mismo que uno apagado. La
pantalla lo consulta al construirse, al abrir la sesión y en cada fotograma que
graba — que son los tres momentos en que puede cambiar. TC-AUTO-060.

**El texto técnico del diagnóstico es el registro; la instrucción es aparte.**
`gui/coaching.py` traduce «TSUKI: HIPEREXTENDIDO» a «No bloquees el codo al
impacto». El texto técnico no se cambia porque es la clave con la que la base
agrupa los errores frecuentes.

---

**Más resolución no mejora el análisis** (medido el 28-sep-2026). MediaPipe
redimensiona el fotograma a la entrada fija de su modelo, así que la etapa de
estimación de pose cuesta prácticamente lo mismo a 1080×1920 (13,4 ms), a
1280×720 (11,7 ms) y a 640×480 (12,0 ms). Los píxeles de más no llegan al
modelo: solo encarecen la captura, el espejo y sobre todo el despliegue. En una
medición real sobre video vertical de 2,1 MP, `cv2.imshow` se llevó 20,4 de los
42,3 ms por fotograma — la mitad del presupuesto en una ventana de depuración
que la interfaz no usa. Grabar a la máxima calidad no ayuda; grabar con el
cuerpo entero en cuadro, sí.

**La medición de rendimiento se configura, no se corre a ciegas**
(28-sep-2026). `test_rendimiento.py` tomaba la marca de tiempo como
`procesados * 1000 / 30`, suponiendo 30 fps. Las grabaciones de prueba son de
**60 fps**, así que cada marca salía al doble: de ahí se derivan la velocidad
angular del Kime y los plazos de la máquina de estados del Mae Geri. Ahora usa
`Camera.marca_de_tiempo_ms()`, igual que el resto del sistema.

Dos banderas nuevas, y las dos nacieron de mediciones equivocadas:

- `--desde SEG` descarta los primeros segundos. Medir desde el fotograma cero de
  un video casero describe a la persona caminando hacia su sitio.
- `--sin-ventana` mide sin `cv2.imshow`. Medido sobre un video de 1080×1920 a
  60 fps: **36,2 fps con la ventana, 50,1 fps sin ella**. La ventana es de
  depuración y la interfaz del dojo no la usa, así que conviene reportar ambas
  cifras diciendo cuál es cuál — y medir la interfaz aparte antes de afirmar
  nada sobre el RF-01.

**El bucle del análisis en vivo lleva guardia de reentrada, y es obligatoria**
(28-sep-2026). Desde que el refresco se reprograma descontando lo ya gastado, el
temporizador del siguiente fotograma está vencido casi siempre: el trabajo de
uno supera el intervalo. CustomTkinter llama a `update_idletasks()` por su
cuenta al dibujar widgets, y **en macOS esa llamada atiende los temporizadores
vencidos**, así que dibujar el fotograma reentraba en `_actualizar_frame`, que
volvía a dibujar, hasta agotar la pila con `RecursionError`. En Linux no ocurre.

Es exactamente la diferencia entre sistemas que ya está documentada más abajo,
en la sección de `update()` — estaba escrita y no se aplicó al cambiar el ritmo
del bucle. Si alguna vez se toca el intervalo, la guardia se queda.

Lo fija `test_el_bucle_no_se_reentra_a_si_mismo`, que provoca la reentrada desde
`_mostrar_frame` —donde macOS la provoca— y reproduce el mismo `RecursionError`
sin la guardia. Ojo: una primera versión de esa prueba la provocaba desde
`_pintar_correcciones` y **pasaba sin la guardia**, porque la cámara sintética
no produce pose detectada y ese camino nunca se ejecuta. Toda prueba nueva sobre
el bucle en vivo tiene que verificarse quitando el arreglo.

**El intervalo del bucle en vivo es FIJO, y revertirlo costó una caída**
(30-sep-2026). El 28-sep se «optimizó» descontando del intervalo el tiempo ya
gastado en el fotograma, para recuperar los 15,3 ms que se sumaban al trabajo.
Subió de 18,1 a 24,2 fps. **Hubo que revertirlo el 30-sep.**

Como el trabajo de un fotograma (~40 ms) supera el intervalo (15 ms), la resta
daba **siempre el mínimo de 1 ms**, y el temporizador siguiente quedaba vencido
casi siempre. Dos fallos medidos en la Mac, los dos graves:

- **`RecursionError` durante un análisis en vivo**, con la aplicación cerrada.
  La guardia de reentrada impide que el bucle se llame a sí mismo, pero **no**
  que los ciclos de eventos anidados de Tk se acumulen, y en macOS
  `update_idletasks()` atiende los temporizadores vencidos. Nótese que la traza
  era corta —siete marcos— y aun así agotó el límite: la profundidad no venía
  del lado de Python.
- **La ventana dejaba de responder a los clics.** Con 1 ms de espera entre
  fotogramas de 40 ms, Tk recibe el 2 % del tiempo para atender al usuario; con
  el intervalo completo, cerca del 27 %. Sebastián lo describió como «doy clics
  y no responde hasta después de varios intentos», y encaja exactamente.

**Los ~6 fps no valen una caída en la defensa.** Lo fija
`test_el_ciclo_reprograma_con_el_intervalo_completo` (TC-AUTO-055), que
intercepta `after` y comprueba el plazo. `espera_hasta_el_siguiente` se retiró.

**Verificado en su Mac el 30-sep**, y esa verificación hacía falta: la
reversión se envió como razonada y sin comprobar, porque el contenedor no
reproduce el fallo. Con el intervalo fijo, un análisis en vivo sostenido no
se cayó y los clics volvieron a responder. **Que los dos síntomas
desaparecieran juntos es la evidencia de que la causa era una sola.**

**La otra optimización del 28-sep sí se conserva**, porque reduce trabajo sin
tocar la planificación: `_mostrar_frame` convertía 2 MP para dibujarlos en 0,25;
ahora reduce con `cv2.resize` antes de convertir. Medido: 20,1 ms → 5,9.

Lección general: **una optimización que cambia el ritmo del ciclo de eventos no
es una optimización local**. Si vuelve a tocarse el intervalo, hay que medir en
macOS antes de darlo por bueno — el contenedor de desarrollo no reproduce este
fallo.

Y una hipótesis mía que los datos desmintieron: supuse que la grabación de
sesión era la culpable porque aquí costaba 10 ms. En la Mac cuesta **2,2 ms**.
No era eso.

**El RF-01 depende de qué se mida, y hay tres cifras distintas**
(medido en la Mac de Sebastián el 27-sep, sobre grabación de 1080×1920 a 60 fps,
descartando los primeros 10 s):

| Qué se mide | Herramienta | fps sostenidos |
|---|---|---|
| Encadenamiento de análisis, sin ventana | `test_rendimiento.py --sin-ventana` | **44,1** ✓ |
| Encadenamiento + ventana de OpenCV | `test_rendimiento.py` | 22,0 ✗ |
| **La interfaz real** | `test_rendimiento_interfaz.py` | *pendiente en su equipo* |

La ventana de OpenCV es de depuración y el dojo no la usa, así que la cifra de
22,0 no describe el producto — pero la de 44,1 tampoco, porque la interfaz hace
cosas que esa medición no incluye: convertir el fotograma a imagen de
CustomTkinter, refrescar métricas y panel, escribir en SQLite y **grabar el video
crudo**. En el contenedor de desarrollo (Xvfb, mucho más lento que un M1) la
interfaz dio 15,2 fps con `grabacion` costando 10 ms por fotograma y
`despliegue` 21,8. Esas cifras no son las de su equipo; lo que vale es que la
herramienta ya permite medirlo donde importa.

**La cifra que va a la tesis es la de la interfaz**, porque es la que el dojo
ejecuta. Antes de tocar el requisito conviene mirar si la grabación de sesión
—que se puede apagar por equipo— es lo que lo hunde.

**Encuadre bueno medido el 28-sep**: sobre una grabación con el ejecutante de
cuerpo completo, la detección de pose es del **98 %** y la visibilidad media de
las rodillas de **0,95–0,98**; el codo derecho baja a 0,75 (79 % sobre el
umbral) porque el hikite lo oculta en parte. Esos son los números de referencia
para elegir el umbral del aviso de encuadre: un encuadre malo da 0,00, así que
la separación es limpia.

**Una herramienta de diagnóstico muestrea el video entero, no su principio**
(28-sep-2026). La primera versión de `diagnostico_video.py` leía los primeros
sesenta fotogramas y concluyó que las rodillas no se veían nunca en una
grabación donde se ven perfectamente. Dos segundos de un video que uno se graba
a sí mismo son el tramo en que la persona todavía camina hacia su sitio después
de pulsar grabar. Lo mismo vale para `test_rendimiento.py`: sus 300 fotogramas
salen del arranque, así que la medición conviene hacerla sobre un video que ya
empiece con el ejecutante colocado.

---

## Convenciones de pruebas

**Dos entornos, y las cifras difieren a propósito:**

| Entorno | Comando | Resultado |
|---|---|---|
| Completo (con cámara y pantalla) | `python3 -m pytest -q` | 822 passed |
| CI / sin entorno gráfico | igual | 679 passed, 10 skipped |

El 679 está medido en el contenedor. El 822 sale de las 816 confirmadas en su
Mac más la del arranque del golpe, las tres del plan y las dos de la corrida
parcial — **pendiente de confirmar**.

**Los diez módulos que CI omite son un punto ciego, y ya costó una corrida**
(30-sep-2026). Al añadir `timestamp_ms` a `analyze_tsuki` se actualizaron los
dieciséis puntos de llamada visibles desde el contenedor y quedaron **dos en
`tests/e2e/test_gui_vivo.py`**. Aquí pasaron las 652; en su Mac, `TypeError`.

De ahí sale `tests/unit/test_firmas_del_analizador.py` (TC-AUTO-058): lee el
árbol sintáctico de **todo** el repositorio y contrasta cada llamada a
`analyze_tsuki`, `analyze_stance` y `analyze_mae_geri` contra la firma real del
método. Al ser estática alcanza a los módulos que este entorno no puede
importar, que es la única forma de verificarlos desde aquí. Nombra archivo y
línea. Lleva además una guarda de sí misma —`test_la_busqueda_encuentra_las_
llamadas_que_debe`— porque una prueba que recorre archivos y no encuentra nada
pasa siempre.

Regla que sigue valiendo aunque exista la guarda: **al cambiar una firma
pública, `grep -rn` sobre el repositorio entero y sin `head`**. El `head -30`
de esa búsqueda fue lo que ocultó las dos llamadas.

Los módulos de `tests/e2e/` se omiten solos con `pytest.importorskip`. Por eso
toda regla de presentación que pueda expresarse sin CustomTkinter **se extrae a
un módulo puro** (`gui/panel_vivo.py`, `gui/coaching.py`,
`gui/validacion_umbrales.py`, `gui/registro_alumno.py`, `vision/fuentes.py`,
`vision/nombres_camara.py`, `vision/grabacion.py`) para que CI la verifique.

**Fichas de caso de prueba.** Los casos formales llevan `@ficha(...)` de
`tests/reporte/plantilla.py`, validado al importar. Los IDs `TC-AUTO-NNN` deben
ser únicos y correlativos — **el siguiente libre es TC-AUTO-063**. Cada módulo
de pruebas necesita al menos una ficha o `--exigir-fichas` falla.

```bash
python3 -m pytest --exigir-fichas --reporte-formal   # lo que corre CI
```

`docs/casos_prueba_automatizados.generado.md` está versionado y **solo se
reescribe en corridas completas**; una corrida parcial informa por qué no lo
actualizó, para que no borre evidencia.

**Una corrida parcial tiene DOS causas y no significan lo mismo** (30-sep-2026).
El auditor de formato distinguía solo entre corrida completa y módulos omitidos
por el entorno, así que ejecutar una prueba suelta —`pytest
tests/unit/test_guardia.py`— imprimía «**incumplimiento**: la serie de IDs tiene
huecos» seguido de cuarenta y nueve identificadores. La suite estaba perfecta;
lo único que pasaba es que no se había pedido entera. Se vio preparando una
demostración, y ahí es donde más daño hace: un aviso que grita ante lo normal se
aprende a ignorar, y deja de servir cuando el hueco es real.

| Por qué faltan módulos | Qué significa |
|---|---|
| El entorno no puede importarlos | Este equipo no sirve: hay que correrlos en otro |
| No se pidieron | No se pidieron. Nada más |

Se cuenta comparando **archivos en disco** contra los recolectados, no
interpretando los argumentos: `pytest archivo.py::prueba` y `pytest -k patrón`
seleccionan igual de parcialmente por caminos distintos. El inventario vive en
`self.modulos_en_disco` y no dentro del cálculo, para que un doble pueda
**declarar** qué considera «completo» en vez de heredar lo que haya en el disco
de quien ejecuta.

En una corrida elegida la lista de huecos ya no se imprime: falta casi toda la
serie por construcción y volcarla escondía el único renglón que importaba.

**El plan de pruebas se genera, no se escribe** (30-sep-2026). `plan_de_pruebas.py`
(raíz) produce `docs/plan_de_pruebas.csv` —que abre en Excel o Project, con las
columnas de planificación **vacías**— y `docs/plan_de_pruebas.md`, con el
comando exacto de cada caso y su criterio de aceptación.

Lee el **árbol sintáctico**, no importa los módulos, y esa decisión es la que
lo hace servir: los diez módulos de `tests/e2e/` se omiten solos sin entorno
gráfico, así que un plan generado importándolos saldría **sin los casos de
interfaz**, que son justamente los que hay que ejecutar a mano delante de
alguien. Cada fila declara si necesita pantalla y cámara o corre en cualquier
equipo, porque eso decide si una prueba se puede planificar en integración
continua o hace falta una sesión presencial.

Las columnas de fecha, responsable y resultado salen vacías a propósito:
rellenarlas convertiría el plan en el registro de unas pruebas que nadie
ejecutó. Lo fija `test_las_columnas_de_planificacion_salen_vacias`, y
TC-AUTO-062 comprueba además que **el comando de cada fila ejecuta de verdad**
—se corre uno— y que la serie de identificadores no tiene huecos.

**Dobles de prueba:** `CamaraSintetica` y `pose_sintetica()` en
`tests/helpers/fakes.py` permiten ejercitar el encadenamiento completo sin
cámara ni ejecutante. La prueba *declara* los ángulos y verifica qué concluye el
sistema.

**La navegación está contada, no supuesta** (RNF-04, 16-sep-2026).
`gui/navegacion.py` declara la secuencia exacta de controles de cada tarea
principal; ninguna pasa de tres pulsaciones. Lo vigilan dos pruebas:
`tests/unit/test_navegacion.py` cuenta los pasos (corre también en CI, porque el
módulo no importa CustomTkinter) y `tests/e2e/test_navegacion_rnf04.py` recorre
cada ruta **pulsando los widgets reales** que encuentra por su etiqueta. Al
mover, renombrar o intercalar un control hay que actualizar la ruta, o el
recorrido falla nombrando el paso y listando los botones que sí están. Escribir
no cuenta como pulsación: el requisito mide profundidad de navegación.

**En las pruebas de interfaz, `update()` nunca; `update_idletasks()` sí.**
`update()` atiende el ciclo de eventos completo y deja correr el reloj mientras
lo hace, así que el `after(15 ms)` del análisis en vivo vence dentro de la
propia llamada: ejecuta un fotograma (~100 ms con MediaPipe real), ese fotograma
programa el siguiente refresco, que ya está vencido, y la llamada no vuelve
nunca. Colgó la suite en la Mac el 18-sep-2026; en Linux no, porque ahí
`update()` no llega a dejar vencer el temporizador. Lo fija
`test_el_recorrido_no_llama_a_update`.

Y una lección sobre **qué se puede afirmar en esa prueba**, que costó dos
intentos fallidos: cuánto avanza el ciclo de video depende del sistema
operativo. Con el intervalo forzado a cero, macOS encadena sin parar y Linux se
detiene, con el mismo código correcto. Cualquier aserción sobre el número de
vueltas es verdad en una máquina y mentira en la otra. Lo que sí es igual en
todas —y lo único que la prueba afirma— es que este recorrido no llama a
`update()`; medido, no lo llama ni una vez, ni siquiera desde dentro de
CustomTkinter.

---

## Varios chats sobre el mismo repositorio

Sebastián trabaja con **dos chats**: uno para código y otro para la
documentación de las pruebas. El 27-sep se construyó dos veces lo mismo —el
reloj de las grabaciones— porque se generaron parches desde una base vieja.
Para que no vuelva a pasar:

1. **`git fetch origin main` ANTES de generar cualquier parche**, y generarlo
   desde `origin/main`, no desde lo que el contenedor tenga guardado. Esto es
   responsabilidad mía, no suya.
2. Si `origin/main` trae cosas que no conozco, **leerlas antes de escribir
   nada**: puede que lo que iba a construir ya exista, y hecho de otra forma.
3. Él empuja antes de cambiar de chat. Lo que no está en `origin/main` no
   existe para el otro chat.

`CLAUDE.md` es la memoria compartida, pero solo sirve si está empujado.

---

## Entrega de cambios

El `git push` desde el contenedor está bloqueado (403). El flujo es:
**commitear local → `git format-patch` → enviar los `.patch` → Sebastián los
aplica con `git am` y empuja él.**

Lecciones aprendidas, todas por haberlas sufrido:

- **Un solo lote a la vez, con nombre único** (`final14sep-01-…`). Lotes que se
  solapan provocan `git am` fallidos difíciles de diagnosticar.
- **Generar el lote desde el commit que Sebastián ya tiene publicado**, no desde
  `origin/main` del contenedor (los hashes difieren porque él es el committer).
- **Ensayar siempre** sobre un clon limpio partiendo de su commit real, y correr
  los dos entornos antes de enviar.
- Decirle que borre los parches viejos de `~/Downloads` antes de aplicar.
- **Nunca repetirle un `git am` de un parche que ya aplicó** (30-sep-2026, tres
  veces el mismo día). Un `git am` que falla por estar ya aplicado deja
  `.git/rebase-apply` a medias, y a partir de ahí **todos** los siguientes
  mueren con «previous rebase directory still exists but mbox given» — así que
  el error no se ve donde se produjo. Sale de darle un bloque de comandos que
  incluye parches anteriores «por si acaso». No: **un solo `git am` por
  mensaje**, el que falta, y antes comprobar contra la cuenta de pruebas que
  informó cuál tiene ya aplicado. Si el lote se enreda, la salida es siempre
  `git am --abort` y luego el parche que falte, uno a uno.
- **Comprobar que el parche anterior está aplicado antes de generar el
  siguiente.** El 30-sep se construyó un lote sobre un `CLAUDE.md` que incluía
  cambios que él no tenía, y no aplicó. La cuenta de pruebas de su última
  corrida es la forma rápida de saberlo.
- `zsh` **no** trata `#` como comentario en la línea interactiva: nunca mandarle
  comandos con comentarios al final.
- **Los commits van sin líneas de atribución** (28-sep-2026). Nada de
  `Co-Authored-By:` ni `Claude-Session:` al final del mensaje: el repositorio es
  de Sebastián y los commits son suyos. Los ya publicados se quedan como están
  —reescribir veinte commits ya empujados para quitar un renglón obligaría a un
  `push --force` que rompe el clon del otro chat y no arregla nada.
- **Nunca borrar con globs dentro de `evidencias/`.** Ahí conviven archivos
  versionados con los que generan las corridas, y un `rm evidencias/*.md` se
  lleva la evidencia de la tesis por delante. Ha pasado tres veces. Borrar
  siempre por nombre completo, y comprobar antes con
  `git ls-files --error-unmatch <archivo>`.

---

## Estado y pendientes

**Funciona y está verificado:** captura, estimación de pose, inferencia,
retroalimentación en vivo con correcciones, persistencia, panel de inicio,
historial, perfil del alumno con gráfica de evolución, reporte de sesión con
prevención de lesiones, biblioteca de técnicas, calibración de umbrales,
selección de cámara, **grabación del video crudo de cada sesión** y
**re-análisis de una grabación** desde la pantalla de cámara.

**Bloqueado por hardware:** RF-02 y RF-04 (sensores inerciales). Sebastián tiene
el ESP32 y los IMU pero **no tiene cautín**. La contingencia ya está tomada: el
sistema funciona solo con visión y declara la ausencia.

**Pendiente de Sebastián, no mío:** confirmar con su sensei los rangos de
**Kokutsu Dachi** (145–175° rodilla delantera, 90–120° trasera). Esos números
los deduje yo del principio biomecánico, no salen del dojo, y hoy gobiernan el
clasificador. Desde el 19-sep **ya no bloquea la toma de datos**: lo que se
mida ahora se puede volver a juzgar cuando el sensei conteste.

**Sin resolver, decisión de Sebastián:** el consentimiento para grabar a los
alumnos del dojo, en particular a los menores. El sistema permite apagar la
grabación por equipo, pero el permiso en sí es un trámite fuera del código y
conviene tenerlo firmado antes de la primera visita.

**Abierto tras la prueba en vivo del 28-sep** (ver `docs/bitacora_28sep2026.md`):

- **El sistema se queda en 2D** (medido el 29-sep-2026, `comparar_2d_3d.py`
  sobre 3190 fotogramas de Zenkutsu Dachi, ya con el eje sagital corregido):

  | | 2D | 3D |
  |---|---|---|
  | Zenkutsu reconocido | 20,0 % | 22,8 % |
  | Heiko Dachi | 45 % | 12 % |
  | Kiba Dachi | 1 % | **33 %** |

  El 2,8 % de ventaja del 3D no paga el cambio, y la fila de Kiba dice por
  qué **no** conviene: el 3D lee las rodillas 15,3° más flexionadas de
  mediana, así que convierte en «postura de jinete» un tercio de los
  fotogramas en que el ejecutante simplemente está de pie. Heiko y Kiba son
  justamente las dos posturas que se verificaron correctas en el dojo con la
  medida 2D. **El 3D tiene un sesgo sistemático hacia la flexión.**
  `BiomechanicsMath.calculate_angle_3d` y la herramienta quedan para poder
  repetir la comparación; el sistema no las usa.

  Esto desbloquea la **sección 4.3**: describe un sistema 2D con su
  limitación medida y mitigada por protocolo de cámara, no uno 3D.

- **La guardia NO es el problema, el criterio sí** (29-sep-2026, medido).
  Separando los ángulos por la guardia deducida sobre 2533 fotogramas:

  | Guardia | n | rodilla izq (mediana / P5) | rodilla der (mediana / P5) |
  |---|---|---|---|
  | IZQ ADELANTE | 546 | **141,4 / 135,9** | 177,3 / 159,4 |
  | DER ADELANTE | 1693 | 173,6 / 167,9 | **135,2 / 104,4** |

  La guardia acierta: la rodilla que declara delantera es siempre la más
  flexionada. Lo que falla es que **la delantera no baja lo suficiente**. El
  clasificador exige `< 130°` (`RODILLA_FLEXIONADA`) y la mediana medida de
  una rodilla delantera real es 135–141°. Con la derecha adelante solo pasa
  la cola de la distribución; con la izquierda no pasa nunca.

  **Los umbrales de evaluación, en cambio, están bien.** De las 637 posturas
  reconocidas, **el 90 % se juzga CORRECTO** (delantera dentro de 90–115°,
  trasera dentro de 165–180°). Llegué a escribir aquí que el criterio
  reprobaría una ejecución buena; era falso, y salió de mirar la mediana
  global (135°) en vez de la distribución condicionada. Los fotogramas que
  se reconocen son justo los que se miden bien, y ahí el criterio acierta.
  **El Zenkutsu no necesita recalibración; el Kokutsu sigue pendiente del
  sensei por otro motivo.**

  Lo que falla es la MEDICIÓN, no el criterio ni la guardia. El cruce
  encuadre × guardia lo localiza:

  | Encuadre | IZQ adelante | DER adelante |
  |---|---|---|
  | de frente | 166,7 | 169,1 |
  | a 45° | 146,1 | 148,2 |
  | **de perfil** | **141,1** | **107,4** |

  De frente y a 45° las dos guardias coinciden. **Solo de perfil divergen, y
  en 34°.** Eso descarta el encuadre como explicación.

  **La oclusión también queda descartada, y al revés de lo esperado**: de
  perfil, la pierna delantera *lejana* al sensor mide 113,4° de mediana y la
  *cercana* 135,5°. La lejana se mide mejor.

  Pero esa cifra no concluye nada, y conviene no citarla: en esta grabación
  la cámara estuvo casi siempre del mismo costado, así que «pierna
  izquierda» y «pierna cercana» son **el mismo grupo** (419 contra 352
  fotogramas; 876 contra 943). Los dos criterios están confundidos y esta
  muestra no puede separarlos.

  **Lo que hace falta es una grabación diseñada, no otro corte de la misma:**
  la MISMA guardia —por ejemplo derecha adelante— filmada de perfil desde el
  costado izquierdo y desde el derecho, unos 15 s cada una. Ahí la pierna
  anatómica se mantiene fija y la cercanía al sensor se invierte, que es lo
  único que separa las dos explicaciones. El cruce 2×2 que lo lee ya está en
  `comparar_2d_3d.py`, y avisa cuando faltan celdas con muestra.

  Dato a tener presente en cualquier explicación: la puntuación de
  visibilidad **no delata** el error. La pierna peor medida marca 0,958 de
  media. MediaPipe infiere articulaciones ocultas sin bajar esa cifra, así
  que no sirve como guardia contra este fallo.

- **ABIERTO: por qué una guardia mide la rodilla delantera 34° más
  estirada que la otra** (29-sep-2026). Sobre el video de Zenkutsu, los 637
  reconocidos salen **todos** con la derecha adelante. Las tres explicaciones
  que parecían obvias están **descartadas por medición**:

  | Hipótesis | Qué la descarta |
  |---|---|
  | La guardia se deduce mal | Aparece IZQ ADELANTE en 546 fotogramas (22 %), y ahí la rodilla izquierda ES la más flexionada (141,4 contra 177,3). Acierta. |
  | Es el ángulo de cámara | De frente y a 45° las dos guardias coinciden (166,7/169,1 y 146,1/148,2). Solo divergen de perfil. |
  | Es oclusión de la pierna lejana | La pierna peor medida se ve **mejor**: visibilidad 0,958 contra 0,923. Y de perfil la delantera *lejana* mide 113,4° y la *cercana* 135,5°, al revés de lo esperado. |

  La causa sigue sin identificarse. Lo que impide avanzar es que en esa
  grabación la cámara estuvo casi siempre del mismo costado, así que «pierna
  izquierda» y «pierna cercana al sensor» son el mismo grupo de fotogramas
  (419 contra 352; 876 contra 943) y **no se pueden separar por análisis**.

  **Hace falta una grabación de control, no otro corte:** la MISMA guardia
  filmada de perfil desde el costado izquierdo y desde el derecho, ~15 s cada
  una. La pierna anatómica queda fija y la cercanía al sensor se invierte. El
  cruce 2×2 que lo lee ya está en `comparar_2d_3d.py` y avisa cuando faltan
  celdas con muestra. Sebastián lo graba la noche del 29-sep.

  Mientras no se resuelva, **esto bloquea la campaña de recolección**: si es un
  sesgo de pierna, la mitad de los alumnos se mediría mal según con qué guardia
  entrenen.

  Dato para cualquier explicación que se intente: la puntuación de visibilidad
  **no delata** el error. MediaPipe infiere articulaciones ocultas sin bajarla.

- **Veredicto por rodilla en posturas asimétricas**: ya se informa cuál rodilla
  está fuera de su rango, pero las reglas siguen emitiendo un único veredicto de
  postura. El panel muestra ambos.
- **Calibrar `SEPARACION_MINIMA_EN_CADERAS`** contra grabaciones reales antes de
  fijar el número en la tesis.

**Pendiente de escritura:**

- Empaquetado: `.command` para Mac, `.exe` para Windows (lo compila él).
- Ajustar el prototipo `.dc.html` para que no prometa «340 reglas» ni «red
  neuronal v0.9 entrenando».

**Qué documento del capítulo 4 manda** (aclarado por Sebastián el 29-sep-2026,
y es la principal fuente de desorden entre chats):

| Documento | Qué es |
|---|---|
| `Capitulo 4 - 31 de agosto.docx` | **El canónico.** Es el que él mantiene y el que va a la tesis. Lleva los campos de índice y la numeración automática de Word. |
| `Capitulo_4_consolidado_28_sep_2026.docx` | Una consolidación que **generó ChatGPT** juntando las entregas sueltas. Útil como material, **no es el capítulo**. |
| `Capitulo_4.3…` a `Capitulo_4.8_Manuales_v2.docx` | Mis entregas por sección, de septiembre. Material de origen. |
| `Capitulo_4_actualizacion_29_sep_2026.docx` | Los cuatro bloques que corrigen lo que la sesión del 29-sep dejó desfasado. |

El trabajo pendiente **no es escribir**: es **fusionar** lo anterior dentro del
documento del 31 de agosto sin perder sus campos de índice. Por eso las
entregas van como fragmentos con instrucción de qué reemplazan, y no como un
capítulo regenerado: regenerarlo destruiría la numeración automática.

**Estado por sección** (según la consolidación, que es lo más completo que hay):

| | Sección | Estado |
|---|---|---|
| 4.1 | Estructuración de la arquitectura y modularización | escrita |
| 4.2 | Creación de la base de conocimiento técnica | escrita |
| 4.3 | Codificación de las reglas del motor de inferencia | escrita; 4.3.3 y 4.3.4 **se sustituyen** con la actualización del 29-sep |
| 4.4 | Elaboración de la interfaz de usuario | escrita (4.4.1–4.4.8) |
| 4.5 | Estructuración de la base de datos biomecánica | escrita (4.5.1–4.5.7) |
| 4.6 | Elaboración física de los dispositivos wearables | escrita (4.6.1–4.6.4) |
| 4.7 | Ejecución de las pruebas de validación | escrita (4.7.1–4.7.10); **se añade 4.7.11** |
| 4.8 | Redacción de manuales técnicos y guías de usuario | escrita (4.8.1–4.8.5). Los dos manuales existen y están **pendientes de su revisión** |

Las tablas llegan hasta la **4.14**; la actualización del 29-sep añade la
**4.15**, **4.16** y **4.17**. La siguiente libre es la **4.18**.

Formato de los `.docx`: Times New Roman 12, interlineado 1.5, sangría de primera
línea. Los títulos de **nivel 2 van sin número** (Word los numera solo); los de
nivel 3, con número escrito.

---

## Cómo le sirve más el trabajo

Verificar antes de afirmar. Cuando algo se rompe, reproducirlo con una prueba
antes de arreglarlo, y comprobar que esa prueba falla sin el arreglo. Las cifras
que van a la tesis se cuentan, no se recuerdan — la terna puede correr `pytest`.
Cuando me equivoco, decirlo directo y seguir.
