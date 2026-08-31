# Informe Técnico: Selección e Implementación de Herramientas de Automatización de Pruebas

**Sistema:** Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan
**Curso:** Aseguramiento de la Calidad del Software
**Autor:** Sebastián Holweger
**Repositorio:** `SHolweger/karate_biomecanica`
**Fecha:** agosto de 2026

---

## 1. Objetivo y alcance

Investigar, seleccionar y documentar la herramienta de automatización de pruebas
más adecuada para la arquitectura técnica del sistema Shotokan AI, e implementar
con ella un proyecto de pruebas ejecutable que garantice el control de calidad,
la reusabilidad de los scripts y la eficiencia en la ejecución.

El alcance cubre la lógica de negocio del sistema (biomecánica, sistema experto,
persistencia) y el flujo de la interfaz gráfica. Queda fuera del alcance la
verificación de la precisión del modelo de estimación de pose de MediaPipe, que
es un componente de terceros preentrenado y se valida por contraste experimental,
no por pruebas de software.

---

## 2. Análisis de compatibilidad tecnológica

### 2.1 Pila tecnológica del proyecto

| Dimensión | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Tipo de aplicación | **Aplicación de escritorio monolítica y modular**, de ejecución local |
| Interfaz de usuario | CustomTkinter (GUI) y consola (CLI alterna) |
| Visión por computadora | MediaPipe Pose Landmarker (modelo `.task` local) + OpenCV |
| Cálculo numérico | Python estándar (`math`, `collections.deque`), NumPy |
| Persistencia | SQLite embebido (archivo local, sin servidor) |
| Reportes | Matplotlib (PNG) |
| Arquitectura | Cinco capas: adquisición → biomecánica → inferencia → persistencia → presentación |
| Despliegue | *Edge computing*: 100 % local en el equipo del dojo (RNF-02) |

### 2.2 Consecuencias para la automatización

Cuatro características de esta arquitectura condicionan la elección de la herramienta:

1. **No existe capa web ni API REST.** El sistema no expone endpoints HTTP ni
   renderiza HTML. Toda la familia de herramientas orientadas al navegador
   (Selenium, Cypress, Playwright) y a la prueba de APIs (Postman + Newman,
   REST Assured) queda **técnicamente descartada por incompatibilidad**: no
   habría objeto que automatizar.
2. **No es una aplicación móvil.** Appium queda descartado por la misma razón.
3. **El lenguaje es Python.** Herramientas del ecosistema JVM (JUnit 5, TestNG)
   exigirían reescribir el sistema o construir un puente entre procesos, lo que
   añadiría un punto de fallo sin aportar capacidad de prueba.
4. **La lógica valiosa está desacoplada del hardware.** Las clases
   `BiomechanicsMath`, `KarateRules`, `MaeGeriStateMachine`, `MedicionLogger` y
   `Database` no dependen de la cámara ni de MediaPipe: reciben números,
   diccionarios y marcas de tiempo. Esta separación —ya presente en el diseño
   original del sistema— es lo que hace viable automatizar el 99 % de la lógica
   sin hardware, y es el factor que más peso tuvo en la decisión.

En consecuencia, la comparativa se centra en los tres frameworks de prueba
realmente aplicables a una aplicación de escritorio en Python: **pytest**,
**unittest** (biblioteca estándar) y **Robot Framework**.

---

## 3. Comparativa técnica de herramientas

### 3.1 Herramientas evaluadas

| Herramienta | Descripción | Aplicabilidad al proyecto |
|---|---|---|
| **pytest** | Framework de pruebas de facto en Python. Descubrimiento automático, `assert` nativo, *fixtures*, parametrización y ecosistema amplio de complementos | **Aplicable** |
| **unittest** | Framework incluido en la biblioteca estándar de Python, de estilo xUnit basado en clases | **Aplicable** |
| **Robot Framework** | Framework de automatización dirigido por palabras clave (*keyword-driven*), con sintaxis tabular legible por perfiles no técnicos | **Aplicable con reservas** |
| Selenium / Cypress / Playwright | Automatización de navegadores web | Descartadas: el sistema no tiene interfaz web |
| Postman + Newman | Automatización de APIs REST | Descartada: el sistema no expone una API |
| Appium | Automatización de aplicaciones móviles | Descartada: el sistema no es móvil |
| JUnit 5 / TestNG | Frameworks del ecosistema Java | Descartadas: el sistema está escrito en Python |

### 3.2 Matriz comparativa

Escala de calificación: 1 = deficiente, 5 = excelente. La columna *Peso* refleja
la importancia del criterio para este proyecto en particular.

| Criterio | Peso | pytest | unittest | Robot Framework |
|---|:--:|:--:|:--:|:--:|
| Compatibilidad con la arquitectura (escritorio, Python, sin web) | 25 % | 5 | 5 | 4 |
| Curva de aprendizaje | 15 % | 5 | 4 | 3 |
| Comunidad y documentación | 10 % | 5 | 4 | 4 |
| Integración con CI/CD y ejecución local | 15 % | 5 | 4 | 4 |
| Soporte a los tipos de prueba requeridos (unitaria, integración, UI) | 15 % | 5 | 4 | 3 |
| Medición de cobertura de código | 10 % | 5 | 3 | 3 |
| Reusabilidad de scripts (*fixtures*, parametrización, dobles de prueba) | 10 % | 5 | 3 | 3 |
| **Puntuación ponderada** | **100 %** | **5.00** | **4.05** | **3.55** |

### 3.3 Análisis de los resultados

**pytest (5.00).** Descubre las pruebas automáticamente, usa el `assert` nativo
de Python (sin memorizar métodos como `assertEqual`), y su sistema de *fixtures*
resuelve directamente el problema central de este proyecto: crear una base de
datos aislada y una cámara sintética por cada caso. La parametrización permite
que un solo script cubra decenas de valores límite — por ejemplo, las 60 pruebas
de la base de conocimientos se escriben en 16 funciones. Se integra con
`pytest-cov` para medir cobertura y exporta JUnit XML, formato que GitHub Actions
interpreta de forma nativa.

**unittest (4.05).** Su gran ventaja es no requerir instalación. Sin embargo,
obliga a escribir clases `TestCase` con métodos `setUp`, lo que triplica el
código repetido para el mismo escenario, y no ofrece parametrización nativa
(requiere `subTest`, más verboso y con reportes menos claros). Sigue siendo la
alternativa de respaldo si el proyecto tuviera prohibido instalar dependencias.

**Robot Framework (3.55).** Su sintaxis por palabras clave es valiosa cuando las
pruebas las escriben perfiles no técnicos (por ejemplo, un sensei definiendo
criterios). Pero aquí las pruebas verifican trigonometría, derivadas de velocidad
angular y transiciones de una máquina de estados: expresar `assert angulo ==
pytest.approx(170, abs=0.01)` como palabra clave tabular añade una capa de
indirección sin beneficio. Además exigiría escribir y mantener una biblioteca de
palabras clave en Python sobre el propio sistema — es decir, más código de
pruebas, no menos.

---

## 4. Justificación de la herramienta seleccionada: **pytest**

### 4.1 Compatibilidad con la arquitectura del sistema

pytest es una biblioteca Python que se ejecuta en el mismo intérprete que el
sistema: importa directamente `TechniqueAnalyzer`, `KarateRules` o `Database` y
los ejercita como lo haría `main.py`. No requiere servidor, navegador,
controlador ni protocolo intermedio.

Lo decisivo es cómo resuelve las dos dependencias externas del sistema:

- **La cámara** se sustituye por la clase `CamaraSintetica`, que cumple el mismo
  contrato (`get_frame()` / `release()`) devolviendo cuadros generados en
  memoria. `LiveScreen` ya aceptaba una cámara inyectada por parámetro, así que
  no fue necesario modificar código de producción para hacerlo comprobable.
- **MediaPipe** se sustituye por poses sintéticas: `pose_sintetica()` construye
  los 33 landmarks mediante trigonometría, de modo que la prueba **declara el
  ángulo articular que quiere probar** (por ejemplo, un Zenkutsu de 100° al
  frente y 170° atrás) en lugar de depender de que una persona real lo ejecute
  frente a la cámara. La verificación mostró una fidelidad de ±0.1° entre el
  ángulo solicitado y el medido por el sistema.

Esto convierte pruebas que serían manuales, lentas e irrepetibles —requieren un
karateka, una cámara y buena iluminación— en pruebas deterministas de milisegundos.

### 4.2 Curva de aprendizaje y soporte de la comunidad

Una prueba en pytest es una función que empieza con `test_` y contiene un
`assert`; no hay clases, herencia ni ceremonia que aprender. Esto importa en un
proyecto de tesis desarrollado por una sola persona: el tiempo invertido en
aprender la herramienta compite directamente con el tiempo de desarrollo del
sistema.

En cuanto a soporte: pytest es el framework de pruebas más usado del ecosistema
Python, con documentación oficial extensa, más de mil complementos publicados y
presencia dominante en las respuestas de la comunidad. El proyecto ya contaba con
scripts de verificación escritos en estilo pytest (funciones `test_*` con
`assert`), por lo que la migración fue de sintaxis casi nula: se conservó el
conocimiento acumulado y se ganó la infraestructura.

### 4.3 Integración con el flujo de trabajo (CI/CD y ejecución local)

- **Local:** un solo comando, `pytest`, descubre y ejecuta la suite completa en
  ~2 segundos. Para trabajar sobre un módulo concreto basta con
  `pytest tests/unit/test_knowledge_base.py -k tsuki`.
- **CI/CD:** se configuró el flujo `.github/workflows/pruebas.yml`, que ejecuta
  la suite en Ubuntu con Python 3.11 y 3.12 en cada *push* y cada *pull request*,
  publica el reporte JUnit XML y el informe de cobertura como artefactos
  descargables.
- **Costo de ejecución en CI:** el archivo `requirements-dev.txt` deliberadamente
  **no** incluye MediaPipe, OpenCV ni CustomTkinter. Como la suite está diseñada
  para correr sin ellos, el entorno de CI se instala en segundos en lugar de
  descargar cientos de megabytes de modelos de visión por computadora. Las
  pruebas que sí requieren esas bibliotecas se omiten de forma controlada
  (`pytest.importorskip`) y se ejecutan en el entorno local de desarrollo.

### 4.4 Tipos de prueba que se automatizan

| Tipo | Cobertura en este proyecto | Mecanismo |
|---|---|---|
| **Unitarias** | Geometría articular, filtro anti-jitter, reglas de karate | Funciones puras, sin dependencias; análisis de valores límite |
| **De integración** | Analizador ↔ reglas ↔ filtros; máquina de estados; SQLite; logger; reportes; renderizador | Poses sintéticas y base de datos real en archivo temporal |
| **De interfaz (UI / E2E)** | Login → selección de perfil → análisis en vivo → cierre de sesión | Aplicación real de CustomTkinter con ventana oculta y cámara inyectada |
| **De API** | No aplica | El sistema no expone una API REST (ver sección 2.2) |

---

## 5. Estrategia y diseño de los casos de prueba

### 5.1 Distribución de la suite

Se siguió el modelo de la pirámide de pruebas: muchas pruebas unitarias rápidas
en la base, un conjunto intermedio de integración y unas pocas pruebas de
interfaz, que son las más lentas y frágiles.

| Nivel | Casos | Proporción | Tiempo de ejecución |
|---|:--:|:--:|---|
| Unitarias | 98 | 50 % | < 0.2 s |
| Integración | 91 | 46 % | ~2 s |
| Interfaz (E2E) | 8 | 4 % | ~5 s (solo en entorno local con GUI) |
| **Total** | **197** | 100 % | **~2 s** en CI (sin E2E) |

### 5.2 Técnicas de diseño aplicadas

- **Análisis de valores límite.** Los umbrales del sistema experto se prueban
  justo dentro, justo fuera y exactamente sobre la frontera. Un Tsuki de 175.0°
  es correcto y uno de 175.1° es una hiperextensión peligrosa: esa distinción se
  verifica explícitamente, porque es donde un sistema de evaluación técnica falla.
- **Partición de equivalencia.** Cada regla se ejercita con un representante de
  cada clase de resultado (correcto / insuficiente / excesivo).
- **Pruebas de transición de estados.** La máquina de estados del Mae Geri se
  recorre por todos sus caminos: ciclo completo, abandono por tiempo de espera en
  cada fase, oclusión breve, oclusión prolongada y ejecución de dos patadas
  consecutivas.
- **Pruebas de propiedades e invariantes.** Se verifican propiedades que deben
  cumplirse siempre: el ángulo articular nunca sale del rango [0°, 180°]; el
  ángulo es invariante a la escala (la distancia del atleta a la cámara no
  cambia el diagnóstico); el filtro reduce la dispersión del ruido.
- **Dobles de prueba (*test doubles*).** Cámara sintética, poses sintéticas y
  sustitución de `input()`/`getpass()` para automatizar el flujo de consola.
- **Pruebas de contrato.** Varios casos verifican que los diccionarios de
  diagnóstico traigan todas las claves que consumen el renderizador y la capa de
  persistencia. Una clave faltante no rompería una prueba de lógica, pero sí
  congelaría el video en plena clase.
- **Pruebas de regresión.** Se documentaron como casos permanentes los defectos
  ya corregidos: el reinicio del filtro tras una oclusión y la no herencia de la
  velocidad pico entre dos patadas consecutivas.

### 5.3 Reusabilidad de los scripts

La reusabilidad se implementó en tres niveles:

1. **Fixtures compartidas** (`tests/conftest.py`): `db`, `sesion_de_prueba`,
   `camara_sintetica`. Cada prueba recibe una base de datos limpia y aislada, por
   lo que el orden de ejecución nunca altera el resultado.
2. **Biblioteca de dobles** (`tests/helpers/fakes.py`): un único generador de
   poses parametrizable sirve a todas las pruebas del analizador, la máquina de
   estados y el renderizador.
3. **Parametrización**: 16 funciones de prueba producen 60 casos ejecutables en
   el módulo de la base de conocimientos. Agregar una nueva postura al sistema
   experto cuesta una línea en la lista de parámetros, no un archivo nuevo.

---

## 6. Implementación del proyecto de pruebas

### 6.1 Estructura

```
karate_biomecanica/
├── pytest.ini                 # Configuración: rutas, marcadores, salida
├── conftest.py                # Hace importable el proyecto durante las pruebas
├── .coveragerc                # Configuración de la medición de cobertura
├── requirements-dev.txt       # Dependencias del proyecto de pruebas
├── .github/workflows/pruebas.yml   # Integración continua
└── tests/
    ├── conftest.py            # Fixtures compartidas
    ├── helpers/fakes.py       # Dobles: cámara y poses sintéticas
    ├── unit/                  # 98 casos: geometría, filtros, reglas
    ├── integration/           # 91 casos: analizador, FSM, SQLite, reportes
    └── e2e/                   # 8 casos: flujo completo de la GUI
```

### 6.2 Ejemplo de script funcional

Verificación del clasificador de posturas con una pose sintética (extracto de
`tests/integration/test_analyzer.py`):

```python
@pytest.mark.parametrize("nombre, izq, der, postura_esperada", [
    ("posicion natural",   175, 175, "POSTURA NATURAL"),
    ("postura de jinete",  140, 140, "KIBA DACHI"),
    ("postura adelantada", 100, 170, "ZENKUTSU"),
    ("postura atrasada",   110, 100, "KOKUTSU"),
])
def test_identifica_la_postura_antes_de_evaluarla(analizador, nombre, izq, der,
                                                  postura_esperada):
    landmarks = pose_sintetica(angulo_rodilla_izq=izq, angulo_rodilla_der=der,
                               z_tobillo_izq=-0.2, z_tobillo_der=0.2)

    resultados = analizador.analyze_stance(landmarks, ANCHO, ALTO)

    assert postura_esperada in _por_categoria(resultados, "postura")["mensaje"], nombre
```

Un solo script cubre las cuatro posturas del sistema. Sin la herramienta, cada
una exigiría a un karateka ejecutarla frente a la cámara y a un observador
confirmar el mensaje en pantalla.

---

## 7. Resultados de la ejecución

Ejecución del 25 de agosto de 2026, Python 3.11.15 (evidencia completa en
`evidencias/pruebas_automatizadas_20260825_224707.txt`):

```
189 passed, 1 skipped in 2.27s
```

El caso omitido corresponde al módulo E2E de la interfaz gráfica, que se salta de
forma controlada por ausencia de entorno gráfico en el servidor de integración.

### 7.1 Cobertura de código

| Módulo | Sentencias | Cobertura |
|---|:--:|:--:|
| `biomechanics/geometry.py` | 12 | 100 % |
| `biomechanics/filters.py` | 9 | 100 % |
| `biomechanics/renderer.py` | 25 | 100 % |
| `expert_system/analyzer.py` | 94 | 99 % |
| `expert_system/kick_state_machine.py` | 101 | 96 % |
| `expert_system/knowledge_base.py` | 54 | 100 % |
| `persistence/database.py` | 54 | 100 % |
| `persistence/cli_auth.py` | 46 | 100 % |
| `persistence/medicion_logger.py` | 19 | 100 % |
| `persistence/reportes.py` | 55 | 100 % |
| **Total (lógica de negocio)** | **469** | **99 %** |

Los módulos `vision/camera.py` y `vision/tracker.py` (25 sentencias en total)
quedan sin cobertura automatizada por ser envolturas delgadas sobre hardware y
sobre MediaPipe: su verificación es manual, con el equipo conectado. Los módulos
de `gui/` se cubren mediante las pruebas E2E, que se ejecutan en el entorno local
de desarrollo y no en CI.

### 7.2 Defectos y hallazgos

La suite se construyó sobre código ya estabilizado por verificación manual, por
lo que no se detectaron defectos funcionales nuevos. El valor obtenido es
principalmente **preventivo**: los 197 casos quedan como red de seguridad para la
calibración de umbrales prevista (los valores de velocidad mínima y de tiempos de
espera están marcados como provisionales en el código) y para la futura
integración del sensor inercial (RF-02 y RF-04, planificados). Toda modificación
de un umbral ahora produce un fallo inmediato y localizado en lugar de un error
silencioso en el diagnóstico mostrado al atleta.

---

## 8. Integración continua

El flujo `.github/workflows/pruebas.yml` se dispara en cada *push* y *pull
request* sobre cualquier rama:

1. Descarga el repositorio y prepara Python 3.11 y 3.12 (matriz de dos versiones).
2. Instala únicamente `requirements-dev.txt`.
3. Ejecuta `pytest` con medición de cobertura y reporte JUnit XML.
4. Publica `reporte-pruebas.xml` y `coverage.xml` como artefactos descargables.

Un fallo en cualquiera de las dos versiones de Python marca el *commit* en rojo
antes de que llegue a la rama principal.

---

## 9. Limitaciones

- **La precisión del modelo de pose no se automatiza.** Las poses sintéticas
  verifican que el sistema interpreta correctamente los landmarks que recibe, no
  que MediaPipe los estime bien. Esa validación es experimental (contraste contra
  goniometría) y pertenece al capítulo de resultados de la tesis.
- **Las pruebas E2E no corren en CI.** Requieren entorno gráfico; se ejecutan
  localmente antes de cada entrega.
- **El hardware de captura sigue siendo verificación manual.** `Camera` y
  `PoseTracker` se prueban conectando el equipo.
- **Sin pruebas de desempeño automatizadas.** La tasa de cuadros por segundo del
  bucle en vivo se mide manualmente; automatizarla exigiría un entorno de
  ejecución con hardware controlado.

---

## 10. Conclusiones

1. La comparativa técnica descartó por incompatibilidad arquitectónica a las
   herramientas más difundidas del mercado (Selenium, Cypress, Playwright,
   Postman, Appium): ninguna aplica a una aplicación de escritorio sin capa web
   ni API. La lección metodológica es que la popularidad de una herramienta no
   sustituye al análisis de compatibilidad.
2. **pytest** obtuvo la puntuación ponderada más alta (5.00 sobre 5) por su
   compatibilidad directa con la arquitectura, su curva de aprendizaje mínima, su
   integración natural con GitHub Actions y su soporte a los tres tipos de prueba
   que el sistema necesita.
3. Se implementaron **197 casos de prueba automatizados** distribuidos en 11
   archivos, que alcanzan un **99 % de cobertura de la lógica de negocio** y se
   ejecutan completos en aproximadamente **2 segundos**.
4. El diseño desacoplado del sistema —cuyas clases de inferencia no conocen
   MediaPipe ni los píxeles— fue la condición que hizo viable esta automatización.
   Confirma que la comprobabilidad es una propiedad del diseño, no algo que se
   añade al final.

---

## 11. Referencias

- Krekel, H. y colaboradores. *pytest documentation*. https://docs.pytest.org/
- *pytest-cov documentation*. https://pytest-cov.readthedocs.io/
- Python Software Foundation. *unittest — Unit testing framework*. https://docs.python.org/3/library/unittest.html
- Robot Framework Foundation. *Robot Framework User Guide*. https://robotframework.org/
- Google. *MediaPipe Pose Landmarker*. https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
- GitHub. *GitHub Actions documentation*. https://docs.github.com/actions
- Fowler, M. (2012). *Test Pyramid*. https://martinfowler.com/bliki/TestPyramid.html
- ISTQB. *Certified Tester Foundation Level Syllabus*, sección 4: Técnicas de prueba.
