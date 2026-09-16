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

**El texto técnico del diagnóstico es el registro; la instrucción es aparte.**
`gui/coaching.py` traduce «TSUKI: HIPEREXTENDIDO» a «No bloquees el codo al
impacto». El texto técnico no se cambia porque es la clave con la que la base
agrupa los errores frecuentes.

---

## Convenciones de pruebas

**Dos entornos, y las cifras difieren a propósito:**

| Entorno | Comando | Resultado |
|---|---|---|
| Completo (con cámara y pantalla) | `python3 -m pytest -q` | 564 passed |
| CI / sin entorno gráfico | igual | 466 passed, 8 skipped |

Los módulos de `tests/e2e/` se omiten solos con `pytest.importorskip`. Por eso
toda regla de presentación que pueda expresarse sin CustomTkinter **se extrae a
un módulo puro** (`gui/panel_vivo.py`, `gui/coaching.py`,
`gui/validacion_umbrales.py`, `gui/registro_alumno.py`, `vision/fuentes.py`,
`vision/nombres_camara.py`) para que CI la verifique.

**Fichas de caso de prueba.** Los casos formales llevan `@ficha(...)` de
`tests/reporte/plantilla.py`, validado al importar. Los IDs `TC-AUTO-NNN` deben
ser únicos y correlativos — **el siguiente libre es TC-AUTO-039**. Cada módulo
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
prevención de lesiones, biblioteca de técnicas, calibración de umbrales y
selección de cámara.

**Bloqueado por hardware:** RF-02 y RF-04 (sensores inerciales). Sebastián tiene
el ESP32 y los IMU pero **no tiene cautín**. La contingencia ya está tomada: el
sistema funciona solo con visión y declara la ausencia.

**Pendiente de Sebastián, no mío:** confirmar con su sensei los rangos de
**Kokutsu Dachi** (145–175° rodilla delantera, 90–120° trasera). Esos números
los deduje yo del principio biomecánico, no salen del dojo, y hoy gobiernan el
clasificador.

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
