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

## Ejecución del sistema

```bash
python gui/app.py     # interfaz gráfica (recomendado)
python main.py        # versión de consola con ventana de OpenCV
```

Ambas vías usan el mismo motor de análisis. Si la cámara no abre, ajusta el
índice en `vision/camera.py` (`Camera(source=...)`); `python test_camaras.py`
lista los índices disponibles en el equipo.

---

# Pruebas automatizadas

La suite cubre la lógica biomecánica, las reglas del sistema experto, la máquina
de estados de las patadas, la persistencia y el flujo completo de la interfaz.

**197 casos · 99 % de cobertura de la lógica de negocio · ~2 segundos de ejecución**

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

## Estructura de la suite

| Carpeta | Contenido | Casos |
|---|---|:--:|
| `tests/unit/` | Geometría articular, filtro anti-jitter, reglas de karate | 98 |
| `tests/integration/` | Analizador, máquina de estados, SQLite, logger, reportes, renderizador, consola | 91 |
| `tests/e2e/` | Flujo completo de la GUI: login → perfil → análisis → cierre | 8 |
| `tests/helpers/` | Dobles de prueba: cámara y poses sintéticas | — |
| `tests/conftest.py` | Fixtures compartidas (base de datos temporal, cámara sintética) | — |

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
sobre Ubuntu con Python 3.11 y 3.12, y publica el reporte JUnit XML y el informe
de cobertura como artefactos descargables.

## Scripts de evidencia (no forman parte de la suite)

`test_antijitter.py` y `test_camaras.py` son herramientas manuales que generan
evidencia para la tesis (gráficas del filtro) o inspeccionan el hardware. Se
ejecutan a mano y quedan fuera de `pytest` a propósito (`testpaths = tests`).

## Documentación

- [`docs/informe_tecnico_pruebas_automatizadas.md`](docs/informe_tecnico_pruebas_automatizadas.md) — análisis comparativo de herramientas y justificación de la selección
- [`docs/casos_prueba_automatizados.md`](docs/casos_prueba_automatizados.md) — fichas de los 14 casos de prueba documentados
- [`docs/guia_de_entrega.md`](docs/guia_de_entrega.md) — cómo ejecutar, capturar evidencia y exportar los entregables a PDF
