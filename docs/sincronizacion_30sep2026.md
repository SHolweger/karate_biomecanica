# Shotokan AI — estado al 30 de septiembre de 2026

Documento de sincronización entre chats. Continúa al del 29-sep. **Todo lo que
aquí se afirma está medido**; donde algo es hipótesis, lo dice.

---

## 1. Lo resuelto hoy

### 1.1 La aplicación se caía en macOS — corregido y verificado

El 28-sep se «optimizó» el bucle del análisis en vivo descontando del intervalo
el tiempo ya gastado. Subió de 18,1 a 24,2 fps. **Hubo que revertirlo**: como
el trabajo de un fotograma (~40 ms) supera el intervalo (15 ms), la resta daba
siempre el mínimo de 1 ms y el temporizador siguiente quedaba vencido casi
siempre. Dos fallos, los dos graves:

- `RecursionError` durante un análisis en vivo, con la aplicación cerrada. En
  macOS `update_idletasks()` atiende los temporizadores vencidos, y los ciclos
  de eventos anidados de Tk se acumulaban.
- La ventana dejaba de responder a los clics: con 1 ms de espera entre
  fotogramas de 40 ms, Tk recibe el 2 % del tiempo para atender al usuario.

**Verificado en el equipo de destino**: con el intervalo fijo, un análisis en
vivo sostenido no se cayó y los clics volvieron a responder. Que los dos
síntomas desaparecieran juntos es la evidencia de que la causa era una sola.

Los ~6 fps no valen una caída el 9 de noviembre.

### 1.2 Un defecto que inventaba mediciones — corregido

`analyze_tsuki` juzgaba el codo en **cada fotograma** en que el brazo se viera,
sin preguntar antes si había un golpe. Como el rango de evaluación del Tsuki es
160–175° y un brazo colgando al costado mide entre 160 y 180°, el sistema
calificaba de Tsuki a alguien de pie sin hacer nada.

Medido sobre tres segundos de brazo quieto a 175 ± 2°, **por brazo**:

| | filas de Tsuki en la base |
|---|---|
| código anterior | **90** (45 «EXCELENTE» y 45 «HIPEREXTENDIDO (Peligro)») |
| código actual | 0 |

Es el mismo tipo de fallo que el de la guardia del 28-sep: **no falla,
inventa**. Esas filas entraban con veredicto cerrado, así que contaminaban la
precisión del alumno, su gráfica de evolución y el informe de prevención de
lesiones —que cuenta hiperextensiones para advertir de bloqueo articular.

La corrección es una máquina de estados por brazo que emite **un veredicto por
golpe**, en el instante en que la extensión se detiene (la definición del Kime).
El Mae Geri nunca tuvo el problema porque ya se evaluaba así; la postura
aprendió a abstenerse el 28-sep. **El Tsuki era la única técnica que juzgaba un
estado en vez de una transición.**

Verificado en vivo y sobre grabación, contrastado contra capturas de la misma
mañana:

| Situación | Antes | Después |
|---|---|---|
| De pie, brazos abajo | «TSUKI: EXCELENTE» en ambos brazos | «SIN TSUKI: BRAZO EN REPOSO» |
| En transición, codo a 179° | «HIPEREXTENDIDO (peligro)», veredicto Incorrecto | «SIN TSUKI» |
| Zenkutsu de perfil con Tsuki real | — | «Kime correcto» a los 00:21 |

### 1.3 El aviso de grabación decía lo que no era

Es **la única pieza del sistema dedicada al consentimiento** —existe para que
nadie descubra después que lo filmaron, y en el dojo se entrena con menores— y
se resolvía una sola vez al construir la pantalla, leyendo solo el interruptor
del equipo. Tres situaciones distintas, un solo texto:

| Situación real | Anunciaba | Anuncia ahora |
|---|---|---|
| Sin alumno: ni cámara ni sesión | ● Grabando | ○ Se grabará al comenzar |
| Grabando de verdad | ● Grabando | ● Grabando |
| **El grabador renunció a mitad** | ● Grabando | ⚠ Grabación detenida |
| Apagada en el equipo | ○ Solo midiendo | ○ Solo midiendo |

El tercero es el grave: la decisión de que un fallo de grabación nunca tumbe la
sesión tiene como reverso que la sesión entera transcurre anunciando que graba,
y el instructor se entera al ir a buscar el video.

### 1.4 El protocolo de cámara, confirmado en la interfaz

Ya estaba medido; hoy se vio funcionando. El mismo video que **de frente** daba
«HEIKO DACHI» sobre un Zenkutsu, **de perfil** da «ZENKUTSU (DER ADELANTE):
POSTURA: FIRME», con la rodilla delantera en 106° y la trasera en 168°. Y el
aviso de encuadre cambia solo al girar la toma.

| Técnica | Plano | Cámara |
|---|---|---|
| Heiko Dachi, Kiba Dachi | frontal | de frente |
| Zenkutsu, Kokutsu, Tsuki, Mae Geri | sagital | **de perfil** |

### 1.5 Base de datos limpia

El historial anterior al 30-sep lleva filas de Tsuki producidas por brazos que
no golpeaban, y **no se pueden separar fila por fila**: el código anterior no
registraba si hubo golpe. La base se **renombró, no se borró** —sigue siendo
evidencia— y la nueva vive en `~/Library/Application Support/ShotokanAI/`.

La primera sesión sobre base limpia dio **24 evaluaciones cerradas, 42 % de
precisión**. Es la primera cifra de precisión del proyecto que describe
técnicas ejecutadas y no ruido.

---

## 2. Lo que sigue abierto, con lo que se midió hoy

### 2.1 El umbral del Tsuki — decisión pendiente de datos

El criterio actual exige que el codo se abra 35° en 500 ms, lo que **equivale a
exigir 70°/s**. Sobre grabación real (2911 fotogramas):

| | P50 | P75 | P90 | P95 | P99 |
|---|---|---|---|---|---|
| codo izquierdo | 20,9 | 48,1 | 91,3 | 129,3 | **189,0** |
| codo derecho | 12,3 | 35,4 | 79,0 | 129,2 | **234,0** |

Barrido de umbrales sobre esa misma grabación:

| recorrido | 500 ms | 750 ms | 1000 ms |
|---|---|---|---|
| 20° | 12 | 15 | 17 |
| 25° | 7 | 8 | 10 |
| **35° (vigente)** | **4** | 6 | 7 |
| 40° | 4 | 4 | 5 |

**Falta el dato que decide: cuántos Tsuki hay de verdad en ese video.** Sin él,
la tabla no dice si cuatro son pocos.

Dos correcciones de honestidad que salieron de aquí:

- La justificación que se había escrito —«un Tsuki va entre 500 y 800°/s»— era
  **de literatura, nunca contrastada**, y sobre grabación real no aparece. **No
  citar esa cifra en la tesis.**
- La hipótesis de que el filtro de media móvil deprimiera la medida está
  **descartada por medición**: pierde 20 % en un golpe de 150 ms y 0 % de
  200 ms en adelante.

### 2.2 Un falso positivo confirmado

En el segundo **40,92** el sistema reportó «TSUKI: HIPEREXTENDIDO (Peligro)» a
44,2°/s durante 1382 ms. Contrastado contra el video: el ejecutante **estira el
brazo y lo sostiene unos tres segundos, sin golpear**. La abstención no cerró
el caso que motivó el módulo — lo hizo mucho más raro.

### 2.3 Tres situaciones que hoy se confunden en una

| Lo que ocurre | Lo que el sistema hace | Lo que debería |
|---|---|---|
| Se golpea con potencia | Lo juzga | ✔ |
| Se golpea flojo, pero se golpea | **Silencio** | Decirlo: es lo que hay que corregir |
| Se estira el brazo sin golpear | Silencio | ✔ |

El segundo es el problema: un Tsuki lento es **una ejecución mejorable, no la
ausencia de ejecución**, y callarse es lo contrario de lo que un sistema de
corrección técnica debe hacer.

**El sistema no mide potencia** y conviene decirlo así: la cámara da píxeles, no
newtons. Mide velocidad angular del codo, que se relaciona con la potencia pero
no es ella.

La salida que se perfila, sin decidir: **un segundo umbral por debajo del
actual**, de modo que entre los dos el golpe se reconozca y se informe como
lento. Convierte un umbral en una banda y necesita las dos cifras medidas.

### 2.4 Sin cambios desde el 29-sep

- **Asimetría de la guardia**: los Zenkutsu reconocidos salen casi todos con la
  derecha adelante. Las tres explicaciones obvias están descartadas por
  medición. Hace falta una **grabación de control**: la misma guardia filmada de
  perfil desde ambos costados, ~15 s cada una. **Bloquea la campaña del dojo.**
- **Rangos de Kokutsu Dachi**: pendientes del sensei.
- **Consentimiento** para grabar a menores: trámite fuera del código.
- **IMU (RF-02, RF-04)**: bloqueado por falta de cautín. Contingencia tomada.

---

## 3. Pruebas y plan — lo nuevo para aseguramiento de la calidad

| | |
|---|---|
| Suite completa (con pantalla y cámara) | **820** passed |
| Suite sin entorno gráfico | **677** passed, 10 omitidas |
| Casos formales documentados | **62** |
| Módulos de prueba | 47 |

Reparto de los 62 casos formales:

| Tipo | Casos | | Prioridad | Casos |
|---|---|---|---|---|
| Unitaria | 29 | | Alta | 47 |
| Integración | 20 | | Media | 15 |
| Interfaz (E2E) | 13 | | | |

**13 de los 62 requieren pantalla y cámara**, así que no se pueden planificar en
integración continua: necesitan sesión presencial.

### El plan se genera, no se escribe

`plan_de_pruebas.py` produce dos archivos desde las fichas declaradas junto a
cada prueba:

- `docs/plan_de_pruebas.csv` — abre en Excel o Project. Una fila por caso, con
  ID, nombre, tipo, prioridad, componente, requisito, entorno, **comando de
  ejecución**, resultado esperado y el riesgo que cubre. Las columnas de fecha,
  responsable y resultado **salen vacías**: rellenarlas convertiría el plan en
  el registro de unas pruebas que nadie ejecutó.
- `docs/plan_de_pruebas.md` — el catálogo legible, con los pasos y aserciones de
  cada caso.

Lee el **árbol sintáctico** en vez de importar los módulos, y esa decisión es la
que lo hace servir: los módulos de interfaz se omiten solos sin entorno gráfico,
de modo que un plan generado importándolos saldría sin los 13 casos que
justamente hay que ejecutar a mano.

---

## 4. Para quien redacte

El argumento del capítulo de validación se refuerza hoy con dos casos más, y el
patrón es el mismo de siempre: **ninguno de los defectos importantes lo
encontraron las pruebas automatizadas.** Los encontró ejecutar el sistema con
material real y mirar la pantalla.

Y hay un segundo patrón, que conviene escribir porque es igual de instructivo:
**tres errores seguidos en la propia herramienta de medición**, los tres
encontrados al ejecutarla y no al leerla, y los tres en la única cifra para la
que existía. Informaba 411°/s sobre un golpe de 616; al corregirlo, 205; y
medía el arranque dentro de la ventana de detección, que dura lo que necesita
detectar y no lo que dura el golpe. Una herramienta de medición sin contrastar
es una opinión con decimales.
