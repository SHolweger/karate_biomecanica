# Documentación de Casos de Prueba Automatizados

**Proyecto:** Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do
**Curso:** Aseguramiento de la Calidad del Software
**Fecha:** agosto de 2026
**Repositorio:** `SHolweger/karate_biomecanica`

---

## Ficha General del Proyecto de Automatización

| Campo | Detalle |
|---|---|
| **Nombre del Proyecto / Sistema** | Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan |
| **Módulo o Componente** | Motor biomecánico (`biomechanics`), sistema experto (`expert_system`), persistencia (`persistence`), interfaz gráfica (`gui`) |
| **Herramienta / Framework Seleccionado** | pytest 8.x + pytest-cov (cobertura) + GitHub Actions (CI) |
| **Lenguaje de Scripting / Lenguaje de Pruebas** | Python 3.11 |
| **Entorno de Ejecución** | QA - Local (macOS, Apple Silicon, entorno virtual `venv`) y CI - GitHub Actions (Ubuntu 22.04, Python 3.11 y 3.12, headless) |

**Resumen de la suite**

| Nivel | Archivos | Casos ejecutables | Cobertura de la capa |
|---|---|---|---|
| Unitarias | 3 | 98 | `biomechanics`, `knowledge_base` — 100 % |
| Integración | 7 | 91 | `analyzer`, `kick_state_machine`, `persistence` — 96-100 % |
| E2E (interfaz) | 1 | 8 | flujo `gui` completo |
| **Total** | **11** | **197** | **99 % de la lógica de negocio** |

Las 14 fichas siguientes documentan los casos de prueba de las funcionalidades
críticas. Cada ficha corresponde a una función de prueba real y ejecutable del
repositorio; el resto de los casos son variantes parametrizadas de los mismos
scripts.

---

## TC-AUTO-001 — Cálculo del ángulo articular

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-001 |
| **Nombre de la Prueba** | Reconstrucción exacta del ángulo interno de una articulación en todo el rango de movimiento humano |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — todo diagnóstico del sistema experto depende de este cálculo |
| **Precondiciones** | Ninguna. `BiomechanicsMath` es una clase de utilidad sin estado ni dependencias externas |
| **Datos de Entrada (Test Data)** | Nueve ángulos conocidos del rango articular: `[0, 15, 30, 45, 60, 90, 120, 150, 179]`, con puntos generados por trigonometría a radio 100 px |
| **Archivo / Clase del Script** | `tests/unit/test_geometry.py::test_reconstruye_cualquier_angulo_del_rango_articular` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Construir los tres puntos A, B, C a partir de un ángulo conocido `θ` | Coordenadas válidas en el plano de la imagen |
| 2 | Invocar `BiomechanicsMath.calculate_angle(A, B, C)` | Devuelve un valor de tipo `float` |
| 3 | Comparar el resultado contra `θ` | `assert obtenido == pytest.approx(θ, abs=0.01)` |
| 4 | Repetir para los nueve ángulos del rango | Los nueve casos parametrizados finalizan en PASSED |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED sin excepciones ni tiempos de espera agotados.
- **Evidencia de Ejecución:** reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.

---

## TC-AUTO-002 — Normalización de ángulos reflejos

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-002 |
| **Nombre de la Prueba** | El ángulo devuelto nunca excede 180° aunque los segmentos crucen la discontinuidad de `atan2` |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — un ángulo de 340° no entra en ningún umbral y el sistema dejaría de evaluar la técnica |
| **Precondiciones** | Ninguna |
| **Datos de Entrada (Test Data)** | Pares de orientaciones opuestas al corte ±180°: `(170°, −170°)`, `(150°, −150°)`, `(−179°, 179°)` |
| **Archivo / Clase del Script** | `tests/unit/test_geometry.py::test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Colocar los segmentos proximal y distal a lados opuestos de ±180° | Configuración geométrica que produce un ángulo reflejo interno |
| 2 | Invocar `calculate_angle` | Se ejecuta la rama de normalización `360 − ángulo` |
| 3 | Verificar el ángulo interno equivalente | `assert obtenido == pytest.approx(esperado, abs=0.01)` |
| 4 | Verificar la invariante global de rango | `assert 0.0 <= ángulo <= 180.0` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los tres casos parametrizados.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-003 — Filtro anti-jitter

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-003 |
| **Nombre de la Prueba** | El filtro de media móvil reduce al menos a la mitad la dispersión del ruido de MediaPipe |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — sin el filtro el diagnóstico parpadea, pero el sistema sigue operando |
| **Precondiciones** | Ninguna |
| **Datos de Entrada (Test Data)** | Serie de 10 mediciones ruidosas alrededor de 170°: `[168, 174, 169, 173, 167, 175, 170, 172, 168, 174]`; ventana del filtro = 5 |
| **Archivo / Clase del Script** | `tests/unit/test_filters.py::test_reduce_la_dispersion_del_ruido` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Instanciar `MovingAverageFilter(window=5)` | Buffer circular vacío |
| 2 | Alimentar las 10 mediciones y recolectar las salidas | Se obtiene una serie suavizada de igual longitud |
| 3 | Calcular la desviación estándar de entrada y de salida | Ambas métricas disponibles |
| 4 | Comparar la dispersión | `assert pstdev(salida) < pstdev(entrada) / 2` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Un fallo indica que el suavizado dejó de ser efectivo (ventana mal configurada o buffer sin `maxlen`).
- **Evidencia de Ejecución:** reporte de consola de pytest; evidencia visual complementaria en `evidencias/antijitter_*.png`.

---

## TC-AUTO-004 — Regla de evaluación del Tsuki (valores límite)

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-004 |
| **Nombre de la Prueba** | Clasificación del golpe recto en las fronteras exactas de 160° y 175° |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — un falso positivo aprueba una hiperextensión, que es riesgo de lesión articular |
| **Precondiciones** | Ninguna. `KarateRules` expone métodos estáticos sin estado |
| **Datos de Entrada (Test Data)** | `elbow_angle` = `159.9` (fuera), `160.0` (frontera inferior), `175.0` (frontera superior), `175.1` (fuera) |
| **Archivo / Clase del Script** | `tests/unit/test_knowledge_base.py::test_tsuki_fronteras_exactas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `KarateRules.evaluate_tsuki(angulo)` con cada valor límite | Devuelve la tupla `(correcto, mensaje, color)` |
| 2 | Verificar el veredicto en la frontera inferior | `assert evaluate_tsuki(160.0)[0] is True` y `evaluate_tsuki(159.9)[0] is False` |
| 3 | Verificar el veredicto en la frontera superior | `assert evaluate_tsuki(175.0)[0] is True` y `evaluate_tsuki(175.1)[0] is False` |
| 4 | Verificar el mensaje y el color de cada categoría | `"HIPEREXTENDIDO"` en rojo `(0,0,255)`; `"FLEXIONADO"` en amarillo `(0,255,255)` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro valores límite y en los 11 casos de rango asociados.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-005 — Regla de evaluación del Mae Geri

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-005 |
| **Nombre de la Prueba** | La patada frontal exige simultáneamente extensión (Kime ≥ 160°) y explosividad (≥ 400 °/s) |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la regla con dos condiciones acopladas, la más propensa a error lógico |
| **Precondiciones** | Ninguna |
| **Datos de Entrada (Test Data)** | `(kime=159.9, vel=400)`, `(160.0, 400.0)`, `(170, 399.9)`, `(170, 400)` |
| **Archivo / Clase del Script** | `tests/unit/test_knowledge_base.py::test_mae_geri_fronteras_exactas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `evaluate_mae_geri(kime_angle, velocidad_pico)` | Devuelve `(correcto, mensaje, color)` |
| 2 | Comprobar la frontera de extensión | `assert evaluate_mae_geri(160.0, 400.0)[0] is True` y `(159.9, 400)[0] is False` |
| 3 | Comprobar la frontera de velocidad | `assert evaluate_mae_geri(170, 400)[0] is True` y `(170, 399.9)[0] is False` |
| 4 | Verificar la precedencia del diagnóstico | Con Kime incompleto el mensaje reporta `"KIME INCOMPLETO"` aun con velocidad alta, no `"EXPLOSIVIDAD"` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro valores límite y en los 7 casos de rango asociados.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-006 — Clasificador de posturas (Dachi)

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-006 |
| **Nombre de la Prueba** | El analizador identifica la postura ejecutada antes de evaluarla, a partir de los ángulos de ambas rodillas |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — si clasifica mal la postura, aplica la regla equivocada y todo el diagnóstico es inválido |
| **Precondiciones** | Instancia de `TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)`; pose sintética de 33 landmarks con visibilidad 1.0 |
| **Datos de Entrada (Test Data)** | `(izq=175, der=175)` → Postura natural; `(140, 140)` → Kiba Dachi; `(100, 170)` → Zenkutsu; `(110, 100)` → Kokutsu. Profundidad `z_tobillo_izq=-0.2`, `z_tobillo_der=0.2` |
| **Archivo / Clase del Script** | `tests/integration/test_analyzer.py::test_identifica_la_postura_antes_de_evaluarla` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Generar la pose sintética con `pose_sintetica(...)` | 33 landmarks con los ángulos de rodilla solicitados (±0.1°) |
| 2 | Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)` | Lista de diagnósticos con la categoría `"postura"` |
| 3 | Extraer el diagnóstico de la categoría `postura` | El diccionario contiene la clave `mensaje` |
| 4 | Validar la postura detectada | `assert "KIBA DACHI" in mensaje` (y análogos por cada postura) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en las cuatro posturas parametrizadas.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-007 — Ciclo completo de la patada (máquina de estados)

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-007 |
| **Nombre de la Prueba** | Una patada correcta recorre Reposo → Carga → Extensión → Recuperando → Reposo y se califica como correcta |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la única técnica evaluada en movimiento; un error de transición deja al sistema atascado |
| **Precondiciones** | `MaeGeriStateMachine(ventana_filtro=1)` recién instanciada, con la referencia de "pie en el suelo" registrada (`ankle_y = 0.90`) |
| **Datos de Entrada (Test Data)** | Secuencia de cuadros a ~30 fps: `(175°, y=0.90, t=0)`, `(45°, 0.90, 33 ms)`, `(170°, 0.50, 66 ms)`, `(45°, 0.50, 100 ms)`, `(175°, 0.90, 133 ms)` |
| **Archivo / Clase del Script** | `tests/integration/test_kick_state_machine.py::test_ciclo_completo_de_una_patada_correcta` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Enviar el cuadro de pie y luego el de rodilla flexionada | `assert maquina.estado == "CARGA"` |
| 2 | Enviar el cuadro de extensión explosiva | `assert maquina.estado == "EXTENSION"` |
| 3 | Enviar el cuadro de recojo con el pie aún elevado | `assert resultado["correcto"] is True`; el mensaje contiene `"KIME EXCELENTE"` e `"HIKIASHI: CORRECTO"` |
| 4 | Enviar el cuadro de apoyo final | `assert maquina.estado == "REPOSO"` (lista para la siguiente patada) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED sin excepciones.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-008 — Oclusión prolongada de la extremidad

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-008 |
| **Nombre de la Prueba** | Perder de vista la pierna más allá de la tolerancia aborta la técnica en vez de emitir un diagnóstico inventado |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — evaluar con datos incompletos daría retroalimentación falsa al atleta |
| **Precondiciones** | Máquina de estados en estado `CARGA` (técnica en curso) |
| **Datos de Entrada (Test Data)** | 6 cuadros consecutivos con `visible=False` (tolerancia configurada: 5 cuadros ≈ 165 ms a 30 fps) |
| **Archivo / Clase del Script** | `tests/integration/test_kick_state_machine.py::test_oclusion_prolongada_aborta_la_tecnica` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Llevar la máquina al estado `CARGA` | `maquina.estado == "CARGA"` |
| 2 | Enviar cuadros con `visible=False` dentro de la tolerancia | El estado se conserva y se repite el último diagnóstico |
| 3 | Enviar el cuadro que excede la tolerancia | `assert "TECNICA PERDIDA" in resultado["mensaje"]` |
| 4 | Verificar que no se emite veredicto y la máquina se reinicia | `assert resultado["correcto"] is None` y `assert maquina.estado == "REPOSO"` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso complementario: `test_oclusion_breve_no_interrumpe_la_tecnica`.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-009 — Control de acceso con credenciales inválidas

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-009 |
| **Nombre de la Prueba** | Ninguna credencial incorrecta concede acceso al sistema (RF-08) |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es el control de acceso a los expedientes de los alumnos |
| **Precondiciones** | Base de datos SQLite temporal con un entrenador registrado: `usuario="sholweger"`, `password="clave123"` |
| **Datos de Entrada (Test Data)** | `("sholweger", "clave_incorrecta")`, `("usuario_inexistente", "clave123")`, `("SHOLWEGER", "clave123")`, `("", "")` |
| **Archivo / Clase del Script** | `tests/integration/test_database.py::test_credenciales_invalidas_no_dan_acceso` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear la base temporal y registrar al entrenador | La tabla `entrenador` contiene una fila |
| 2 | Invocar `db.autenticar_entrenador(usuario, password)` con cada par inválido | La consulta se ejecuta sin excepción |
| 3 | Verificar la denegación de acceso | `assert db.autenticar_entrenador(...) is None` |
| 4 | Verificar el camino positivo de control | Con las credenciales correctas devuelve el diccionario del entrenador |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro pares parametrizados.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-010 — Cifrado de contraseñas en reposo (RNF-05)

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-010 |
| **Nombre de la Prueba** | La contraseña se almacena como hash SHA-256, nunca en texto plano |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — requisito no funcional de seguridad verificable automáticamente |
| **Precondiciones** | Base de datos SQLite temporal vacía |
| **Datos de Entrada (Test Data)** | `nombre="Sensei"`, `usuario="sensei"`, `password="MiClaveSecreta"` |
| **Archivo / Clase del Script** | `tests/integration/test_database.py::test_la_contrasena_nunca_se_guarda_en_texto_plano` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Registrar al entrenador con `db.crear_entrenador(...)` | Inserción exitosa |
| 2 | Consultar la fila **cruda** con SQL directo, sin pasar por la API | Se obtiene el campo `password_hash` tal como quedó almacenado |
| 3 | Verificar que no coincide con la contraseña original | `assert fila["password_hash"] != "MiClaveSecreta"` |
| 4 | Verificar el algoritmo y la longitud del digest | `assert fila["password_hash"] == sha256("MiClaveSecreta").hexdigest()` y `len(...) == 64` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-011 — Anti-duplicación de mediciones

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-011 |
| **Nombre de la Prueba** | Treinta cuadros consecutivos con el mismo diagnóstico generan un único registro en la base de datos |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — sin la regla, una sesión de 10 minutos generaría ~18 000 filas idénticas |
| **Precondiciones** | Base temporal con entrenador, atleta y sesión abierta (fixture `sesion_de_prueba`) |
| **Datos de Entrada (Test Data)** | 30 diagnósticos idénticos: `categoria="codo_izq"`, `mensaje="IZQ - TSUKI: EXCELENTE"`, `timestamp_ms = frame * 33` |
| **Archivo / Clase del Script** | `tests/integration/test_medicion_logger.py::test_treinta_frames_identicos_generan_una_sola_fila` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Instanciar `MedicionLogger(db, id_sesion)` | Memoria de últimos mensajes vacía |
| 2 | Invocar `logger.registrar(...)` 30 veces con el mismo mensaje | Cada llamada retorna sin excepción |
| 3 | Consultar `SELECT * FROM tecnica_evaluada WHERE id_sesion = ?` | Se obtiene el conjunto de filas persistidas |
| 4 | Verificar la deduplicación | `assert len(filas) == 1` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso complementario: `test_cada_cambio_real_de_diagnostico_se_registra`.
- **Evidencia de Ejecución:** reporte de consola y XML de pytest.

---

## TC-AUTO-012 — Generación del reporte de progreso

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-012 |
| **Nombre de la Prueba** | El historial de dos sesiones produce un archivo PNG de progreso válido y no vacío |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — es el entregable que el sensei entrega al alumno (RF-07) |
| **Precondiciones** | Base temporal con un entrenador, un atleta y dos sesiones cerradas con mediciones evaluadas |
| **Datos de Entrada (Test Data)** | Sesión 1: 2 de 3 correctas (Tsuki y postura). Sesión 2: 2 de 2 correctas (Tsuki y Mae Geri). Carpeta de salida: directorio temporal |
| **Archivo / Clase del Script** | `tests/integration/test_reportes.py::test_genera_un_png_con_el_historial_de_dos_sesiones` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Poblar la base con dos sesiones de mediciones evaluadas | Las filas quedan asociadas al mismo `id_atleta` |
| 2 | Invocar `generar_reporte_progreso(db, id_atleta, nombre, carpeta)` | Devuelve una ruta de archivo, no `None` |
| 3 | Verificar la existencia y el formato del archivo | `assert os.path.exists(ruta)` y `assert ruta.endswith(".png")` |
| 4 | Verificar que el gráfico no está vacío | `assert os.path.getsize(ruta) > 5000` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso negativo asociado: sin mediciones evaluadas devuelve `None` y no deja archivos basura.
- **Evidencia de Ejecución:** reporte de consola, XML de pytest y el propio PNG generado en el directorio temporal.

---

## TC-AUTO-013 — Flujo E2E: acceso, perfil y apertura de sesión

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-013 |
| **Nombre de la Prueba** | Al elegir un perfil de atleta se abre la pantalla de análisis en vivo y queda registrada una sesión abierta |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es el flujo principal de uso del sistema |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; archivo `pose_landmarker_full.task` presente; entrenador registrado en la base temporal |
| **Datos de Entrada (Test Data)** | Entrenador `usuario="sensei"`, `password="clave123"`; atleta `"Diego Morales"`, grado `"5o kyu"`; cámara sustituida por `CamaraSintetica` (frames 640×480 generados en memoria) |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear la aplicación `App(db)` con la ventana oculta (`withdraw()`) | La pantalla inicial es `LoginScreen` |
| 2 | Disparar `app.on_login_exitoso(entrenador)` | `assert isinstance(app.pantalla_actual, PerfilScreen)` |
| 3 | Navegar a `LiveScreen` inyectando la cámara sintética | `assert isinstance(app.pantalla_actual, LiveScreen)` |
| 4 | Consultar la sesión creada en la base de datos | `assert fila["hora_fin"] is None` (sesión abierta mientras se entrena) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. En entornos sin interfaz gráfica (CI headless) el caso se marca SKIPPED de forma controlada, no FAILED.
- **Evidencia de Ejecución:** reporte de consola de pytest; captura de pantalla manual de la ventana en ejecución local para el expediente.

---

## TC-AUTO-014 — Flujo E2E: cierre de sesión y liberación de hardware

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-014 |
| **Nombre de la Prueba** | Terminar la sesión cierra el registro en la base de datos, libera la cámara y regresa a la selección de perfiles |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — si la cámara no se libera, la siguiente sesión no puede abrirla |
| **Precondiciones** | Las mismas de TC-AUTO-013, con una `LiveScreen` activa |
| **Datos de Entrada (Test Data)** | Instancia de `CamaraSintetica` con bandera `liberada`; atleta `"Diego Morales"` |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_flow.py::test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Abrir `LiveScreen` con la cámara sintética y guardar el `id_sesion` | Sesión abierta en la base de datos |
| 2 | Disparar `app.on_terminar_sesion()` (el mismo manejador del botón "Terminar sesión") | El método se ejecuta sin excepción |
| 3 | Verificar el cierre del registro | `assert fila["hora_fin"] is not None` |
| 4 | Verificar la liberación del hardware y la navegación | `assert camara.liberada is True` y `assert isinstance(app.pantalla_actual, PerfilScreen)` |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. En CI headless se marca SKIPPED de forma controlada.
- **Evidencia de Ejecución:** reporte de consola de pytest y captura de pantalla manual de la ejecución local.

---

## Trazabilidad: casos de prueba contra requisitos y componentes

La numeración de requisitos es la misma del diagrama de clases y del diagrama
de casos de uso del capítulo 3 (`diagramas/3.7.1` y `3.7.3`).

| Caso | Componente bajo prueba | Requisito asociado | Tipo |
|---|---|---|---|
| TC-AUTO-001, 002 | `biomechanics/geometry.py` (`BiomechanicsMath`) | RF-05 — base de cálculo del motor de inferencia | Unitaria |
| TC-AUTO-003 | `biomechanics/filters.py` (`MovingAverageFilter`) | RNF-03 — anti-jitter | Unitaria |
| TC-AUTO-004, 005 | `expert_system/knowledge_base.py` (`KarateRules`) | RF-05 — base de conocimientos | Unitaria |
| TC-AUTO-006 | `expert_system/analyzer.py` (`TechniqueAnalyzer`) | RF-01 / RF-05 — análisis de técnica en tiempo real | Integración |
| TC-AUTO-007, 008 | `expert_system/kick_state_machine.py` | RF-01 / RF-05 — cinemática dinámica de 4 fases | Integración |
| TC-AUTO-009, 010 | `persistence/database.py` (`Database`) | RF-08 — autenticación / RNF-05 — cifrado | Integración |
| TC-AUTO-011 | `persistence/medicion_logger.py` | RF-07 — registro histórico local | Integración |
| TC-AUTO-012 | `persistence/reportes.py` | RF-07 — reportes de progreso | Integración |
| TC-AUTO-013, 014 | `gui/` (flujo completo) | RF-06 — visualización / RNF-04 — ciclo en ≤3 clics | Interfaz (E2E) |
| — (no automatizado) | `vision/tracker.py`, `vision/camera.py` | RF-03 — estimación de pose (dependencia de hardware y del modelo de MediaPipe) | Manual |
| — (fuera de alcance) | `ImuReceiver`, `SensorFusion` | RF-02 / RF-04 — planificados, aún sin implementar | — |
