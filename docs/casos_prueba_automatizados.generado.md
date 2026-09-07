# Casos de prueba automatizados

**Sistema:** Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan
**Generado:** 2026-09-07 04:23:56
**Casos documentados:** 21 de 276 pruebas recolectadas

> **Documento generado automáticamente.** Lo produce el complemento `tests/reporte/plugin.py` a partir de las fichas declaradas en el código con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. No editar a mano: cualquier cambio se pierde en la siguiente corrida. Para modificar una ficha hay que editar la prueba correspondiente.

---

## Resumen

| Nivel | Casos documentados | Pruebas que los ejecutan |
|---|---|---|
| Unitaria | 8 | 28 |
| API/Integración | 10 | 16 |
| Interfaz (UI/E2E) | 3 | 3 |

---

## TC-AUTO-001 — Reconstrucción exacta del ángulo interno de una articulación en todo el rango de movimiento humano

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-001 |
| **Nombre de la Prueba** | Reconstrucción exacta del ángulo interno de una articulación en todo el rango de movimiento humano |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — todo diagnóstico del sistema experto depende de este cálculo |
| **Componente bajo prueba** | `biomechanics/geometry.py (BiomechanicsMath)` |
| **Requisito asociado** | RF-05 |
| **Precondiciones** | Ninguna. `BiomechanicsMath` es una clase de utilidad sin estado ni dependencias externas |
| **Datos de Entrada (Test Data)** | Nueve ángulos conocidos del rango articular: [0, 15, 30, 45, 60, 90, 120, 150, 179], con puntos generados por trigonometría a radio 100 px |
| **Archivo / Clase del Script** | `tests/unit/test_geometry.py::test_reconstruye_cualquier_angulo_del_rango_articular` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Construir los tres puntos A, B, C a partir de un ángulo conocido θ | Coordenadas válidas en el plano de la imagen |
| 2 | Invocar `BiomechanicsMath.calculate_angle(A, B, C)` | Devuelve un valor de tipo `float` |
| 3 | Comparar el resultado contra θ | assert obtenido == pytest.approx(θ, abs=0.01) |
| 4 | Repetir para los nueve ángulos del rango | Los nueve casos parametrizados finalizan en PASSED |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED sin excepciones ni tiempos de espera agotados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-002 — El ángulo devuelto nunca excede 180° aunque los segmentos crucen la discontinuidad de atan2

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-002 |
| **Nombre de la Prueba** | El ángulo devuelto nunca excede 180° aunque los segmentos crucen la discontinuidad de atan2 |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — un ángulo de 340° no entra en ningún umbral y el sistema dejaría de evaluar la técnica |
| **Componente bajo prueba** | `biomechanics/geometry.py (BiomechanicsMath)` |
| **Requisito asociado** | RF-05 |
| **Precondiciones** | Ninguna |
| **Datos de Entrada (Test Data)** | Pares de orientaciones opuestas al corte ±180°: (170°, −170°), (150°, −150°), (−179°, 179°) |
| **Archivo / Clase del Script** | `tests/unit/test_geometry.py::test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Colocar los segmentos proximal y distal a lados opuestos de ±180° | Configuración geométrica que produce un ángulo reflejo interno |
| 2 | Invocar `calculate_angle` | Se ejecuta la rama de normalización `360 − ángulo` |
| 3 | Verificar el ángulo interno equivalente | assert obtenido == pytest.approx(esperado, abs=0.01) |
| 4 | Verificar la invariante global de rango | assert 0.0 <= ángulo <= 180.0 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los tres casos parametrizados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-003 — El filtro de media móvil reduce al menos a la mitad la dispersión del ruido de MediaPipe

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-003 |
| **Nombre de la Prueba** | El filtro de media móvil reduce al menos a la mitad la dispersión del ruido de MediaPipe |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — sin el filtro el diagnóstico parpadea, pero el sistema sigue operando |
| **Componente bajo prueba** | `biomechanics/filters.py (MovingAverageFilter)` |
| **Requisito asociado** | RNF-03 |
| **Precondiciones** | Ninguna |
| **Datos de Entrada (Test Data)** | Serie de 10 mediciones ruidosas alrededor de 170°: [168, 174, 169, 173, 167, 175, 170, 172, 168, 174]; ventana = 5 |
| **Archivo / Clase del Script** | `tests/unit/test_filters.py::test_reduce_la_dispersion_del_ruido` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Instanciar `MovingAverageFilter(window=5)` | Buffer circular vacío |
| 2 | Alimentar las 10 mediciones y recolectar las salidas | Se obtiene una serie suavizada de igual longitud |
| 3 | Calcular la desviación estándar de entrada y de salida | Ambas métricas disponibles |
| 4 | Comparar la dispersión | assert pstdev(salida) < pstdev(entrada) / 2 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Un fallo indica que el suavizado dejó de ser efectivo (ventana mal configurada o buffer sin maxlen)
- **Evidencia de Ejecución:** Reporte de consola de pytest; evidencia visual complementaria en `evidencias/antijitter_*.png` y `evidencias/antijitter_*.csv`.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-004 — Clasificación del golpe recto en las fronteras exactas de 160° y 175°

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-004 |
| **Nombre de la Prueba** | Clasificación del golpe recto en las fronteras exactas de 160° y 175° |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — un falso positivo aprueba una hiperextensión, que es riesgo de lesión articular |
| **Componente bajo prueba** | `expert_system/knowledge_base.py (KarateRules.evaluate_tsuki)` |
| **Requisito asociado** | RF-05 |
| **Precondiciones** | Instancia de `KarateRules()` cargada con los umbrales de literatura |
| **Datos de Entrada (Test Data)** | `elbow_angle` = 159.9 (fuera), 160.0 (frontera inferior), 175.0 (frontera superior), 175.1 (fuera) |
| **Archivo / Clase del Script** | `tests/unit/test_knowledge_base.py::test_tsuki_fronteras_exactas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `reglas.evaluate_tsuki(angulo)` con cada valor límite | Devuelve la tupla `(correcto, mensaje, color)` |
| 2 | Verificar el veredicto en la frontera inferior | assert evaluate_tsuki(160.0)[0] is True y evaluate_tsuki(159.9)[0] is False |
| 3 | Verificar el veredicto en la frontera superior | assert evaluate_tsuki(175.0)[0] is True y evaluate_tsuki(175.1)[0] is False |
| 4 | Verificar el mensaje y el color de cada categoría | "HIPEREXTENDIDO" en rojo (0,0,255); "FLEXIONADO" en amarillo (0,255,255) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro valores límite y en los 11 casos de rango asociados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-005 — La patada frontal exige simultáneamente extensión (Kime ≥ 160°) y explosividad (≥ 400 °/s)

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-005 |
| **Nombre de la Prueba** | La patada frontal exige simultáneamente extensión (Kime ≥ 160°) y explosividad (≥ 400 °/s) |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la regla con dos condiciones acopladas, la más propensa a error lógico |
| **Componente bajo prueba** | `expert_system/knowledge_base.py (KarateRules.evaluate_mae_geri)` |
| **Requisito asociado** | RF-05 |
| **Precondiciones** | Instancia de `KarateRules()` cargada con los umbrales de literatura |
| **Datos de Entrada (Test Data)** | (kime=159.9, vel=400), (160.0, 400.0), (170, 399.9), (170, 400) |
| **Archivo / Clase del Script** | `tests/unit/test_knowledge_base.py::test_mae_geri_fronteras_exactas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `evaluate_mae_geri(kime_angle, velocidad_pico)` | Devuelve `(correcto, mensaje, color)` |
| 2 | Comprobar la frontera de extensión | assert evaluate_mae_geri(160.0, 400.0)[0] is True y (159.9, 400)[0] is False |
| 3 | Comprobar la frontera de velocidad | assert evaluate_mae_geri(170, 400)[0] is True y (170, 399.9)[0] is False |
| 4 | Verificar la precedencia del diagnóstico | Con Kime incompleto el mensaje reporta "KIME INCOMPLETO" aun con velocidad alta, no "EXPLOSIVIDAD" |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro valores límite y en los 7 casos de rango asociados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-006 — El analizador identifica la postura ejecutada antes de evaluarla, a partir de los ángulos de ambas rodillas

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-006 |
| **Nombre de la Prueba** | El analizador identifica la postura ejecutada antes de evaluarla, a partir de los ángulos de ambas rodillas |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — si clasifica mal la postura, aplica la regla equivocada y todo el diagnóstico es inválido |
| **Componente bajo prueba** | `expert_system/analyzer.py (TechniqueAnalyzer)` |
| **Requisito asociado** | RF-01, RF-05 |
| **Precondiciones** | Instancia de `TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)`; pose sintética de 33 landmarks con visibilidad 1.0 |
| **Datos de Entrada (Test Data)** | (izq=175, der=175) → Postura natural; (140, 140) → Kiba Dachi; (100, 170) → Zenkutsu; (110, 100) → Kokutsu. Profundidad z_tobillo_izq=−0.2, z_tobillo_der=0.2 |
| **Archivo / Clase del Script** | `tests/integration/test_analyzer.py::test_identifica_la_postura_antes_de_evaluarla` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Generar la pose sintética con `pose_sintetica(...)` | 33 landmarks con los ángulos de rodilla solicitados (±0.1°) |
| 2 | Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)` | Lista de diagnósticos con la categoría `postura` |
| 3 | Extraer el diagnóstico de la categoría `postura` | El diccionario contiene la clave `mensaje` |
| 4 | Validar la postura detectada | assert "KIBA DACHI" in mensaje (y análogos por cada postura) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en las cuatro posturas parametrizadas
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-007 — Una patada correcta recorre Reposo → Carga → Extensión → Recuperando → Reposo y se califica como correcta

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-007 |
| **Nombre de la Prueba** | Una patada correcta recorre Reposo → Carga → Extensión → Recuperando → Reposo y se califica como correcta |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la única técnica evaluada en movimiento; un error de transición deja al sistema atascado |
| **Componente bajo prueba** | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` |
| **Requisito asociado** | RF-01, RF-05 |
| **Precondiciones** | `MaeGeriStateMachine(ventana_filtro=1)` recién instanciada, con la referencia de "pie en el suelo" registrada (ankle_y = 0.90) |
| **Datos de Entrada (Test Data)** | Secuencia de cuadros a ~30 fps: (175°, y=0.90, t=0), (45°, 0.90, 33 ms), (170°, 0.50, 66 ms), (45°, 0.50, 100 ms), (175°, 0.90, 133 ms) |
| **Archivo / Clase del Script** | `tests/integration/test_kick_state_machine.py::test_ciclo_completo_de_una_patada_correcta` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Enviar el cuadro de pie y luego el de rodilla flexionada | assert maquina.estado == "CARGA" |
| 2 | Enviar el cuadro de extensión explosiva | assert maquina.estado == "EXTENSION" |
| 3 | Enviar el cuadro de recojo con el pie aún elevado | assert resultado["correcto"] is True; el mensaje contiene "KIME EXCELENTE" e "HIKIASHI: CORRECTO" |
| 4 | Enviar el cuadro de apoyo final | assert maquina.estado == "REPOSO" (lista para la siguiente patada) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED sin excepciones
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-008 — Perder de vista la pierna más allá de la tolerancia aborta la técnica en vez de emitir un diagnóstico inventado

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-008 |
| **Nombre de la Prueba** | Perder de vista la pierna más allá de la tolerancia aborta la técnica en vez de emitir un diagnóstico inventado |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — evaluar con datos incompletos daría retroalimentación falsa al atleta |
| **Componente bajo prueba** | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` |
| **Requisito asociado** | RF-01, RF-03 |
| **Precondiciones** | Máquina de estados en estado `CARGA` (técnica en curso) |
| **Datos de Entrada (Test Data)** | 6 cuadros consecutivos con visible=False (tolerancia configurada: 5 cuadros ≈ 165 ms a 30 fps) |
| **Archivo / Clase del Script** | `tests/integration/test_kick_state_machine.py::test_oclusion_prolongada_aborta_la_tecnica` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Llevar la máquina al estado `CARGA` | assert maquina.estado == "CARGA" |
| 2 | Enviar cuadros con visible=False dentro de la tolerancia | El estado se conserva y se repite el último diagnóstico |
| 3 | Enviar el cuadro que excede la tolerancia | assert "TECNICA PERDIDA" in resultado["mensaje"] |
| 4 | Verificar que no se emite veredicto y la máquina se reinicia | assert resultado["correcto"] is None y assert maquina.estado == "REPOSO" |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso complementario: test_oclusion_breve_no_interrumpe_la_tecnica
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-009 — Ninguna credencial incorrecta concede acceso al sistema

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-009 |
| **Nombre de la Prueba** | Ninguna credencial incorrecta concede acceso al sistema |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es el control de acceso a los expedientes de los alumnos |
| **Componente bajo prueba** | `persistence/database.py (Database.autenticar_entrenador)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | Base de datos SQLite temporal con un entrenador registrado: usuario="sholweger", password="clave123" |
| **Datos de Entrada (Test Data)** | ("sholweger", "clave_incorrecta"), ("usuario_inexistente", "clave123"), ("SHOLWEGER", "clave123"), ("", "") |
| **Archivo / Clase del Script** | `tests/integration/test_database.py::test_credenciales_invalidas_no_dan_acceso` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear la base temporal y registrar al entrenador | La tabla `entrenador` contiene una fila |
| 2 | Invocar `db.autenticar_entrenador(usuario, password)` con cada par inválido | La consulta se ejecuta sin excepción |
| 3 | Verificar la denegación de acceso | assert db.autenticar_entrenador(...) is None |
| 4 | Verificar el camino positivo de control | Con las credenciales correctas devuelve el diccionario del entrenador |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los cuatro pares parametrizados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-010 — La contraseña se almacena como hash SHA-256, nunca en texto plano

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-010 |
| **Nombre de la Prueba** | La contraseña se almacena como hash SHA-256, nunca en texto plano |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — requisito no funcional de seguridad verificable automáticamente |
| **Componente bajo prueba** | `persistence/database.py (Database.crear_entrenador)` |
| **Requisito asociado** | RNF-05 |
| **Precondiciones** | Base de datos SQLite temporal vacía |
| **Datos de Entrada (Test Data)** | nombre="Sensei", usuario="sensei", password="MiClaveSecreta" |
| **Archivo / Clase del Script** | `tests/integration/test_database.py::test_la_contrasena_nunca_se_guarda_en_texto_plano` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Registrar al entrenador con `db.crear_entrenador(...)` | Inserción exitosa |
| 2 | Consultar la fila **cruda** con SQL directo, sin pasar por la API | Se obtiene el campo `password_hash` tal como quedó almacenado |
| 3 | Verificar que no coincide con la contraseña original | assert fila["password_hash"] != "MiClaveSecreta" |
| 4 | Verificar el algoritmo y la longitud del digest | assert fila["password_hash"] == sha256("MiClaveSecreta").hexdigest() y len(...) == 64 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-011 — Treinta cuadros consecutivos con el mismo diagnóstico generan un único registro en la base de datos

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-011 |
| **Nombre de la Prueba** | Treinta cuadros consecutivos con el mismo diagnóstico generan un único registro en la base de datos |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — sin la regla, una sesión de 10 minutos generaría ~18 000 filas idénticas |
| **Componente bajo prueba** | `persistence/medicion_logger.py (MedicionLogger)` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | Base temporal con entrenador, atleta y sesión abierta (fixture `sesion_de_prueba`) |
| **Datos de Entrada (Test Data)** | 30 diagnósticos idénticos: categoria="codo_izq", mensaje="IZQ - TSUKI: EXCELENTE", timestamp_ms = frame * 33 |
| **Archivo / Clase del Script** | `tests/integration/test_medicion_logger.py::test_treinta_frames_identicos_generan_una_sola_fila` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Instanciar `MedicionLogger(db, id_sesion)` | Memoria de últimos mensajes vacía |
| 2 | Invocar `logger.registrar(...)` 30 veces con el mismo mensaje | Cada llamada retorna sin excepción |
| 3 | Consultar `SELECT * FROM tecnica_evaluada WHERE id_sesion = ?` | Se obtiene el conjunto de filas persistidas |
| 4 | Verificar la deduplicación | assert len(filas) == 1 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso complementario: test_cada_cambio_real_de_diagnostico_se_registra
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-012 — El historial de dos sesiones produce un archivo PNG de progreso válido y no vacío

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-012 |
| **Nombre de la Prueba** | El historial de dos sesiones produce un archivo PNG de progreso válido y no vacío |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — es el entregable que el sensei entrega al alumno |
| **Componente bajo prueba** | `persistence/reportes.py (generar_reporte_progreso)` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | Base temporal con un entrenador, un atleta y dos sesiones cerradas con mediciones evaluadas; matplotlib instalado |
| **Datos de Entrada (Test Data)** | Sesión 1: 2 de 3 correctas (Tsuki y postura). Sesión 2: 2 de 2 correctas (Tsuki y Mae Geri). Carpeta de salida: directorio temporal |
| **Archivo / Clase del Script** | `tests/integration/test_reportes.py::test_genera_un_png_con_el_historial_de_dos_sesiones` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Poblar la base con dos sesiones de mediciones evaluadas | Las filas quedan asociadas al mismo `id_atleta` |
| 2 | Invocar `generar_reporte_progreso(db, id_atleta, nombre, carpeta)` | Devuelve una ruta de archivo, no `None` |
| 3 | Verificar la existencia y el formato del archivo | assert os.path.exists(ruta) y assert ruta.endswith(".png") |
| 4 | Verificar que el gráfico no está vacío | assert os.path.getsize(ruta) > 5000 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso negativo asociado: sin mediciones evaluadas devuelve None y no deja archivos basura
- **Evidencia de Ejecución:** Reporte de consola, XML de pytest y el propio PNG generado en el directorio temporal de la corrida.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-013 — Al elegir un perfil de atleta se abre la pantalla de análisis en vivo y queda registrada una sesión abierta

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-013 |
| **Nombre de la Prueba** | Al elegir un perfil de atleta se abre la pantalla de análisis en vivo y queda registrada una sesión abierta |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es el flujo principal de uso del sistema |
| **Componente bajo prueba** | `gui/ (App, LoginScreen, PerfilScreen, LiveScreen)` |
| **Requisito asociado** | RF-06, RNF-04 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; archivo `pose_landmarker_full.task` presente; entrenador registrado en la base temporal |
| **Datos de Entrada (Test Data)** | Entrenador usuario="sensei", password="clave123"; atleta "Diego Morales", grado "5o kyu"; cámara sustituida por `CamaraSintetica` (frames 640×480 generados en memoria) |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear la aplicación `App(db)` con la ventana oculta (`withdraw()`) | La pantalla inicial es `LoginScreen` |
| 2 | Disparar `app.on_login_exitoso(entrenador)` | assert isinstance(app.pantalla_actual, PerfilScreen) |
| 3 | Navegar a `LiveScreen` inyectando la cámara sintética | assert isinstance(app.pantalla_actual, LiveScreen) |
| 4 | Consultar la sesión creada en la base de datos | assert fila["hora_fin"] is None (sesión abierta mientras se entrena) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. En entornos sin interfaz gráfica (CI headless) el caso se marca SKIPPED de forma controlada, no FAILED
- **Evidencia de Ejecución:** Reporte de consola de pytest; captura de pantalla manual de la ventana en ejecución local para el expediente.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-014 — Terminar la sesión cierra el registro en la base de datos, libera la cámara y regresa a la selección de perfiles

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-014 |
| **Nombre de la Prueba** | Terminar la sesión cierra el registro en la base de datos, libera la cámara y regresa a la selección de perfiles |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — si la cámara no se libera, la siguiente sesión no puede abrirla |
| **Componente bajo prueba** | `gui/ (App.on_terminar_sesion, LiveScreen)` |
| **Requisito asociado** | RF-06, RF-07 |
| **Precondiciones** | Las mismas de TC-AUTO-013, con una `LiveScreen` activa |
| **Datos de Entrada (Test Data)** | Instancia de `CamaraSintetica` con bandera `liberada`; atleta "Diego Morales" |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_flow.py::test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Abrir `LiveScreen` con la cámara sintética y guardar el `id_sesion` | Sesión abierta en la base de datos |
| 2 | Disparar `app.on_terminar_sesion()` (el mismo manejador del botón "Terminar sesión") | El método se ejecuta sin excepción |
| 3 | Verificar el cierre del registro | assert fila["hora_fin"] is not None |
| 4 | Verificar la liberación del hardware y la navegación | assert camara.liberada is True y assert isinstance(app.pantalla_actual, PerfilScreen) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. En CI headless se marca SKIPPED de forma controlada
- **Evidencia de Ejecución:** Reporte de consola de pytest y captura de pantalla manual de la ejecución local.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-015 — El instrumento que mide la latencia del pipeline cronometra cada etapa por separado con un reloj determinista

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-015 |
| **Nombre de la Prueba** | El instrumento que mide la latencia del pipeline cronometra cada etapa por separado con un reloj determinista |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — es el instrumento con el que se declara el cumplimiento del RNF-01; si mide mal, el resultado reportado en el capítulo 4 no vale |
| **Componente bajo prueba** | `biomechanics/metrics.py (PerformanceMonitor)` |
| **Requisito asociado** | RNF-01, RF-01 |
| **Precondiciones** | `PerformanceMonitor` construido con `descartar_iniciales=0` y un reloj simulado inyectado por parámetro |
| **Datos de Entrada (Test Data)** | Secuencia de lecturas del reloj: iniciar=0.0 s, marcar('pose')=0.010 s, marcar('analisis')=0.035 s, cerrar=0.040 s |
| **Archivo / Clase del Script** | `tests/unit/test_metrics.py::test_mide_cada_etapa_por_separado` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Inyectar el reloj determinista y abrir un fotograma | El monitor no consulta el reloj real del sistema |
| 2 | Marcar las etapas `pose` y `analisis` y cerrar el fotograma | Cada marca queda asociada a su etapa |
| 3 | Consultar `resumen_etapas()` | assert abs(etapas['pose']['media'] - 10.0) < 1e-6 y abs(etapas['analisis']['media'] - 25.0) < 1e-6 |
| 4 | Consultar el total del fotograma | assert abs(resumen_total()['media'] - 40.0) < 1e-6 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La aritmética de las mediciones coincide con los valores conocidos de antemano en milisegundos
- **Evidencia de Ejecución:** Reporte de consola de pytest; medición real del sistema en `evidencias/rendimiento_*.csv` y `evidencias/rendimiento_*.png`.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-016 — Una contraseña equivocada permite reintentar el acceso sin abortar el programa

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-016 |
| **Nombre de la Prueba** | Una contraseña equivocada permite reintentar el acceso sin abortar el programa |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — es el camino de recuperación del acceso por consola; si el bucle aborta, el entrenador queda fuera del sistema tras un error de tecleo |
| **Componente bajo prueba** | `persistence/cli_auth.py (login_o_registro)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | Base temporal con el entrenador `sensei` / `clave123` registrado; `input()` y `getpass()` sustituidos por un guion de respuestas (monkeypatch) |
| **Datos de Entrada (Test Data)** | Guion de teclado: ("sensei", "mala", "r") para el primer intento fallido y el reintento, luego ("sensei", "clave123") |
| **Archivo / Clase del Script** | `tests/integration/test_cli_auth.py::test_reintento_tras_una_contrasena_equivocada` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Cargar el guion de respuestas en el doble de teclado | `input()` y `getpass()` devuelven los valores previstos en orden |
| 2 | Invocar `cli_auth.login_o_registro(db)` | El primer intento es rechazado y el bucle vuelve a pedir las credenciales |
| 3 | Responder "r" (reintentar) y entregar la contraseña correcta | La función retorna en vez de terminar el proceso |
| 4 | Verificar la identidad autenticada | assert entrenador["usuario"] == "sensei" |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El guion se consume por completo: si el programa pidiera más datos de los previstos, el doble de teclado falla la prueba
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-017 — Sin persona detectada, el fotograma se devuelve intacto y no se dibuja ningún esqueleto

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-017 |
| **Nombre de la Prueba** | Sin persona detectada, el fotograma se devuelve intacto y no se dibuja ningún esqueleto |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — dibujar sobre un fotograma sin pose detectada mostraría un esqueleto fantasma al alumno; una excepción aquí congela el video en plena clase |
| **Componente bajo prueba** | `biomechanics/renderer.py (SkeletonRenderer.draw)` |
| **Requisito asociado** | RF-06 |
| **Precondiciones** | OpenCV y NumPy instalados; `SkeletonRenderer()` recién construido |
| **Datos de Entrada (Test Data)** | Lienzo negro de 640×480×3 (`np.zeros`, dtype uint8) y lista de poses igual a `None` |
| **Archivo / Clase del Script** | `tests/integration/test_renderer.py::test_sin_persona_detectada_el_video_se_devuelve_intacto` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Construir el lienzo en negro | Cualquier píxel distinto de cero será algo que se dibujó |
| 2 | Invocar `renderer.draw(frame, None)` | Retorna sin lanzar excepción |
| 3 | Verificar que no se copió ni sustituyó el fotograma | assert resultado is frame_negro |
| 4 | Verificar que no se pintó nada | assert resultado.sum() == 0 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Caso complementario: test_dibuja_el_esqueleto_cuando_hay_pose comprueba el camino positivo
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-018 — Recalibrar un umbral crea una versión nueva y conserva la anterior en el historial

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-018 |
| **Nombre de la Prueba** | Recalibrar un umbral crea una versión nueva y conserva la anterior en el historial |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — si la recalibración sobrescribiera el umbral, las mediciones antiguas quedarían juzgadas por un criterio que ya no existe y el reporte de progreso dejaría de ser trazable |
| **Componente bajo prueba** | `persistence/database.py (actualizar_umbral, historial_umbral)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | Base temporal con los umbrales de literatura ya sembrados (fixture `db_sembrada`) |
| **Datos de Entrada (Test Data)** | Umbral `kokutsu_dachi` / `rodilla_frontal` recalibrado a 95-125 con fuente `modelado_experto` |
| **Archivo / Clase del Script** | `tests/integration/test_umbrales.py::test_recalibrar_crea_version_nueva_sin_borrar_la_anterior` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Leer el umbral vigente antes de recalibrar | Se obtiene su `id_umbral` original |
| 2 | Invocar `actualizar_umbral(...)` con los valores nuevos | assert id_nuevo != original["id_umbral"] (fila nueva, no sobrescritura) |
| 3 | Consultar `historial_umbral(tecnica, articulacion)` | assert len(historial) == 2 |
| 4 | Verificar cuál versión quedó vigente | Exactamente una fila del historial tiene `vigente` verdadero y es la nueva |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Es la garantía de trazabilidad que sostiene el requisito de umbrales parametrizados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-019 — Una ficha incompleta es rechazada y el error enumera todos los campos que incumplen el formato

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-019 |
| **Nombre de la Prueba** | Una ficha incompleta es rechazada y el error enumera todos los campos que incumplen el formato |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — si la plantilla aceptara fichas incompletas, el documento de casos se vería impecable y estaría vacío por dentro |
| **Componente bajo prueba** | `tests/reporte/plantilla.py (FichaCasoPrueba)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | Ninguna. La ficha se construye directamente, sin pasar por el decorador ni por el registro global |
| **Datos de Entrada (Test Data)** | Ficha válida con tres campos corrompidos a la vez: id_caso="MALO", nombre="corto", requisitos="X-1" |
| **Archivo / Clase del Script** | `tests/unit/test_plantilla_reporte.py::test_el_error_enumera_todos_los_problemas_de_una_vez` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Construir la ficha con los tres campos inválidos | Se lanza `FichaInvalida` en el momento de la construcción |
| 2 | Inspeccionar la lista de problemas del error | assert len(error.value.problemas) >= 3 |
| 3 | Verificar que el mensaje nombra cada campo incumplido | El texto del error menciona id_caso, nombre y requisitos |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La validación es acumulativa: quien escribe una ficha ve de una sola vez todo lo que le falta
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-020 — El formulario de calibración rechaza todo rango imposible antes de escribirlo en la base de datos

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-020 |
| **Nombre de la Prueba** | El formulario de calibración rechaza todo rango imposible antes de escribirlo en la base de datos |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — un umbral invertido o fuera del rango articular medible haría que una técnica no pueda aprobarse nunca, y el atleta recibiría correcciones imposibles de satisfacer sin que nada delate el error |
| **Componente bajo prueba** | `gui/validacion_umbrales.py (interpretar_rango)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | Ninguna. `interpretar_rango` es una función pura, sin estado ni dependencias de la interfaz gráfica |
| **Datos de Entrada (Test Data)** | Cinco rangos inválidos: mínimo vacío, mínimo no numérico, máximo menor que el mínimo (175–160), valor negativo (-5) y ángulo de 200° (fuera del rango articular de 0–180°) |
| **Archivo / Clase del Script** | `tests/unit/test_validacion_umbrales.py::test_rechaza_los_rangos_imposibles` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `interpretar_rango(texto_min, texto_max)` con cada rango inválido | assert se levanta `ValorInvalido` en los cinco casos |
| 2 | Leer el mensaje de la excepción | assert el fragmento esperado aparece en el mensaje (indica al entrenador cuál campo corregir, no un rastro técnico) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Ningún rango inválido llega a `Database.actualizar_umbral`, de modo que no se crea una versión de umbral inservible
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-021 — Recalibrar un umbral desde la interfaz cambia el criterio con el que el sistema experto evalúa, sin modificar el código fuente

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-021 |
| **Nombre de la Prueba** | Recalibrar un umbral desde la interfaz cambia el criterio con el que el sistema experto evalúa, sin modificar el código fuente |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la única vía por la que un instructor puede ajustar el criterio técnico del sistema; si la pantalla no escribe en la base de datos, el RF-08 queda sostenido solo por código que nadie del dojo puede ejecutar |
| **Componente bajo prueba** | `gui/umbrales_screen.py (UmbralesScreen) + persistence/database.py (actualizar_umbral)` |
| **Requisito asociado** | RF-08 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; entrenador autenticado; umbrales de literatura ya sembrados por `App` al arrancar |
| **Datos de Entrada (Test Data)** | Umbral `tsuki` / `codo`, vigente en 160–175°, editado a 170–175° desde el formulario; ángulo de prueba 165°, correcto con el criterio anterior |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_umbrales.py::test_recalibrar_cambia_el_criterio_del_sistema_experto` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Autenticarse y abrir la pantalla con `_abrir_umbrales()` (el manejador del botón real) | assert isinstance(app.pantalla_actual, UmbralesScreen) |
| 2 | Escribir 170 en el campo del mínimo y disparar `_guardar_cambios()` | assert guardados == 1 (se escribe solo el umbral modificado) |
| 3 | Releer los umbrales vigentes y construir `KarateRules` con ellos | assert reglas.evaluate_tsuki(165)[0] is False (165° ya no aprueba) |
| 4 | Consultar `historial_umbral('tsuki', 'codo')` | assert len(historial) == 2 y la versión vigente quedó firmada por el entrenador que la guardó |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El criterio nuevo rige la siguiente sesión de análisis y la versión anterior permanece en el historial, de modo que las mediciones ya registradas siguen siendo interpretables
- **Evidencia de Ejecución:** Reporte de consola de pytest; captura de pantalla de la pantalla de calibración para el expediente.
- **Resultado Obtenido en la última corrida:** PASSED

---

## Trazabilidad: casos de prueba contra requisitos y componentes

| Caso | Componente bajo prueba | Requisito asociado | Tipo |
|---|---|---|---|
| TC-AUTO-001 | `biomechanics/geometry.py (BiomechanicsMath)` | RF-05 | Unitaria |
| TC-AUTO-002 | `biomechanics/geometry.py (BiomechanicsMath)` | RF-05 | Unitaria |
| TC-AUTO-003 | `biomechanics/filters.py (MovingAverageFilter)` | RNF-03 | Unitaria |
| TC-AUTO-004 | `expert_system/knowledge_base.py (KarateRules.evaluate_tsuki)` | RF-05 | Unitaria |
| TC-AUTO-005 | `expert_system/knowledge_base.py (KarateRules.evaluate_mae_geri)` | RF-05 | Unitaria |
| TC-AUTO-006 | `expert_system/analyzer.py (TechniqueAnalyzer)` | RF-01, RF-05 | API/Integración |
| TC-AUTO-007 | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` | RF-01, RF-05 | API/Integración |
| TC-AUTO-008 | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` | RF-01, RF-03 | API/Integración |
| TC-AUTO-009 | `persistence/database.py (Database.autenticar_entrenador)` | RF-08 | API/Integración |
| TC-AUTO-010 | `persistence/database.py (Database.crear_entrenador)` | RNF-05 | API/Integración |
| TC-AUTO-011 | `persistence/medicion_logger.py (MedicionLogger)` | RF-07 | API/Integración |
| TC-AUTO-012 | `persistence/reportes.py (generar_reporte_progreso)` | RF-07 | API/Integración |
| TC-AUTO-013 | `gui/ (App, LoginScreen, PerfilScreen, LiveScreen)` | RF-06, RNF-04 | Interfaz (UI/E2E) |
| TC-AUTO-014 | `gui/ (App.on_terminar_sesion, LiveScreen)` | RF-06, RF-07 | Interfaz (UI/E2E) |
| TC-AUTO-015 | `biomechanics/metrics.py (PerformanceMonitor)` | RNF-01, RF-01 | Unitaria |
| TC-AUTO-016 | `persistence/cli_auth.py (login_o_registro)` | RF-08 | API/Integración |
| TC-AUTO-017 | `biomechanics/renderer.py (SkeletonRenderer.draw)` | RF-06 | API/Integración |
| TC-AUTO-018 | `persistence/database.py (actualizar_umbral, historial_umbral)` | RF-08 | API/Integración |
| TC-AUTO-019 | `tests/reporte/plantilla.py (FichaCasoPrueba)` | RF-08 | Unitaria |
| TC-AUTO-020 | `gui/validacion_umbrales.py (interpretar_rango)` | RF-08 | Unitaria |
| TC-AUTO-021 | `gui/umbrales_screen.py (UmbralesScreen) + persistence/database.py (actualizar_umbral)` | RF-08 | Interfaz (UI/E2E) |
