# Protocolo de grabación y límites del sistema

Documento de trabajo para la sesión del sábado y base para el manual de usuario.
Todas las cifras citadas están **medidas sobre grabaciones reales**, no estimadas;
la fuente de cada una está en `CLAUDE.md` y en la bitácora.

---

## Por qué existe este protocolo

El sistema mide ángulos sobre la imagen en **dos dimensiones**. Cuando el plano
de la técnica no es perpendicular al sensor, el ángulo proyectado no es el real,
y la proyección **arrastra todo ángulo hacia 90°**:

| giro de la cámara | rodilla real 120° | rodilla real 160° | codo real 175° |
|---|---|---|---|
| 0° (perpendicular) | 120,0 | 160,0 | 175,0 |
| 45° | 112,2 | 152,8 | 172,9 |
| 75° | 98,5 | 125,4 | 161,3 |
| **90°** | **90,0** | **90,0** | **90,0** |

A 90° de giro, *cualquier* ángulo real mide 90°. Esto no es un defecto que se
pueda arreglar en el código: es geometría de la proyección.

Medido sobre 3190 fotogramas de Zenkutsu Dachi grabados desde tres ángulos en
una misma sesión:

| Ángulo de cámara | fotogramas | Zenkutsu reconocido |
|---|---|---|
| De frente | 1156 | **0,0 %** |
| A 45° | 411 | 8,8 % |
| De perfil | 1623 | **37,2 %** |

**De frente el sistema es ciego a esa postura.** No acierta menos: no la
reconoce ni una sola vez.

---

## Tabla de planos — la regla que manda

| Técnica | Plano del gesto | Dónde va la cámara |
|---|---|---|
| Heiko Dachi, Kiba Dachi | frontal | **de frente** |
| Zenkutsu Dachi, Kokutsu Dachi | sagital | **de perfil** |
| Tsuki, Mae Geri | sagital | **de perfil** |

«De perfil» significa que la cámara mira tu costado, a 90° de la línea de tus
hombros. La pantalla en vivo lo indica sola: muestra «Cámara de perfil» o
«Cámara de frente» según lo que detecta.

---

## Guion de tomas para el sábado

### Bloque 0 — Preparación, una sola vez

- Cámara **fija**: trípode, o apoyada en algo estable. Nada de sostenerla.
- Altura: a la **altura de tu cadera**, no del pecho ni del suelo.
- Encuadre: **cuerpo completo** con holgura. Pies y cabeza dentro, con margen
  a los lados para que no te salgas al moverte.
- Resolución: **1080p basta**. Está medido que subir a más no mejora el
  análisis —el modelo reescala el fotograma a su tamaño interno— y solo
  encarece la captura.
- Luz: que **no haya ventana ni lámpara detrás de ti**. El contraluz convierte
  el cuerpo en silueta.
- **Nadie más en cuadro.** El sistema analiza una sola persona.

### Bloque 1 — Grabación de control  ⟵ *la más importante*

Resuelve el pendiente abierto: por qué una guardia mide la rodilla delantera
**34° más estirada** que la otra. Hasta que esto se aclare, la campaña de
recolección en el dojo está bloqueada: si fuera un sesgo de pierna, la mitad de
los alumnos se mediría mal según con qué guardia entrenen.

Dos tomas, **~20 segundos cada una**:

| Toma | Postura | Dónde te pones la cámara |
|---|---|---|
| **A** | Zenkutsu, **derecha adelante** | de perfil, a tu **costado izquierdo** |
| **B** | Zenkutsu, **derecha adelante** | de perfil, a tu **costado derecho** |

**La guardia no cambia entre las dos tomas. Lo único que se mueve es la
cámara.** Eso es lo que separa las dos explicaciones posibles: si el error
sigue a la pierna anatómica, es sesgo de pierna; si sigue al lado donde está la
cámara, es oclusión.

Si cambias la guardia entre tomas, la grabación no sirve para esto.

### Bloque 2 — Técnicas etiquetadas

Un **archivo por técnica**. Di el nombre al empezar, ya colocado en posición.

**De perfil:**

| Técnica | Repeticiones | Cómo |
|---|---|---|
| Zenkutsu Dachi | 8 | sostén cada una **3 segundos**, vuelve a natural entre una y otra |
| **Kokutsu Dachi** | 8 | igual. *Es el que resuelve el pendiente del sensei* |
| Tsuki | 10 | a **velocidad de combate**, no de demostración |
| Mae Geri | 8 | patada completa **de un solo tirón**, sin pausas |

**De frente:**

| Técnica | Repeticiones | Cómo |
|---|---|---|
| Heiko Dachi | — | 15 segundos quieto |
| Kiba Dachi | 8 | sostén cada una 3 segundos |

### Bloque 3 — Tsuki lento contra Tsuki rápido

Decide un umbral que hoy está **abierto**. El sistema exige que el codo recorra
35° en medio segundo (unos 70°/s) para reconocer un golpe; por debajo de eso,
**calla**. Y callar ante un Tsuki lento es justo lo contrario de lo que un
sistema de corrección debe hacer: un golpe flojo es una ejecución mejorable, no
la ausencia de ejecución.

Dos archivos separados, de perfil:

1. **10 Tsuki a velocidad de combate.**
2. **10 Tsuki deliberadamente lentos**, como se practica frente al espejo.

Con las dos distribuciones se puede fijar una banda en vez de un umbral: entre
las dos cifras, el golpe se reconoce y se informa como lento.

---

## Cómo NO grabar

| ❌ | Por qué |
|---|---|
| Filmar Zenkutsu, Kokutsu, Tsuki o Mae Geri **de frente** | 0,0 % de reconocimiento. Medido. |
| Quedarte **a 45°** | Es la peor zona: 8,8 %. Siete de tus trece videos cayeron ahí. |
| **Sostener la técnica** para leer la pantalla | Rompe las máquinas de estado. El Mae Geri nunca cerró su ciclo por esto, y un Tsuki sostenido más de medio segundo vuelve a «SIN TSUKI». |
| Grabar **a máxima resolución** creyendo que mejora | No mejora nada y encarece la captura. |
| Pulsar grabar y **después caminar** al sitio | Los primeros segundos son inútiles y contaminan las mediciones de rendimiento. |
| Ponerte **de espaldas** a la cámara | El eje sagital se invierte y la guardia sale al revés. |
| **Cortar pies o cabeza** del encuadre | Sin tobillos no hay ángulo de rodilla ni guardia. |
| Dejar **otra persona** en cuadro | El modelo está configurado para un solo cuerpo. |
| Fiarte de la **puntuación de visibilidad** | **No delata este error.** La pierna peor medida marcó 0,958 de visibilidad: el modelo infiere articulaciones ocultas sin bajar esa cifra. |

## Cómo SÍ grabar

| ✅ | |
|---|---|
| Cámara **perpendicular al plano** de la técnica | es la regla que gobierna todo lo demás |
| **Cuerpo completo** con margen | con buen encuadre la detección llega al 98 % y la visibilidad de rodillas a 0,95–0,98 |
| Empezar **ya colocado** y decir la técnica | el nombre hablado es la etiqueta de verdad del archivo |
| Dinámicas **de un solo tirón**; posturas **sostenidas 3 s** | cada tipo de técnica se evalúa distinto |
| **Un archivo por técnica** | permite medir precisión por técnica |
| Nombrar el archivo con la técnica, si puedes | ahorra la lista de etiquetas después |

---

## Límites del sistema — qué NO hace, y conviene decirlo en la tesis

**No mide potencia ni fuerza.** La cámara entrega píxeles, no newtons. Lo que
mide es **velocidad angular del codo**, que se relaciona con la potencia pero no
es ella. Afirmar lo contrario sería del mismo tipo que mostrar velocidades en
metros por segundo, que el sistema tiene prohibido por la misma razón.

**No reconoce la técnica por su forma.** Para el sistema, un Tsuki es «una
extensión rápida del codo». Cualquier otra extensión rápida del codo se le
parece. No distingue un Gyaku de un Kizami ni de un estiramiento enérgico.

**Es bidimensional.** Se evaluó pasar a 3D y se descartó con datos: el 3D da
2,8 puntos más en Zenkutsu pero lee las rodillas **15,3° más flexionadas** de
mediana, y convierte en «Kiba Dachi» un tercio de los fotogramas en que
simplemente estás de pie. Tiene un sesgo sistemático hacia la flexión.

**Hoy no informa el Tsuki lento.** Está declarado como pendiente abierto, y el
Bloque 3 del sábado existe para cerrarlo.

**No muestra lo que no mide.** Sin evaluaciones cerradas la precisión aparece
como un guion, nunca como 0 %: un alumno sin medir no falla el 100 % de sus
técnicas. Los sensores inerciales se declaran ausentes, no en cero.

---

## Cómo NO usar el sistema en el dojo

- **No como juez absoluto.** Los rangos de Kokutsu Dachi (145–175° delantera,
  90–120° trasera) los deduje del principio biomecánico, **no salen del dojo**.
  Siguen pendientes de que el sensei los confirme.
- **No comparar alumnos medidos con encuadres distintos.** Dos personas filmadas
  en planos diferentes no son comparables, aunque el número se vea igual.
- **No grabar a menores sin consentimiento firmado.** La grabación se puede
  apagar por equipo, pero el permiso es un trámite fuera del código y conviene
  tenerlo antes de la primera visita al dojo.
- **No leer el historial anterior al 30 de septiembre** para calcular precisión:
  contiene filas de Tsuki producidas por brazos que no golpeaban.
