# Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do

Sistema de escritorio que analiza en tiempo real la ejecución técnica de un
karateka mediante visión por computadora. Captura video, estima la pose corporal
(33 puntos anatómicos), calcula ángulos articulares, los evalúa contra una base
de conocimientos de Karate-Do Shotokan y registra el progreso del atleta.

## Arquitectura

```
vision/          Adquisición: cámara (OpenCV) y estimación de pose (MediaPipe)
biomechanics/    Cálculo de ángulos, filtro anti-jitter y renderizado del esqueleto
expert_system/   Motor de inferencia, base de conocimientos y máquina de estados
persistence/     SQLite local, registro de mediciones y reportes de progreso
gui/             Interfaz gráfica (CustomTkinter)
tests/           Suite de pruebas automatizadas (pytest)
docs/            Informe técnico y fichas de casos de prueba
```

## Instalación

Requiere Python 3.11 o superior.

```bash
git clone https://github.com/SHolweger/karate_biomecanica.git
cd karate_biomecanica

python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate

pip install -r requirements.txt
```

El modelo de estimación de pose (`pose_landmarker_full.task`) ya viene incluido
en el repositorio.

> **Nombre del intérprete.** En macOS y en la mayoría de distribuciones de Linux
> el comando es `python3`; `python` a secas puede no existir o apuntar a Python 2.
> En Windows suele ser `python` o `py`. Los ejemplos de este documento usan
> `python3`: sustitúyelo por el que corresponda a tu sistema.

## Ejecución del sistema

```bash
python3 main.py              # interfaz gráfica — la forma normal de usarlo
python3 main.py --consola    # versión de terminal con ventana de OpenCV
```

Ambas vías usan el mismo motor de análisis. Si la cámara no abre, ajusta el
índice en `vision/camera.py` (`Camera(source=...)`); `python3 test_camaras.py`
lista los índices disponibles en el equipo.

## Pantallas del sistema

| Pantalla | Para qué sirve |
|---|---|
| Acceso | Autenticación del entrenador (RF-08) |
| Perfiles | Selección del alumno que entrena hoy |
| Análisis en vivo | Video, esqueleto y diagnóstico técnico en tiempo real |
| Cámara | Elección de la fuente de video: dispositivo del sistema o cámara IP |
| Calibrar umbrales | Edición de los criterios biomecánicos, con historial de versiones |
| Biblioteca de técnicas | Qué evalúa el sistema y con qué criterio |
| Alumnos y progreso | Estado de cada atleta: sesiones, última fecha y precisión |
| Perfil del alumno | Dominio por técnica, sesiones y generación del reporte de progreso |
| Reporte de sesión | Precisión, puntos de control y los errores más repetidos |

## Calibración de umbrales (RF-08)

En la selección de perfiles, el botón **Calibrar umbrales** abre la edición de
los criterios biomecánicos con los que el sistema experto evalúa cada técnica.
Los umbrales son datos de la tabla `umbral_referencia`, no constantes del código
fuente: un instructor puede endurecer o relajar un criterio sin tocar Python.

Cada guardado **crea una versión nueva y conserva la anterior**, marcada como no
vigente. Las mediciones ya registradas siguen apuntando por `id_umbral` al
criterio con el que fueron evaluadas, así que recalibrar no invalida en silencio
el historial de progreso de un atleta. El botón *Historial* de cada fila muestra
esas versiones con su fuente (`literatura` o `modelado_experto`) y su fecha.

Los cambios rigen desde la siguiente sesión de análisis: la pantalla en vivo
carga los umbrales al abrirse, para no cambiar el criterio a mitad de una
medición.

---

# Pruebas automatizadas

La suite cubre la lógica biomecánica, las reglas del sistema experto, la máquina
de estados de las patadas, la persistencia y el flujo completo de la interfaz.

**352 casos · 28 documentados con ficha formal · 92 % de cobertura · ~6 segundos de ejecución**

## Instalación de las dependencias de prueba

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` no incluye MediaPipe, OpenCV ni CustomTkinter a propósito:
la mayor parte de la suite corre sin cámara, sin GPU y sin entorno gráfico. Las
pruebas que sí los necesitan se omiten solas (`SKIPPED`) cuando no están
instalados.

## Ejecución

```bash
pytest                                   # suite completa
pytest -v                                # con el nombre de cada caso
pytest tests/unit                        # solo pruebas unitarias
pytest tests/integration                 # solo pruebas de integración
pytest tests/e2e                         # solo pruebas de interfaz (requiere GUI)
pytest -m unitaria                       # por marcador: unitaria, integracion, e2e, lenta
pytest -k tsuki                           # por nombre: todo lo relacionado con Tsuki
pytest tests/unit/test_geometry.py       # un archivo concreto
pytest -x                                 # detenerse en el primer fallo
```

## Cobertura de código

```bash
pytest --cov --cov-report=term-missing   # resumen en consola
pytest --cov --cov-report=html           # reporte navegable en htmlcov/index.html
```

## Reportes con formato normalizado

Cada caso de prueba documentado declara su ficha formal (ID, tipo, prioridad,
precondiciones, datos de entrada, pasos, aserciones y criterio de salida) junto
al script que lo ejecuta, con el decorador `@ficha(...)` de
[`tests/reporte/plantilla.py`](tests/reporte/plantilla.py). La ficha se valida
al importar el módulo: una ficha incompleta rompe la recolección de pytest antes
de ejecutar nada.

```bash
pytest --reporte-formal                  # genera la evidencia y el documento de casos
pytest --exigir-fichas                   # falla si el formato documental no se cumple
pytest --reporte-formal --cov            # la evidencia incluye el % de cobertura
```

`--reporte-formal` escribe dos documentos, ambos generados y no editables a mano:

| Archivo | Contenido |
|---|---|
| `evidencias/evidencia_ejecucion_<fecha>.md` | Identificación de la corrida (entorno, commit, comando), resumen por nivel, veredicto de cada caso documentado, cobertura y detalle prueba por prueba |
| `docs/casos_prueba_automatizados.generado.md` | Las fichas completas de todos los casos y la tabla de trazabilidad contra requisitos |

`--exigir-fichas` convierte en error tres incumplimientos del formato: un módulo
de pruebas sin ningún caso documentado, IDs repetidos y huecos en la serie
`TC-AUTO-###`.

## Estructura de la suite

| Carpeta | Contenido | Casos |
|---|---|:--:|
| `tests/unit/` | Geometría articular, filtro anti-jitter, reglas de karate, instrumentación de latencia, fuentes de video, validación de la calibración, punto de entrada, plantilla de reportes | 190 |
| `tests/integration/` | Analizador, máquina de estados, SQLite, logger, reportes, renderizador, consola, umbrales, configuración y consultas de progreso | 125 |
| `tests/e2e/` | Flujo completo de la GUI: acceso, perfiles, análisis, calibración de umbrales, cámara, historial, reportes y biblioteca de técnicas | 37 |
| `tests/helpers/` | Dobles de prueba: cámara y poses sintéticas | — |
| `tests/reporte/` | Plantilla formal de los casos y complemento de pytest que emite los reportes | — |
| `tests/conftest.py` | Fixtures compartidas (base de datos temporal, cámara sintética) | — |
| `tests/e2e/conftest.py` | Andamiaje de interfaz: aplicación con ventana oculta, entrenador registrado, guardia de entorno gráfico | — |

## Cómo se prueba sin cámara ni karateka

Dos dobles de prueba (`tests/helpers/fakes.py`) sustituyen las dependencias
externas del sistema:

- **`CamaraSintetica`** cumple el contrato de `vision.camera.Camera`
  (`get_frame()` / `release()`) devolviendo cuadros generados en memoria.
- **`pose_sintetica()`** construye los 33 landmarks de MediaPipe por
  trigonometría, de modo que la prueba **declara el ángulo que quiere verificar**
  en lugar de depender de una persona ejecutando la técnica frente al lente:

```python
# Un Zenkutsu Dachi con la guardia izquierda adelante
landmarks = pose_sintetica(angulo_rodilla_izq=100, angulo_rodilla_der=170,
                           z_tobillo_izq=-0.3, z_tobillo_der=0.3)
```

## Integración continua

`.github/workflows/pruebas.yml` ejecuta la suite en cada *push* y *pull request*
sobre Ubuntu con Python 3.11 y 3.12 con `--exigir-fichas --reporte-formal`, y
publica como artefactos descargables el reporte JUnit XML, el informe de
cobertura, la evidencia de ejecución y el documento de casos generado.

## Scripts de evidencia (no forman parte de la suite)

`test_antijitter.py` y `test_camaras.py` son herramientas manuales que generan
evidencia para la tesis (gráficas del filtro) o inspeccionan el hardware. Se
ejecutan a mano y quedan fuera de `pytest` a propósito (`testpaths = tests`).

## Documentación

- [`docs/informe_tecnico_pruebas_automatizadas.md`](docs/informe_tecnico_pruebas_automatizadas.md) — análisis comparativo de herramientas y justificación de la selección
- [`docs/casos_prueba_automatizados.md`](docs/casos_prueba_automatizados.md) — versión redactada a mano de las fichas (la de entrega del curso)
- `docs/casos_prueba_automatizados.generado.md` — la misma información generada desde el código en cada corrida con `--reporte-formal`, con el veredicto real de cada caso
- [`docs/guia_de_entrega.md`](docs/guia_de_entrega.md) — cómo ejecutar, capturar evidencia y exportar los entregables a PDF
