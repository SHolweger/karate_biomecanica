# Plan de pruebas — Shotokan AI

Sistema experto de análisis biomecánico del Karate-Do Shotokan.

> **Documento generado.** Lo produce `plan_de_pruebas.py` leyendo las fichas
> `@ficha(...)` declaradas junto a cada prueba. No editar a mano: para cambiar
> un caso hay que editar su prueba, que es lo que garantiza que el plan y lo
> que se ejecuta no se separen.

## Cómo se ejecuta todo

```bash
python3 -m pytest -q                              # la suite completa
python3 -m pytest --exigir-fichas --reporte-formal   # lo que corre CI
```

La suite completa **solo corre entera en un equipo con pantalla y cámara**.
Sin entorno gráfico, los diez módulos de `tests/e2e/` se omiten solos: sus
casos aparecen aquí marcados como «Con pantalla y cámara» y hay que
planificarlos como sesión presencial.

## Resumen

**Casos formales documentados:** 62

| Tipo | Casos |
|---|---|
| E2e | 13 |
| Integracion | 20 |
| Unitaria | 29 |

| Prioridad | Casos |
|---|---|
| Alta | 47 |
| Media | 15 |

**Requieren pantalla y cámara:** 13 de 62

---

## Catálogo

### TC-AUTO-001 — Reconstrucción exacta del ángulo interno de una articulación en todo el rango de movimiento humano

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `biomechanics/geometry.py (BiomechanicsMath)` |
| **Requisito** | RF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. `BiomechanicsMath` es una clase de utilidad sin estado ni dependencias externas |
| **Datos de entrada** | Nueve ángulos conocidos del rango articular: [0, 15, 30, 45, 60, 90, 120, 150, 179], con puntos generados por trigonometría a radio 100 px |

**Por qué existe este caso:** todo diagnóstico del sistema experto depende de este cálculo.

**Comando**

```bash
python3 -m pytest "tests/unit/test_geometry.py::test_reconstruye_cualquier_angulo_del_rango_articular" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Construir los tres puntos A, B, C a partir de un ángulo conocido θ | Coordenadas válidas en el plano de la imagen |
| 2 | Invocar `BiomechanicsMath.calculate_angle(A, B, C)` | Devuelve un valor de tipo `float` |
| 3 | Comparar el resultado contra θ | assert obtenido == pytest.approx(θ, abs=0.01) |
| 4 | Repetir para los nueve ángulos del rango | Los nueve casos parametrizados finalizan en PASSED |

**Criterio de aceptación:** PASSED sin excepciones ni tiempos de espera agotados

---

### TC-AUTO-002 — El ángulo devuelto nunca excede 180° aunque los segmentos crucen la discontinuidad de atan2

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `biomechanics/geometry.py (BiomechanicsMath)` |
| **Requisito** | RF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna |
| **Datos de entrada** | Pares de orientaciones opuestas al corte ±180°: (170°, −170°), (150°, −150°), (−179°, 179°) |

**Por qué existe este caso:** un ángulo de 340° no entra en ningún umbral y el sistema dejaría de evaluar la técnica.

**Comando**

```bash
python3 -m pytest "tests/unit/test_geometry.py::test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Colocar los segmentos proximal y distal a lados opuestos de ±180° | Configuración geométrica que produce un ángulo reflejo interno |
| 2 | Invocar `calculate_angle` | Se ejecuta la rama de normalización `360 − ángulo` |
| 3 | Verificar el ángulo interno equivalente | assert obtenido == pytest.approx(esperado, abs=0.01) |
| 4 | Verificar la invariante global de rango | assert 0.0 <= ángulo <= 180.0 |

**Criterio de aceptación:** PASSED en los tres casos parametrizados

---

### TC-AUTO-003 — El filtro de media móvil reduce al menos a la mitad la dispersión del ruido de MediaPipe

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `biomechanics/filters.py (MovingAverageFilter)` |
| **Requisito** | RNF-03 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna |
| **Datos de entrada** | Serie de 10 mediciones ruidosas alrededor de 170°: [168, 174, 169, 173, 167, 175, 170, 172, 168, 174]; ventana = 5 |

**Por qué existe este caso:** sin el filtro el diagnóstico parpadea, pero el sistema sigue operando.

**Comando**

```bash
python3 -m pytest "tests/unit/test_filters.py::test_reduce_la_dispersion_del_ruido" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Instanciar `MovingAverageFilter(window=5)` | Buffer circular vacío |
| 2 | Alimentar las 10 mediciones y recolectar las salidas | Se obtiene una serie suavizada de igual longitud |
| 3 | Calcular la desviación estándar de entrada y de salida | Ambas métricas disponibles |
| 4 | Comparar la dispersión | assert pstdev(salida) < pstdev(entrada) / 2 |

**Criterio de aceptación:** PASSED. Un fallo indica que el suavizado dejó de ser efectivo (ventana mal configurada o buffer sin maxlen)

---

### TC-AUTO-004 — Clasificación del golpe recto en las fronteras exactas de 160° y 175°

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/knowledge_base.py (KarateRules.evaluate_tsuki)` |
| **Requisito** | RF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Instancia de `KarateRules()` cargada con los umbrales de literatura |
| **Datos de entrada** | `elbow_angle` = 159.9 (fuera), 160.0 (frontera inferior), 175.0 (frontera superior), 175.1 (fuera) |

**Por qué existe este caso:** un falso positivo aprueba una hiperextensión, que es riesgo de lesión articular.

**Comando**

```bash
python3 -m pytest "tests/unit/test_knowledge_base.py::test_tsuki_fronteras_exactas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `reglas.evaluate_tsuki(angulo)` con cada valor límite | Devuelve la tupla `(correcto, mensaje, color)` |
| 2 | Verificar el veredicto en la frontera inferior | assert evaluate_tsuki(160.0)[0] is True y evaluate_tsuki(159.9)[0] is False |
| 3 | Verificar el veredicto en la frontera superior | assert evaluate_tsuki(175.0)[0] is True y evaluate_tsuki(175.1)[0] is False |
| 4 | Verificar el mensaje y el color de cada categoría | "HIPEREXTENDIDO" en rojo (0,0,255); "FLEXIONADO" en amarillo (0,255,255) |

**Criterio de aceptación:** PASSED en los cuatro valores límite y en los 11 casos de rango asociados

---

### TC-AUTO-005 — La patada frontal exige simultáneamente extensión (Kime ≥ 160°) y explosividad (≥ 400 °/s)

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/knowledge_base.py (KarateRules.evaluate_mae_geri)` |
| **Requisito** | RF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Instancia de `KarateRules()` cargada con los umbrales de literatura |
| **Datos de entrada** | (kime=159.9, vel=400), (160.0, 400.0), (170, 399.9), (170, 400) |

**Por qué existe este caso:** es la regla con dos condiciones acopladas, la más propensa a error lógico.

**Comando**

```bash
python3 -m pytest "tests/unit/test_knowledge_base.py::test_mae_geri_fronteras_exactas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `evaluate_mae_geri(kime_angle, velocidad_pico)` | Devuelve `(correcto, mensaje, color)` |
| 2 | Comprobar la frontera de extensión | assert evaluate_mae_geri(160.0, 400.0)[0] is True y (159.9, 400)[0] is False |
| 3 | Comprobar la frontera de velocidad | assert evaluate_mae_geri(170, 400)[0] is True y (170, 399.9)[0] is False |
| 4 | Verificar la precedencia del diagnóstico | Con Kime incompleto el mensaje reporta "KIME INCOMPLETO" aun con velocidad alta, no "EXPLOSIVIDAD" |

**Criterio de aceptación:** PASSED en los cuatro valores límite y en los 7 casos de rango asociados

---

### TC-AUTO-006 — El analizador identifica la postura ejecutada antes de evaluarla, a partir de los ángulos de ambas rodillas

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py (TechniqueAnalyzer)` |
| **Requisito** | ['RF-01', 'RF-05'] |
| **Entorno** | Cualquiera |
| **Precondiciones** | Instancia de `TechniqueAnalyzer(umbral_visibilidad=0.65, ventana_filtro=1)`; pose sintética de 33 landmarks con visibilidad 1.0 |
| **Datos de entrada** | (izq=175, der=175) → Postura natural; (140, 140) → Kiba Dachi; (100, 170) → Zenkutsu (peso adelante); (165, 105) → Kokutsu (peso atrás). Profundidad z_tobillo_izq=−0.2, z_tobillo_der=0.2 |

**Por qué existe este caso:** si clasifica mal la postura, aplica la regla equivocada y todo el diagnóstico es inválido.

**Comando**

```bash
python3 -m pytest "tests/integration/test_analyzer.py::test_identifica_la_postura_antes_de_evaluarla" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Generar la pose sintética con `pose_sintetica(...)` | 33 landmarks con los ángulos de rodilla solicitados (±0.1°) |
| 2 | Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)` | Lista de diagnósticos con la categoría `postura` |
| 3 | Extraer el diagnóstico de la categoría `postura` | El diccionario contiene la clave `mensaje` |
| 4 | Validar la postura detectada | assert "KIBA DACHI" in mensaje (y análogos por cada postura) |

**Criterio de aceptación:** PASSED en las cuatro posturas parametrizadas

---

### TC-AUTO-007 — Una patada correcta recorre Reposo → Carga → Extensión → Recuperando → Reposo y se califica como correcta

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` |
| **Requisito** | ['RF-01', 'RF-05'] |
| **Entorno** | Cualquiera |
| **Precondiciones** | `MaeGeriStateMachine(ventana_filtro=1)` recién instanciada, con la referencia de "pie en el suelo" registrada (ankle_y = 0.90) |
| **Datos de entrada** | Secuencia de cuadros a ~30 fps: (175°, y=0.90, t=0), (45°, 0.90, 33 ms), (170°, 0.50, 66 ms), (45°, 0.50, 100 ms), (175°, 0.90, 133 ms) |

**Por qué existe este caso:** es la única técnica evaluada en movimiento; un error de transición deja al sistema atascado.

**Comando**

```bash
python3 -m pytest "tests/integration/test_kick_state_machine.py::test_ciclo_completo_de_una_patada_correcta" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Enviar el cuadro de pie y luego el de rodilla flexionada | assert maquina.estado == "CARGA" |
| 2 | Enviar el cuadro de extensión explosiva | assert maquina.estado == "EXTENSION" |
| 3 | Enviar el cuadro de recojo con el pie aún elevado | assert resultado["correcto"] is True; el mensaje contiene "KIME EXCELENTE" e "HIKIASHI: CORRECTO" |
| 4 | Enviar el cuadro de apoyo final | assert maquina.estado == "REPOSO" (lista para la siguiente patada) |

**Criterio de aceptación:** PASSED sin excepciones

---

### TC-AUTO-008 — Perder de vista la pierna más allá de la tolerancia aborta la técnica en vez de emitir un diagnóstico inventado

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/kick_state_machine.py (MaeGeriStateMachine)` |
| **Requisito** | ['RF-01', 'RF-03'] |
| **Entorno** | Cualquiera |
| **Precondiciones** | Máquina de estados en estado `CARGA` (técnica en curso) |
| **Datos de entrada** | 6 cuadros consecutivos con visible=False (tolerancia configurada: 5 cuadros ≈ 165 ms a 30 fps) |

**Por qué existe este caso:** evaluar con datos incompletos daría retroalimentación falsa al atleta.

**Comando**

```bash
python3 -m pytest "tests/integration/test_kick_state_machine.py::test_oclusion_prolongada_aborta_la_tecnica" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Llevar la máquina al estado `CARGA` | assert maquina.estado == "CARGA" |
| 2 | Enviar cuadros con visible=False dentro de la tolerancia | El estado se conserva y se repite el último diagnóstico |
| 3 | Enviar el cuadro que excede la tolerancia | assert "TECNICA PERDIDA" in resultado["mensaje"] |
| 4 | Verificar que no se emite veredicto y la máquina se reinicia | assert resultado["correcto"] is None y assert maquina.estado == "REPOSO" |

**Criterio de aceptación:** PASSED. Caso complementario: test_oclusion_breve_no_interrumpe_la_tecnica

---

### TC-AUTO-009 — Ninguna credencial incorrecta concede acceso al sistema

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `persistence/database.py (Database.autenticar_entrenador)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base de datos SQLite temporal con un entrenador registrado: usuario="sholweger", password="clave123" |
| **Datos de entrada** | ("sholweger", "clave_incorrecta"), ("usuario_inexistente", "clave123"), ("SHOLWEGER", "clave123"), ("", "") |

**Por qué existe este caso:** es el control de acceso a los expedientes de los alumnos.

**Comando**

```bash
python3 -m pytest "tests/integration/test_database.py::test_credenciales_invalidas_no_dan_acceso" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Crear la base temporal y registrar al entrenador | La tabla `entrenador` contiene una fila |
| 2 | Invocar `db.autenticar_entrenador(usuario, password)` con cada par inválido | La consulta se ejecuta sin excepción |
| 3 | Verificar la denegación de acceso | assert db.autenticar_entrenador(...) is None |
| 4 | Verificar el camino positivo de control | Con las credenciales correctas devuelve el diccionario del entrenador |

**Criterio de aceptación:** PASSED en los cuatro pares parametrizados

---

### TC-AUTO-010 — La contraseña se almacena como hash SHA-256, nunca en texto plano

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `persistence/database.py (Database.crear_entrenador)` |
| **Requisito** | RNF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base de datos SQLite temporal vacía |
| **Datos de entrada** | nombre="Sensei", usuario="sensei", password="MiClaveSecreta" |

**Por qué existe este caso:** requisito no funcional de seguridad verificable automáticamente.

**Comando**

```bash
python3 -m pytest "tests/integration/test_database.py::test_la_contrasena_nunca_se_guarda_en_texto_plano" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Registrar al entrenador con `db.crear_entrenador(...)` | Inserción exitosa |
| 2 | Consultar la fila **cruda** con SQL directo, sin pasar por la API | Se obtiene el campo `password_hash` tal como quedó almacenado |
| 3 | Verificar que no coincide con la contraseña original | assert fila["password_hash"] != "MiClaveSecreta" |
| 4 | Verificar el algoritmo y la longitud del digest | assert fila["password_hash"] == sha256("MiClaveSecreta").hexdigest() y len(...) == 64 |

**Criterio de aceptación:** PASSED

---

### TC-AUTO-011 — Treinta cuadros consecutivos con el mismo diagnóstico generan un único registro en la base de datos

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Media |
| **Componente** | `persistence/medicion_logger.py (MedicionLogger)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con entrenador, atleta y sesión abierta (fixture `sesion_de_prueba`) |
| **Datos de entrada** | 30 diagnósticos idénticos: categoria="codo_izq", mensaje="IZQ - TSUKI: EXCELENTE", timestamp_ms = frame * 33 |

**Por qué existe este caso:** sin la regla, una sesión de 10 minutos generaría ~18 000 filas idénticas.

**Comando**

```bash
python3 -m pytest "tests/integration/test_medicion_logger.py::test_treinta_frames_identicos_generan_una_sola_fila" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Instanciar `MedicionLogger(db, id_sesion)` | Memoria de últimos mensajes vacía |
| 2 | Invocar `logger.registrar(...)` 30 veces con el mismo mensaje | Cada llamada retorna sin excepción |
| 3 | Consultar `SELECT * FROM tecnica_evaluada WHERE id_sesion = ?` | Se obtiene el conjunto de filas persistidas |
| 4 | Verificar la deduplicación | assert len(filas) == 1 |

**Criterio de aceptación:** PASSED. Caso complementario: test_cada_cambio_real_de_diagnostico_se_registra

---

### TC-AUTO-012 — El historial de dos sesiones produce un archivo PNG de progreso válido y no vacío

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Media |
| **Componente** | `persistence/reportes.py (generar_reporte_progreso)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con un entrenador, un atleta y dos sesiones cerradas con mediciones evaluadas; matplotlib instalado |
| **Datos de entrada** | Sesión 1: 2 de 3 correctas (Tsuki y postura). Sesión 2: 2 de 2 correctas (Tsuki y Mae Geri). Carpeta de salida: directorio temporal |

**Por qué existe este caso:** es el entregable que el sensei entrega al alumno.

**Comando**

```bash
python3 -m pytest "tests/integration/test_reportes.py::test_genera_un_png_con_el_historial_de_dos_sesiones" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Poblar la base con dos sesiones de mediciones evaluadas | Las filas quedan asociadas al mismo `id_atleta` |
| 2 | Invocar `generar_reporte_progreso(db, id_atleta, nombre, carpeta)` | Devuelve una ruta de archivo, no `None` |
| 3 | Verificar la existencia y el formato del archivo | assert os.path.exists(ruta) y assert ruta.endswith(".png") |
| 4 | Verificar que el gráfico no está vacío | assert os.path.getsize(ruta) > 5000 |

**Criterio de aceptación:** PASSED. Caso negativo asociado: sin mediciones evaluadas devuelve None y no deja archivos basura

---

### TC-AUTO-013 — Al abrir el análisis en vivo con un alumno elegido queda registrada una sesión abierta a su nombre

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/ (App, LoginScreen, InicioScreen, LiveScreen)` |
| **Requisito** | ['RF-06', 'RNF-04'] |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; archivo `pose_landmarker_full.task` presente; entrenador registrado en la base temporal |
| **Datos de entrada** | Entrenador usuario="sensei", password="clave123"; atleta "Diego Morales", grado "5o kyu"; cámara sustituida por `CamaraSintetica` (frames 640×480 generados en memoria) |

**Por qué existe este caso:** es el flujo principal de uso del sistema.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Crear la aplicación `App(db)` con la ventana oculta (`withdraw()`) | La pantalla inicial es `LoginScreen` |
| 2 | Disparar `app.on_login_exitoso(entrenador)` | assert isinstance(app.pantalla_actual, InicioScreen) |
| 3 | Navegar a `LiveScreen` inyectando la cámara sintética | assert isinstance(app.pantalla_actual, LiveScreen) |
| 4 | Consultar la sesión creada en la base de datos | assert fila["hora_fin"] is None (sesión abierta mientras se entrena) |

**Criterio de aceptación:** PASSED. En entornos sin interfaz gráfica (CI headless) el caso se marca SKIPPED de forma controlada, no FAILED

---

### TC-AUTO-014 — Terminar la sesión cierra el registro en la base de datos, libera la cámara y regresa a la selección de perfiles

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/ (App.on_terminar_sesion, LiveScreen)` |
| **Requisito** | ['RF-06', 'RF-07'] |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | Las mismas de TC-AUTO-013, con una `LiveScreen` activa |
| **Datos de entrada** | Instancia de `CamaraSintetica` con bandera `liberada`; atleta "Diego Morales" |

**Por qué existe este caso:** si la cámara no se libera, la siguiente sesión no puede abrirla.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_flow.py::test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Abrir `LiveScreen` con la cámara sintética y guardar el `id_sesion` | Sesión abierta en la base de datos |
| 2 | Disparar `app.on_terminar_sesion()` (el mismo manejador del botón "Terminar sesión") | El método se ejecuta sin excepción |
| 3 | Verificar el cierre del registro | assert fila["hora_fin"] is not None |
| 4 | Verificar la liberación del hardware y la navegación | assert camara.liberada is True y assert isinstance(app.pantalla_actual, InicioScreen) |

**Criterio de aceptación:** PASSED. En CI headless se marca SKIPPED de forma controlada

---

### TC-AUTO-015 — El instrumento que mide la latencia del pipeline cronometra cada etapa por separado con un reloj determinista

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `biomechanics/metrics.py (PerformanceMonitor)` |
| **Requisito** | ['RNF-01', 'RF-01'] |
| **Entorno** | Cualquiera |
| **Precondiciones** | `PerformanceMonitor` construido con `descartar_iniciales=0` y un reloj simulado inyectado por parámetro |
| **Datos de entrada** | Secuencia de lecturas del reloj: iniciar=0.0 s, marcar('pose')=0.010 s, marcar('analisis')=0.035 s, cerrar=0.040 s |

**Por qué existe este caso:** es el instrumento con el que se declara el cumplimiento del RNF-01; si mide mal, el resultado reportado en el capítulo 4 no vale.

**Comando**

```bash
python3 -m pytest "tests/unit/test_metrics.py::test_mide_cada_etapa_por_separado" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Inyectar el reloj determinista y abrir un fotograma | El monitor no consulta el reloj real del sistema |
| 2 | Marcar las etapas `pose` y `analisis` y cerrar el fotograma | Cada marca queda asociada a su etapa |
| 3 | Consultar `resumen_etapas()` | assert abs(etapas['pose']['media'] - 10.0) < 1e-6 y abs(etapas['analisis']['media'] - 25.0) < 1e-6 |
| 4 | Consultar el total del fotograma | assert abs(resumen_total()['media'] - 40.0) < 1e-6 |

**Criterio de aceptación:** PASSED. La aritmética de las mediciones coincide con los valores conocidos de antemano en milisegundos

---

### TC-AUTO-016 — Una contraseña equivocada permite reintentar el acceso sin abortar el programa

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Media |
| **Componente** | `persistence/cli_auth.py (login_o_registro)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con el entrenador `sensei` / `clave123` registrado; `input()` y `getpass()` sustituidos por un guion de respuestas (monkeypatch) |
| **Datos de entrada** | Guion de teclado: ("sensei", "mala", "r") para el primer intento fallido y el reintento, luego ("sensei", "clave123") |

**Por qué existe este caso:** es el camino de recuperación del acceso por consola; si el bucle aborta, el entrenador queda fuera del sistema tras un error de tecleo.

**Comando**

```bash
python3 -m pytest "tests/integration/test_cli_auth.py::test_reintento_tras_una_contrasena_equivocada" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Cargar el guion de respuestas en el doble de teclado | `input()` y `getpass()` devuelven los valores previstos en orden |
| 2 | Invocar `cli_auth.login_o_registro(db)` | El primer intento es rechazado y el bucle vuelve a pedir las credenciales |
| 3 | Responder "r" (reintentar) y entregar la contraseña correcta | La función retorna en vez de terminar el proceso |
| 4 | Verificar la identidad autenticada | assert entrenador["usuario"] == "sensei" |

**Criterio de aceptación:** PASSED. El guion se consume por completo: si el programa pidiera más datos de los previstos, el doble de teclado falla la prueba

---

### TC-AUTO-017 — Sin persona detectada, el fotograma se devuelve intacto y no se dibuja ningún esqueleto

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Media |
| **Componente** | `biomechanics/renderer.py (SkeletonRenderer.draw)` |
| **Requisito** | RF-06 |
| **Entorno** | Cualquiera |
| **Precondiciones** | OpenCV y NumPy instalados; `SkeletonRenderer()` recién construido |
| **Datos de entrada** | Lienzo negro de 640×480×3 (`np.zeros`, dtype uint8) y lista de poses igual a `None` |

**Por qué existe este caso:** dibujar sobre un fotograma sin pose detectada mostraría un esqueleto fantasma al alumno; una excepción aquí congela el video en plena clase.

**Comando**

```bash
python3 -m pytest "tests/integration/test_renderer.py::test_sin_persona_detectada_el_video_se_devuelve_intacto" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Construir el lienzo en negro | Cualquier píxel distinto de cero será algo que se dibujó |
| 2 | Invocar `renderer.draw(frame, None)` | Retorna sin lanzar excepción |
| 3 | Verificar que no se copió ni sustituyó el fotograma | assert resultado is frame_negro |
| 4 | Verificar que no se pintó nada | assert resultado.sum() == 0 |

**Criterio de aceptación:** PASSED. Caso complementario: test_dibuja_el_esqueleto_cuando_hay_pose comprueba el camino positivo

---

### TC-AUTO-018 — Recalibrar un umbral crea una versión nueva y conserva la anterior en el historial

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `persistence/database.py (actualizar_umbral, historial_umbral)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con los umbrales de literatura ya sembrados (fixture `db_sembrada`) |
| **Datos de entrada** | Umbral `kokutsu_dachi` / `rodilla_frontal` recalibrado a 95-125 con fuente `modelado_experto` |

**Por qué existe este caso:** si la recalibración sobrescribiera el umbral, las mediciones antiguas quedarían juzgadas por un criterio que ya no existe y el reporte de progreso dejaría de ser trazable.

**Comando**

```bash
python3 -m pytest "tests/integration/test_umbrales.py::test_recalibrar_crea_version_nueva_sin_borrar_la_anterior" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Leer el umbral vigente antes de recalibrar | Se obtiene su `id_umbral` original |
| 2 | Invocar `actualizar_umbral(...)` con los valores nuevos | assert id_nuevo != original["id_umbral"] (fila nueva, no sobrescritura) |
| 3 | Consultar `historial_umbral(tecnica, articulacion)` | assert len(historial) == 2 |
| 4 | Verificar cuál versión quedó vigente | Exactamente una fila del historial tiene `vigente` verdadero y es la nueva |

**Criterio de aceptación:** PASSED. Es la garantía de trazabilidad que sostiene el requisito de umbrales parametrizados

---

### TC-AUTO-019 — Una ficha incompleta es rechazada y el error enumera todos los campos que incumplen el formato

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `tests/reporte/plantilla.py (FichaCasoPrueba)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. La ficha se construye directamente, sin pasar por el decorador ni por el registro global |
| **Datos de entrada** | Ficha válida con tres campos corrompidos a la vez: id_caso="MALO", nombre="corto", requisitos="X-1" |

**Por qué existe este caso:** si la plantilla aceptara fichas incompletas, el documento de casos se vería impecable y estaría vacío por dentro.

**Comando**

```bash
python3 -m pytest "tests/unit/test_plantilla_reporte.py::test_el_error_enumera_todos_los_problemas_de_una_vez" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Construir la ficha con los tres campos inválidos | Se lanza `FichaInvalida` en el momento de la construcción |
| 2 | Inspeccionar la lista de problemas del error | assert len(error.value.problemas) >= 3 |
| 3 | Verificar que el mensaje nombra cada campo incumplido | El texto del error menciona id_caso, nombre y requisitos |

**Criterio de aceptación:** PASSED. La validación es acumulativa: quien escribe una ficha ve de una sola vez todo lo que le falta

---

### TC-AUTO-020 — El formulario de calibración rechaza todo rango imposible antes de escribirlo en la base de datos

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `gui/validacion_umbrales.py (interpretar_rango)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. `interpretar_rango` es una función pura, sin estado ni dependencias de la interfaz gráfica |
| **Datos de entrada** | Cinco rangos inválidos: mínimo vacío, mínimo no numérico, máximo menor que el mínimo (175–160), valor negativo (-5) y ángulo de 200° (fuera del rango articular de 0–180°) |

**Por qué existe este caso:** un umbral invertido o fuera del rango articular medible haría que una técnica no pueda aprobarse nunca, y el atleta recibiría correcciones imposibles de satisfacer sin que nada delate el error.

**Comando**

```bash
python3 -m pytest "tests/unit/test_validacion_umbrales.py::test_rechaza_los_rangos_imposibles" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `interpretar_rango(texto_min, texto_max)` con cada rango inválido | assert se levanta `ValorInvalido` en los cinco casos |
| 2 | Leer el mensaje de la excepción | assert el fragmento esperado aparece en el mensaje (indica al entrenador cuál campo corregir, no un rastro técnico) |

**Criterio de aceptación:** PASSED. Ningún rango inválido llega a `Database.actualizar_umbral`, de modo que no se crea una versión de umbral inservible

---

### TC-AUTO-021 — Recalibrar un umbral desde la interfaz cambia el criterio con el que el sistema experto evalúa, sin modificar el código fuente

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/umbrales_screen.py (UmbralesScreen) + persistence/database.py (actualizar_umbral)` |
| **Requisito** | RF-08 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; entrenador autenticado; umbrales de literatura ya sembrados por `App` al arrancar |
| **Datos de entrada** | Umbral `tsuki` / `codo`, vigente en 160–175°, editado a 170–175° desde el formulario; ángulo de prueba 165°, correcto con el criterio anterior |

**Por qué existe este caso:** es la única vía por la que un instructor puede ajustar el criterio técnico del sistema; si la pantalla no escribe en la base de datos, el RF-08 queda sostenido solo por código que nadie del dojo puede ejecutar.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_umbrales.py::test_recalibrar_cambia_el_criterio_del_sistema_experto" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Autenticarse y abrir la pantalla con `_abrir_umbrales()` (el manejador del botón real) | assert isinstance(app.pantalla_actual, UmbralesScreen) |
| 2 | Escribir 170 en el campo del mínimo y disparar `_guardar_cambios()` | assert guardados == 1 (se escribe solo el umbral modificado) |
| 3 | Releer los umbrales vigentes y construir `KarateRules` con ellos | assert reglas.evaluate_tsuki(165)[0] is False (165° ya no aprueba) |
| 4 | Consultar `historial_umbral('tsuki', 'codo')` | assert len(historial) == 2 y la versión vigente quedó firmada por el entrenador que la guardó |

**Criterio de aceptación:** PASSED. El criterio nuevo rige la siguiente sesión de análisis y la versión anterior permanece en el historial, de modo que las mediciones ya registradas siguen siendo interpretables

---

### TC-AUTO-022 — La fuente de video elegida se verifica antes de guardarse y sobrevive al reinicio del sistema

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/camara_screen.py (CamaraScreen) + persistence/database.py (guardar_config)` |
| **Requisito** | RF-01 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; entrenador autenticado; dispositivos de captura sustituidos por dobles de prueba |
| **Datos de entrada** | Dos cámaras simuladas (índices 0 y 1); se selecciona el índice 1 |

**Por qué existe este caso:** con el índice de cámara escrito en el código, el sistema fallaba en silencio en cualquier equipo distinto al de desarrollo: la ventana quedaba en negro sin informar la causa, que es el peor escenario posible durante una demostración en vivo.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_camara.py::test_la_fuente_elegida_se_verifica_y_persiste" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Autenticarse y abrir la pantalla con `_abrir_camara()` (el manejador del botón real) | assert isinstance(app.pantalla_actual, CamaraScreen) |
| 2 | Seleccionar la cámara de índice 1 y disparar `guardar_seleccion()` | assert guardado is True (la fuente entregó un fotograma verificable) |
| 3 | Consultar la preferencia almacenada en la base de datos | assert db.leer_config('fuente_video') == '1' |
| 4 | Resolver la fuente como lo hace la pantalla de análisis al abrirse | assert fuente_configurada(db) == '1' |

**Criterio de aceptación:** PASSED. La fuente queda configurada solo después de comprobar que entrega imagen, y la pantalla de análisis la reutiliza sin que el entrenador vuelva a elegirla

---

### TC-AUTO-023 — Un índice de cámara escrito como texto se convierte a entero antes de llegar a OpenCV

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `vision/camera.py (normalizar)` |
| **Requisito** | RF-01 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. `normalizar` es una función pura que no abre dispositivos |
| **Datos de entrada** | Cuatro fuentes locales: los enteros 0 y 2, y las cadenas "0" y "2" |

**Por qué existe este caso:** OpenCV distingue por tipo: con el entero 2 abre la tercera cámara del equipo, pero con la cadena "2" busca un archivo de video llamado "2". Como el valor llega desde un formulario de la interfaz, siempre viene en texto, y sin la conversión el sistema nunca abriría la cámara seleccionada.

**Comando**

```bash
python3 -m pytest "tests/unit/test_fuentes_video.py::test_los_indices_se_convierten_a_entero" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `normalizar(entrada)` con cada una de las cuatro fuentes | assert resultado == esperado en los cuatro casos |
| 2 | Verificar el tipo del valor devuelto | assert isinstance(resultado, int) — nunca una cadena |

**Criterio de aceptación:** PASSED. Las direcciones de cámara IP, en cambio, se conservan como texto: es el tipo con el que OpenCV las interpreta como flujo de red

---

### TC-AUTO-024 — La fuente de video configurada persiste entre ejecuciones del sistema

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Media |
| **Componente** | `persistence/database.py (guardar_config, leer_config)` |
| **Requisito** | RF-01 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Archivo de base de datos temporal; sin preferencias previas |
| **Datos de entrada** | Fuente de video `http://192.168.1.50:8080/video` (cámara IP del dojo) |

**Por qué existe este caso:** si la preferencia no sobreviviera al reinicio, configurar la cámara dejaría de ser una tarea de instalación y pasaría a ser un paso que el entrenador repite cada sesión, en contra del ciclo de uso breve que exige el RNF-04.

**Comando**

```bash
python3 -m pytest "tests/integration/test_configuracion.py::test_la_preferencia_sobrevive_al_reinicio_del_sistema" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Abrir la base, guardar la fuente con `guardar_config` y cerrar la conexión | La escritura se confirma sin excepción |
| 2 | Abrir de nuevo el MISMO archivo, como ocurre al reiniciar el programa | assert leer_config('fuente_video') devuelve la dirección íntegra |

**Criterio de aceptación:** PASSED. La preferencia vive en el mismo archivo SQLite que el resto del estado del dojo, de modo que un respaldo la incluye

---

### TC-AUTO-025 — Un Kokutsu Dachi correctamente ejecutado se reconoce como tal y no como una transición entre posturas

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py (clasificador de posturas)` |
| **Requisito** | ['RF-01', 'RF-05'] |
| **Entorno** | Cualquiera |
| **Precondiciones** | Instancia de `TechniqueAnalyzer(ventana_filtro=1)`; poses sintéticas de 33 landmarks con visibilidad 1.0 |
| **Datos de entrada** | Cinco ejecuciones con la pierna frontal extendida y la trasera flexionada: (170, 100), (165, 105), (160, 110), (155, 115) y (150, 120) |

**Por qué existe este caso:** es una prueba de regresión de un defecto real: el clasificador exigía la rodilla frontal flexionada para reconocer un Kokutsu, cuando en esa postura el peso va atrás y la frontal queda casi extendida. Toda ejecución correcta caía en la rama por defecto y se reportaba como "EN TRANSICION", de modo que una de las posturas del alcance no se evaluaba nunca y nada lo delataba.

**Comando**

```bash
python3 -m pytest "tests/integration/test_analyzer.py::test_un_kokutsu_real_no_se_confunde_con_una_transicion" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Generar la pose sintética con la pierna izquierda adelante (z_tobillo_izq < z_tobillo_der) | 33 landmarks con los ángulos de rodilla solicitados |
| 2 | Invocar `analyzer.analyze_stance(landmarks, 1000, 1000)` | assert "KOKUTSU" in mensaje en las cinco ejecuciones |
| 3 | Comprobar que no se reportó como movimiento | assert "TRANSICION" not in mensaje y assert "MOVIENDOSE" not in mensaje |

**Criterio de aceptación:** PASSED. Con el clasificador anterior las cinco ejecuciones fallaban, por lo que esta prueba impide que la corrección se revierta

---

### TC-AUTO-026 — La precisión de un alumno se calcula solo sobre evaluaciones cerradas, ignorando los estados transitorios

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `persistence/database.py (resumen_atletas)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con un atleta que acumula 4 evaluaciones correctas, 3 incorrectas y 1 estado transitorio sin veredicto |
| **Datos de entrada** | Sesión 1: dos tsukis correctos, uno hiperextendido y un "EN TRANSICION". Sesión 2: dos tsukis correctos y dos posturas incorrectas |

**Por qué existe este caso:** durante una sesión el sistema emite muchos diagnósticos sin veredicto ("EN TRANSICION", "MAE GERI: CARGA", articulación no visible). Contarlos como fallos hundiría el porcentaje de cualquier alumno por el solo hecho de haberse movido frente a la cámara, y el instructor tomaría decisiones de entrenamiento sobre una cifra falsa.

**Comando**

```bash
python3 -m pytest "tests/integration/test_consultas_progreso.py::test_la_precision_ignora_los_estados_transitorios" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `resumen_atletas()` | assert el atleta aparece con sesiones == 2 |
| 2 | Verificar el denominador del porcentaje | assert evaluaciones == 7, no 8: el estado transitorio queda fuera |
| 3 | Verificar el porcentaje calculado | assert precision == pytest.approx(4 / 7 * 100) |

**Criterio de aceptación:** PASSED. Un alumno sin mediciones aparece con precisión None y no con 0 %, porque "sin datos" y "falla todo" son afirmaciones distintas

---

### TC-AUTO-027 — El reporte de progreso de un atleta se genera desde la interfaz y produce un archivo de imagen válido

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/alumno_screen.py (AlumnoScreen) + persistence/reportes.py` |
| **Requisito** | RF-07 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV, Pillow y Matplotlib instalados; entorno gráfico disponible; atleta con una sesión cerrada que dejó evaluaciones con veredicto |
| **Datos de entrada** | Atleta "Diego Morales" con una sesión de 3 evaluaciones cerradas (1 correcta, 2 incorrectas) y 1 estado transitorio |

**Por qué existe este caso:** el módulo de reportes funcionaba y estaba probado, pero no se invocaba desde ninguna pantalla ni desde la consola: era código inalcanzable para el usuario. El diagrama de casos de uso, en cambio, declaraba la función como implementada, de modo que el sistema prometía algo que nadie podía ejecutar.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_historial.py::test_el_reporte_de_progreso_se_genera_desde_la_pantalla" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Navegar alumnos → perfil del alumno con `on_abrir_alumno(id)` | assert isinstance(app.pantalla_actual, AlumnoScreen) |
| 2 | Disparar `generar_reporte()` (el manejador del botón real) | assert ruta is not None — se produjo un archivo |
| 3 | Verificar el archivo en disco | assert el archivo existe y su tamaño es mayor que cero |
| 4 | Leer el mensaje mostrado al instructor | assert la ruta del reporte aparece en el texto de estado de la pantalla |

**Criterio de aceptación:** PASSED. Si el atleta no tiene evaluaciones cerradas, no se genera un archivo vacío: se explica por qué todavía no hay nada que graficar

---

### TC-AUTO-028 — Ejecutar el programa sin argumentos abre la interfaz gráfica, no la versión de terminal

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `main.py (main)` |
| **Requisito** | RNF-04 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Las dos funciones de arranque se sustituyen por dobles; no se abre ninguna ventana ni se toca la cámara |
| **Datos de entrada** | Línea de comandos vacía, y la variante `--consola` |

**Por qué existe este caso:** `python main.py` es lo primero que ejecuta cualquiera que reciba el proyecto. Mientras ese comando abría la versión de consola, el usuario terminaba en un formulario de terminal y concluía que el sistema no tenía interfaz gráfica, cuando sí la tiene.

**Comando**

```bash
python3 -m pytest "tests/unit/test_punto_de_entrada.py::test_la_linea_de_comandos_elige_la_via_correcta" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar `main.main()` con argv sin argumentos | assert se eligió la vía gráfica y no la de consola |
| 2 | Invocar `main.main()` con argv = ['--consola'] | assert se eligió la vía de consola |

**Criterio de aceptación:** PASSED. Ambas vías comparten el mismo motor de análisis; solo cambia cómo se presentan los resultados

---

### TC-AUTO-029 — El panel de inicio cuenta la actividad reciente del dojo y descarta la anterior a la ventana de siete días

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `persistence/database.py (metricas_dojo)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base de datos limpia con un entrenador y dos alumnos registrados |
| **Datos de entrada** | Tres sesiones fechadas a 1, 3 y 20 días atrás; la de 20 días queda fuera de la ventana de siete. Seis evaluaciones cerradas dentro de la ventana, cuatro correctas |

**Por qué existe este caso:** es la primera cifra que el instructor ve al abrir el sistema y la que usará para decidir cómo va la semana; si la ventana no filtra, el número crece para siempre y deja de significar «actividad reciente», convirtiendo el panel en un contador histórico disfrazado.

**Comando**

```bash
python3 -m pytest "tests/integration/test_panel_inicio.py::test_la_ventana_de_actividad_deja_fuera_las_sesiones_viejas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Crear las tres sesiones y reescribir su fecha hacia el pasado | assert las tres existen en la tabla `sesion` |
| 2 | Registrar mediciones cerradas solo en las dos sesiones recientes | assert se guardaron con `correcto` no nulo |
| 3 | Invocar `metricas_dojo()` con la ventana por defecto | assert metricas['sesiones'] == 2 (la de 20 días no cuenta) |
| 4 | Comprobar alumnos activos y precisión | assert metricas['alumnos_activos'] == 1 y metricas['precision'] == pytest.approx(66.67) |

**Criterio de aceptación:** PASSED. El panel refleja la actividad de los últimos siete días y la precisión se calcula solo sobre evaluaciones cerradas de ese periodo.

---

### TC-AUTO-030 — El panel de correcciones no repite una corrección que sigue vigente, de modo que la retroalimentación en pantalla conserve solo lo que cambió

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `gui/panel_vivo.py (FeedCorrecciones)` |
| **Requisito** |  |
| **Entorno** | Cualquiera |
| **Precondiciones** | Feed recién creado, sin correcciones previas |
| **Datos de entrada** | Treinta fotogramas con el mismo diagnóstico incorrecto de codo; luego un diagnóstico distinto; luego el primero otra vez |

**Por qué existe este caso:** el análisis corre a unos 30 fotogramas por segundo y el mismo diagnóstico se repite en decenas consecutivos; sin el filtro, un solo error sostenido durante un segundo llena la lista con treinta copias idénticas y empuja fuera de pantalla las demás correcciones, incumpliendo de fondo el RF-06 aunque el panel se dibuje.

**Comando**

```bash
python3 -m pytest "tests/unit/test_panel_vivo.py::test_una_correccion_vigente_no_se_vuelve_a_anotar" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Registrar el mismo diagnóstico incorrecto en 30 fotogramas seguidos | assert len(feed.entradas) == 1 |
| 2 | Registrar un diagnóstico distinto de la misma articulación | assert len(feed.entradas) == 2 y el más reciente queda primero |
| 3 | Volver a registrar el diagnóstico original | assert len(feed.entradas) == 3 (la recaída sí es información nueva) |
| 4 | Registrar 20 correcciones distintas con un tope de 8 | assert len(feed.entradas) == 8 y conserva las más recientes |

**Criterio de aceptación:** PASSED. El panel muestra la secuencia de correcciones reales del alumno y no la frecuencia de muestreo de la cámara.

---

### TC-AUTO-031 — Un grado numérico escrito bajo un color de cinta que no lo admite se descarta al guardar, en vez de producir una ficha que se contradice

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `gui/registro_alumno.py (interpretar_formulario)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna; la función es pura y no toca la base de datos |
| **Datos de entrada** | Formulario con nombre «Marta Similox», color de cinta «Blanca» y grado «1er kyu» remanente de una selección anterior |

**Por qué existe este caso:** el campo de grado aparece y desaparece según el color elegido, de modo que un sensei que escribe «1er kyu» y después corrige la cinta a «Blanca» deja un valor huérfano en el formulario; guardarlo registraría a un principiante como alumno avanzado y ese dato alimenta después las estadísticas por grado.

**Comando**

```bash
python3 -m pytest "tests/unit/test_registro_alumno.py::test_un_grado_huerfano_no_se_guarda" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Interpretar el formulario con cinta Café y grado «1er kyu» | assert datos['grado_cinturon'] == '1er kyu' (el café sí admite grado) |
| 2 | Interpretar el mismo formulario cambiando la cinta a «Blanca» | assert datos['grado_cinturon'] is None (el grado se descarta) |
| 3 | Comprobar que el resto de la ficha se conserva intacto | assert datos['nombre'] == 'Marta Similox' y datos['color_cinta'] == 'Blanca' |

**Criterio de aceptación:** PASSED. La ficha guardada nunca afirma un grado que su color de cinta contradice.

---

### TC-AUTO-032 — Elegir un perfil de sensei exige su contraseña y no da acceso con un solo clic

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/perfil_screen.py (PerfilScreen) + persistence/database.py (autenticar_entrenador)` |
| **Requisito** |  |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; un sensei registrado con usuario «sensei» y contraseña «clave123» |
| **Datos de entrada** | Tarjeta del sensei registrado; primero una contraseña equivocada («incorrecta»), después la correcta («clave123») |

**Por qué existe este caso:** la pantalla se parece a un selector de perfiles al estilo Netflix, donde elegir una tarjeta entra sin más; si aquí se comportara igual, sería una puerta trasera al inicio de sesión —cualquiera operaría como el sensei principal con un clic— y dejaría sin valor el hash SHA-256 del RNF-05, además de falsear la firma que queda en cada umbral recalibrado y en cada sesión registrada.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_inicio.py::test_cambiar_de_perfil_pide_la_contrasena_del_sensei" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Abrir la selección de perfiles con `on_cambiar_perfil()` | assert isinstance(app.pantalla_actual, PerfilScreen) y app.barra is None |
| 2 | Pulsar la tarjeta del sensei sin escribir contraseña y disparar `_entrar()` | assert la aplicación sigue en PerfilScreen |
| 3 | Escribir una contraseña equivocada y disparar `_entrar()` | assert 'Contraseña incorrecta' en el mensaje de error y no se entró |
| 4 | Escribir la contraseña correcta y disparar `_entrar()` | assert isinstance(app.pantalla_actual, InicioScreen) y app.entrenador quedó fijado |

**Criterio de aceptación:** PASSED. Cambiar de perfil pasa siempre por la verificación de credenciales, de modo que la firma de cada medición corresponde a quien realmente la tomó.

---

### TC-AUTO-033 — El video se ajusta al espacio disponible conservando su proporción, en vez de imponer su resolución al resto de la pantalla

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/live_screen.py (_escalar, _mostrar_frame)` |
| **Requisito** |  |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, MediaPipe, OpenCV y Pillow instalados; entorno gráfico disponible; cámara sustituida por `CamaraSintetica` |
| **Datos de entrada** | Huecos de 560x420 y 300x300 contra fotogramas de 1280x720 y 640x480 |

**Por qué existe este caso:** una cámara entrega 1280x720 y el fotograma se dibujaba a tamaño nativo, de modo que empujaba al panel derecho —donde viven las correcciones del sistema experto— hasta reducirlo a 193 px de los 320 que pide, recortando el texto de cada corrección; en un equipo con pantalla pequeña el panel quedaría fuera de cuadro y el RF-06 dejaría de cumplirse en la práctica.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_vivo.py::test_el_video_se_ajusta_al_hueco_sin_deformarse" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Calcular el tamaño de un fotograma 1280x720 en un hueco de arranque | assert el resultado cabe en el hueco y conserva la proporción 16:9 |
| 2 | Comprobar que un fotograma más alto que ancho también se limita por el alto | assert alto <= hueco disponible |
| 3 | Verificar que la proporción original se conserva en ambos casos | assert ancho/alto se mantiene dentro de un 1 % del original |

**Criterio de aceptación:** PASSED. El panel de correcciones conserva su ancho y los ángulos se ven sin deformar, que es condición para que lo mostrado corresponda a lo medido.

---

### TC-AUTO-034 — Todo veredicto que la base de conocimientos puede emitir tiene su corrección redactada para el alumno

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `gui/coaching.py (CORRECCIONES) + expert_system/knowledge_base.py` |
| **Requisito** |  |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna; se inspecciona el código fuente de la base de conocimientos |
| **Datos de entrada** | Los veredictos que `knowledge_base.py` devuelve en sus sentencias `return` |

**Por qué existe este caso:** el panel de correcciones es la forma en que el sistema cumple el RF-06; si se agrega una regla nueva y se olvida su traducción, la pantalla no falla —muestra el texto técnico— y el descuido pasa inadvertido hasta que un instructor lee «MAE GERI: KIME INCOMPLETO» en medio de una clase y tiene que interpretarlo él.

**Comando**

```bash
python3 -m pytest "tests/unit/test_coaching.py::test_ningun_veredicto_del_motor_se_queda_sin_correccion" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Extraer de la base de conocimientos todos los veredictos que puede emitir | assert la lista no viene vacía (si lo estuviera, la prueba no probaría nada) |
| 2 | Restarle los veredictos que la tabla de correcciones cubre | assert el conjunto resultante está vacío |

**Criterio de aceptación:** PASSED. Cada veredicto llega al alumno como una instrucción y no como lenguaje de máquina.

---

### TC-AUTO-035 — Una cámara sin nombre se omite de la lista en vez de desplazar a las siguientes, de modo que ningún dispositivo quede etiquetado con el nombre de otro

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `vision/nombres_camara.py (analizar_salida_macos)` |
| **Requisito** | RF-01 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna; la función es pura y no consulta el sistema operativo |
| **Datos de entrada** | Respuesta de `system_profiler` con dos entradas, la primera sin campo `_name` ni `spcamera_model-id` |

**Por qué existe este caso:** la posición en la lista ES el índice del dispositivo, así que un hueco correría a todas las cámaras posteriores y el entrenador elegiría la webcam integrada creyendo que elige la cámara del tatami; una etiqueta equivocada es peor que no tener etiqueta, porque induce a confiar en ella.

**Comando**

```bash
python3 -m pytest "tests/unit/test_nombres_camara.py::test_una_camara_sin_nombre_se_omite_en_vez_de_correr_las_demas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Analizar la salida con la primera entrada incompleta | assert el resultado contiene solo el nombre de la segunda cámara |
| 2 | Comprobar que no se insertó un marcador de posición | assert len(nombres) == 1, no 2 |

**Criterio de aceptación:** PASSED. La cámara sin nombre se muestra por su índice y las demás conservan el suyo.

---

### TC-AUTO-036 — La asimetría entre lados solo se reporta cuando hay repeticiones suficientes en ambos, de modo que un fallo aislado no se presente como señal de lesión

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/riesgos.py (evaluar_asimetria)` |
| **Requisito** |  |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna; la función es pura y no consulta la base de datos |
| **Datos de entrada** | Lado izquierdo con 3 evaluaciones al 33 % y derecho con 3 al 100 % (67 puntos de diferencia, por debajo del mínimo de repeticiones); después los mismos porcentajes con 12 evaluaciones por lado |

**Por qué existe este caso:** con tres repeticiones por lado un solo fallo mueve el porcentaje 33 puntos, de modo que casi cualquier sesión corta produciría una «asimetría marcada»; un instructor que recibe esa alerta cambia el entrenamiento de un alumno sano, y si la alerta salta siempre deja de creerle también cuando es real.

**Comando**

```bash
python3 -m pytest "tests/unit/test_riesgos.py::test_la_asimetria_exige_repeticiones_suficientes_en_ambos_lados" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Evaluar la asimetría con 3 repeticiones por lado | assert el resultado es None pese a los 67 puntos de diferencia |
| 2 | Evaluar los mismos porcentajes con 12 repeticiones por lado | assert se reporta un hallazgo de nivel 'riesgo' |
| 3 | Comprobar que el hallazgo nombra el lado rezagado | assert 'izquierdo' aparece en el título |

**Criterio de aceptación:** PASSED. El sistema se pronuncia sobre asimetría solo cuando la muestra lo respalda, y nombra qué lado trabajar.

---

### TC-AUTO-037 — Ninguna tarea principal del sistema cuesta más de tres pulsaciones

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `gui/navegacion.py (RUTAS, exceden_el_limite)` |
| **Requisito** | RNF-04 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el mapa de navegación es un módulo sin dependencias gráficas |
| **Datos de entrada** | Las nueve rutas declaradas en `gui.navegacion.RUTAS`, cada una con la secuencia de controles que hay que pulsar desde el panel de inicio |

**Por qué existe este caso:** es la verificación directa del RNF-04; sin ella el requisito se daba por cumplido sin haber contado nunca las pulsaciones reales.

**Comando**

```bash
python3 -m pytest "tests/unit/test_navegacion.py::test_ninguna_tarea_pasa_de_tres_pulsaciones" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Contar los pasos de cada ruta declarada | Cada ruta tiene entre 1 y 3 pasos |
| 2 | Invocar `exceden_el_limite(RUTAS, limite=3)` | assert resultado == [] (ninguna tarea supera el límite) |
| 3 | Invocar el mismo verificador sobre una ruta artificial de cuatro pasos | assert la ruta aparece en el resultado: el verificador sí detecta un incumplimiento, de modo que el resultado vacío anterior no es vacuo |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-038 — Cada tarea principal se completa pulsando los controles reales de la interfaz, en no más de tres pulsaciones desde el panel de inicio

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/ (App, BarraLateral y las nueve pantallas), gui/navegacion.py` |
| **Requisito** | RNF-04 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, OpenCV, MediaPipe, Pillow y Matplotlib instalados; entorno gráfico disponible; sensei autenticado; un alumno con una sesión cerrada en la base temporal |
| **Datos de entrada** | Las nueve rutas de `gui.navegacion.RUTAS`; sensei "Sensei Ejemplo" (clave123, rol principal); alumno "Diego Morales" con 2 evaluaciones cerradas; cámara y enumeración de dispositivos sustituidas por dobles |

**Por qué existe este caso:** verifica el RNF-04 sobre la interfaz construida y no sobre una declaración: una pantalla intermedia o un botón renombrado rompen el recorrido y quedan a la vista.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_navegacion_rnf04.py::test_cada_tarea_principal_se_completa_en_tres_pulsaciones" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Situar la aplicación en el panel de inicio con el sensei autenticado | assert la pantalla actual es `InicioScreen` |
| 2 | Para cada ruta, buscar en el árbol de widgets el control que declara cada paso y activarlo (botón, desplegable, casilla o tarjeta) | Cada control existe en ese punto del recorrido; si no, el fallo nombra el control buscado y lista los botones disponibles |
| 3 | Contar las pulsaciones dadas | assert pulsaciones <= 3 |
| 4 | Comprobar dónde terminó el recorrido | assert la pantalla actual es la que la ruta declara como destino |

**Criterio de aceptación:** PASSED para las nueve rutas. En entornos sin interfaz gráfica (CI headless) el caso se marca SKIPPED de forma controlada, no FAILED

---

### TC-AUTO-039 — Una medición de Kokutsu Dachi se vuelve a juzgar cuando el sensei corrige el umbral

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/reevaluacion.py (reevaluar)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. El módulo no depende de base de datos ni de cámara |
| **Datos de entrada** | Kokutsu con rodilla frontal 160° y trasera 105°, juzgada correcta con el umbral vigente (trasera 90-120°); umbral corregido a 90-100° |

**Por qué existe este caso:** los rangos de Kokutsu Dachi vigentes son provisionales; sin re-evaluación, confirmarlos con el cuerpo técnico obligaría a repetir toda la toma de datos en el dojo.

**Comando**

```bash
python3 -m pytest "tests/unit/test_reevaluacion.py::test_corregir_el_umbral_trasero_cambia_el_veredicto_de_un_kokutsu_guardado" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Construir reglas con el umbral corregido de la rodilla trasera | KarateRules toma el rango nuevo |
| 2 | Invocar reevaluar() con los dos ángulos guardados | assert correcto is False: 105° queda fuera de 90-100° |

**Criterio de aceptación:** El veredicto recalculado es Incorrecto, sin haber vuelto a medir

---

### TC-AUTO-040 — Corregir un umbral revela qué mediciones del historial cambiarían de veredicto, sin repetir la toma de datos

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py + persistence/medicion_logger.py + expert_system/reevaluacion.py` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Base temporal con entrenador, atleta y sesión abierta (fixture `sesion_de_prueba`) |
| **Datos de entrada** | Kokutsu sintético: rodilla frontal 160°, trasera 105°, guardia izquierda |

**Por qué existe este caso:** los rangos de Kokutsu Dachi vigentes están pendientes de confirmación del cuerpo técnico; sin recalibración retroactiva, esa confirmación invalidaría toda la toma de datos de campo hecha antes.

**Comando**

```bash
python3 -m pytest "tests/integration/test_recalibracion_retroactiva.py::test_una_correccion_de_umbral_se_aplica_a_lo_ya_medido" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Medir la postura con TechniqueAnalyzer y registrarla con MedicionLogger | Una fila con tecnica_clave='kokutsu_dachi' y sus dos ángulos |
| 2 | Recuperarla con Database.mediciones_reevaluables() | La fila trae los argumentos de la regla |
| 3 | Comparar contra un umbral de rodilla trasera corregido a 90-100° | assert el informe reporta exactamente una medición que cambia de veredicto |

**Criterio de aceptación:** El informe identifica el cambio de Correcto a Incorrecto sin volver a medir

---

### TC-AUTO-041 — La velocidad de grabación se deduce del análisis real y no de la que declara la cámara

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `vision/grabacion.py (fps_estimado)` |
| **Requisito** | RF-01 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. El módulo no importa OpenCV |
| **Datos de entrada** | Once marcas de tiempo separadas 100 ms: [0, 100, ..., 1000] |

**Por qué existe este caso:** el bucle corre a la velocidad que permite la estimación de pose, no a la de captura; declarar 30 fps sobre un flujo real de 10 produce un video que se reproduce al triple y deja de coincidir con los tiempos de las mediciones guardadas.

**Comando**

```bash
python3 -m pytest "tests/unit/test_grabacion.py::test_la_velocidad_se_mide_por_intervalos_no_por_fotogramas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar fps_estimado() con las marcas observadas | Se miden los intervalos, no los fotogramas |
| 2 | Comparar contra la velocidad real del flujo | assert fps == 10.0, no 11.0 ni la nominal de la cámara |

**Criterio de aceptación:** 10.0 fps: diez intervalos de 100 ms entre once fotogramas

---

### TC-AUTO-042 — Una sesión analizada deja un archivo de video reproducible con todos sus fotogramas

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `vision/grabador.py (GrabadorSesion)` |
| **Requisito** | RF-01, RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | OpenCV disponible con al menos un códec de la lista CODECS |
| **Datos de entrada** | 30 fotogramas sintéticos de 320x240 separados 100 ms |

**Por qué existe este caso:** sin la grabación, una ejecución medida en el dojo no se puede volver a analizar; repetirla no es equivalente porque sería otra ejecución, de otro día.

**Comando**

```bash
python3 -m pytest "tests/integration/test_grabador.py::test_una_sesion_deja_un_video_reproducible_con_todos_sus_fotogramas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Escribir los 30 fotogramas con GrabadorSesion.escribir() | Los primeros 12 se retienen para medir la velocidad real |
| 2 | Cerrar la grabación | El archivo queda en disco |
| 3 | Reabrir el archivo con cv2.VideoCapture y contar los fotogramas | assert se recuperan los 30, ninguno perdido en el tramo de estimación |

**Criterio de aceptación:** Un .mp4 legible con los 30 fotogramas y la velocidad medida

---

### TC-AUTO-043 — Un fallo al escribir el video no interrumpe la sesión de medición

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `vision/grabador.py (GrabadorSesion.escribir)` |
| **Requisito** | RF-01, RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | OpenCV disponible |
| **Datos de entrada** | Un escritor que levanta excepción al escribir, tras 12 fotogramas normales |

**Por qué existe este caso:** se graba sobre el equipo de un dojo, no sobre un servidor vigilado: un disco lleno o un códec ausente no puede costar las mediciones de toda una tarde.

**Comando**

```bash
python3 -m pytest "tests/integration/test_grabador.py::test_un_fallo_al_escribir_apaga_la_grabacion_pero_no_levanta" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Grabar hasta que el archivo se abra | El escritor real queda creado |
| 2 | Sustituirlo por uno que falla y seguir escribiendo 10 fotogramas | escribir() no levanta |
| 3 | Consultar el estado | assert grabando is False y error explica el motivo |

**Criterio de aceptación:** La grabación se apaga con su motivo registrado; el bucle sigue corriendo

---

### TC-AUTO-044 — Una sesión de análisis en vivo deja un video atado a la sesión en la base de datos

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/live_screen.py + vision/grabador.py + persistence/database.py` |
| **Requisito** | RF-01, RF-07 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | Entorno gráfico, CustomTkinter, OpenCV y MediaPipe disponibles; cámara sintética inyectada y carpeta de grabaciones temporal |
| **Datos de entrada** | Veinte fotogramas de la cámara sintética |

**Por qué existe este caso:** sin video, una toma de datos en el dojo es irrepetible: si el criterio de evaluación cambia, la ejecución medida ya no se puede volver a analizar.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_vivo.py::test_una_sesion_en_vivo_deja_video_atado_a_la_sesion" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Avanzar el ciclo de video 20 veces con _actualizar_frame() | El grabador retiene, estima la velocidad y escribe |
| 2 | Cerrar la pantalla | Se cierra el archivo y se anota la ruta en la sesión |
| 3 | Consultar la columna ruta_video de la sesión | assert el archivo existe en disco y la fila lo apunta |

**Criterio de aceptación:** Un .mp4 en la carpeta configurada, referenciado por la sesión

---

### TC-AUTO-045 — Una sesión grabada se puede elegir como fuente y queda configurada para volver a analizarse

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/camara_screen.py (CamaraScreen) + vision/fuentes.py (validar_grabacion)` |
| **Requisito** | RF-01 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, OpenCV, MediaPipe y Pillow instalados; entorno gráfico; un archivo de video existente |
| **Datos de entrada** | Ruta de un .mp4 con contenido |

**Por qué existe este caso:** si la grabación no se puede volver a analizar desde la interfaz, el video de una sesión solo sirve para mirarlo, y corregir un umbral seguiría exigiendo repetir la medición en el dojo.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_camara.py::test_una_grabacion_se_elige_y_queda_configurada" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Elegir la opción de video grabado y escribir la ruta | fuente_elegida() devuelve la ruta |
| 2 | Pulsar «Usar esta cámara» | La fuente se verifica y se guarda |
| 3 | Consultar fuente_configurada() | assert devuelve la ruta del video |

**Criterio de aceptación:** La grabación queda como fuente del próximo análisis

---

### TC-AUTO-046 — El instructor decide si las sesiones se graban, y la decisión persiste entre arranques

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/camara_screen.py (CamaraScreen) + vision/grabacion.py (grabacion_activada)` |
| **Requisito** | RF-01 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | CustomTkinter, OpenCV, MediaPipe y Pillow instalados; entorno gráfico |
| **Datos de entrada** | El interruptor de grabación, apagado y vuelto a encender |

**Por qué existe este caso:** grabar sin que el usuario lo haya decidido llena su disco sin aviso y, con alumnos menores de edad, lo pone a filmar sin el consentimiento de sus encargados.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_camara.py::test_el_instructor_decide_si_se_graba_y_se_recuerda" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Apagar el interruptor | Se guarda en la tabla de configuración al instante |
| 2 | Volver a abrir la pantalla | El interruptor sigue apagado |
| 3 | Encenderlo de nuevo | assert la configuración vuelve a activar la grabación |

**Criterio de aceptación:** La elección del instructor se respeta y sobrevive al reinicio

---

### TC-AUTO-047 — El impacto de una recalibración se expresa en veredictos que cambian, no en filas

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `gui/impacto_umbrales.py (titular)` |
| **Requisito** | RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna. El módulo no importa CustomTkinter |
| **Datos de entrada** | Informe con 3 mediciones que cambian y 2 que sostienen su veredicto |

**Por qué existe este caso:** recalibrar sin ver el efecto es cambiar la vara de medir a ciegas; el número de veredictos que se mueven es lo que le dice al cuerpo técnico si el ajuste describe mejor la postura o si se pasó de estricto.

**Comando**

```bash
python3 -m pytest "tests/unit/test_impacto_umbrales.py::test_el_titular_cuenta_los_cambios_sobre_las_juzgadas" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Invocar titular() con el informe | Se cuentan cambios sobre juzgadas |
| 2 | Leer la frase resultante | assert dice «3 de 5 mediciones cambiarían de veredicto» |

**Criterio de aceptación:** Una frase que el cuerpo técnico puede usar para decidir

---

### TC-AUTO-048 — Antes de adoptar una recalibración, el sistema informa cuántas mediciones del historial cambiarían de veredicto

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/umbrales_screen.py + expert_system/reevaluacion.py + gui/impacto_umbrales.py` |
| **Requisito** | RF-08 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | Entorno gráfico y dependencias de GUI; cinco Kokutsu registrados como correctos con el umbral vigente de rodilla trasera (90–120°) |
| **Datos de entrada** | Rodilla trasera de Kokutsu Dachi corregida de 90–120° a 90–100° |

**Por qué existe este caso:** recalibrar sin ver el efecto es cambiar a ciegas la vara con que se mide a los alumnos: el mismo historial puede pasar de 100 % a 40 % de precisión sin que nadie haya vuelto a medir.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_umbrales.py::test_el_impacto_se_ve_antes_de_guardar" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Escribir el rango corregido en la fila de Kokutsu · rodilla trasera | El formulario difiere del umbral vigente |
| 2 | Pulsar «Ver impacto en el historial» | Se vuelve a juzgar lo registrado con el criterio propuesto |
| 3 | Leer el resumen | assert reporta 3 de 5 mediciones que cambian de veredicto |

**Criterio de aceptación:** El resumen identifica las tres ejecuciones afectadas sin escribir nada

---

### TC-AUTO-049 — El tiempo de una grabación lo dicta el video y no la velocidad a la que se analiza

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `vision/camera.py (Camera.marca_de_tiempo_ms) + vision/fuentes.py` |
| **Requisito** | RF-01, RF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | OpenCV disponible; una grabación de 30 fotogramas a 30 fps |
| **Datos de entrada** | La misma grabación leída dos veces: de corrido y con una pausa de 50 ms entre lecturas |

**Por qué existe este caso:** la velocidad angular del Kime se deriva del intervalo entre fotogramas; medirlo con el reloj de pared sobre una grabación lo infla varias veces y reporta como falta de explosividad toda patada correcta del video, de forma sistemática.

**Comando**

```bash
python3 -m pytest "tests/integration/test_marca_de_tiempo.py::test_una_pausa_en_el_analisis_no_altera_el_tiempo_de_la_grabacion" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Leer la grabación completa registrando la marca de cada fotograma | Las marcas avanzan a razón de 1000/30 ms |
| 2 | Repetir la lectura intercalando una pausa artificial entre fotogramas | El reloj de pared avanza mucho más que el video |
| 3 | Comparar ambas secuencias de marcas | assert son idénticas: la pausa no altera el tiempo del video |

**Criterio de aceptación:** Las marcas dependen del contenido y no de la velocidad del análisis

---

### TC-AUTO-050 — Sin separación suficiente entre los tobillos, el sistema no afirma qué pierna va adelante en lugar de elegir una

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/guardia.py (pierna_adelantada, separacion_sagital)` |
| **Requisito** | RF-03, RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el módulo es geometría pura sin dependencias gráficas |
| **Datos de entrada** | Posiciones (x, z) de caderas y tobillos con separaciones sagitales de 0,0, de justo por debajo del mínimo y de muy por encima |

**Por qué existe este caso:** Zenkutsu Dachi y Kokutsu Dachi son la misma postura con las piernas intercambiadas, de modo que la guardia es lo único que las distingue. El cálculo anterior decidía por el signo de una resta, sin zona muerta, así que el ruido de la estimación de profundidad bastaba para reportar un Zenkutsu como Kokutsu CON VEREDICTO POSITIVO: la medición se guardaba con la técnica equivocada y contaminaba el historial y la gráfica de evolución del alumno. Es el único defecto conocido que corrompe datos en vez de limitarse a fallar.

**Comando**

```bash
python3 -m pytest "tests/unit/test_guardia.py::test_sin_separacion_suficiente_la_guardia_queda_sin_definir" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Medir la separación con los dos tobillos a la misma profundidad | assert separacion == 0 y pierna_adelantada(...) is None |
| 2 | Medir con una separación por debajo del mínimo exigido | assert pierna_adelantada(...) is None: el sistema se abstiene |
| 3 | Medir con la separación propia de una postura adelantada real | assert pierna_adelantada(...) == IZQ_ADELANTE, de modo que la abstención anterior no se deba a un comprobador que nunca decide |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-051 — Con los tobillos casi a la misma profundidad, el analizador no reporta Zenkutsu ni Kokutsu en lugar de elegir uno de los dos

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py (analyze_stance) sobre expert_system/guardia.py` |
| **Requisito** | RF-03, RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Analizador con ventana de filtro 1 y pose sintética de piernas visibles |
| **Datos de entrada** | Pose con rodilla izquierda a 100° y derecha a 175° (la firma de una postura adelantada) y los dos tobillos separados 0,02 en profundidad, muy por debajo del medio ancho de cadera exigido |

**Por qué existe este caso:** es la comprobación de extremo a extremo del defecto que corrompía el historial: el analizador decidía la guardia por el signo de una resta de profundidades, sin zona muerta, de modo que el ruido de la estimación bastaba para que un Zenkutsu correcto se guardara como un Kokutsu correcto. La prueba unitaria TC-AUTO-050 verifica la geometría; esta verifica que el analizador efectivamente se abstiene y no persiste técnica ni ángulos de regla.

**Comando**

```bash
python3 -m pytest "tests/integration/test_analyzer.py::test_una_guardia_ambigua_no_se_inventa" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Analizar la postura con la separación ambigua | El diagnóstico de categoría `postura` sale con correcto=None |
| 2 | Leer el mensaje emitido | assert 'GUARDIA INDEFINIDA' in mensaje: se nombra la causa, no se confunde con una transición entre posturas |
| 3 | Comprobar qué se persistiría | assert tecnica is None y angulos_regla is None: no entra al historial con una técnica que el sistema no pudo determinar |
| 4 | Repetir con la misma geometría y la profundidad invertida | assert vuelve a abstenerse: la ambigüedad no se resuelve por el lado hacia el que apunte el ruido |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-052 — La herramienta de comparación 2D/3D clasifica igual que el analizador del sistema en todas las posturas del catálogo

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `comparar_2d_3d.py (_clasificar) contra expert_system/analyzer.py` |
| **Requisito** | RF-03 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: ambas implementaciones operan sobre ángulos, sin cámara |
| **Datos de entrada** | Ocho poses sintéticas que cubren las cuatro posturas del catálogo con ambas guardias, más la guardia ambigua y una transición |

**Por qué existe este caso:** la herramienta replica el árbol de decisión de `analyze_stance` para poder alimentarlo con dos juegos de ángulos sobre los mismos landmarks. De esa comparación depende decidir si los ángulos del sistema pasan a calcularse en tres dimensiones, así que una réplica desactualizada no daría un error visible: daría una recomendación equivocada sobre una decisión de arquitectura.

**Comando**

```bash
python3 -m pytest "tests/unit/test_comparar_2d_3d.py::test_la_herramienta_clasifica_igual_que_el_sistema" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Analizar cada pose con TechniqueAnalyzer.analyze_stance | Se obtiene el mensaje de diagnóstico de la categoría `postura` |
| 2 | Clasificar los mismos ángulos con `_clasificar` de la herramienta | Se obtiene una clave de postura |
| 3 | Contrastar ambas respuestas caso por caso | assert coinciden en los ocho casos |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-053 — El sistema advierte para qué técnicas sirve la posición actual de la cámara, aunque todas las articulaciones estén visibles

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `vision/encuadre.py (evaluar, clasificar_plano)` |
| **Requisito** | RF-01, RF-03 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el módulo no importa MediaPipe ni OpenCV |
| **Datos de entrada** | Una pose sintética con todas las articulaciones visibles y valores de orientación correspondientes a cámara frontal, oblicua y de perfil |

**Por qué existe este caso:** una toma frontal deja todas las articulaciones perfectamente visibles y, aun así, impide medir las técnicas del plano sagital: medido sobre 637 fotogramas de Zenkutsu Dachi grabados de frente, la postura no se reconoció ni una sola vez, frente al 40,5 % de perfil. El fallo no se manifiesta en pantalla —el esqueleto se dibuja bien y la visibilidad es alta—, de modo que sin este aviso una campaña de recolección puede completarse entera y producir datos inservibles.

**Comando**

```bash
python3 -m pytest "tests/unit/test_encuadre.py::test_avisa_del_plano_aunque_todo_se_vea" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Evaluar una toma frontal con el cuerpo completo visible | assert se emite un aviso que nombra Heiko y Kiba como medibles y Zenkutsu, Kokutsu, Tsuki y Mae Geri como necesitados de perfil |
| 2 | Evaluar la misma pose con orientación de perfil | assert el aviso se invierte: nombra las técnicas del plano sagital |
| 3 | Evaluar una toma en diagonal | assert el aviso se eleva de nivel informativo a nivel medio, porque ninguna técnica se mide bien en esa posición |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-054 — El modelo y la base de datos se resuelven sin depender del directorio desde el que se lanzó la aplicación

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `rutas.py (modelo, base_de_datos, raiz_aplicacion)` |
| **Requisito** | RF-01, RNF-02 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el módulo no importa MediaPipe, OpenCV ni sqlite3 |
| **Datos de entrada** | Carpetas temporales que simulan la raíz de la aplicación y el directorio personal, más un entorno declarado explícitamente |

**Por qué existe este caso:** el modelo de pose se pedía como ruta relativa en seis módulos y la base de datos en uno. Una ruta relativa se resuelve contra el directorio de trabajo, que durante el desarrollo coincide con la carpeta del proyecto y deja de coincidir en cuanto la aplicación se empaqueta: un `.command` abierto con doble clic arranca en la carpeta personal del usuario. El fallo resultante impide arrancar y el error que produce MediaPipe no nombra el archivo que falta.

**Comando**

```bash
python3 -m pytest "tests/unit/test_rutas.py::test_las_rutas_no_dependen_del_directorio_de_trabajo" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Resolver el modelo con la raíz declarada y el archivo presente | assert devuelve una ruta absoluta que apunta al archivo |
| 2 | Resolver el modelo cuando el archivo no está | assert lanza ModeloNoEncontrado y el mensaje nombra el archivo y la carpeta donde se buscó, en vez de dejar que falle MediaPipe |
| 3 | Resolver la base de datos sin base heredada junto al código | assert cae en la carpeta de datos del sistema operativo |
| 4 | Resolver la base de datos con una base ya existente junto al código | assert devuelve ESA y no la del sistema: actualizar el programa no puede dejar huérfano el historial de mediciones |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-055 — El bucle de análisis reprograma siempre con el intervalo completo y nunca con una espera mínima

| | |
|---|---|
| **Tipo** | E2e |
| **Prioridad** | Alta |
| **Componente** | `gui/live_screen.py (_procesar_fotograma)` |
| **Requisito** | RF-01, RNF-01 |
| **Entorno** | Con pantalla y cámara |
| **Precondiciones** | Entorno gráfico disponible; cámara sustituida por `CamaraSintetica` |
| **Datos de entrada** | Un fotograma procesado por la pantalla de análisis en vivo, con el método `after` interceptado para registrar los plazos solicitados |

**Por qué existe este caso:** entre el 28 y el 30 de septiembre el ciclo descontaba el tiempo ya gastado antes de reprogramarse, con la intención de recuperar fotogramas por segundo. Como el trabajo de un fotograma supera el intervalo, la resta daba siempre el mínimo, y el temporizador siguiente quedaba vencido casi siempre. En macOS eso produjo dos fallos: la aplicación se cerró con RecursionError durante un análisis en vivo, y la ventana dejó de responder a los clics porque Tk recibía alrededor del 2 % del tiempo para atender al usuario. La guardia de reentrada no basta: impide que el bucle se llame a sí mismo, no que los ciclos de eventos anidados se acumulen.

**Comando**

```bash
python3 -m pytest "tests/e2e/test_gui_vivo.py::test_el_ciclo_reprograma_con_el_intervalo_completo" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Interceptar `after` en la pantalla y procesar un fotograma | Se registran los plazos con que el ciclo se reprograma |
| 2 | Comprobar el plazo de la reprogramación del ciclo | assert es igual a INTERVALO_MS: el ciclo cede a Tk una fracción fija del tiempo, independientemente de lo que haya costado el fotograma |

**Criterio de aceptación:** PASSED en el entorno con interfaz gráfica

---

### TC-AUTO-056 — Un brazo en reposo no produce veredicto de Tsuki, y un golpe produce exactamente uno

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/tsuki.py (TsukiStateMachine)` |
| **Requisito** | RF-03, RF-07, RF-08 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el módulo no importa MediaPipe, OpenCV ni sqlite3, y la máquina se construye con los umbrales de literatura si no se le pasa base de conocimientos |
| **Datos de entrada** | Dos secuencias de ángulos de codo con marca de tiempo: un brazo quieto a 164-179 grados durante tres segundos (las cifras medidas en la prueba en vivo del 30-sep) y un Tsuki completo desde Hikite |

**Por qué existe este caso:** hasta el 30-sep-2026 el codo se evaluaba en cada fotograma en que el brazo se viera, sin comprobar antes que hubiera un golpe. Como el rango de evaluación del Tsuki es 160-175 grados y un brazo colgando al costado mide entre 160 y 180, una persona de pie recibía veredictos de Tsuki: EXCELENTE mientras el ángulo quedaba dentro e HIPEREXTENDIDO (Peligro) al cruzarlo. Esas filas entraban a la base con tecnica='tsuki' y veredicto cerrado, de modo que contaminaban la precisión del alumno, su gráfica de evolución y el informe de prevención de lesiones, que cuenta hiperextensiones para advertir de bloqueo articular. Es un fallo que corrompe datos en vez de limitarse a fallar, del mismo tipo que el de la guardia del 28-sep.

**Comando**

```bash
python3 -m pytest "tests/unit/test_tsuki.py::test_un_brazo_en_reposo_no_produce_veredicto_de_tsuki" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Reproducir tres segundos de brazo quieto cruzando el límite de 175 grados | assert no se emite ningún veredicto cerrado: `correcto` es None en los noventa fotogramas, y el mensaje es el de abstención |
| 2 | Reproducir un Tsuki completo (Hikite -> extensión -> recogida) | assert se emite exactamente UN veredicto cerrado, no uno por fotograma |
| 3 | Comprobar con qué ángulo se juzgó ese veredicto | assert se juzgó con el máximo de la extensión (el Kime) y no con el ángulo del fotograma en que el brazo ya venía de vuelta |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz gráfica

---

### TC-AUTO-057 — El analizador no emite veredicto de Tsuki mientras el brazo no golpea

| | |
|---|---|
| **Tipo** | Integracion |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py (analyze_tsuki) sobre expert_system/tsuki.py` |
| **Requisito** | RF-03, RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Analizador con ventana de filtro 1, sin base de datos: usa los umbrales de literatura |
| **Datos de entrada** | Pose sintetica de una persona de pie con los brazos casi extendidos (172 grados, la cifra medida en la prueba en vivo del 30-sep), repetida durante dos segundos de marcas de tiempo |

**Por qué existe este caso:** la maquina de estados del Tsuki puede ser correcta y aun asi no proteger nada si el analizador sigue llamando a la regla por su cuenta, que es exactamente lo que hacia hasta el 30-sep-2026. Esta prueba recorre la costura completa -landmarks, pixeles, angulo, filtro, maquina, diagnostico- porque es en esa costura donde vivia el defecto: la regla siempre estuvo bien, lo que estaba mal era cuando se consultaba.

**Comando**

```bash
python3 -m pytest "tests/integration/test_analyzer.py::test_estar_de_pie_no_produce_veredicto_de_tsuki" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Analizar sesenta fotogramas de esa pose inmovil | assert ningun diagnostico de codo lleva veredicto cerrado, ni de un brazo ni del otro |
| 2 | Comprobar que el angulo si se informa | assert los grados del codo aparecen en el diagnostico: el codo esta medido, lo que falta es la tecnica |
| 3 | Comprobar que la fila no se marca como medicion de Tsuki | assert `tecnica` es None, para que no entre en el informe de recalibracion retroactiva |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

### TC-AUTO-058 — Ninguna llamada al analizador queda desfasada de su firma, incluidas las de los modulos que la integracion continua omite

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `expert_system/analyzer.py (firmas publicas) contra todo el repositorio` |
| **Requisito** | RNF-03 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: se lee el arbol sintactico, no se ejecuta ningun modulo |
| **Datos de entrada** | Todos los archivos .py del repositorio, excluyendo .git, __pycache__ y entornos virtuales |

**Por qué existe este caso:** el contenedor sin entorno grafico omite los diez modulos de tests/e2e/, asi que una llamada desfasada dentro de ellos pasa la suite completa aqui y solo falla en el equipo de destino. Ocurrio el 30-sep-2026 al anadir timestamp_ms a analyze_tsuki: se actualizaron los dieciseis puntos de llamada visibles y quedaron dos invisibles. La comprobacion estatica alcanza a los modulos que este entorno no puede importar, que es la unica forma de verificarlos desde aqui.

**Comando**

```bash
python3 -m pytest "tests/unit/test_firmas_del_analizador.py::test_toda_llamada_al_analizador_pasa_los_argumentos_de_su_firma" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Leer la firma real de cada metodo publico del analizador con inspect | assert se obtiene el numero de argumentos posicionales que pide |
| 2 | Recorrer el arbol sintactico de cada archivo buscando llamadas a esos metodos | assert se encuentran las llamadas de main.py, gui/, test_rendimiento.py y las tres carpetas de pruebas |
| 3 | Contrastar los argumentos de cada llamada contra la firma | assert ninguna se queda corta ni se pasa, nombrando archivo y linea cuando falla |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

### TC-AUTO-059 — La cota de contaminacion cuenta el reposo y no cuenta los golpes reales

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `revisar_base.py (alternancias_rapidas, resumen_por_tecnica)` |
| **Requisito** | RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: la logica es pura y no abre la base de datos |
| **Datos de entrada** | Dos series sinteticas de mediciones: un brazo en reposo alternando veredictos cada 33 ms y cuatro Tsukis reales separados 800 ms |

**Por qué existe este caso:** la cifra que produce esta herramienta esta destinada a la seccion de validacion de la tesis, donde sostiene cuanto contamino el historial el defecto del Tsuki del 30-sep. Una herramienta que contara de mas al describir su propio defecto produciria evidencia que la terna puede desmontar corriendo la consulta, que es peor que no tener cifra. Por eso se verifica en las dos direcciones: que detecte la firma del brazo en reposo y que NO marque una serie de golpes reales.

**Comando**

```bash
python3 -m pytest "tests/unit/test_revisar_base.py::test_la_cota_cuenta_el_reposo_y_respeta_los_golpes" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Contar alternancias sobre la serie del brazo en reposo | assert marca las filas implicadas: veredictos opuestos a menos de 150 ms no pueden venir de dos golpes |
| 2 | Contar alternancias sobre la serie de golpes reales | assert no marca ninguna, aunque los veredictos sean cerrados |
| 3 | Comprobar que no se mezclan dos sesiones distintas | assert filas de sesiones diferentes con marcas cercanas no se cuentan como una alternancia |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

### TC-AUTO-060 — El aviso de grabacion no anuncia que graba cuando no esta grabando

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `vision/grabacion.py (estado_en_vivo)` |
| **Requisito** | RF-09, RNF-05 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: la funcion es pura y recibe el estado ya resuelto |
| **Datos de entrada** | Las cuatro combinaciones que se dan en la pantalla: configurada sin sesion, configurada con grabador activo, configurada con grabador que renuncio, y apagada |

**Por qué existe este caso:** este aviso es la unica pieza del sistema dedicada al consentimiento: existe para que nadie descubra despues que lo filmaron, y en el dojo se entrena con menores. Hasta el 30-sep-2026 la pantalla lo resolvia una sola vez al construirse, leyendo solo el interruptor del equipo, de modo que anunciaba «Grabando» sin alumno elegido --sin camara ni sesion, sin nada que grabar-- y seguia anunciandolo si el grabador renunciaba a mitad de sesion por disco lleno o codec caido. El segundo caso deja al sensei creyendo que tiene el video de la sesion, y se entera al ir a buscarlo. Un punto rojo que a veces no significa nada es peor que no tener punto rojo.

**Comando**

```bash
python3 -m pytest "tests/unit/test_grabacion.py::test_el_aviso_no_anuncia_que_graba_cuando_no_graba" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Pedir el estado con la grabacion configurada pero sin sesion iniciada | assert NO dice «Grabando»: sin alumno no hay camara ni sesion, asi que no se escribe nada |
| 2 | Pedir el estado con sesion iniciada y grabador activo | assert dice «Grabando» con el punto lleno |
| 3 | Pedir el estado con sesion iniciada y grabador que ya renuncio | assert avisa de que la grabacion se detuvo, en vez de seguir anunciando que graba |
| 4 | Pedir el estado con la grabacion apagada en el equipo | assert dice «Solo midiendo», que ya era correcto |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

### TC-AUTO-061 — La herramienta reconoce el Tsuki rapido, no el lento, y ninguno al recoger

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Alta |
| **Componente** | `revisar_tsuki.py sobre expert_system/tsuki.py` |
| **Requisito** | RF-03, RF-07 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: la logica es pura y no abre video ni base de datos |
| **Datos de entrada** | Series sinteticas de angulo de codo con marca de tiempo: un Tsuki rapido (122 grados en 200 ms), uno lento (los mismos grados en 3 segundos) y una recogida sin golpe previo |

**Por qué existe este caso:** los dos umbrales del Tsuki (35 grados en 500 ms) salieron de la definicion de la tecnica y no de una medicion, y gobiernan que se registra. Probando en vivo el 30-sep-2026 aparecio que un Tsuki lento no se reconoce --coherente con exigir 70 grados/s-- y la sospecha de que recoger el brazo encendia el veredicto, que si seria un defecto. Esta herramienta es la que va a fijar los numeros con datos reales, asi que si ella cuenta mal, el error pasa directo a la tesis.

**Comando**

```bash
python3 -m pytest "tests/unit/test_revisar_tsuki.py::test_reconoce_el_golpe_rapido_y_no_el_lento_ni_la_recogida" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Pasar un Tsuki rapido por la herramienta | assert reconoce exactamente un golpe, y reporta de que angulo salio, a cual llego y a que velocidad |
| 2 | Pasar el mismo recorrido repartido en tres segundos | assert NO lo reconoce con el umbral vigente, que es lo observado en vivo, y el barrido muestra con que umbral si aparecería |
| 3 | Pasar una recogida del brazo, sin extension previa | assert no se reconoce ningun golpe: la maquina solo dispara al abrir el codo |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

### TC-AUTO-062 — El plan de pruebas recoge todos los casos y sus comandos ejecutan

| | |
|---|---|
| **Tipo** | Unitaria |
| **Prioridad** | Media |
| **Componente** | `plan_de_pruebas.py` |
| **Requisito** | RNF-03 |
| **Entorno** | Cualquiera |
| **Precondiciones** | Ninguna: el generador no importa los modulos de prueba, los lee |
| **Datos de entrada** | Los archivos test_*.py del repositorio |

**Por qué existe este caso:** el plan es un entregable que se firma y se presenta, y su utilidad depende de dos cosas que nada mas vigila: que no falte ningun caso y que el comando de cada fila ejecute de verdad. Los diez modulos de tests/e2e/ se omiten solos sin entorno grafico, asi que un plan generado importando los modulos saldria SIN los casos de interfaz --justo los que hay que ejecutar a mano delante de alguien--. Por eso el generador lee el arbol sintactico y no importa nada, y por eso esto se verifica.

**Comando**

```bash
python3 -m pytest "tests/unit/test_plan_de_pruebas.py::test_el_plan_recoge_todos_los_casos_y_sus_comandos_ejecutan" -v
```

**Pasos y aserciones**

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Leer los casos con ficha del arbol sintactico | assert aparecen tambien los de tests/e2e/, que este entorno no puede importar |
| 2 | Comprobar que los identificadores son unicos y sin huecos | assert la serie TC-AUTO-NNN es correlativa: un hueco significa una ficha borrada sin renumerar |
| 3 | Ejecutar el comando generado para un caso concreto | assert pytest lo recoge y lo ejecuta, en vez de fallar por una ruta mal armada |

**Criterio de aceptación:** PASSED en los dos entornos, con y sin interfaz grafica

---

