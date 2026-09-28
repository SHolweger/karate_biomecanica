# Bitácora de trabajo — 28 de septiembre de 2026

Shotokan AI · Sistema experto de análisis biomecánico
Sebastián Holweger — Universidad Mariano Gálvez

Este documento resume qué se avanzó hoy, qué se descubrió en la prueba en vivo
y qué queda pendiente. Está pensado para dos lectores: Sebastián, y el chat de
documentación que tiene que sincronizar el Capítulo 4.

---

## 1. Lo que se avanzó hoy

### 1.1 Rendimiento: el RF-01 quedó medido de verdad

Hasta hoy la cifra de fotogramas por segundo que iba a la tesis venía de
`test_rendimiento.py`, que mide el encadenamiento de análisis con una ventana
de OpenCV. Esa ventana es de depuración y el dojo no la usa, así que la cifra
no describía el producto.

Se construyó `test_rendimiento_interfaz.py`, que abre la pantalla de análisis
en vivo real —con conversión a imagen de CustomTkinter, refresco de métricas,
escritura en SQLite y grabación del video crudo— y cronometra ocho etapas.

**Resultado sobre 11 515 fotogramas** (grabación de 1080×1920 a 60 fps, Mac M1):

| Etapa | Media (ms) | Mediana | P95 | Máx |
|---|---|---|---|---|
| captura | 4,9 | 4,6 | 5,9 | 68,8 |
| grabacion | 2,1 | 1,7 | 3,5 | 67,1 |
| **estimacion_pose** | **19,2** | 17,8 | 24,8 | 186,6 |
| analisis | 0,1 | 0,1 | 0,2 | 5,1 |
| renderizado | 0,2 | 0,2 | 0,2 | 0,7 |
| persistencia | 0,1 | 0,0 | 0,7 | 28,2 |
| panel | 1,0 | 0,5 | 0,8 | 44,6 |
| despliegue | 8,4 | 8,3 | 8,9 | 26,3 |
| **TOTAL** | **35,9** | 33,8 | **45,4** | 222,4 |

- **RNF-01 (cómputo < 500 ms): CUMPLE.** De once mil quinientos fotogramas, el
  peor tardó 222 ms — menos de la mitad del límite. No es «cumple en la
  muestra»: no hubo un solo fotograma que rozara el límite.
- **RF-01 (≥ 30 fps): NO CUMPLE.** 24,2 fps sostenidos.

### 1.2 Dos fugas de rendimiento, encontradas midiendo y corregidas

| | Antes | Después |
|---|---|---|
| `despliegue` (convertir 2 MP para dibujar en 0,25 MP) | 20,1 ms | **8,4 ms** |
| Holgura perdida esperando (el intervalo se sumaba al trabajo) | 15,3 ms | **5,5 ms** |
| Interfaz real | 18,1 fps | **24,2 fps** |

Una hipótesis mía quedó desmentida por los datos: supuse que la grabación de
sesión era la culpable porque en el contenedor costaba 10 ms. En la Mac cuesta
**2,1 ms**. No era eso.

### 1.3 Por qué el RF-01 no va a llegar a 30 fps

`estimacion_pose` cuesta 19,2 ms y es de MediaPipe, no del código de la tesis.
Sumando solo lo imprescindible —captura 4,9 + pose 19,2 + mostrar la imagen
8,4— van 32,5 ms, que son **30,8 fps con el análisis, la grabación, la
persistencia y el panel en cero**. El techo teórico está pegado al requisito.
No hay optimización que abra ese hueco.

Dos matices que conviene llevar a la tesis:

1. Los picos **crecen en el último tercio** de la corrida (pasados los cinco
   minutos): es el M1 estrangulando por temperatura. Una clase en el dojo dura
   más de ocho minutos, así que la cifra sostenida en sesión larga estará algo
   por debajo de 24,2.
2. El video medido es de **60 fps** y se procesó fotograma por fotograma: 192 s
   de grabación en 476 s de cómputo. En vivo con una cámara a 30 fps el caso es
   otro —OpenCV entrega el fotograma más reciente y lo que importa es la
   latencia, que cumple con 10× de margen—. El 24,2 fps es el **peor escenario**:
   re-analizar una grabación completa.

**Recomendación sobre el requisito.** Bajar RF-01 a ≥ 20 fps es defendible,
pero la justificación no puede ser «no llegamos». Tiene que ser de dominio:
(a) el coste dominante es la inferencia de un modelo de terceros, medida e
independiente de la resolución; (b) un tsuki dura ~150–200 ms, y a 24 fps se
muestrea 4–5 veces frente a 5–6 a 30 fps, diferencia que no cambia ningún
veredicto porque las reglas evalúan rangos angulares, no derivadas finas;
(c) el requisito que protege la retroalimentación en vivo es RNF-01, y cumple
sobradamente. **Consultarlo con el asesor antes de reescribirlo.**

### 1.4 Un error de mi herramienta de medición

La medición pidió 300 fotogramas y procesó **11 515** (el video entero: 11 520
menos los 5 de descarte). El vigilante estaba programado con `after(200 ms)`,
pero el bucle de análisis se reprograma con `after(1 ms)` y lo dejaba sin turno:
despertó cada ~4 s en vez de cinco veces por segundo. Ocho minutos de cómputo y
el ventilador encendido. Queda por arreglar (que el límite lo aplique el propio
bucle, no un temporizador).

La muestra resultante, sin embargo, es mucho mejor que la pedida: **no hay que
repetir esa medición.**

### 1.5 Corrección de fechas

Varias entradas de `CLAUDE.md` están fechadas «29-sep-2026» cuando los commits
correspondientes son del **28-sep-2026**. Error mío al redactarlas. Importa
porque la tesis cita fechas de medición.

---

## 2. Hallazgos de la prueba en vivo — lo más importante del día

Sebastián hizo una prueba en vivo y reportó cuatro observaciones. Las cuatro
son correctas, y tres de ellas comparten una misma causa raíz. **Esto es lo más
serio que hay ahora mismo en el proyecto, por encima del rendimiento.**

### 2.1 El síntoma que lo delata todo

> «El heikodachi está perfecto. Igualmente el kibadachi frontal. Las
> dificultades fueron con el zenkutsudachi» — y el Zenkutsu se reportó como
> Kokutsu.

Eso no es casualidad. Mirando el clasificador de `expert_system/analyzer.py`:

| Postura | ¿De qué depende el reconocimiento? | ¿Funciona? |
|---|---|---|
| Heiko Dachi | solo de los dos ángulos de rodilla | ✅ |
| Kiba Dachi | solo de los dos ángulos de rodilla (es simétrica) | ✅ |
| **Zenkutsu Dachi** | **de cuál pierna está adelante (eje Z)** | ❌ |
| **Kokutsu Dachi** | **de cuál pierna está adelante (eje Z)** | ❌ |

Las dos posturas que fallan son exactamente las dos que dependen del eje Z. Las
dos que funcionan son exactamente las dos que no lo usan.

### 2.2 Defecto 1 — La guardia invertida convierte un Zenkutsu en un Kokutsu

Zenkutsu y Kokutsu son, para el clasificador, **la misma postura con las
piernas intercambiadas**: una rodilla flexionada y otra extendida. Lo único que
las distingue es cuál de las dos está adelante, y eso lo decide el eje Z de
MediaPipe.

Reproducido con la misma geometría corporal, cambiando **solo el signo de Z**:

```
--- Z CORRECTA (izq adelante) ---
  ZENKUTSU (IZQ ADELANTE): POSTURA: FIRME
--- Z INVERTIDA (mismo cuerpo, misma flexión) ---
  KOKUTSU (DER ADELANTE): POSTURA: ESTABLE
```

Lo grave no es que se equivoque: es que **se equivoca con veredicto positivo**.
El sistema certifica un Zenkutsu bien ejecutado como un Kokutsu bien ejecutado,
y esa fila entra a la base de datos con `correcto = True` y la técnica
equivocada. Contamina el historial y la gráfica de evolución del alumno.

**La causa de fondo, y por qué es un defecto de diseño y no de calibración:**

```python
z_diff = self.filtros["guardia_z"].update(tobillo_izq_lm.z - tobillo_der_lm.z)
if z_diff < 0:
    guardia = "IZQ ADELANTE"
else:
    guardia = "DER ADELANTE"
```

No hay zona muerta. Un `z_diff` de 0,0001 —ruido puro— decide la guardia con la
misma firmeza que uno de 0,3. El eje Z de MediaPipe es su magnitud menos fiable,
y desde una cámara frontal el orden de profundidad de dos tobillos es
precisamente lo más difícil de estimar. **No existe la rama «no lo sé».**

Y eso contradice el criterio que gobierna todo el sistema, ya escrito en
`CLAUDE.md`: *la interfaz no muestra lo que el sistema no mide*. El veredicto
ya es ternario (`correcto = True/False/None`); **la guardia también tiene que
poder abstenerse.**

### 2.3 Defecto 2 — El plano 2D arrastra todos los ángulos hacia 90°

Sebastián lo intuyó («creo que estamos topándonos con el hecho de que el plano
es 2D»). Es exacto, y ahora está cuantificado.

`BiomechanicsMath.calculate_angle` usa solo `(x, y)`: descarta la profundidad.
Cuando el plano en que ocurre la técnica no es paralelo al sensor, el ángulo
proyectado no es el ángulo real. Medido:

```
Ángulo de codo MEDIDO por el sistema (2D) según cuánto se
desvía el plano de la técnica respecto del sensor:

 giro |  real 90 | real 120 | real 160 | real 175
------+----------+----------+----------+---------
   0° |     90.0 |    120.0 |    160.0 |    175.0
  30° |     90.0 |    116.6 |    157.2 |    174.2
  45° |     90.0 |    112.2 |    152.8 |    172.9
  60° |     90.0 |    106.1 |    143.9 |    170.1
  75° |     90.0 |     98.5 |    125.4 |    161.3
  85° |     90.0 |     92.9 |    103.5 |    134.9
  90° |     90.0 |     90.0 |     90.0 |     90.0
```

**La ley es simple: la proyección 2D arrastra todo ángulo hacia 90°, y el
arrastre crece con lo que el segmento apunte a la cámara.** A 90° de giro —una
técnica ejecutada de frente al sensor— *cualquier* ángulo real mide 90°.

Esto explica el tsuki frontal sin necesidad de nada más. Un tsuki perfecto
(175°, «EXCELENTE») lanzado hacia la cámara mide 90° y se reporta **«TSUKI:
FLEXIONADO»**. Incluso a 85° de giro mide 134,9°: sigue siendo «FLEXIONADO». El
sistema no es que «no lo detecte» — lo mide con un número que no guarda relación
con el codo real, y la visibilidad sigue alta, así que ninguna guarda lo atrapa.

**Consecuencia de protocolo, y es un hallazgo legítimo de tesis:** cada técnica
debe filmarse perpendicular al plano en que ocurre.

| Técnica | Plano | Cámara |
|---|---|---|
| Heiko Dachi, Kiba Dachi | frontal | **de frente** ✅ (es lo que hizo) |
| Zenkutsu, Kokutsu, Tsuki, Mae Geri | sagital | **de perfil** ❌ (filmó de frente) |

No es un error suyo: es un requisito que el sistema nunca declaró.

### 2.4 Defecto 3 — El panel en vivo no puede mostrar las rodillas

Sebastián observó que la pantalla muestra «brazo izq, brazo der, piernas» en
plural, y que debería separar cada pierna. Es más que una preferencia: **las
filas ya existen y están permanentemente vacías.**

`gui/panel_vivo.py` declara cuatro filas (`codo_izq`, `codo_der`,
`rodilla_izq`, `rodilla_der`), pero `analyze_stance` emite las categorías
`postura` y `postura_der_numero`. Nunca coinciden. Comprobado:

```
--- FILAS DEL PANEL EN VIVO (con un Zenkutsu reconocido) ---
  Codo izquierdo       valor=—      correcto=None
  Codo derecho         valor=—      correcto=None
  Rodilla izquierda    valor=—      correcto=None
  Rodilla derecha      valor=—      correcto=None
```

Las dos rodillas se miden, se filtran y se usan para clasificar — pero el panel
no las recibe porque la etiqueta con que viajan no es la que busca.

### 2.5 Un dato que MediaPipe ya calcula y el sistema tira a la basura

`vision/tracker.py` devuelve el resultado completo de MediaPipe, pero tanto
`live_screen.py` como `main.py` usan **solo** `result.pose_landmarks` (las
coordenadas normalizadas en el plano de la imagen).

MediaPipe entrega además `result.pose_world_landmarks`: coordenadas **3D en
metros** relativas al centro de las caderas, calculadas en el mismo paso de
inferencia. **Ya se está pagando su coste en cada fotograma y se descarta.**

Calcular los ángulos sobre esas coordenadas atacaría a la vez el defecto 1 (el
orden de profundidad) y el defecto 2 (el arrastre hacia 90°), sin coste de
cómputo adicional. **No es una promesa: hay que medirlo antes de afirmarlo.** La
Z de un modelo monocular es estimada y puede ser peor que el plano de imagen en
algunos casos. Pero es la vía estructural, y es barata de probar.

---

## 3. Lo que falta, en orden de prioridad

### Bloque A — Corrección del análisis (nuevo, y ahora lo más urgente)

| # | Tarea | Por qué |
|---|---|---|
| A1 | **Zona muerta y abstención en la guardia.** Si \|z_diff\| no supera un mínimo, no afirmar qué pierna está adelante: reportar «EN TRANSICIÓN» y `correcto = None`. | Hoy el sistema guarda Zenkutsus como Kokutsus con veredicto positivo. Es el único defecto que **corrompe datos**. |
| A2 | **Evaluar `pose_world_landmarks`** contra las grabaciones existentes y decidir con la medición en la mano. | Ataca la causa raíz de A1 y del tsuki frontal. Coste de cómputo cero. |
| A3 | **Declarar el plano de cada técnica** y avisar cuando la vista no corresponde. | Convierte un fallo mudo en una instrucción. Requisito de protocolo para el dojo. |
| A4 | **Separar rodilla izquierda y derecha en el panel.** | Las filas existen vacías. |

### Bloque B — Lo que bloquea la salida al dojo

| # | Tarea | Estado |
|---|---|---|
| B1 | **Aviso de encuadre** | umbrales ya medidos: cuerpo entero da visibilidad 0,95–0,98 en rodillas, encuadre malo da 0,00. Separación limpia. |
| B2 | **Rutas absolutas** (modelo `.task` y base de datos) | sin esto no hay empaquetado |
| B3 | **Empaquetado `.command`** (Mac) y `.exe` (Windows) | pendiente |
| B4 | **Aviso de cámara caída** | parcialmente hecho (`_motivo_detencion`) |
| B5 | **Exportación y respaldo** de datos | pendiente |
| B6 | Arreglar el vigilante de `test_rendimiento_interfaz.py` | menor |

### Bloque C — Verificación pendiente en su equipo

- **¿`python3 main.py` normal se cae con SIGABRT?** Apareció un crash de Python
  (`EXC_CRASH`, `abort()`) durante las pruebas. Yo toqué el bucle de la pantalla
  en vivo (intervalo adaptativo, pre-escalado, guardia de reentrada) y **desde
  el contenedor no puedo validar comportamiento de macOS**. Si se cae, se
  revierten esos dos cambios de rendimiento: son ganancia, no supervivencia.
  Para el 9 de noviembre es preferible 18 fps estables que 24 que se caen.

### Bloque D — Fuera del código, decisión de Sebastián

- **Rangos de Kokutsu Dachi** (145–175° frontal, 90–120° trasera): los deduje
  del principio biomecánico, no salen del dojo. Pendiente del sensei. Desde el
  19-sep ya no bloquea la toma de datos: lo medido se puede volver a juzgar.
- **Consentimiento para grabar a los alumnos**, en particular menores. Trámite
  fuera del código; conviene firmarlo antes de la primera visita.
- **IMU / RF-02 y RF-04**: tiene los sensores y el ESP32, falta cautín y estaño.
  La contingencia ya está tomada: el sistema funciona solo con visión y declara
  la ausencia.

### Bloque E — Documentación

- **Capítulo 4, sección 4.8** (manuales técnicos y guías de usuario) — falta.
  Conviene escribir primero los manuales y luego la sección que los describe.
- **Sincronizar cifras**: el README cita 692 pruebas, el desarrollo va en 720.
  Versiones del Capítulo 4 citan cifras anteriores.
- **Prototipo `.dc.html`**: promete «340 reglas» y «red neuronal v0.9
  entrenando». Ninguna de las dos cosas existe.
- **Nuevo: el hallazgo de la sección 2 merece entrar en el Capítulo 4.** Ver §5.

---

## 4. Sobre la estimación de avance

La estimación que salió del análisis con ChatGPT (≈ 75 % global, software 93 %)
es razonable en su estructura —acierta en que el hardware y la validación
experimental son lo que tira el número abajo—, pero **el 93 % de software hay
que bajarlo a la luz de lo de hoy**.

No porque falte funcionalidad: el recorrido está completo. Es que el núcleo del
sistema —clasificar la postura y medir el ángulo— tiene un defecto que produce
resultados confiadamente equivocados en tres de las técnicas del catálogo, y eso
no se descubre contando pantallas. Lo descubrió una prueba en vivo.

Mi lectura: **software ~85 %**, y el trabajo restante es de precisión, no de
alcance. Es buena noticia que haya aparecido el 28 de septiembre y no en la
campaña de recolección de datos de octubre: si la campaña se hubiera corrido con
este defecto, los datos recogidos habrían sido inservibles y no habría habido
tiempo de repetirla.

Coincido con la recomendación de **congelar funcionalidades**: de aquí en
adelante, solo corrección, calibración y lo que exija un requisito.

---

## 5. Para el chat de documentación

Lo de hoy da material para el Capítulo 4 y **para el Capítulo 5**, y conviene
que se escriba antes de que se olvide cómo se encontró.

**Tablas nuevas disponibles** (la siguiente libre es la 4.10):

1. **Composición del tiempo de cómputo por etapa** sobre la interfaz real,
   11 515 fotogramas — §1.1. Va en 4.7 (pruebas de validación).
2. **Error de proyección 2D según el ángulo de cámara** — §2.3. Es la tabla más
   valiosa del día: cuantifica una limitación conocida de la estimación de pose
   monocular sobre el caso concreto del karate.
3. **Dependencia de cada postura respecto del eje de profundidad** — §2.1.

**Puntos de redacción:**

- La sección de **limitaciones** ya no es genérica: hay una limitación medida,
  con su magnitud, su causa y su mitigación (protocolo de cámara por plano).
  Eso es mucho más fuerte ante la terna que «el sistema usa visión monocular y
  por tanto tiene limitaciones».
- El **protocolo de pruebas de campo** debe incorporar la vista requerida por
  técnica (§2.3). Sin eso, la campaña de recolección produce datos inválidos
  para Zenkutsu, Kokutsu, Tsuki y Mae Geri.
- **RF-01**: hay tres cifras distintas según qué se mida, y la que va a la tesis
  es la de la interfaz real porque es la que ejecuta el dojo. Documentar las
  tres y decir cuál es cuál.
- **Corregir las fechas «29-sep» a «28-sep»** en `CLAUDE.md` (§1.5).

**Advertencia de sincronización:** nada de esto existe para el otro chat hasta
que esté empujado a `origin/main`.

---

## 6. Resumen en una línea

El rendimiento quedó medido y es defendible; **lo que hay que arreglar ahora es
que el sistema confunde Zenkutsu con Kokutsu y no sabe medir un tsuki lanzado
de frente**, y ambas cosas salen de la misma raíz: se están midiendo ángulos 3D
sobre una proyección 2D sin declarar cuándo eso deja de ser válido.
