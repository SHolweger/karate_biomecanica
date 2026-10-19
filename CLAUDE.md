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

**El veredicto sigue a la vista mientras se sostiene el Kime** (18-oct-2026;
antes era un efecto de diseño pendiente de decidir para la defensa). Sostener
el brazo extendido más de `VENTANA_RECORRIDO_MS` aplanaba la ventana, la
máquina volvía a REPOSO —correctamente: el golpe terminó— y el aviso pasaba a
«SIN TSUKI» con el brazo todavía extendido. En la demostración el texto
desaparecía del video mientras la terna miraba.

**Se resolvió en la presentación, no en la detección, y el primer intento
enseñó por qué.** Ese intento cambiaba la condición de salida de RECOGIENDO
para que «estar cerca del pico» no contara como reposo. Pasaba las pruebas
escritas para él. Una comparación contra la máquina anterior sobre 20 000
secuencias aleatorias —golpes, sostenidos, recogidas parciales, extensiones
lentas, temblor— encontró que **perdía golpes en el 0,6 %**: una extensión que
seguía subiendo tras juzgarse por `TIEMPO_MAXIMO_EXTENSION_MS`, o una recogida
parcial que volvía a subir atravesando la altura del pico, se leían como
«sostener». Corregir esos casos los bajó a 7 de 20 000, no a cero: perseguirlos
uno por uno no cerraba la clase de error.

La versión que queda no toca ninguna transición. `_sostiene_el_kime` solo
decide qué texto se devuelve en los fotogramas de REPOSO: si el brazo **no se ha
alejado** más de `MARGEN_PICO` del ángulo en que se juzgó el golpe, **en ningún
fotograma desde entonces**, se sigue mostrando el veredicto. La banda se vigila
en todos los fotogramas —también mientras se recoge—, porque pasar por la altura
del Kime al volver a subir no es sostenerlo. Medido contra la máquina anterior,
60 000 secuencias con tres semillas:

| | resultado |
|---|---|
| Golpes emitidos (fotograma, mensaje, ángulo) | **idénticos en todas** |
| Filas de veredicto cerrado en la base | **idénticas en todas** |
| Secuencias donde el veredicto se ve más tiempo | ~34 % |
| Filas totales | ~1,5 % menos |

Las filas que desaparecen son todas **«SIN TSUKI»** —`correcto` NULL—, que la
máquina anterior escribía al aplanarse la ventana cuando el brazo pasaba del
sostenido directamente a otro golpe. No cuentan para la precisión: todas las
consultas agregadas filtran `correcto IS NOT NULL`.

Tres pruebas en TC-AUTO-068 (`tests/unit/test_tsuki.py`), y cada una se comprobó
**fallando contra lo que debe impedir**:

- `test_el_veredicto_sigue_a_la_vista_mientras_se_sostiene_el_kime` falla con la
  máquina anterior;
- `test_los_dos_casos_que_rompieron_la_primera_version` lleva los dos tramos
  **reales** que delató la comparación —extraídos del generador, no escritos a
  mano: una primera versión aproximada a mano no reproducía el caso ni siquiera
  con la máquina vieja— y falla contra el primer intento;
- `test_sostener_solo_cambia_el_texto_nunca_los_golpes` anula el sostenido sobre
  800 secuencias y exige los mismos golpes; falla si alguien conecta
  `_sostiene_el_kime` a una transición.

**Y el codo solo no bastaba** (19-oct-2026, visto en su Mac sobre «Zenkusu
dachi.mp4»): «IZQ - TSUKI: EXCELENTE» seguía en pantalla **con el brazo
colgando junto a la cadera**. Bajar el brazo estirado deja el codo en los mismos
~160°, así que para el sostenido era lo mismo que mantener el Kime. Ahora
`TsukiStateMachine.update` recibe además, opcional, la **dirección del brazo**
(de hombro a muñeca, en grados sobre la imagen; la calcula el analizador), y el
sostenido termina si gira más de `MARGEN_DIRECCION` (25°) respecto de la que
tenía **cuando el codo llegó a su máximo** —no cuando se juzgó: un brazo que se
queda extendido se juzga a los 1,5 s, cuando quizá ya bajó; la primera versión
del arreglo guardaba esa y las pruebas la delataron—. Bajarlo al costado gira
~90°; el vaivén de sostener, ±8° en la prueba.

Sigue siendo **solo texto**: `test_la_direccion_solo_cambia_el_texto_nunca_los_golpes`
compara 800 secuencias aleatorias con direcciones que vagan al azar contra no
informar dirección, y los golpes salen idénticos. Quien no la informe
—`revisar_tsuki.py`, las pruebas viejas— tiene la máquina de antes. Lo que sí
cambia: el anillo rojo de un Tsuki incorrecto ya no se queda sobre el codo de
un brazo bajado. TC-AUTO-075.

Un efecto que conviene saber: el falso positivo confirmado del 30-sep —estirar
el brazo y sostenerlo, juzgado «HIPEREXTENDIDO» por tiempo— ahora también se ve
mientras se sostiene, en vez de desaparecer a los 500 ms. No escribe más filas;
solo dura más en pantalla.

La lección, que vale para cualquier cambio en una máquina de estados ya
validada en vivo: **las pruebas escritas para el arreglo comprueban lo que uno
pensó; una comparación contra la versión anterior sobre entradas aleatorias
comprueba lo que uno no pensó.** Esta encontró en un minuto dos casos que ninguna
de las pruebas escritas a mano cubría.

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

**Una imagen congelada no es un alumno quieto, y hay que decirlo**
(1-oct-2026). Cuando la fuente dejaba de entregar fotogramas, el bucle anotaba
el motivo en `_motivo_detencion`, aumentaba `_sin_fotograma` y **se reprogramaba
igual**. Ninguna de las dos variables se leía desde la interfaz: sus únicos
lectores eran las dos últimas líneas de `test_rendimiento_interfaz.py`. Un
contador que se incrementa y nadie consulta es peor que no tenerlo — al leer el
código parece que hay una guarda donde no la hay.

Lo que veía el sensei era la última imagen congelada, indefinidamente, con la
sesión abierta y el último veredicto a la vista. En un dojo eso no es
hipotético: alguien tropieza con el USB, o el teléfono que hace de cámara IP
pierde la red. Y contradice el criterio que gobierna toda la presentación: una
imagen congelada **muestra algo que ya no se está midiendo**.

`vision/senal.py` (puro, corre en CI) redacta el aviso y distingue las dos
situaciones, que no son la misma: de una grabación significa que se acabó el
archivo —final normal, no fallo— y de una cámara, que hay que ir a mirar el
cable. Se mide en **segundos de reloj**, no en fotogramas perdidos: el bucle
corre a la velocidad de MediaPipe, así que «treinta fotogramas» dura cosas
distintas en dos equipos. El umbral es 1,5 s, holgadamente por encima de un
fotograma perdido (40 ms a 24 fps) y por debajo de lo que tarda alguien en
dudar de lo que ve. **El aviso se retira solo** cuando la imagen vuelve: uno
que se queda puesto enseña a ignorarlo.

Lo fija TC-AUTO-063 (unitaria, la redacción) y TC-AUTO-064
(`test_la_pantalla_avisa_cuando_la_imagen_deja_de_llegar`, e2e, **la costura**),
porque lo que faltaba no era el texto sino que alguien lo consultara. La e2e
retrasa `_desde_sin_imagen` en vez de dormir 1,5 s: lo que verifica es la
costura, no el reloj.

**El texto técnico del diagnóstico es el registro; la instrucción es aparte.**
`gui/coaching.py` traduce «TSUKI: HIPEREXTENDIDO» a «No bloquees el codo al
impacto». El texto técnico no se cambia porque es la clave con la que la base
agrupa los errores frecuentes.

**Y ninguna postura llegaba traducida** (encontrado el 18-oct-2026). El
analizador no entrega el veredicto pelado: le antepone la postura que
reconoció —`ZENKUTSU (IZQ ADELANTE): POSTURA: CORREGIR ALTURA`,
`POSTURA NATURAL: HEIKO DACHI: CORRECTO`—, y `traducir` solo sabía quitar el
prefijo de lado de los golpes. La búsqueda fallaba y, por diseño, un veredicto
sin entrada se muestra tal cual. **El Tsuki se traducía; Heiko, Kiba, Zenkutsu
y Kokutsu, nunca**, ni en el panel en vivo ni en el reporte de sesión.
Reproducido: 8 de 8 geometrías de postura llegaban en lenguaje técnico.

La guarda de la tabla, TC-AUTO-034, pasaba todo ese tiempo, porque comprobaba
que cada veredicto tuviera entrada **en la tabla**, no que el mensaje que la
pantalla recibe se tradujera. Es la lección del doble de MediaPipe otra vez: una
guarda que mira el lugar equivocado no verifica, ratifica.

`traducir` prueba ahora el mensaje entero y lo que queda tras cada «: », del más
largo al más corto (`veredicto_conocido`). Un veredicto desconocido sigue
mostrándose tal cual. Lo fija **TC-AUTO-066**
(`tests/integration/test_correcciones_de_postura.py`), que hace el recorrido
real —geometría corporal, analizador, mensaje, traducción— y falla sin el
arreglo.

**El veredicto de postura dice qué rodilla corregir** (18-oct-2026).
Zenkutsu y Kokutsu se juzgan con un rango por rodilla, pero cuando fallaban
respondían «POSTURA: CORREGIR ALTURA», igual que Kiba Dachi. En una postura
simétrica eso basta; en una asimétrica no dice cuál de las dos rodillas
corregir ni hacia dónde, y el sistema tenía el dato. Ahora:

| Qué falla | Veredicto | Lo que lee el alumno |
|---|---|---|
| Delantera menos doblada que su rango | `POSTURA: FLEXIONA MAS LA RODILLA DELANTERA` | Flexiona más la rodilla de adelante |
| Delantera más doblada que su rango | `POSTURA: EXTIENDE LA RODILLA DELANTERA` | Abre un poco la rodilla de adelante |
| Trasera menos doblada que su rango | `POSTURA: FLEXIONA MAS LA RODILLA TRASERA` | Flexiona más la rodilla de atrás |
| Trasera más doblada que su rango | `POSTURA: EXTIENDE LA RODILLA TRASERA` | Estira la pierna de atrás |
| Las dos | `POSTURA: CORREGIR AMBAS RODILLAS` | Corrige las dos rodillas |

**Y Kiba dice hacia dónde** (mismo día). Es simétrica y no hay rodilla que
nombrar, pero «CORREGIR ALTURA» no decía si subir o bajar, ni nombraba el error
típico de la postura, que es cargar el peso en una pierna:

| Qué falla | Veredicto | Lo que lee el alumno |
|---|---|---|
| Las rodillas, por encima de su rango | `POSTURA: FLEXIONA MAS LAS RODILLAS` | Baja más la postura |
| Por debajo | `POSTURA: EXTIENDE LAS RODILLAS` | Sube un poco la postura |
| Una por encima y otra por debajo | `POSTURA: REPARTE EL PESO EN LAS DOS PIERNAS` | Reparte el peso entre las dos piernas |

**No se nombra el lado, y es a propósito**: el analizador trabaja en modo
espejo y Kiba se filma de frente, así que la «izquierda» de la pantalla es la
pierna derecha del alumno. Decirle «la izquierda» le haría corregir la pierna
equivocada.

Con los cortes del clasificador (130–160°) y el rango de literatura (130–150°),
una rodilla de Kiba reconocida nunca queda por debajo de su rango, así que hoy
solo se ve «Baja más la postura». Las otras dos existen porque los umbrales son
datos: si el cuerpo técnico sube el mínimo, aparecen. TC-AUTO-069.

**Ninguna regla emite ya «POSTURA: CORREGIR ALTURA»**, pero su traducción se
queda en `gui/coaching.py`: las sesiones registradas antes del 18-oct lo llevan
y su reporte se sigue abriendo.

Tres cosas que conviene saber de este cambio:

- **El veredicto booleano no se mueve; solo el texto.** Lo fija
  `test_solo_cambia_el_texto_nunca_el_veredicto`, que recorre una rejilla de
  ángulos y pasaba **antes y después** del cambio — que es justo lo que tiene
  que hacer. La precisión del alumno, su gráfica de evolución y
  `reevaluacion.py` comparan por `correcto`, así que no les afecta.
- **El sentido sale del rango vigente**, no de números escritos en la regla:
  si el cuerpo técnico recalibra, la corrección sigue al criterio nuevo.
- **Sí cambia la clave con que se agrupan los errores frecuentes**, y se
  decidió hacerlo a propósito **antes de la campaña de recolección**: lo medido
  antes del 30-sep ya no sirve para precisión y la base se aparta antes de
  empezar. Hecho después, el reporte habría mostrado el mismo error con dos
  nombres. A cambio, «errores frecuentes» pasa a decir **qué rodilla** falla
  más, que es un dato que el sensei puede usar.

Los veredictos que se construyen en un método y no en un `return` literal
están declarados en `knowledge_base.VEREDICTOS_DECLARADOS`, porque
`sin_traduccion()` lee el código fuente y no los vería.
`test_todo_veredicto_por_rodilla_esta_declarado` recorre la regla y comprueba
que la declaración está completa. Lo fija **TC-AUTO-067**
(`tests/unit/test_veredicto_por_rodilla.py`).

**Lo que se trajo del prototipo y lo que no** (19-oct-2026, a pedido de
Sebastián, tras revisar sus dos videos del `.dc.html`). Tres cosas se
trajeron, **con datos reales en vez de cifras de adorno**:

1. **La técnica ideal se calcula, no se dibuja.** En el prototipo era decoración:
   el código interpolaba entre dos poses fijas de puñetazo para *todas* las
   técnicas, así que «Técnica ideal · Mae-geri» lanzaba un puño.
   `gui/tecnica_ideal.py` (puro, corre en CI) coloca cada articulación juzgada
   en el **centro de su rango vigente**, con proporciones antropométricas fijas
   (ningún segmento se estira para que el ángulo cuadre) y **en el plano en que
   se filma la técnica**. Sale del mismo `KarateRules` que juzga, así que
   recalibrar cambia la figura. Las pruebas no miran el dibujo sino lo que el
   sistema concluye de él: medida con `calculate_angle`, la figura da los
   ángulos del criterio, el clasificador la reconoce y la regla la aprueba —la
   guía no puede enseñar algo que el sistema reprobaría—. El Tsuki y la Mae
   Geri se dibujan en dos fases, la de salida tenue detrás del Kime.
   Aparece en cada tarjeta de «Técnicas» y en un panel de «Análisis en vivo»
   que **sigue a la última técnica reconocida** (Mae Geri en curso > Tsuki en
   extensión o juzgado > postura) y conserva la anterior en las transiciones
   para no parpadear. Solo se redibuja al cambiar. **Sin animación, a
   propósito**: otro temporizador junto al bucle de análisis es lo que tumbó la
   aplicación en macOS el 28-sep. El trazado no importa Tk —usa
   `create_line`/`create_oval`/`create_text` sobre el lienzo que le pasen—, y
   un lienzo simulado lo verifica en CI. TC-AUTO-072.

   Límite que conviene saber: las pruebas comprueban que el clasificador
   reconoce la figura **con los rangos de literatura**. Si el cuerpo técnico
   recalibra un rango de modo que su centro caiga fuera de los cortes del
   clasificador (130°, 150°, 160°), la guía enseñaría una postura que el
   sistema no reconoce. Hoy no ocurre con ningún rango.

2. **La articulación que falla, en rojo sobre el video.** Solo las de veredicto
   **incorrecto propio**: rodilla por rodilla (no el veredicto de la postura
   entera, que teñiría las dos y escondería cuál falla), el codo del Tsuki
   juzgado y la rodilla de la Mae Geri. Ni las correctas ni los veredictos
   nulos, que inventarían un fallo. El analizador entrega ahora
   `pos_articulacion` junto a cada veredicto por articulación, y
   `gui/panel_vivo.articulaciones_con_error` (puro) decide. TC-AUTO-073.

3. **El reporte dice lo medido contra el criterio.** Por articulación juzgada:
   mediana, rango y cuántas evaluaciones cupieron, con ✓/✗ **sobre la
   mediana** —por eso va al lado la cuenta: una mediana dentro con la mitad
   fuera no es una técnica dominada—. Sale de `angulo_regla_1/2`, no del número
   que se dibuja. El rango es **el que regía al empezar la sesión**:
   `Database.umbral_en` lo reconstruye por fecha, porque la fila solo guarda la
   versión de la articulación principal. Si se recalibra *durante* una sesión,
   se muestra el del inicio. Kiba resume las dos rodillas sin nombrar el lado;
   la Mae Geri queda fuera porque su veredicto usa la velocidad, que no se
   guarda. TC-AUTO-074.

**Lo que NO se trae, y es decisión, no pendiente**: puntaje 0–100 y «puntaje
global», «AUTO 94 %» (MediaPipe no da una confianza de qué técnica se
ejecutó), rotación de cadera, velocidad del puño en m/s, balance, alineación
hombro-puño en cm, «Datos IMU de la sesión», técnicas que el sistema no
distingue ni evalúa (Oi / Gyaku / Kizami-zuki, Mawashi-geri, Gedan-barai),
«Kata · pronto», «Kumite · pronto», «Voz activa», el QR de una app móvil que
no existe, «4/4 sensores», «340 reglas» y «red neuronal v0.9». Todo eso es lo
que el criterio de presentación prohíbe.

**Y una incoherencia del sistema que salió al hacerlo**: la biblioteca
listaba **Age Uke** como técnica evaluada, y el análisis en vivo nunca la
consulta —`evaluate_age_uke` solo la usa `reevaluacion.py`—. La tarjeta lo
dice ahora. No se le dibuja figura.

**Hallazgo pendiente de confirmar con video: la Mae Geri sin Hikiashi no
recibe veredicto** (19-oct-2026, leyendo el código y simulándolo). Si la pierna
baja estirada, la rodilla nunca vuelve a doblarse por debajo de
`UMBRAL_CARGA` (75°), la máquina sigue en EXTENSION y a los
`TIMEOUT_EXTENSION_MS` (3 s) **descarta el intento en silencio**. «Recoge la
pierna antes de bajarla» solo aparece si se recoge **tarde**, no si no se
recoge. Es el mismo tipo de silencio que el del Tsuki lento. La toma
`err_mae_geri_sin_recoger.mp4` del protocolo del 19-oct existe para
confirmarlo; si se confirma, va a la tesis como limitación.

---

**Una postura se registra cuando se sostiene medio segundo** (19-oct-2026,
decisión de Sebastián sobre el valor). Pasada por el analizador real su
sesión en vivo `s10` (107 s a 11 fps): de **101 veredictos de postura
escritos**, 56 duraron menos de 0,2 s y 75 menos de 0,5 s. La precisión
registrada era del **26 %**; contando solo los sostenidos, del **58 %**. Dos
causas ajenas a la técnica: el **temblor sobre el límite de un rango** —de
pie, las rodillas rondan los 165°, el mínimo del Heiko, y cada cruce alternaba
CORRECTO y DEMASIADO FLEXIONADO— y los **fotogramas de paso** entre posturas,
que el clasificador reconocía uno o dos fotogramas como Kiba, Kokutsu o
Zenkutsu. Otra vez **no falla, inventa**: un alumno quieto sacaba ~50 % por
temblor.

`expert_system/estabilidad.py` (puro): en la categoría `postura`, un mensaje
solo se registra —en la base y en la lista de correcciones— cuando lleva
`SOSTENIDO_MINIMO_MS` (500) sin cambiar, medido en tiempo del video. **El video
y las métricas siguen al fotograma**; el Tsuki y la Mae Geri no esperan, porque
sus máquinas ya juzgan una transición. Un parpadeo entre dos tramos de la misma
postura ya no la parte en dos. La prueba usa **el tramo real** de los segundos
70–88 de s10, codificado por tramos: sin la regla escribe 34 veredictos
cerrados; con ella, 3. TC-AUTO-076.

El coste, que conviene decir en la tesis: una postura que el clasificador
reconoce de forma intermitente —uno o dos fotogramas sí, uno no— ya no se
registra. En ese tramo de s10 se perdieron así varios Kiba y Zenkutsu; es lo
honesto: no se sostuvo el reconocimiento, así que no hay medición que afirmar.

**La sesión se graba sin espejo** (19-oct-2026). Se grababa el fotograma ya
volteado y, al re-analizarlo —los archivos también se voltean—, el espejo se
aplicaba dos veces: izquierda y derecha quedaban **intercambiadas respecto de
la sesión en vivo**. Medido sobre s10: la guardia izquierda en 56 fotogramas en
vivo pasaba a 38 al re-analizar y la derecha de 38 a 62. Las posturas se
reconocían igual; lo que cambiaba era el lado, y con él el desempeño por lado
y la asimetría del reporte de prevención. `Camera.fotograma_crudo` guarda el
fotograma antes del espejo y es el que se graba. TC-AUTO-077.

**Las grabaciones hechas hasta el 19-oct (s10 y anteriores) están volteadas.**
Re-analizarlas desde la interfaz intercambia los lados; para análisis con las
herramientas de consola hay que leerlas con `Camera(ruta, espejo=False)`.

**En vivo, el bucle corrió a ~11 fps** en esa sesión (la grabación sale a la
velocidad real del bucle: 11,02 fps). Con cámara, cada vuelta además espera al
siguiente fotograma del sensor, así que la cadencia en vivo puede salir
**peor** que sobre un archivo. La cifra del RF-01 que va a la tesis tiene que
medirse **con la cámara y con alguien delante**: `test_rendimiento_interfaz.py
0 900`, sin tocar la ventana mientras mide. La primera corrida del 19-oct se
cortó a los 79 fotogramas porque se navegó a otra pantalla durante la medición
y no había nadie en cuadro: sus 17,2 fps no valen.

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
| **La interfaz real** | `test_rendimiento_interfaz.py` | **≤ ~20** (cota desde el CSV; ver abajo) ✗ |

La ventana de OpenCV es de depuración y el dojo no la usa, así que la cifra de
22,0 no describe el producto — pero la de 44,1 tampoco, porque la interfaz hace
cosas que esa medición no incluye: convertir el fotograma a imagen de
CustomTkinter, refrescar métricas y panel, escribir en SQLite y **grabar el video
crudo**. En el contenedor de desarrollo (Xvfb, mucho más lento que un M1) la
interfaz dio 15,2 fps con `grabacion` costando 10 ms por fotograma y
`despliegue` 21,8. Esas cifras no son las de su equipo; lo que vale es que la
herramienta ya permite medirlo donde importa.

**La cifra que va a la tesis es la de la interfaz**, porque es la que el dojo
ejecuta.

**CORRECCIÓN del 18-oct-2026: la cifra del 15-oct era el cómputo, no la
cadencia.** El 15-oct se procesaron las dos corridas de
`test_rendimiento_interfaz.py` que había en `evidencias/` y se escribió aquí que
la interfaz daba **27,8 fps de media y 29,6 de mediana**, «a 0,4 de cumplir», y
que apagar la grabación bastaba. **Era falso**, y se le comunicó así a
Sebastián. Se calculó como 1000 / `total_ms`, y `total_ms` es el **cómputo** de
cada fotograma; la tasa sostenida se mide entre **inicios** de fotograma
consecutivos (`PerformanceMonitor.resumen_fps`), e incluye la espera fija de
`LiveScreen.INTERVALO_MS` (15 ms) y lo que Tk tarda en atender eventos. La
propia prueba del monitor lo decía —«el fps NO se deduce del tiempo de cómputo,
sino del intervalo real»— y la herramienta imprimía la cifra correcta en
pantalla; lo que no hacía era **guardarla**: el CSV solo traía el cómputo.

Lo que la corrida larga (`rendimiento_20260927_224259.csv`, 11 520 fotogramas,
la misma que el capítulo 5 cita por el «defecto del vigilante») sí permite
afirmar, descartando los primeros 10 s:

| | mediana | media |
|---|---|---|
| Cómputo por fotograma | 33,8 ms | 36,0 ms |
| ~~«Tasa» = 1000 / cómputo (lo del 15-oct)~~ | ~~29,6 fps~~ | ~~27,8 fps~~ |
| **Proyección con el intervalo fijo de hoy** = 1000 / (cómputo + 15 ms) | **20,5 fps** | **19,6 fps** |

**Precisión del 19-oct-2026 a lo anterior:** esa corrida **no** tenía la espera
de 15 ms. Se lanzó a las 22:42 del 27-sep, una hora después de aplicar la espera
adaptativa (commit de las 21:31, `espera_hasta_el_siguiente`, revertida el
30-sep), así que el bucle se reprogramaba con ~1 ms. Su cadencia propia es la
que imprimió la consola y cita el capítulo 5: **24,2 fps**, y el capítulo la
atribuye bien a «la configuración experimental cuya espera adaptativa después
se revirtió». Los 20,5 / 19,6 no describen esa corrida: **proyectan** el mismo
cómputo sobre el intervalo fijo que hoy usa la interfaz. Son techo de esa
proyección, porque no incluyen el tiempo de Tk. La decisión de abajo no cambia;
la cifra que la sostiene sale de la corrida nueva.

La cifra exacta de hoy no se puede recuperar de esos CSV. Desde el 18-oct el CSV guarda
también `intervalo_ms` —el tiempo hasta el inicio del siguiente fotograma— y la
consola imprime las dos cifras rotuladas («Sostenida» y «Techo por cómputo:
NO es la tasa sostenida»). Lo fija **TC-AUTO-070**
(`tests/unit/test_metrics.py`), que escribe el error como prueba: con 34 ms de
cómputo y 49 ms entre inicios, 1000 / cómputo da 29,4 y la cadencia es 20,4.
**Hace falta volver a correr `test_rendimiento_interfaz.py` en su Mac** para
tener la cifra exacta que va a la tesis.

Desglose por etapa de la corrida larga, en mediana (este sí era correcto: son
tiempos de cómputo):

| Etapa | ms |
|---|---|
| Estimación de pose | 17,84 |
| Despliegue | 8,32 |
| Captura | 4,62 |
| Grabación de sesión | 1,73 |
| Análisis + panel + persistencia | 0,66 |

**DECISIÓN de Sebastián (18-oct-2026): el RF-01 se reporta como CUMPLIDO
PARCIALMENTE.** Lo que se puede sostener ante la terna:

- **Cómputo < 500 ms: cumple con margen enorme** —34 ms de mediana—.
- **Cadencia ≥ 30 fps: no cumple en la interfaz**, que va a ~18–20 fps.
- **El encadenamiento de análisis sí la alcanza**: 44,1 fps sin interfaz. Lo
  que limita la cadencia en pantalla no es el análisis sino la espera fija del
  bucle, que se eligió **a propósito** el 30-sep para que la aplicación no se
  cayera en macOS y respondiera a los clics (ver «El intervalo del bucle en
  vivo es FIJO»).

**Apagar la grabación NO basta**, al revés de lo que se escribió el 15-oct:
libera 1,73 ms y la cota sube a ~21 fps. **Con una espera fija de 15 ms los 30
fps no son alcanzables**: a 30 fps cada fotograma dispone de 33,3 ms, quedan
18,3 para el cómputo, y la estimación de pose sola gasta 17,8. Cumplirlo exige
acortar la espera —que es exactamente lo que tumbó la aplicación el 28-sep, y
que no se toca sin medir en macOS— o sacar la estimación de pose a otro hilo,
que es un cambio de arquitectura. Ninguna de las dos cosas conviene a tres
semanas de la defensa.

Lo que sí queda en pie: la sospecha de que la grabación de sesión fuera lo que
hunde el rendimiento está descartada por medición: cuesta **1,73 ms**.

La lección, para no repetirla: **una cifra que va a la tesis se recalcula con la
misma definición que usa el criterio, no con la columna que está a mano.** Y una
evidencia que no guarda la magnitud con que se juzga el criterio no es
evidencia de ese criterio.

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
| Completo (con cámara y pantalla) | `python3 -m pytest -q` | **1033 passed** (19-oct, medido en su Mac, lote `kime19oct`); **1041 esperadas** tras `estable19oct` |
| CI / sin entorno gráfico | igual | 915 passed, 7 skipped (19-oct, tras `estable19oct`) |

Las 881, 905, 908, 922, 1023 y 1033 se predijeron y se contaron en su Mac:
cuadraron todas, incluidas las de interfaz que el contenedor no puede ejecutar
porque no tiene Tk. Las 1041 son otra **expectativa** —1033 + 7 de
`test_estabilidad.py` + 1 de interfaz— y no se citan hasta contarlas. Una de las pruebas
(`test_el_csv_de_evidencia_guarda_el_intervalo`) importa OpenCV y se omite sola
donde no esté instalado.

Las dos cifras están **medidas** el 15-oct-2026 sobre `origin/main`, no
deducidas: el 727 en el contenedor y el 848 en su Mac (macOS, Python 3.11.0).

**Y cuadran, que es lo que las hace citables.** Los siete módulos que este
entorno omite aportan 18 + 20 + 14 + 15 + 15 + 23 + 16 = **121** pruebas, y
727 + 121 = 848. No sobra ni falta ninguna, así que los «skipped» de aquí son
exactamente las que allá sí corren — no hay un tercer grupo escondido.

El 727 exige el plan **fuera del índice**: con `docs/plan_de_pruebas.{csv,md}`
todavía versionados salen dos fallos de `test_entrega.py`, que son los que
cierra el `git rm --cached`.

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
ser únicos y correlativos — **el siguiente libre es TC-AUTO-078**. Cada módulo
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

**Ninguno de los dos se versiona** (1-oct-2026): se deducen de las fichas, que
sí lo están, y versionar la derivación rompió una entrega. Se regeneran con
`python3 plan_de_pruebas.py` cuando hagan falta.

La causa costó **tres diagnósticos equivocados** y bloqueó dos días la entrega
del aviso de señal perdida —un cambio que no toca el plan por ningún lado—:

```
error: patch failed: docs/plan_de_pruebas.csv:1
error: docs/plan_de_pruebas.csv: patch does not apply
```

No era el BOM, ni bastaba con poner `lineterminator="\n"` en el generador.
**`git am` aplica `--no-keep-cr` por omisión**: borra el CR del final de cada
línea del parche, así que las líneas `-` del CSV dejaban de coincidir con el
blob que sí los tenía. El archivo estaba bien; el que lo rompía era el
transporte.

La decisión no es de formato sino de naturaleza: la fuente de verdad —los
decoradores `@ficha(...)`— ya está versionada, así que los dos archivos son
**derivaciones**, y versionar una derivación obliga a que las dos máquinas la
tengan byte a byte idéntica. En cuanto divergen, ningún parche que las toque
puede aplicar en los dos lados.

`docs/casos_prueba_automatizados.generado.md` **sí** se versiona, y la
diferencia no es arbitraria: registra qué pruebas *pasaron* en una corrida
—evidencia de un hecho, material de la tesis— y solo se reescribe en corridas
completas. Uno es un registro; el otro, una vista.

Lo fija **TC-AUTO-065** (`tests/unit/test_entrega.py`), que comprueba **la
salida del generador** y no lo que haya en el disco —el disco puede estar en
cualquier estado y con esta decisión ya no importa—: ni CRLF, ni línea en
blanco al final, y BOM en el CSV porque Excel lo necesita.
`test_el_plan_generado_no_esta_versionado` vigila la decisión y su mensaje de
fallo trae el `git rm --cached` que la restablece; `test_el_registro_de_la_
corrida_si_esta_versionado` vigila la otra mitad, para que no se lea como «lo
generado no se versiona nunca».

**Y el paso de sacarlos del índice lo da él, no un parche.** Un parche que los
borrara tendría que arrastrar su contenido como líneas `-`, con los CRLF
dentro, que es exactamente lo que no sobrevive a `git am`. `git rm --cached`
toca el índice y no necesita que ningún contenido coincida. Va **antes** del
`git am`, para que la suite pase en la primera corrida.

**Y además están en `.gitignore`** (18-oct-2026). Que no estén versionados hoy
no impedía que volvieran: al regenerarlos aparecían como «sin seguimiento» —se
vio en su `git status`— y un `git add .` los habría metido otra vez. La entrada
va **después** de `!docs/*.md`, porque en `.gitignore` gana la última regla que
coincide; puesta antes, el `.md` quedaba des-ignorado de rebote.
`test_el_plan_generado_esta_ignorado` lo vigila y se comprobó fallando en los
dos casos: sin la entrada, y con la entrada en el orden equivocado.

Regla general que queda: **ningún parche debe tocar un archivo que una
herramienta regenera.** Si uno aparece en `git format-patch --stat`, el lote
está mal armado.

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

**Hecho el 19-oct y pendiente de verlo en su Mac** (el contenedor no tiene Tk,
así que la parte de pantalla solo se verificó con un lienzo simulado): la
técnica ideal en «Técnicas» y en «Análisis en vivo», la articulación que falla
en rojo sobre el video y los ángulos contra el criterio en el reporte.

**Bloqueado por hardware:** RF-02 y RF-04 (sensores inerciales). Sebastián
tiene los IMU —**Adafruit BNO055**, 9-DOF con fusión en el propio
encapsulado—, el ESP32 y, desde el 15-oct, **cautín y estaño**; le faltan el
resto de materiales. La contingencia ya está tomada: el sistema funciona solo
con visión y declara la ausencia.

**Recomendación del 15-oct: cerrarlo como está.** Soldar es la parte corta; lo
que no cabe en lo que queda es alimentación, sujeción, canal inalámbrico,
**sincronización temporal con el video** —un problema de ingeniería por sí
solo— y validar que los datos sirvan. Un montaje a medias y sin validar abre
preguntas que no se van a poder contestar el 9 de noviembre; el capítulo, en
cambio, ya documenta una decisión de ingeniería defendible.

Consecuencia técnica del BNO055 que conviene no olvidar: entrega orientación
absoluta ya resuelta, así que **el microcontrolador no ejecuta el filtro de
fusión**. Eso deja obsoleta la prueba «Verificación algorítmica de conversión
geométrica (matemática de cuaterniones)» del plan de validación del capítulo 3.

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

- ~~**Veredicto por rodilla en posturas asimétricas**~~ **Resuelto el
  18-oct-2026**: el veredicto de Zenkutsu y Kokutsu nombra la rodilla y el
  sentido de la corrección. Ver «El veredicto de postura dice qué rodilla
  corregir».
- **Calibrar `SEPARACION_MINIMA_EN_CADERAS`** contra grabaciones reales antes de
  fijar el número en la tesis. **Desde el 19-oct la herramienta existe**:
  `comparar_2d_3d.py --esperado zenkutsu_dachi` (o `kokutsu_dachi`) imprime
  «UMBRAL DE ABSTENCION DE LA GUARDIA», un barrido de 0 a 1,5 anchos de cadera
  que cuenta por umbral los fotogramas que deciden la guardia correcta, la
  **contraria** y los que se abstienen, y la mayor separación con que se
  decidió la contraria — la cifra que acota el umbral por abajo. Antes, la
  herramienta calculaba la separación y no la informaba, así que ninguna
  grabación podía calibrarlo.

  La referencia **no sale de los pies**, que es lo que se juzga, sino de las
  rodillas: con qué guardia esos ángulos son la postura declarada. Eso tiene un
  límite que conviene decir en la tesis: solo entran los fotogramas que el
  clasificador **reconoce** con alguna de las dos guardias. Si el sesgo de 34°
  impide reconocer una guardia, sus fotogramas no aparecen en el barrido.
  No elige el umbral: lo dice. TC-AUTO-071.

**Pendiente de escritura:**

- Empaquetado: `.command` para Mac, `.exe` para Windows (lo compila él).
  **Antes, la carpeta de grabaciones**: `vision/grabacion.DIRECTORIO_POR_DEFECTO`
  es `"grabaciones"`, una ruta **relativa**, el mismo defecto que `rutas.py`
  corrigió el 30-sep para la base. Lanzado desde la carpeta del proyecto
  funciona —ahí aparecieron sus videos del 19-oct—, pero un `.command` abierto
  con doble clic arranca en la carpeta personal y un ejecutable de
  PyInstaller en una temporal: los videos irían a parar a otro lado o se
  perderían. Tiene que resolverse como la base: carpeta de datos del sistema,
  con excepción para la que ya existe junto al código.
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
