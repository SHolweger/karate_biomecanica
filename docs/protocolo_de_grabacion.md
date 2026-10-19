# Protocolo de grabación — Shotokan AI

**Versión del 19-oct-2026. Sustituye a la anterior.**

Qué se graba, cómo se ejecuta cada técnica para que la toma sea medible y con
qué comando se analiza cada video. Todas las cifras citadas están **medidas
sobre grabaciones reales**; la fuente de cada una está en `CLAUDE.md`.

Un principio antes de empezar: **ejecuta cada técnica como se enseña en clase.**
Lo que este documento explica es qué mira el sistema, para que la toma se pueda
medir, no cómo adaptar la técnica al sistema. Si una técnica bien ejecutada no
se reconoce, eso no es una toma fallida: es un resultado, y hay que conservarlo.

---

## Qué cambió respecto a la versión anterior

- **Grabación de control: cuatro tomas en vez de dos.** Las dos guardias, cada
  una desde los dos costados. Con dos tomas solo se podía responder la mitad de
  la pregunta.
- **El Tsuki se ejecuta con el brazo cercano a la cámara.** El codo del brazo
  lejano se perdió en el **33 %** de los fotogramas de la grabación del 30-sep.
- **Nuevo: video de rendimiento** para la cifra exacta del RF-01, en el mismo
  formato que la medición del 27-sep, para que la comparación sea limpia.
- **Nuevo: tomas con errores a propósito**, para comprobar que las correcciones
  del 18-oct llegan traducidas al panel y al reporte.
- **Sostener el Tsuki ya no borra el veredicto** (desde el 18-oct). La versión
  anterior decía lo contrario.
- **Cada video trae su comando de análisis**, listo para copiar.

---

## 1. La lista de hoy

Todos los archivos van en **`~/Movies/shotokan_18oct/`** con estos nombres
exactos (la carpeta conserva el nombre que ya usan los comandos anteriores).

| Prioridad | Archivo | Qué es | Cámara |
|---|---|---|---|
| **1** | `zen_der_desde_izq.mp4` | Control: Zenkutsu, derecha adelante | perfil, ve tu costado izquierdo |
| **1** | `zen_der_desde_der.mp4` | Control: Zenkutsu, derecha adelante | perfil, ve tu costado derecho |
| **1** | `zen_izq_desde_izq.mp4` | Control: Zenkutsu, izquierda adelante | perfil, ve tu costado izquierdo |
| **1** | `zen_izq_desde_der.mp4` | Control: Zenkutsu, izquierda adelante | perfil, ve tu costado derecho |
| 2 | `tsuki_rapido_5.mp4` | 5 Tsuki a velocidad de combate | perfil |
| 2 | `tsuki_lento_5.mp4` | 5 Tsuki deliberadamente lentos | perfil |
| 2 | `rendimiento.mp4` | Práctica continua, ≥ 60 s, **vertical** | perfil |
| 3 | `tec_heiko.mp4` | Heiko Dachi | **de frente** |
| 3 | `tec_kiba.mp4` | Kiba Dachi, 5 repeticiones | **de frente** |
| 3 | `tec_kokutsu.mp4` | Kokutsu Dachi, 5 repeticiones | perfil |
| 3 | `tec_mae_geri.mp4` | Mae Geri, 5 patadas | perfil |
| 4 | `err_zen_alto.mp4` | Zenkutsu alto, a propósito | perfil |
| 4 | `err_zen_trasera.mp4` | Zenkutsu con la rodilla trasera doblada | perfil |
| 4 | `err_kiba_alto.mp4` | Kiba Dachi alto, a propósito | **de frente** |
| 4 | `err_tsuki_corto.mp4` | Tsuki que no termina de extender | perfil |
| 4 | `err_mae_geri_sin_recoger.mp4` | Mae Geri sin Hikiashi | perfil |

**La prioridad 1 es la única que bloquea algo**: hasta saber de dónde sale el
sesgo de 34°, la campaña del dojo no puede empezar. Si solo hay tiempo para un
bloque, es ese.

El Zenkutsu Dachi no tiene archivo propio en la prioridad 3 porque ya queda
grabado, con las dos guardias, en las cuatro tomas de control.

Tiempo estimado: unos 15 minutos de preparación y entre 45 y 60 minutos de
grabación. Cada toma dura menos de un minuto.

---

## 2. Preparación, una sola vez

### El teléfono

- **Cámara trasera** si alguien te ayuda a grabar.
- Si te grabas solo con la **frontal**, desactiva el espejo:
  *Ajustes → Cámara → Reflejar cámara frontal → apagado*. Un video espejado
  **intercambia izquierda y derecha**, y la grabación de control depende
  justamente de saber qué pierna es cuál. Una toma espejada no sirve para eso.
- Formato: **1080p a 60 fps**. No 4K: está medido que más resolución no mejora
  el análisis —el modelo reescala el fotograma a su tamaño interno— y solo
  encarece la captura. Los 60 fps sí ayudan: el Tsuki y la Mae Geri se miden
  con ±17 ms de resolución en vez de ±33.
- Orientación **horizontal** para las técnicas de perfil: cabe el paso del
  Zenkutsu y la extensión de la patada sin salirte de cuadro.
  **Excepción: el video de rendimiento va vertical**, igual que el del 27-sep
  (1080×1920 a 60 fps), para que su cifra se compare con la Tabla 5.5 sin que la
  resolución sea otra variable.

### El lugar

- **Trípode** o apoyo firme. Nada sostenido en la mano.
- **Altura de la cadera** (unos 90 cm), no del pecho ni del suelo.
- **Unos 3 metros** de distancia. Cuerpo completo con margen: un palmo sobre la
  cabeza, los pies enteros y espacio a los lados para el paso y la patada.
- **Marca el suelo con cinta**: una marca donde van los pies en Heiko Dachi y
  otra donde cae el pie delantero en el Zenkutsu. Así todas las repeticiones
  salen en el mismo sitio y a la misma distancia de la cámara.
- **Luz de frente o de lado, nunca detrás de ti.** Una ventana o una lámpara a
  tu espalda convierte el cuerpo en silueta.
- Fondo liso y, si se puede, que contraste con la ropa.
- **La misma ropa en las cuatro tomas de control.**
- **Nadie más en cuadro.** El sistema analiza a una sola persona.
- Ponte **de perfil o de frente, nunca de espaldas**: de espaldas, el sistema
  confunde el frente con el dorso y la guardia sale al revés.

### Cómo empieza y termina cada toma

1. Pulsa grabar.
2. Colócate en la marca y **di en voz alta el nombre de la toma**. Es el
   respaldo de la etiqueta si un archivo se renombra mal.
3. Quédate **3 segundos quieto en Heiko Dachi**. El análisis descarta los
   primeros 3 s (`--desde 3`), que es el tramo en que caminas a tu sitio.
4. Ejecuta las repeticiones.
5. Termina con 2 segundos quieto y corta.

### De la cámara a la Mac

- Pasa los videos por **AirDrop**, que conserva la calidad original.
- **Renómbralos exactamente** como en la tabla de la sección 1 y déjalos en
  `~/Movies/shotokan_18oct/`.
- Si el teléfono guarda `.mov` en vez de `.mp4`, sirve igual: cambia la
  extensión en los comandos.

### Comprueba la primera toma antes de grabar las demás

Graba la primera toma de control, pásala a la Mac y corre:

```
python3 diagnostico_video.py ~/Movies/shotokan_18oct/zen_der_desde_izq.mp4
```

Mira dos líneas del informe. «Con pose detectada» debe acercarse al **98 %**,
que es lo que da un buen encuadre. Y en la tabla de articulaciones (codos y
rodillas), las rodillas deben quedar casi siempre «Sobre 0,65», con una
visibilidad media entre **0,95 y 0,98**. El codo del lado lejano puede salir
más bajo, porque el Hikite lo tapa: es esperable. Al final debería decir «Las
cuatro articulaciones que el sistema evalúa se ven con holgura» o, como mucho,
nombrar ese codo. Si sale muy por debajo, corrige el
encuadre o la luz **antes** de grabar el resto: es mucho más barato que
repetir quince tomas.

---

## 3. La regla de planos

El sistema mide ángulos sobre la imagen, en **dos dimensiones**. Si el plano en
que ocurre la técnica no es perpendicular a la cámara, el ángulo que ve no es
el real, y la proyección **arrastra todo ángulo hacia 90°**:

| giro de la cámara | rodilla real 120° | rodilla real 160° | codo real 175° |
|---|---|---|---|
| 0° (perpendicular) | 120,0 | 160,0 | 175,0 |
| 45° | 112,2 | 152,8 | 172,9 |
| 75° | 98,5 | 125,4 | 161,3 |
| **90°** | **90,0** | **90,0** | **90,0** |

Medido sobre 3190 fotogramas de Zenkutsu Dachi: **0,0 %** reconocido de
frente, 8,8 % a 45° y 37,2 % de perfil. De frente, el sistema es ciego a esa
postura.

| Técnica | Plano del gesto | Dónde va la cámara |
|---|---|---|
| Heiko Dachi, Kiba Dachi | frontal | **de frente** |
| Zenkutsu Dachi, Kokutsu Dachi, Tsuki, Mae Geri | sagital | **de perfil** |

«De perfil» significa que la cámara mira tu costado: la línea de tus hombros
apunta hacia ella. La pantalla en vivo lo indica sola con «Cámara de perfil» o
«Cámara de frente».

---

## 4. Prioridad 1 — Grabación de control

### Para qué

En la grabación del 29-sep, de perfil, la rodilla delantera midió **34° más
estirada** con una guardia que con la otra (141° contra 107° de mediana). Las
explicaciones obvias ya están descartadas por medición: la guardia se deduce
bien, no es el ángulo de cámara y no es la pierna que queda oculta. Queda una
pregunta que esa grabación no puede contestar, porque la cámara estuvo casi
siempre del mismo costado: **¿el error sigue a la pierna, o sigue a la
cercanía con la cámara?**

Las cuatro tomas lo separan, porque cruzan las dos cosas:

| Archivo | Pierna adelante | La cámara ve tu costado… | Pierna delantera respecto a la cámara |
|---|---|---|---|
| `zen_der_desde_izq.mp4` | derecha | izquierdo | **lejana** |
| `zen_der_desde_der.mp4` | derecha | derecho | **cercana** |
| `zen_izq_desde_izq.mp4` | izquierda | izquierdo | **cercana** |
| `zen_izq_desde_der.mp4` | izquierda | derecho | **lejana** |

- Si los 34° aparecen con la **misma pierna** desde los dos costados, es un
  **sesgo de pierna**, y la mitad de los alumnos se mediría mal según su
  guardia.
- Si aparecen con la **pierna lejana** sea cual sea, es un **efecto de la
  cámara**, y se resuelve con protocolo (filmar desde el costado de la pierna
  delantera).
- Si **no aparecen** en ninguna, el sesgo era de aquella grabación.

Las mismas tomas sirven además para **fijar el umbral de separación de
caderas**: la herramienta cuenta, para cada umbral posible, cuántos fotogramas
deciden la guardia correcta, cuántos la contraria y cuántos se abstienen.

### Cómo se ejecuta el Zenkutsu Dachi

- **Largo**: unos dos anchos de hombros entre los pies, de adelante hacia
  atrás. **Ancho**: más o menos un ancho de cadera de lado a lado.
- **Rodilla delantera** flexionada sobre el pie, con la espinilla casi
  vertical: la rodilla queda por encima de los dedos, no más adelante.
- **Pierna trasera** estirada y firme, con el talón en el suelo y el pie
  girado unos 45° hacia afuera.
- Peso **más adelante que atrás** (alrededor de 60/40), cadera baja y tronco
  erguido. Brazos en Gedan Barai o en la cadera, **igual en las cuatro tomas**.

Qué mira el sistema: reconoce el Zenkutsu cuando la rodilla delantera baja de
**130°** y la trasera supera los **150°**, y lo juzga correcto con la
delantera entre **90° y 115°** y la trasera entre **165° y 180°**.

### Cómo se graba cada toma

1. Heiko Dachi en tu marca, **de perfil a la cámara**.
2. Avanza un paso a Zenkutsu Dachi **con la pierna que indica el archivo**,
   cayendo en la segunda marca.
3. Sostén la postura **4 segundos**, quieto, mirando al frente.
4. Vuelve a Heiko Dachi sobre la primera marca y espera 2 segundos.
5. **Cinco repeticiones.** Siempre con la misma pierna adelante: **nunca
   alternes** dentro de un archivo.

Unos 40 segundos por toma.

**Para cambiar de costado, no muevas la cámara: gira tú 180°.** Así la altura,
la distancia y el encuadre son idénticos en las cuatro tomas, y lo único que
cambia es lo que la comparación necesita que cambie.

### Cómo se analiza

```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/zen_der_desde_izq.mp4 --esperado zenkutsu_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/zen_der_desde_izq.txt
```
```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/zen_der_desde_der.mp4 --esperado zenkutsu_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/zen_der_desde_der.txt
```
```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/zen_izq_desde_izq.mp4 --esperado zenkutsu_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/zen_izq_desde_izq.txt
```
```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/zen_izq_desde_der.mp4 --esperado zenkutsu_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/zen_izq_desde_der.txt
```

La tabla «UMBRAL DE ABSTENCION DE LA GUARDIA» solo aparece después de aplicar
el parche `separacion19oct`. Sin él, la herramienta corre igual, pero esa
sección no sale.

Cada informe dice qué guardia leyó el sistema. Como el archivo dice qué
pierna adelantaste tú, compararlos responde también una pregunta que quedó
abierta en el código: si el «IZQ» del sistema es tu pierna izquierda.

---

## 5. Prioridad 2 — Tsuki rápido y Tsuki lento

### Para qué

Hoy el sistema exige que el codo se abra **35° en medio segundo** (unos
70°/s) para reconocer un golpe. Por debajo, **calla**. Y callar ante un Tsuki
lento es lo contrario de lo que debe hacer un sistema de corrección: un golpe
flojo es una ejecución mejorable, no la ausencia de una ejecución. Además,
`riesgos.py` recomienda «trabajar el Tsuki a velocidad media frente al
espejo», así que hoy recomienda una práctica que después no mide.

Con un video rápido y uno lento, **sabiendo que en cada uno hay exactamente
cinco golpes**, se pueden fijar dos cifras en vez de una: por encima de la
alta, el golpe se juzga; entre las dos, se reconoce y se informa como lento;
por debajo de la baja, no hay golpe.

### Cómo se ejecuta

- **De perfil**, en Heiko Dachi sobre tu marca.
- **Golpea con el brazo cercano a la cámara.** El lejano queda tapado por tu
  propio cuerpo y el sistema lo pierde.
- Sale del **Hikite**: puño en la cadera, palma hacia arriba y codo atrás.
- Golpe **Chudan**, a la altura del plexo, girando el puño al final.
- Extiende hasta que el brazo quede recto, **sin bloquear el codo**.
- Regresa al Hikite enseguida y **espera 2 segundos** antes del siguiente.
  La pausa es lo que permite contar los golpes uno por uno.
- **Exactamente cinco golpes.** Cuéntalos en voz alta.
- **No sostengas el brazo extendido.** Estirarlo y dejarlo ahí, sin golpear, es
  justamente el falso positivo confirmado del 30-sep.

| Archivo | Velocidad |
|---|---|
| `tsuki_rapido_5.mp4` | **de combate**, con Kime |
| `tsuki_lento_5.mp4` | deliberadamente lenta: **unos 2 segundos** para el recorrido completo, **sin detenerte a mitad**, como frente al espejo |

### Cómo se analiza

```
python3 revisar_tsuki.py ~/Movies/shotokan_18oct/tsuki_rapido_5.mp4 --golpes 5 2>&1 | tee ~/Movies/shotokan_18oct/tsuki_rapido_5.txt
```
```
python3 revisar_tsuki.py ~/Movies/shotokan_18oct/tsuki_lento_5.mp4 --golpes 5 2>&1 | tee ~/Movies/shotokan_18oct/tsuki_lento_5.txt
```

Qué esperar: en el rápido, cerca de cinco golpes reconocidos. En el lento,
probablemente ninguno o casi ninguno con el criterio vigente, y eso es lo que
se quiere medir. La tabla de barrido muestra con qué recorrido y qué ventana
empiezan a aparecer los cinco, y de ahí sale la cifra baja.

---

## 6. Prioridad 2 — Video de rendimiento (RF-01)

### Para qué

La cifra que va a la tesis es la **cadencia sostenida de la interfaz**, medida
entre el inicio de un fotograma y el del siguiente, no el tiempo de cómputo. La
corrida del 27-sep (24,2 fps) tenía una espera del bucle que después se
revirtió; con la espera fija de hoy, la proyección es de unos 20 fps. Este
video da la cifra exacta.

### Cómo se graba

- **Vertical, 1080×1920 a 60 fps**, como el del 27-sep.
- **Al menos 60 segundos**, de perfil, practicando sin parar: Zenkutsu,
  Tsuki, vuelta a Heiko. El contenido no se juzga; lo que importa es que haya
  **una persona en cuadro todo el tiempo**, porque el costo del análisis
  depende de que se detecte una pose.
- **Empieza ya colocado.** Medir desde el fotograma cero de un video casero
  describe a alguien caminando hacia su sitio.

### Cómo se mide

Antes de correrlo: Mac **conectada a la corriente**, **sin modo de bajo
consumo** y con las demás aplicaciones cerradas.

```
python3 test_rendimiento_interfaz.py ~/Movies/shotokan_18oct/rendimiento.mp4 900 2>&1 | tee ~/Movies/shotokan_18oct/rendimiento.txt
```

Son 900 fotogramas, unos 45 segundos de medición, en vez de los 300 de la vez
anterior, que eran apenas 15 s. La cifra que importa es la línea
**«Sostenida (media)»**. La del «Techo por cómputo» **no** es la tasa
sostenida: lo dice la propia consola. La herramienta deja además un CSV
nuevo en `evidencias/` con la columna `intervalo_ms`; ese archivo es la
evidencia.

**Opcional, para el capítulo 6 (sesión prolongada):** graba al menos 4
minutos de práctica continua y mide 10 000 fotogramas, unos 8 minutos de
análisis. Sirve para ver si vuelve el aumento de picos que apareció después del
quinto minuto en la corrida del 27-sep. Se puede dejar para el dojo.

```
python3 test_rendimiento_interfaz.py ~/Movies/shotokan_18oct/sesion_larga.mp4 10000 2>&1 | tee ~/Movies/shotokan_18oct/sesion_larga.txt
```

---

## 7. Prioridad 3 — Las técnicas, una por una

Un archivo por técnica. Entre repeticiones, vuelve siempre a Heiko Dachi: el
sistema escribe una evaluación cada vez que el diagnóstico cambia, y diez
repeticiones encadenadas sin pausa pueden quedar registradas como una sola.

### Heiko Dachi — `tec_heiko.mp4` — de frente

- Pies separados al **ancho de la cadera**, paralelos y apuntando al frente.
- Rodillas **estiradas sin bloquear**, peso repartido en las dos piernas.
- Tronco erguido, brazos relajados.

Grabación: **tres tandas de 10 segundos** quieto, sacudiendo las piernas entre
una y otra.

Qué mira el sistema: reconoce Heiko Dachi cuando **las dos rodillas superan
160°**, y lo juzga correcto entre **165° y 180°**.

```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/tec_heiko.mp4 --esperado heiko_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/tec_heiko.txt
```

### Kiba Dachi — `tec_kiba.mp4` — de frente

- Pies separados unos **dos anchos de hombros**, paralelos.
- Rodillas flexionadas y **empujadas hacia afuera**, por encima de los pies,
  sin que se metan hacia adentro.
- Cadera baja, tronco erguido, peso **repartido por igual** en las dos piernas.

Grabación: **cinco repeticiones**. Desde Heiko Dachi, paso lateral a Kiba
Dachi, sostener **4 segundos** y volver.

Qué mira el sistema: reconoce el Kiba Dachi con **las dos rodillas entre 130° y
160°**, y lo juzga correcto entre **130° y 150°**.

```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/tec_kiba.mp4 --esperado kiba_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/tec_kiba.txt
```

### Kokutsu Dachi — `tec_kokutsu.mp4` — de perfil

**Este video también es para el sensei.** Los rangos de Kokutsu que usa el
sistema (delantera 145–175°, trasera 90–120°) los deduje del principio
biomecánico, **no salen del dojo**. Mostrarle este video con los ángulos que
mide el sistema es la forma más directa de que los confirme o los corrija.

- **Pierna derecha adelante, con la cámara viendo tu costado izquierdo**: la
  misma combinación que `zen_der_desde_izq`.
- Peso **cargado atrás**, alrededor de 70/30.
- **Rodilla trasera** muy flexionada y abierta hacia afuera, con el pie
  trasero girado unos 90° respecto de la línea de la postura.
- **Pierna delantera** casi estirada, con la rodilla apenas flexionada y el
  pie apuntando al frente.
- Talones sobre una misma línea, cadera de medio lado (Hanmi) y tronco erguido.

Grabación: **cinco repeticiones**. Desde Heiko Dachi, paso a Kokutsu Dachi,
sostener **4 segundos** y volver.

Qué mira el sistema: reconoce el Kokutsu cuando la rodilla delantera mide **al
menos 140°** y la trasera **no más de 135°**, y lo juzga correcto con la
delantera entre **145° y 175°** y la trasera entre **90° y 120°**
(provisionales).

```
python3 comparar_2d_3d.py ~/Movies/shotokan_18oct/tec_kokutsu.mp4 --esperado kokutsu_dachi --desde 3 2>&1 | tee ~/Movies/shotokan_18oct/tec_kokutsu.txt
```

### Mae Geri — `tec_mae_geri.mp4` — de perfil

- **Zenkutsu Dachi con la derecha adelante y la cámara viendo tu costado
  izquierdo.** Patea con la **pierna izquierda**, la de atrás, que es la
  cercana a la cámara.
- **Carga**: lleva la rodilla al frente, a la altura de la cadera o más, con el
  **talón recogido junto al glúteo**.
- **Extensión**: golpea con la base de los dedos extendiendo la rodilla **de un
  solo tirón**, sin pausa entre la carga y el golpe.
- **Hikiashi**: recoge la pierna **doblando la rodilla antes de bajar el pie**.
- Apoya el pie de vuelta atrás, en la misma postura.
- **Cinco patadas**, con **3 segundos** de pausa entre una y otra.

Qué mira el sistema, en este orden:

1. Que la rodilla **baje de 75°** al cargar. Una carga poco recogida no inicia
   la técnica.
2. Que se **abra por encima de 160°** (Kime) y con una velocidad pico de
   **400°/s** o más. Por debajo de 160° informa «Kime incompleto»; abierta
   pero lenta, «falta explosividad».
3. Que **vuelva a bajar de 75° con el pie todavía en el aire** (Hikiashi).
4. Si te quedas **más de 4 s cargando** o **más de 3 s con la pierna
   extendida**, descarta el intento sin decir nada. No te detengas a mirar la
   pantalla a mitad de la patada.

No hay una herramienta de consola para la Mae Geri: se analiza en la interfaz,
con la sesión de prueba de la sección 9.

---

## 8. Prioridad 4 — Errores a propósito

### Para qué

El 18-oct cambiaron las correcciones: ahora dicen qué rodilla corregir y hacia
dónde, y llegan traducidas al panel y al reporte. Hasta ese día, **ninguna
postura llegaba traducida**. Estas tomas comprueban el recorrido entero con
MediaPipe real, que las pruebas automatizadas no cubren.

Cinco repeticiones por archivo, igual que las técnicas correctas: desde Heiko
Dachi, entrar, sostener 4 s y volver.

| Archivo | Cámara | Qué haces | Lo que debe decir el panel |
|---|---|---|---|
| `err_zen_alto.mp4` | perfil | Zenkutsu con la rodilla delantera **menos flexionada** de lo correcto: algo alto, pero no de pie | «Flexiona más la rodilla de adelante» |
| `err_zen_trasera.mp4` | perfil | Zenkutsu con la delantera bien y la **rodilla trasera doblada** | «Estira la pierna de atrás» |
| `err_kiba_alto.mp4` | de frente | Kiba Dachi **más alto** de lo correcto | «Baja más la postura» |
| `err_tsuki_corto.mp4` | perfil | Tsuki a velocidad normal que **no termina de extender**: el codo se queda en unos 140–150° | «Extiende más el brazo» |
| `err_mae_geri_sin_recoger.mp4` | perfil | Mae Geri que **baja la pierna estirada**, sin recoger | **Nada**: ver abajo |

Dos cosas que conviene saber antes de grabarlas:

- **Si exageras el error, la postura deja de reconocerse.** Un Zenkutsu
  demasiado alto o con la trasera muy doblada sale como «EN TRANSICION», y un
  Kiba casi de pie, como Heiko Dachi. No es un fallo de la toma: es otro
  resultado, y se anota igual.
- **La Mae Geri sin Hikiashi no recibe veredicto.** Según el código —y lo
  comprobé simulándolo—, si la pierna baja estirada la rodilla nunca vuelve a
  doblarse por debajo de 75°, la máquina espera 3 segundos y **descarta el
  intento en silencio**. El aviso «Recoge la pierna antes de bajarla» solo
  aparece si la recoges tarde, no si no la recoges. Es el mismo tipo de
  silencio que el del Tsuki lento. Esta toma lo confirma con video real, y si
  se confirma, va a la tesis como limitación.

**Por seguridad, no grabes hiperextensiones a propósito**, ni de codo ni de
rodilla. El «No bloquees el codo» ya está cubierto por las pruebas
automatizadas y no vale una lesión.

---

## 9. Sesión de prueba en la interfaz

Para la Mae Geri, para los errores a propósito y para ver los mensajes tal como
los verá el sensei. Se usa una **base de datos aparte**, para no mezclar estas
pruebas con nada:

```
SHOTOKAN_BD=~/Movies/shotokan_18oct/pruebas_19oct.db python3 main.py
```

1. La base nace vacía: crea una cuenta de entrenador de prueba.
2. En «Alumnos y progreso», registra un alumno llamado **Prueba**.
3. En «Cámara y fuente de video», elige **«Video grabado»**, pulsa
   **«Elegir archivo…»**, selecciona el video y confirma con **«Usar esta
   cámara»**.
4. En «Análisis en vivo», elige al alumno **Prueba**. El video empieza a
   analizarse.
5. Mira el panel de correcciones mientras corre. Al terminar el video aparece
   «■ La grabación terminó»: es el final normal, no un fallo.
6. Pulsa «Terminar sesión». Abre el reporte con **«Alumnos y progreso» →
   «Ver perfil» → «Ver reporte»**.
7. **Captura de pantalla** del panel y del reporte.

Repite los pasos 3 a 7 con cada archivo: `tec_mae_geri` y los cinco `err_`.

---

## 10. Pruebas en vivo, frente a la cámara

Cinco minutos, sin grabar archivos. Comprueban los cambios del 18-oct con
MediaPipe real. Usa la misma base de prueba de la sección 9, con la cámara del
equipo como fuente.

| Qué haces | Lo que debe pasar |
|---|---|
| Un Tsuki y **sostienes el brazo extendido** 3 s | El veredicto **se queda a la vista** mientras sostienes; antes desaparecía a los 0,5 s |
| Kiba Dachi alto, de frente | «Baja más la postura» |
| Zenkutsu de perfil con la rodilla delantera algo recta | «Flexiona más la rodilla de adelante» |
| Terminar la sesión y abrir el reporte | Las correcciones de postura aparecen **como instrucción**, no como «POSTURA: …» |

---

## 11. Qué me mandas

- Los **`.txt`** de `~/Movies/shotokan_18oct/`: los cuatro de control, los dos
  de Tsuki, el de rendimiento y los que hayas corrido de la sección 7.
- El **CSV nuevo** de `evidencias/` que dejó la medición de rendimiento.
- Las **capturas** de la sección 9 y de la 10.
- Cualquier cosa rara que hayas visto en pantalla mientras grababas.

Los videos **no hace falta mandarlos**: con los `.txt` alcanza. Guárdalos, eso
sí: son la evidencia y permiten repetir cualquier análisis con otra versión del
sistema.

---

## Cómo NO grabar

| ❌ | Por qué |
|---|---|
| Filmar Zenkutsu, Kokutsu, Tsuki o Mae Geri **de frente** | 0,0 % de reconocimiento. Medido. |
| Quedarte **a 45°** | Es la peor zona: 8,8 %. |
| Usar la cámara frontal **con el espejo activado** | Intercambia izquierda y derecha y anula la grabación de control. |
| **Alternar la guardia** dentro de una toma de control | La toma deja de separar pierna de cercanía. |
| Golpear con el **brazo lejano** a la cámara | El codo lejano se perdió en el 33 % de los fotogramas. |
| **Pausar a mitad de una Mae Geri** para mirar la pantalla | Más de 4 s cargando o 3 s extendido y el intento se descarta. |
| **Estirar el brazo y sostenerlo sin golpear** | Es el falso positivo confirmado del 30-sep. |
| Grabar a **máxima resolución** creyendo que mejora | No mejora nada y encarece la captura. |
| Pulsar grabar y **después caminar** al sitio sin la pausa de 3 s | Esos segundos contaminan la medición. |
| Ponerte **de espaldas** a la cámara | El eje adelante-atrás se invierte y la guardia sale al revés. |
| **Cortar pies o cabeza** del encuadre | Sin tobillos no hay ángulo de rodilla ni guardia. |
| Dejar **otra persona** en cuadro | El modelo está configurado para un solo cuerpo. |
| Fiarte de la **puntuación de visibilidad** | **No delata el error.** La pierna peor medida marcó 0,958: el modelo infiere las articulaciones ocultas sin bajar esa cifra. |

---

## Límites del sistema — qué NO hace, y conviene decirlo en la tesis

**No mide potencia ni fuerza.** La cámara entrega píxeles, no newtons. Mide la
**velocidad angular del codo y de la rodilla**, que se relaciona con la potencia
pero no es ella.

**No reconoce la técnica por su forma.** Para el sistema, un Tsuki es «una
extensión rápida del codo». No distingue un Gyaku Zuki de un Kizami Zuki ni de
un estiramiento enérgico.

**Es bidimensional, y se decidió con datos.** El 3D da 2,8 puntos más en
Zenkutsu, pero lee las rodillas **15,3° más flexionadas** de mediana y
convierte en Kiba Dachi un tercio de los fotogramas en que simplemente estás de
pie.

**Calla en dos casos donde debería corregir**: el Tsuki lento (por debajo de
unos 70°/s) y, según el código, la Mae Geri sin Hikiashi. Los dos son
ejecuciones mejorables, no ausencias de ejecución. El primero está abierto y
este protocolo trae los datos para cerrarlo; el segundo, para confirmarlo.

**No muestra lo que no mide.** Sin evaluaciones cerradas la precisión aparece
como un guion, nunca como 0 %. Los sensores inerciales se declaran ausentes, no
en cero.

## Cómo NO usar el sistema en el dojo

- **No como juez absoluto.** Los rangos de Kokutsu Dachi siguen pendientes de
  que el sensei los confirme.
- **No comparar alumnos filmados con encuadres distintos.** Dos personas
  filmadas en planos diferentes no son comparables, aunque el número se vea
  igual.
- **No grabar a menores sin consentimiento firmado.** La grabación se puede
  apagar por equipo, pero el permiso es un trámite fuera del código.
- **No leer el historial anterior al 30 de septiembre** para calcular
  precisión: contiene filas de Tsuki producidas por brazos que no golpeaban.
