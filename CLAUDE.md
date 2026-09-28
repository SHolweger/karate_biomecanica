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

**Lo que esto NO arregla:** si la toma es frontal y MediaPipe estima la
profundidad con el signo cambiado de forma sostenida, la proyección saldrá
grande y con el sentido incorrecto. El remedio de ese caso es de protocolo, no
numérico. Ver el punto siguiente.

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

`guardia.orientacion_frente_a_camara()` mide esto (0 = de perfil, 1 = de
frente) y está listo para el aviso de encuadre; **todavía no está conectado a
la interfaz**.

**MediaPipe ya calcula coordenadas 3D y se están descartando** (28-sep-2026).
`vision/tracker.py` devuelve el resultado completo, pero `live_screen.py` y
`main.py` usan solo `result.pose_landmarks`. `result.pose_world_landmarks`
—coordenadas en metros relativas al centro de las caderas— sale del mismo paso
de inferencia, así que su coste ya está pagado. Calcular los ángulos ahí
atacaría a la vez la guardia y el arrastre hacia 90°. **No está comprobado que
funcione mejor**: la Z de un modelo monocular es estimada. Hay que medirlo
contra las grabaciones antes de afirmarlo.

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

**Dos fugas de rendimiento de la interfaz, medidas y corregidas**
(28-sep-2026). La medición sobre la interfaz real en la Mac dio 18,1 fps, pero
las etapas sumaban 39,8 ms —25 fps—. Los 15,3 ms de diferencia eran exactamente
`INTERVALO_MS`:

1. **El bucle sumaba el intervalo al trabajo en vez de solaparlo.** Se
   reprogramaba con `after(15)` *después* de terminar todo. Ahora descuenta lo
   gastado (`espera_hasta_el_siguiente` en `gui/panel_vivo.py`, puro y probado
   en CI). Nunca devuelve cero: sin un hueco, Tk no atiende los clics y el
   instructor no puede pulsar «Terminar sesión».
2. **Se convertían 2 MP para dibujarlos en 0,25.** `_mostrar_frame` pasaba el
   fotograma entero a `CTkImage` y dejaba que CustomTkinter lo redujera. Ahora
   se reduce con `cv2.resize` antes de convertir: medido, 20,1 ms → 5,9.

En el contenedor: **15,2 → 28,4 fps**. Proyección para la Mac: ~33 fps, que
cumpliría el RF-01 — **falta confirmarlo en su equipo**.

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
| Completo (con cámara y pantalla) | `python3 -m pytest -q` | 735 passed |
| CI / sin entorno gráfico | igual | 593 passed, 10 skipped |

El 593 está medido en el contenedor. El 735 es aritmética sobre dos cifras
medidas —720 en su Mac el 28-sep más las 15 pruebas de la guardia, que son
unitarias y de integración y corren en los dos entornos—, **pendiente de
confirmar** en su equipo.

Los módulos de `tests/e2e/` se omiten solos con `pytest.importorskip`. Por eso
toda regla de presentación que pueda expresarse sin CustomTkinter **se extrae a
un módulo puro** (`gui/panel_vivo.py`, `gui/coaching.py`,
`gui/validacion_umbrales.py`, `gui/registro_alumno.py`, `vision/fuentes.py`,
`vision/nombres_camara.py`, `vision/grabacion.py`) para que CI la verifique.

**Fichas de caso de prueba.** Los casos formales llevan `@ficha(...)` de
`tests/reporte/plantilla.py`, validado al importar. Los IDs `TC-AUTO-NNN` deben
ser únicos y correlativos — **el siguiente libre es TC-AUTO-052**. Cada módulo
de pruebas necesita al menos una ficha o `--exigir-fichas` falla.

```bash
python3 -m pytest --exigir-fichas --reporte-formal   # lo que corre CI
```

`docs/casos_prueba_automatizados.generado.md` está versionado y **solo se
reescribe en corridas completas**; una corrida parcial informa por qué no lo
actualizó, para que no borre evidencia.

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
- `zsh` **no** trata `#` como comentario en la línea interactiva: nunca mandarle
  comandos con comentarios al final.

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

- **Medir `pose_world_landmarks`** contra las grabaciones y decidir con el dato
  en la mano si los ángulos deben calcularse en 3D.
- **Conectar el aviso de plano** (`orientacion_frente_a_camara`) junto con el
  aviso de encuadre: hoy la función existe y nadie la llama.
- **Veredicto por rodilla en posturas asimétricas**: ya se informa cuál rodilla
  está fuera de su rango, pero las reglas siguen emitiendo un único veredicto de
  postura. El panel muestra ambos.
- **Calibrar `SEPARACION_MINIMA_EN_CADERAS`** contra grabaciones reales antes de
  fijar el número en la tesis.

**Pendiente de escritura:**

- Capítulo 4, sección **4.8** (manuales técnicos y guías de usuario). Conviene
  escribir primero los manuales y luego la sección que los describe.
- Empaquetado: `.command` para Mac, `.exe` para Windows (lo compila él).
- Ajustar el prototipo `.dc.html` para que no prometa «340 reglas» ni «red
  neuronal v0.9 entrenando».

**Numeración real del capítulo 4** (la de los campos de índice de Word, no la
del listado en texto plano, que está desactualizado):

| | Sección | Estado |
|---|---|---|
| 4.1 | Estructuración de la arquitectura y modularización | escrita por él |
| 4.2 | Creación de la base de conocimiento técnica | escrita por él |
| 4.3 | Codificación de las reglas del motor de inferencia | escrita por él |
| 4.4 | Elaboración de la interfaz de usuario | entregada 14-sep |
| 4.5 | Estructuración de la base de datos biomecánica | entregada 14-sep |
| 4.6 | Elaboración física de los dispositivos wearables | entregada 14-sep |
| 4.7 | Ejecución de las pruebas de validación | entregada 14-sep |
| 4.8 | Redacción de manuales técnicos y guías de usuario | **falta** |

Tablas repartidas así: **4.1–4.3** en 4.4, **4.4–4.5** en 4.5, **4.6** en 4.6,
**4.7–4.9** en 4.7. La siguiente libre es la **4.10**.

Formato de los `.docx`: Times New Roman 12, interlineado 1.5, sangría de primera
línea. Los títulos de **nivel 2 van sin número** (Word los numera solo); los de
nivel 3, con número escrito.

---

## Cómo le sirve más el trabajo

Verificar antes de afirmar. Cuando algo se rompe, reproducirlo con una prueba
antes de arreglarlo, y comprobar que esa prueba falla sin el arreglo. Las cifras
que van a la tesis se cuentan, no se recuerdan — la terna puede correr `pytest`.
Cuando me equivoco, decirlo directo y seguir.
