# Casos de prueba automatizados

**Sistema:** Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan
**Casos documentados:** 38

> **Documento generado automáticamente.** Lo produce el complemento `tests/reporte/plugin.py` a partir de las fichas declaradas en el código con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. No editar a mano: cualquier cambio se pierde en la siguiente corrida. Para modificar una ficha hay que editar la prueba correspondiente.

---

## Resumen

| Nivel | Casos documentados | Pruebas que los ejecutan |
|---|---|---|
| Unitaria | 16 | 40 |
| API/Integración | 14 | 24 |
| Interfaz (UI/E2E) | 8 | 16 |

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
| **Datos de Entrada (Test Data)** | (izq=175, der=175) → Postura natural; (140, 140) → Kiba Dachi; (100, 170) → Zenkutsu (peso adelante); (165, 105) → Kokutsu (peso atrás). Profundidad z_tobillo_izq=−0.2, z_tobillo_der=0.2 |
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

## TC-AUTO-013 — Al abrir el análisis en vivo con un alumno elegido queda registrada una sesión abierta a su nombre

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-013 |
| **Nombre de la Prueba** | Al abrir el análisis en vivo con un alumno elegido queda registrada una sesión abierta a su nombre |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es el flujo principal de uso del sistema |
| **Componente bajo prueba** | `gui/ (App, LoginScreen, InicioScreen, LiveScreen)` |
| **Requisito asociado** | RF-06, RNF-04 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; archivo `pose_landmarker_full.task` presente; entrenador registrado en la base temporal |
| **Datos de Entrada (Test Data)** | Entrenador usuario="sensei", password="clave123"; atleta "Diego Morales", grado "5o kyu"; cámara sustituida por `CamaraSintetica` (frames 640×480 generados en memoria) |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear la aplicación `App(db)` con la ventana oculta (`withdraw()`) | La pantalla inicial es `LoginScreen` |
| 2 | Disparar `app.on_login_exitoso(entrenador)` | assert isinstance(app.pantalla_actual, InicioScreen) |
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
| 4 | Verificar la liberación del hardware y la navegación | assert camara.liberada is True y assert isinstance(app.pantalla_actual, InicioScreen) |

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

## TC-AUTO-022 — La fuente de video elegida se verifica antes de guardarse y sobrevive al reinicio del sistema

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-022 |
| **Nombre de la Prueba** | La fuente de video elegida se verifica antes de guardarse y sobrevive al reinicio del sistema |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — con el índice de cámara escrito en el código, el sistema fallaba en silencio en cualquier equipo distinto al de desarrollo: la ventana quedaba en negro sin informar la causa, que es el peor escenario posible durante una demostración en vivo |
| **Componente bajo prueba** | `gui/camara_screen.py (CamaraScreen) + persistence/database.py (guardar_config)` |
| **Requisito asociado** | RF-01 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; entrenador autenticado; dispositivos de captura sustituidos por dobles de prueba |
| **Datos de Entrada (Test Data)** | Dos cámaras simuladas (índices 0 y 1); se selecciona el índice 1 |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_camara.py::test_la_fuente_elegida_se_verifica_y_persiste` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Autenticarse y abrir la pantalla con `_abrir_camara()` (el manejador del botón real) | assert isinstance(app.pantalla_actual, CamaraScreen) |
| 2 | Seleccionar la cámara de índice 1 y disparar `guardar_seleccion()` | assert guardado is True (la fuente entregó un fotograma verificable) |
| 3 | Consultar la preferencia almacenada en la base de datos | assert db.leer_config('fuente_video') == '1' |
| 4 | Resolver la fuente como lo hace la pantalla de análisis al abrirse | assert fuente_configurada(db) == '1' |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La fuente queda configurada solo después de comprobar que entrega imagen, y la pantalla de análisis la reutiliza sin que el entrenador vuelva a elegirla
- **Evidencia de Ejecución:** Reporte de consola de pytest; captura de la pantalla de cámara para el expediente.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-023 — Un índice de cámara escrito como texto se convierte a entero antes de llegar a OpenCV

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-023 |
| **Nombre de la Prueba** | Un índice de cámara escrito como texto se convierte a entero antes de llegar a OpenCV |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — OpenCV distingue por tipo: con el entero 2 abre la tercera cámara del equipo, pero con la cadena "2" busca un archivo de video llamado "2". Como el valor llega desde un formulario de la interfaz, siempre viene en texto, y sin la conversión el sistema nunca abriría la cámara seleccionada |
| **Componente bajo prueba** | `vision/camera.py (normalizar)` |
| **Requisito asociado** | RF-01 |
| **Precondiciones** | Ninguna. `normalizar` es una función pura que no abre dispositivos |
| **Datos de Entrada (Test Data)** | Cuatro fuentes locales: los enteros 0 y 2, y las cadenas "0" y "2" |
| **Archivo / Clase del Script** | `tests/unit/test_fuentes_video.py::test_los_indices_se_convierten_a_entero` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `normalizar(entrada)` con cada una de las cuatro fuentes | assert resultado == esperado en los cuatro casos |
| 2 | Verificar el tipo del valor devuelto | assert isinstance(resultado, int) — nunca una cadena |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Las direcciones de cámara IP, en cambio, se conservan como texto: es el tipo con el que OpenCV las interpreta como flujo de red
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-024 — La fuente de video configurada persiste entre ejecuciones del sistema

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-024 |
| **Nombre de la Prueba** | La fuente de video configurada persiste entre ejecuciones del sistema |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — si la preferencia no sobreviviera al reinicio, configurar la cámara dejaría de ser una tarea de instalación y pasaría a ser un paso que el entrenador repite cada sesión, en contra del ciclo de uso breve que exige el RNF-04 |
| **Componente bajo prueba** | `persistence/database.py (guardar_config, leer_config)` |
| **Requisito asociado** | RF-01 |
| **Precondiciones** | Archivo de base de datos temporal; sin preferencias previas |
| **Datos de Entrada (Test Data)** | Fuente de video `http://192.168.1.50:8080/video` (cámara IP del dojo) |
| **Archivo / Clase del Script** | `tests/integration/test_configuracion.py::test_la_preferencia_sobrevive_al_reinicio_del_sistema` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Abrir la base, guardar la fuente con `guardar_config` y cerrar la conexión | La escritura se confirma sin excepción |
| 2 | Abrir de nuevo el MISMO archivo, como ocurre al reiniciar el programa | assert leer_config('fuente_video') devuelve la dirección íntegra |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La preferencia vive en el mismo archivo SQLite que el resto del estado del dojo, de modo que un respaldo la incluye
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-025 — Un Kokutsu Dachi correctamente ejecutado se reconoce como tal y no como una transición entre posturas

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-025 |
| **Nombre de la Prueba** | Un Kokutsu Dachi correctamente ejecutado se reconoce como tal y no como una transición entre posturas |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es una prueba de regresión de un defecto real: el clasificador exigía la rodilla frontal flexionada para reconocer un Kokutsu, cuando en esa postura el peso va atrás y la frontal queda casi extendida. Toda ejecución correcta caía en la rama por defecto y se reportaba como "EN TRANSICION", de modo que una de las posturas del alcance no se evaluaba nunca y nada lo delataba |
| **Componente bajo prueba** | `expert_system/analyzer.py (clasificador de posturas)` |
| **Requisito asociado** | RF-01, RF-05 |
| **Precondiciones** | Instancia de `TechniqueAnalyzer(ventana_filtro=1)`; poses sintéticas de 33 landmarks con visibilidad 1.0 |
| **Datos de Entrada (Test Data)** | Cinco ejecuciones con la pierna frontal extendida y la trasera flexionada: (170, 100), (165, 105), (160, 110), (155, 115) y (150, 120) |
| **Archivo / Clase del Script** | `tests/integration/test_analyzer.py::test_un_kokutsu_real_no_se_confunde_con_una_transicion` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Generar la pose sintética con la pierna izquierda adelante (z_tobillo_izq < z_tobillo_der) | 33 landmarks con los ángulos de rodilla solicitados |
| 2 | Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)` | assert "KOKUTSU" in mensaje en las cinco ejecuciones |
| 3 | Comprobar que no se reportó como movimiento | assert "TRANSICION" not in mensaje y assert "MOVIENDOSE" not in mensaje |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Con el clasificador anterior las cinco ejecuciones fallaban, por lo que esta prueba impide que la corrección se revierta
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-026 — La precisión de un alumno se calcula solo sobre evaluaciones cerradas, ignorando los estados transitorios

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-026 |
| **Nombre de la Prueba** | La precisión de un alumno se calcula solo sobre evaluaciones cerradas, ignorando los estados transitorios |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — durante una sesión el sistema emite muchos diagnósticos sin veredicto ("EN TRANSICION", "MAE GERI: CARGA", articulación no visible). Contarlos como fallos hundiría el porcentaje de cualquier alumno por el solo hecho de haberse movido frente a la cámara, y el instructor tomaría decisiones de entrenamiento sobre una cifra falsa |
| **Componente bajo prueba** | `persistence/database.py (resumen_atletas)` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | Base temporal con un atleta que acumula 4 evaluaciones correctas, 3 incorrectas y 1 estado transitorio sin veredicto |
| **Datos de Entrada (Test Data)** | Sesión 1: dos tsukis correctos, uno hiperextendido y un "EN TRANSICION". Sesión 2: dos tsukis correctos y dos posturas incorrectas |
| **Archivo / Clase del Script** | `tests/integration/test_consultas_progreso.py::test_la_precision_ignora_los_estados_transitorios` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `resumen_atletas()` | assert el atleta aparece con sesiones == 2 |
| 2 | Verificar el denominador del porcentaje | assert evaluaciones == 7, no 8: el estado transitorio queda fuera |
| 3 | Verificar el porcentaje calculado | assert precision == pytest.approx(4 / 7 * 100) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Un alumno sin mediciones aparece con precisión None y no con 0 %, porque "sin datos" y "falla todo" son afirmaciones distintas
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-027 — El reporte de progreso de un atleta se genera desde la interfaz y produce un archivo de imagen válido

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-027 |
| **Nombre de la Prueba** | El reporte de progreso de un atleta se genera desde la interfaz y produce un archivo de imagen válido |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — el módulo de reportes funcionaba y estaba probado, pero no se invocaba desde ninguna pantalla ni desde la consola: era código inalcanzable para el usuario. El diagrama de casos de uso, en cambio, declaraba la función como implementada, de modo que el sistema prometía algo que nadie podía ejecutar |
| **Componente bajo prueba** | `gui/alumno_screen.py (AlumnoScreen) + persistence/reportes.py` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV, Pillow y Matplotlib instalados; entorno gráfico disponible; atleta con una sesión cerrada que dejó evaluaciones con veredicto |
| **Datos de Entrada (Test Data)** | Atleta "Diego Morales" con una sesión de 3 evaluaciones cerradas (1 correcta, 2 incorrectas) y 1 estado transitorio |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_historial.py::test_el_reporte_de_progreso_se_genera_desde_la_pantalla` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Navegar alumnos → perfil del alumno con `on_abrir_alumno(id)` | assert isinstance(app.pantalla_actual, AlumnoScreen) |
| 2 | Disparar `generar_reporte()` (el manejador del botón real) | assert ruta is not None — se produjo un archivo |
| 3 | Verificar el archivo en disco | assert el archivo existe y su tamaño es mayor que cero |
| 4 | Leer el mensaje mostrado al instructor | assert la ruta del reporte aparece en el texto de estado de la pantalla |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Si el atleta no tiene evaluaciones cerradas, no se genera un archivo vacío: se explica por qué todavía no hay nada que graficar
- **Evidencia de Ejecución:** Reporte de consola de pytest y el PNG de progreso generado durante la corrida.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-028 — Ejecutar el programa sin argumentos abre la interfaz gráfica, no la versión de terminal

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-028 |
| **Nombre de la Prueba** | Ejecutar el programa sin argumentos abre la interfaz gráfica, no la versión de terminal |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — `python main.py` es lo primero que ejecuta cualquiera que reciba el proyecto. Mientras ese comando abría la versión de consola, el usuario terminaba en un formulario de terminal y concluía que el sistema no tenía interfaz gráfica, cuando sí la tiene |
| **Componente bajo prueba** | `main.py (main)` |
| **Requisito asociado** | RNF-04 |
| **Precondiciones** | Las dos funciones de arranque se sustituyen por dobles; no se abre ninguna ventana ni se toca la cámara |
| **Datos de Entrada (Test Data)** | Línea de comandos vacía, y la variante `--consola` |
| **Archivo / Clase del Script** | `tests/unit/test_punto_de_entrada.py::test_la_linea_de_comandos_elige_la_via_correcta` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Invocar `main.main()` con argv sin argumentos | assert se eligió la vía gráfica y no la de consola |
| 2 | Invocar `main.main()` con argv = ['--consola'] | assert se eligió la vía de consola |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Ambas vías comparten el mismo motor de análisis; solo cambia cómo se presentan los resultados
- **Evidencia de Ejecución:** Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) publicado como artefacto en GitHub Actions.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-029 — El panel de inicio cuenta la actividad reciente del dojo y descarta la anterior a la ventana de siete días

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-029 |
| **Nombre de la Prueba** | El panel de inicio cuenta la actividad reciente del dojo y descarta la anterior a la ventana de siete días |
| **Tipo de Prueba** | [ ] Unitaria **[X]** API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la primera cifra que el instructor ve al abrir el sistema y la que usará para decidir cómo va la semana; si la ventana no filtra, el número crece para siempre y deja de significar «actividad reciente», convirtiendo el panel en un contador histórico disfrazado |
| **Componente bajo prueba** | `persistence/database.py (metricas_dojo)` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | Base de datos limpia con un entrenador y dos alumnos registrados |
| **Datos de Entrada (Test Data)** | Tres sesiones fechadas a 1, 3 y 20 días atrás; la de 20 días queda fuera de la ventana de siete. Seis evaluaciones cerradas dentro de la ventana, cuatro correctas |
| **Archivo / Clase del Script** | `tests/integration/test_panel_inicio.py::test_la_ventana_de_actividad_deja_fuera_las_sesiones_viejas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Crear las tres sesiones y reescribir su fecha hacia el pasado | assert las tres existen en la tabla `sesion` |
| 2 | Registrar mediciones cerradas solo en las dos sesiones recientes | assert se guardaron con `correcto` no nulo |
| 3 | Invocar `metricas_dojo()` con la ventana por defecto | assert metricas['sesiones'] == 2 (la de 20 días no cuenta) |
| 4 | Comprobar alumnos activos y precisión | assert metricas['alumnos_activos'] == 1 y metricas['precision'] == pytest.approx(66.67) |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El panel refleja la actividad de los últimos siete días y la precisión se calcula solo sobre evaluaciones cerradas de ese periodo.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-030 — El panel de correcciones no repite una corrección que sigue vigente, de modo que la retroalimentación en pantalla conserve solo lo que cambió

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-030 |
| **Nombre de la Prueba** | El panel de correcciones no repite una corrección que sigue vigente, de modo que la retroalimentación en pantalla conserve solo lo que cambió |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — el análisis corre a unos 30 fotogramas por segundo y el mismo diagnóstico se repite en decenas consecutivos; sin el filtro, un solo error sostenido durante un segundo llena la lista con treinta copias idénticas y empuja fuera de pantalla las demás correcciones, incumpliendo de fondo el RF-06 aunque el panel se dibuje |
| **Componente bajo prueba** | `gui/panel_vivo.py (FeedCorrecciones)` |
| **Requisito asociado** | RF-05, RF-06 |
| **Precondiciones** | Feed recién creado, sin correcciones previas |
| **Datos de Entrada (Test Data)** | Treinta fotogramas con el mismo diagnóstico incorrecto de codo; luego un diagnóstico distinto; luego el primero otra vez |
| **Archivo / Clase del Script** | `tests/unit/test_panel_vivo.py::test_una_correccion_vigente_no_se_vuelve_a_anotar` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Registrar el mismo diagnóstico incorrecto en 30 fotogramas seguidos | assert len(feed.entradas) == 1 |
| 2 | Registrar un diagnóstico distinto de la misma articulación | assert len(feed.entradas) == 2 y el más reciente queda primero |
| 3 | Volver a registrar el diagnóstico original | assert len(feed.entradas) == 3 (la recaída sí es información nueva) |
| 4 | Registrar 20 correcciones distintas con un tope de 8 | assert len(feed.entradas) == 8 y conserva las más recientes |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El panel muestra la secuencia de correcciones reales del alumno y no la frecuencia de muestreo de la cámara.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-031 — Un grado numérico escrito bajo un color de cinta que no lo admite se descarta al guardar, en vez de producir una ficha que se contradice

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-031 |
| **Nombre de la Prueba** | Un grado numérico escrito bajo un color de cinta que no lo admite se descarta al guardar, en vez de producir una ficha que se contradice |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — el campo de grado aparece y desaparece según el color elegido, de modo que un sensei que escribe «1er kyu» y después corrige la cinta a «Blanca» deja un valor huérfano en el formulario; guardarlo registraría a un principiante como alumno avanzado y ese dato alimenta después las estadísticas por grado |
| **Componente bajo prueba** | `gui/registro_alumno.py (interpretar_formulario)` |
| **Requisito asociado** | RF-07 |
| **Precondiciones** | Ninguna; la función es pura y no toca la base de datos |
| **Datos de Entrada (Test Data)** | Formulario con nombre «Marta Similox», color de cinta «Blanca» y grado «1er kyu» remanente de una selección anterior |
| **Archivo / Clase del Script** | `tests/unit/test_registro_alumno.py::test_un_grado_huerfano_no_se_guarda` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Interpretar el formulario con cinta Café y grado «1er kyu» | assert datos['grado_cinturon'] == '1er kyu' (el café sí admite grado) |
| 2 | Interpretar el mismo formulario cambiando la cinta a «Blanca» | assert datos['grado_cinturon'] is None (el grado se descarta) |
| 3 | Comprobar que el resto de la ficha se conserva intacto | assert datos['nombre'] == 'Marta Similox' y datos['color_cinta'] == 'Blanca' |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La ficha guardada nunca afirma un grado que su color de cinta contradice.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-032 — Elegir un perfil de sensei exige su contraseña y no da acceso con un solo clic

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-032 |
| **Nombre de la Prueba** | Elegir un perfil de sensei exige su contraseña y no da acceso con un solo clic |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — la pantalla se parece a un selector de perfiles al estilo Netflix, donde elegir una tarjeta entra sin más; si aquí se comportara igual, sería una puerta trasera al inicio de sesión —cualquiera operaría como el sensei principal con un clic— y dejaría sin valor el hash SHA-256 del RNF-05, además de falsear la firma que queda en cada umbral recalibrado y en cada sesión registrada |
| **Componente bajo prueba** | `gui/perfil_screen.py (PerfilScreen) + persistence/database.py (autenticar_entrenador)` |
| **Requisito asociado** | RF-08, RNF-05 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; un sensei registrado con usuario «sensei» y contraseña «clave123» |
| **Datos de Entrada (Test Data)** | Tarjeta del sensei registrado; primero una contraseña equivocada («incorrecta»), después la correcta («clave123») |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_inicio.py::test_cambiar_de_perfil_pide_la_contrasena_del_sensei` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Abrir la selección de perfiles con `on_cambiar_perfil()` | assert isinstance(app.pantalla_actual, PerfilScreen) y app.barra is None |
| 2 | Pulsar la tarjeta del sensei sin escribir contraseña y disparar `_entrar()` | assert la aplicación sigue en PerfilScreen |
| 3 | Escribir una contraseña equivocada y disparar `_entrar()` | assert 'Contraseña incorrecta' en el mensaje de error y no se entró |
| 4 | Escribir la contraseña correcta y disparar `_entrar()` | assert isinstance(app.pantalla_actual, InicioScreen) y app.entrenador quedó fijado |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Cambiar de perfil pasa siempre por la verificación de credenciales, de modo que la firma de cada medición corresponde a quien realmente la tomó.
- **Evidencia de Ejecución:** Reporte de consola de pytest; captura de pantalla de la selección de perfiles.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-033 — El video se ajusta al espacio disponible conservando su proporción, en vez de imponer su resolución al resto de la pantalla

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-033 |
| **Nombre de la Prueba** | El video se ajusta al espacio disponible conservando su proporción, en vez de imponer su resolución al resto de la pantalla |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — una cámara entrega 1280x720 y el fotograma se dibujaba a tamaño nativo, de modo que empujaba al panel derecho —donde viven las correcciones del sistema experto— hasta reducirlo a 193 px de los 320 que pide, recortando el texto de cada corrección; en un equipo con pantalla pequeña el panel quedaría fuera de cuadro y el RF-06 dejaría de cumplirse en la práctica |
| **Componente bajo prueba** | `gui/live_screen.py (_escalar, _mostrar_frame)` |
| **Requisito asociado** | RF-01, RF-06 |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; cámara sustituida por `CamaraSintetica` |
| **Datos de Entrada (Test Data)** | Huecos de 560x420 y 300x300 contra fotogramas de 1280x720 y 640x480 |
| **Archivo / Clase del Script** | `tests/e2e/test_gui_vivo.py::test_el_video_se_ajusta_al_hueco_sin_deformarse` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Calcular el tamaño de un fotograma 1280x720 en un hueco de arranque | assert el resultado cabe en el hueco y conserva la proporción 16:9 |
| 2 | Comprobar que un fotograma más alto que ancho también se limita por el alto | assert alto <= hueco disponible |
| 3 | Verificar que la proporción original se conserva en ambos casos | assert ancho/alto se mantiene dentro de un 1 % del original |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El panel de correcciones conserva su ancho y los ángulos se ven sin deformar, que es condición para que lo mostrado corresponda a lo medido.
- **Evidencia de Ejecución:** Reporte de consola de pytest; captura de pantalla del análisis en vivo.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-034 — Todo veredicto que la base de conocimientos puede emitir tiene su corrección redactada para el alumno

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-034 |
| **Nombre de la Prueba** | Todo veredicto que la base de conocimientos puede emitir tiene su corrección redactada para el alumno |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — el panel de correcciones es la forma en que el sistema cumple el RF-06; si se agrega una regla nueva y se olvida su traducción, la pantalla no falla —muestra el texto técnico— y el descuido pasa inadvertido hasta que un instructor lee «MAE GERI: KIME INCOMPLETO» en medio de una clase y tiene que interpretarlo él |
| **Componente bajo prueba** | `gui/coaching.py (CORRECCIONES) + expert_system/knowledge_base.py` |
| **Requisito asociado** | RF-05, RF-06 |
| **Precondiciones** | Ninguna; se inspecciona el código fuente de la base de conocimientos |
| **Datos de Entrada (Test Data)** | Los veredictos que `knowledge_base.py` devuelve en sus sentencias `return` |
| **Archivo / Clase del Script** | `tests/unit/test_coaching.py::test_ningun_veredicto_del_motor_se_queda_sin_correccion` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Extraer de la base de conocimientos todos los veredictos que puede emitir | assert la lista no viene vacía (si lo estuviera, la prueba no probaría nada) |
| 2 | Restarle los veredictos que la tabla de correcciones cubre | assert el conjunto resultante está vacío |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. Cada veredicto llega al alumno como una instrucción y no como lenguaje de máquina.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-035 — Una cámara sin nombre se omite de la lista en vez de desplazar a las siguientes, de modo que ningún dispositivo quede etiquetado con el nombre de otro

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-035 |
| **Nombre de la Prueba** | Una cámara sin nombre se omite de la lista en vez de desplazar a las siguientes, de modo que ningún dispositivo quede etiquetado con el nombre de otro |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | [ ] Alta **[X]** Media [ ] Baja — la posición en la lista ES el índice del dispositivo, así que un hueco correría a todas las cámaras posteriores y el entrenador elegiría la webcam integrada creyendo que elige la cámara del tatami; una etiqueta equivocada es peor que no tener etiqueta, porque induce a confiar en ella |
| **Componente bajo prueba** | `vision/nombres_camara.py (analizar_salida_macos)` |
| **Requisito asociado** | RF-01 |
| **Precondiciones** | Ninguna; la función es pura y no consulta el sistema operativo |
| **Datos de Entrada (Test Data)** | Respuesta de `system_profiler` con dos entradas, la primera sin campo `_name` ni `spcamera_model-id` |
| **Archivo / Clase del Script** | `tests/unit/test_nombres_camara.py::test_una_camara_sin_nombre_se_omite_en_vez_de_correr_las_demas` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Analizar la salida con la primera entrada incompleta | assert el resultado contiene solo el nombre de la segunda cámara |
| 2 | Comprobar que no se insertó un marcador de posición | assert len(nombres) == 1, no 2 |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. La cámara sin nombre se muestra por su índice y las demás conservan el suyo.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-036 — La asimetría entre lados solo se reporta cuando hay repeticiones suficientes en ambos, de modo que un fallo aislado no se presente como señal de lesión

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-036 |
| **Nombre de la Prueba** | La asimetría entre lados solo se reporta cuando hay repeticiones suficientes en ambos, de modo que un fallo aislado no se presente como señal de lesión |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — con tres repeticiones por lado un solo fallo mueve el porcentaje 33 puntos, de modo que casi cualquier sesión corta produciría una «asimetría marcada»; un instructor que recibe esa alerta cambia el entrenamiento de un alumno sano, y si la alerta salta siempre deja de creerle también cuando es real |
| **Componente bajo prueba** | `expert_system/riesgos.py (evaluar_asimetria)` |
| **Requisito asociado** | RF-05, RF-07 |
| **Precondiciones** | Ninguna; la función es pura y no consulta la base de datos |
| **Datos de Entrada (Test Data)** | Lado izquierdo con 3 evaluaciones al 33 % y derecho con 3 al 100 % (67 puntos de diferencia, por debajo del mínimo de repeticiones); después los mismos porcentajes con 12 evaluaciones por lado |
| **Archivo / Clase del Script** | `tests/unit/test_riesgos.py::test_la_asimetria_exige_repeticiones_suficientes_en_ambos_lados` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Evaluar la asimetría con 3 repeticiones por lado | assert el resultado es None pese a los 67 puntos de diferencia |
| 2 | Evaluar los mismos porcentajes con 12 repeticiones por lado | assert se reporta un hallazgo de nivel 'riesgo' |
| 3 | Comprobar que el hallazgo nombra el lado rezagado | assert 'izquierdo' aparece en el título |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED. El sistema se pronuncia sobre asimetría solo cuando la muestra lo respalda, y nombra qué lado trabajar.
- **Evidencia de Ejecución:** Reporte de consola de pytest.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-037 — Ninguna tarea principal del sistema cuesta más de tres pulsaciones

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-037 |
| **Nombre de la Prueba** | Ninguna tarea principal del sistema cuesta más de tres pulsaciones |
| **Tipo de Prueba** | **[X]** Unitaria [ ] API/Integración [ ] Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — es la verificación directa del RNF-04; sin ella el requisito se daba por cumplido sin haber contado nunca las pulsaciones reales |
| **Componente bajo prueba** | `gui/navegacion.py (RUTAS, exceden_el_limite)` |
| **Requisito asociado** | RNF-04 |
| **Precondiciones** | Ninguna: el mapa de navegación es un módulo sin dependencias gráficas |
| **Datos de Entrada (Test Data)** | Las nueve rutas declaradas en `gui.navegacion.RUTAS`, cada una con la secuencia de controles que hay que pulsar desde el panel de inicio |
| **Archivo / Clase del Script** | `tests/unit/test_navegacion.py::test_ninguna_tarea_pasa_de_tres_pulsaciones` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Contar los pasos de cada ruta declarada | Cada ruta tiene entre 1 y 3 pasos |
| 2 | Invocar `exceden_el_limite(RUTAS, limite=3)` | assert resultado == [] (ninguna tarea supera el límite) |
| 3 | Invocar el mismo verificador sobre una ruta artificial de cuatro pasos | assert la ruta aparece en el resultado: el verificador sí detecta un incumplimiento, de modo que el resultado vacío anterior no es vacuo |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED en los dos entornos, con y sin interfaz gráfica
- **Evidencia de Ejecución:** Reporte de consola de pytest y documento de casos generado con `--reporte-formal`.
- **Resultado Obtenido en la última corrida:** PASSED

---

## TC-AUTO-038 — Cada tarea principal se completa pulsando los controles reales de la interfaz, en no más de tres pulsaciones desde el panel de inicio

| Campo | Descripción / Detalle |
|---|---|
| **ID del Caso de Prueba** | TC-AUTO-038 |
| **Nombre de la Prueba** | Cada tarea principal se completa pulsando los controles reales de la interfaz, en no más de tres pulsaciones desde el panel de inicio |
| **Tipo de Prueba** | [ ] Unitaria [ ] API/Integración **[X]** Interfaz (UI/E2E) [ ] Desempeño |
| **Prioridad / Riesgo** | **[X]** Alta [ ] Media [ ] Baja — verifica el RNF-04 sobre la interfaz construida y no sobre una declaración: una pantalla intermedia o un botón renombrado rompen el recorrido y quedan a la vista |
| **Componente bajo prueba** | `gui/ (App, BarraLateral y las nueve pantallas), gui/navegacion.py` |
| **Requisito asociado** | RNF-04 |
| **Precondiciones** | CustomTkinter, OpenCV, MediaPipe, Pillow y Matplotlib instalados; entorno gráfico disponible; sensei autenticado; un alumno con una sesión cerrada en la base temporal |
| **Datos de Entrada (Test Data)** | Las nueve rutas de `gui.navegacion.RUTAS`; sensei "Sensei Ejemplo" (clave123, rol principal); alumno "Diego Morales" con 2 evaluaciones cerradas; cámara y enumeración de dispositivos sustituidas por dobles |
| **Archivo / Clase del Script** | `tests/e2e/test_navegacion_rnf04.py::test_cada_tarea_principal_se_completa_en_tres_pulsaciones` |

**Pasos de Ejecución Automatizada y Aserciones**

| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |
|---|---|---|
| 1 | Situar la aplicación en el panel de inicio con el sensei autenticado | assert la pantalla actual es `InicioScreen` |
| 2 | Para cada ruta, buscar en el árbol de widgets el control que declara cada paso y activarlo (botón, desplegable, casilla o tarjeta) | Cada control existe en ese punto del recorrido; si no, el fallo nombra el control buscado y lista los botones disponibles |
| 3 | Contar las pulsaciones dadas | assert pulsaciones <= 3 |
| 4 | Comprobar dónde terminó el recorrido | assert la pantalla actual es la que la ruta declara como destino |

**Criterios de Salida y Manejo de Errores**
- **Resultado Esperado Global:** PASSED para las nueve rutas. En entornos sin interfaz gráfica (CI headless) el caso se marca SKIPPED de forma controlada, no FAILED
- **Evidencia de Ejecución:** Reporte de consola de pytest, con una línea por tarea auditada.
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
| TC-AUTO-013 | `gui/ (App, LoginScreen, InicioScreen, LiveScreen)` | RF-06, RNF-04 | Interfaz (UI/E2E) |
| TC-AUTO-014 | `gui/ (App.on_terminar_sesion, LiveScreen)` | RF-06, RF-07 | Interfaz (UI/E2E) |
| TC-AUTO-015 | `biomechanics/metrics.py (PerformanceMonitor)` | RNF-01, RF-01 | Unitaria |
| TC-AUTO-016 | `persistence/cli_auth.py (login_o_registro)` | RF-08 | API/Integración |
| TC-AUTO-017 | `biomechanics/renderer.py (SkeletonRenderer.draw)` | RF-06 | API/Integración |
| TC-AUTO-018 | `persistence/database.py (actualizar_umbral, historial_umbral)` | RF-08 | API/Integración |
| TC-AUTO-019 | `tests/reporte/plantilla.py (FichaCasoPrueba)` | RF-08 | Unitaria |
| TC-AUTO-020 | `gui/validacion_umbrales.py (interpretar_rango)` | RF-08 | Unitaria |
| TC-AUTO-021 | `gui/umbrales_screen.py (UmbralesScreen) + persistence/database.py (actualizar_umbral)` | RF-08 | Interfaz (UI/E2E) |
| TC-AUTO-022 | `gui/camara_screen.py (CamaraScreen) + persistence/database.py (guardar_config)` | RF-01 | Interfaz (UI/E2E) |
| TC-AUTO-023 | `vision/camera.py (normalizar)` | RF-01 | Unitaria |
| TC-AUTO-024 | `persistence/database.py (guardar_config, leer_config)` | RF-01 | API/Integración |
| TC-AUTO-025 | `expert_system/analyzer.py (clasificador de posturas)` | RF-01, RF-05 | API/Integración |
| TC-AUTO-026 | `persistence/database.py (resumen_atletas)` | RF-07 | API/Integración |
| TC-AUTO-027 | `gui/alumno_screen.py (AlumnoScreen) + persistence/reportes.py` | RF-07 | Interfaz (UI/E2E) |
| TC-AUTO-028 | `main.py (main)` | RNF-04 | Unitaria |
| TC-AUTO-029 | `persistence/database.py (metricas_dojo)` | RF-07 | API/Integración |
| TC-AUTO-030 | `gui/panel_vivo.py (FeedCorrecciones)` | RF-05, RF-06 | Unitaria |
| TC-AUTO-031 | `gui/registro_alumno.py (interpretar_formulario)` | RF-07 | Unitaria |
| TC-AUTO-032 | `gui/perfil_screen.py (PerfilScreen) + persistence/database.py (autenticar_entrenador)` | RF-08, RNF-05 | Interfaz (UI/E2E) |
| TC-AUTO-033 | `gui/live_screen.py (_escalar, _mostrar_frame)` | RF-01, RF-06 | Interfaz (UI/E2E) |
| TC-AUTO-034 | `gui/coaching.py (CORRECCIONES) + expert_system/knowledge_base.py` | RF-05, RF-06 | Unitaria |
| TC-AUTO-035 | `vision/nombres_camara.py (analizar_salida_macos)` | RF-01 | Unitaria |
| TC-AUTO-036 | `expert_system/riesgos.py (evaluar_asimetria)` | RF-05, RF-07 | Unitaria |
| TC-AUTO-037 | `gui/navegacion.py (RUTAS, exceden_el_limite)` | RNF-04 | Unitaria |
| TC-AUTO-038 | `gui/ (App, BarraLateral y las nueve pantallas), gui/navegacion.py` | RNF-04 | Interfaz (UI/E2E) |
