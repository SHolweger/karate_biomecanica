# Evidencia de ejecución — Suite de pruebas automatizadas

> **Documento generado automáticamente.** Lo produce el complemento `tests/reporte/plugin.py` a partir de las fichas declaradas en el código con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. No editar a mano: cualquier cambio se pierde en la siguiente corrida. Para modificar una ficha hay que editar la prueba correspondiente.

## 1. Identificación de la corrida

| Campo | Valor |
|---|---|
| **Sistema bajo prueba** | Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan |
| **Framework de automatización** | pytest 9.1.1 |
| **Comando ejecutado** | `pytest -q --exigir-fichas --reporte-formal` |
| **Fecha y hora de inicio** | 2026-09-20 23:35:16 |
| **Duración total** | 17.27 s |
| **Entorno de ejecución** | Darwin 25.6.0 (arm64) |
| **Intérprete** | Python 3.11.0 |
| **Rama / commit** | `main` @ `3f7135d` (con cambios sin confirmar) |
| **Pruebas recolectadas** | 709 |
| **Veredicto global** | **APROBADA** |

## 2. Resumen de resultados por nivel

| Nivel | Pruebas | PASSED | FAILED | SKIPPED | Tiempo (s) |
|---|---|---|---|---|---|
| Unitaria | 419 | 419 | 0 | 0 | 0.07 |
| Integración | 172 | 172 | 0 | 0 | 2.74 |
| Interfaz (UI/E2E) | 118 | 118 | 0 | 0 | 13.75 |
| **Total** | **709** | **709** | **0** | **0** | **16.56** |

## 3. Casos de prueba documentados

Cada fila corresponde a una ficha declarada con la plantilla formal. El veredicto es el peor resultado entre las variantes parametrizadas del caso.

| ID | Caso | Requisito | Script | Ejecuciones | Veredicto |
|---|---|---|---|---|---|
| TC-AUTO-001 | Reconstrucción exacta del ángulo interno de una articulación en todo el rango de movimiento humano | RF-05 | `tests/unit/test_geometry.py::test_reconstruye_cualquier_angulo_del_rango_articular` | 9 PASSED | **PASSED** |
| TC-AUTO-002 | El ángulo devuelto nunca excede 180° aunque los segmentos crucen la discontinuidad de atan2 | RF-05 | `tests/unit/test_geometry.py::test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular` | 3 PASSED | **PASSED** |
| TC-AUTO-003 | El filtro de media móvil reduce al menos a la mitad la dispersión del ruido de MediaPipe | RNF-03 | `tests/unit/test_filters.py::test_reduce_la_dispersion_del_ruido` | 1 PASSED | **PASSED** |
| TC-AUTO-004 | Clasificación del golpe recto en las fronteras exactas de 160° y 175° | RF-05 | `tests/unit/test_knowledge_base.py::test_tsuki_fronteras_exactas` | 4 PASSED | **PASSED** |
| TC-AUTO-005 | La patada frontal exige simultáneamente extensión (Kime ≥ 160°) y explosividad (≥ 400 °/s) | RF-05 | `tests/unit/test_knowledge_base.py::test_mae_geri_fronteras_exactas` | 4 PASSED | **PASSED** |
| TC-AUTO-006 | El analizador identifica la postura ejecutada antes de evaluarla, a partir de los ángulos de ambas rodillas | RF-01, RF-05 | `tests/integration/test_analyzer.py::test_identifica_la_postura_antes_de_evaluarla` | 4 PASSED | **PASSED** |
| TC-AUTO-007 | Una patada correcta recorre Reposo → Carga → Extensión → Recuperando → Reposo y se califica como correcta | RF-01, RF-05 | `tests/integration/test_kick_state_machine.py::test_ciclo_completo_de_una_patada_correcta` | 1 PASSED | **PASSED** |
| TC-AUTO-008 | Perder de vista la pierna más allá de la tolerancia aborta la técnica en vez de emitir un diagnóstico inventado | RF-01, RF-03 | `tests/integration/test_kick_state_machine.py::test_oclusion_prolongada_aborta_la_tecnica` | 1 PASSED | **PASSED** |
| TC-AUTO-009 | Ninguna credencial incorrecta concede acceso al sistema | RF-08 | `tests/integration/test_database.py::test_credenciales_invalidas_no_dan_acceso` | 4 PASSED | **PASSED** |
| TC-AUTO-010 | La contraseña se almacena como hash SHA-256, nunca en texto plano | RNF-05 | `tests/integration/test_database.py::test_la_contrasena_nunca_se_guarda_en_texto_plano` | 1 PASSED | **PASSED** |
| TC-AUTO-011 | Treinta cuadros consecutivos con el mismo diagnóstico generan un único registro en la base de datos | RF-07 | `tests/integration/test_medicion_logger.py::test_treinta_frames_identicos_generan_una_sola_fila` | 1 PASSED | **PASSED** |
| TC-AUTO-012 | El historial de dos sesiones produce un archivo PNG de progreso válido y no vacío | RF-07 | `tests/integration/test_reportes.py::test_genera_un_png_con_el_historial_de_dos_sesiones` | 1 PASSED | **PASSED** |
| TC-AUTO-013 | Al abrir el análisis en vivo con un alumno elegido queda registrada una sesión abierta a su nombre | RF-06, RNF-04 | `tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis` | 1 PASSED | **PASSED** |
| TC-AUTO-014 | Terminar la sesión cierra el registro en la base de datos, libera la cámara y regresa a la selección de perfiles | RF-06, RF-07 | `tests/e2e/test_gui_flow.py::test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` | 1 PASSED | **PASSED** |
| TC-AUTO-015 | El instrumento que mide la latencia del pipeline cronometra cada etapa por separado con un reloj determinista | RNF-01, RF-01 | `tests/unit/test_metrics.py::test_mide_cada_etapa_por_separado` | 1 PASSED | **PASSED** |
| TC-AUTO-016 | Una contraseña equivocada permite reintentar el acceso sin abortar el programa | RF-08 | `tests/integration/test_cli_auth.py::test_reintento_tras_una_contrasena_equivocada` | 1 PASSED | **PASSED** |
| TC-AUTO-017 | Sin persona detectada, el fotograma se devuelve intacto y no se dibuja ningún esqueleto | RF-06 | `tests/integration/test_renderer.py::test_sin_persona_detectada_el_video_se_devuelve_intacto` | 1 PASSED | **PASSED** |
| TC-AUTO-018 | Recalibrar un umbral crea una versión nueva y conserva la anterior en el historial | RF-08 | `tests/integration/test_umbrales.py::test_recalibrar_crea_version_nueva_sin_borrar_la_anterior` | 1 PASSED | **PASSED** |
| TC-AUTO-019 | Una ficha incompleta es rechazada y el error enumera todos los campos que incumplen el formato | RF-08 | `tests/unit/test_plantilla_reporte.py::test_el_error_enumera_todos_los_problemas_de_una_vez` | 1 PASSED | **PASSED** |
| TC-AUTO-020 | El formulario de calibración rechaza todo rango imposible antes de escribirlo en la base de datos | RF-08 | `tests/unit/test_validacion_umbrales.py::test_rechaza_los_rangos_imposibles` | 5 PASSED | **PASSED** |
| TC-AUTO-021 | Recalibrar un umbral desde la interfaz cambia el criterio con el que el sistema experto evalúa, sin modificar el código fuente | RF-08 | `tests/e2e/test_gui_umbrales.py::test_recalibrar_cambia_el_criterio_del_sistema_experto` | 1 PASSED | **PASSED** |
| TC-AUTO-022 | La fuente de video elegida se verifica antes de guardarse y sobrevive al reinicio del sistema | RF-01 | `tests/e2e/test_gui_camara.py::test_la_fuente_elegida_se_verifica_y_persiste` | 1 PASSED | **PASSED** |
| TC-AUTO-023 | Un índice de cámara escrito como texto se convierte a entero antes de llegar a OpenCV | RF-01 | `tests/unit/test_fuentes_video.py::test_los_indices_se_convierten_a_entero` | 4 PASSED | **PASSED** |
| TC-AUTO-024 | La fuente de video configurada persiste entre ejecuciones del sistema | RF-01 | `tests/integration/test_configuracion.py::test_la_preferencia_sobrevive_al_reinicio_del_sistema` | 1 PASSED | **PASSED** |
| TC-AUTO-025 | Un Kokutsu Dachi correctamente ejecutado se reconoce como tal y no como una transición entre posturas | RF-01, RF-05 | `tests/integration/test_analyzer.py::test_un_kokutsu_real_no_se_confunde_con_una_transicion` | 5 PASSED | **PASSED** |
| TC-AUTO-026 | La precisión de un alumno se calcula solo sobre evaluaciones cerradas, ignorando los estados transitorios | RF-07 | `tests/integration/test_consultas_progreso.py::test_la_precision_ignora_los_estados_transitorios` | 1 PASSED | **PASSED** |
| TC-AUTO-027 | El reporte de progreso de un atleta se genera desde la interfaz y produce un archivo de imagen válido | RF-07 | `tests/e2e/test_gui_historial.py::test_el_reporte_de_progreso_se_genera_desde_la_pantalla` | 1 PASSED | **PASSED** |
| TC-AUTO-028 | Ejecutar el programa sin argumentos abre la interfaz gráfica, no la versión de terminal | RNF-04 | `tests/unit/test_punto_de_entrada.py::test_la_linea_de_comandos_elige_la_via_correcta` | 2 PASSED | **PASSED** |
| TC-AUTO-029 | El panel de inicio cuenta la actividad reciente del dojo y descarta la anterior a la ventana de siete días | RF-07 | `tests/integration/test_panel_inicio.py::test_la_ventana_de_actividad_deja_fuera_las_sesiones_viejas` | 1 PASSED | **PASSED** |
| TC-AUTO-030 | El panel de correcciones no repite una corrección que sigue vigente, de modo que la retroalimentación en pantalla conserve solo lo que cambió | RF-05, RF-06 | `tests/unit/test_panel_vivo.py::test_una_correccion_vigente_no_se_vuelve_a_anotar` | 1 PASSED | **PASSED** |
| TC-AUTO-031 | Un grado numérico escrito bajo un color de cinta que no lo admite se descarta al guardar, en vez de producir una ficha que se contradice | RF-07 | `tests/unit/test_registro_alumno.py::test_un_grado_huerfano_no_se_guarda` | 1 PASSED | **PASSED** |
| TC-AUTO-032 | Elegir un perfil de sensei exige su contraseña y no da acceso con un solo clic | RF-08, RNF-05 | `tests/e2e/test_gui_inicio.py::test_cambiar_de_perfil_pide_la_contrasena_del_sensei` | 1 PASSED | **PASSED** |
| TC-AUTO-033 | El video se ajusta al espacio disponible conservando su proporción, en vez de imponer su resolución al resto de la pantalla | RF-01, RF-06 | `tests/e2e/test_gui_vivo.py::test_el_video_se_ajusta_al_hueco_sin_deformarse` | 1 PASSED | **PASSED** |
| TC-AUTO-034 | Todo veredicto que la base de conocimientos puede emitir tiene su corrección redactada para el alumno | RF-05, RF-06 | `tests/unit/test_coaching.py::test_ningun_veredicto_del_motor_se_queda_sin_correccion` | 1 PASSED | **PASSED** |
| TC-AUTO-035 | Una cámara sin nombre se omite de la lista en vez de desplazar a las siguientes, de modo que ningún dispositivo quede etiquetado con el nombre de otro | RF-01 | `tests/unit/test_nombres_camara.py::test_una_camara_sin_nombre_se_omite_en_vez_de_correr_las_demas` | 1 PASSED | **PASSED** |
| TC-AUTO-036 | La asimetría entre lados solo se reporta cuando hay repeticiones suficientes en ambos, de modo que un fallo aislado no se presente como señal de lesión | RF-05, RF-07 | `tests/unit/test_riesgos.py::test_la_asimetria_exige_repeticiones_suficientes_en_ambos_lados` | 1 PASSED | **PASSED** |
| TC-AUTO-037 | Ninguna tarea principal del sistema cuesta más de tres pulsaciones | RNF-04 | `tests/unit/test_navegacion.py::test_ninguna_tarea_pasa_de_tres_pulsaciones` | 1 PASSED | **PASSED** |
| TC-AUTO-038 | Cada tarea principal se completa pulsando los controles reales de la interfaz, en no más de tres pulsaciones desde el panel de inicio | RNF-04 | `tests/e2e/test_navegacion_rnf04.py::test_cada_tarea_principal_se_completa_en_tres_pulsaciones` | 9 PASSED | **PASSED** |
| TC-AUTO-039 | Una medición de Kokutsu Dachi se vuelve a juzgar cuando el sensei corrige el umbral | RF-08 | `tests/unit/test_reevaluacion.py::test_corregir_el_umbral_trasero_cambia_el_veredicto_de_un_kokutsu_guardado` | 1 PASSED | **PASSED** |
| TC-AUTO-040 | Corregir un umbral revela qué mediciones del historial cambiarían de veredicto, sin repetir la toma de datos | RF-08 | `tests/integration/test_recalibracion_retroactiva.py::test_una_correccion_de_umbral_se_aplica_a_lo_ya_medido` | 1 PASSED | **PASSED** |
| TC-AUTO-041 | La velocidad de grabación se deduce del análisis real y no de la que declara la cámara | RF-01 | `tests/unit/test_grabacion.py::test_la_velocidad_se_mide_por_intervalos_no_por_fotogramas` | 1 PASSED | **PASSED** |
| TC-AUTO-042 | Una sesión analizada deja un archivo de video reproducible con todos sus fotogramas | RF-01, RF-07 | `tests/integration/test_grabador.py::test_una_sesion_deja_un_video_reproducible_con_todos_sus_fotogramas` | 1 PASSED | **PASSED** |
| TC-AUTO-043 | Un fallo al escribir el video no interrumpe la sesión de medición | RF-01, RF-07 | `tests/integration/test_grabador.py::test_un_fallo_al_escribir_apaga_la_grabacion_pero_no_levanta` | 1 PASSED | **PASSED** |
| TC-AUTO-044 | Una sesión de análisis en vivo deja un video atado a la sesión en la base de datos | RF-01, RF-07 | `tests/e2e/test_gui_vivo.py::test_una_sesion_en_vivo_deja_video_atado_a_la_sesion` | 1 PASSED | **PASSED** |
| TC-AUTO-045 | Una sesión grabada se puede elegir como fuente y queda configurada para volver a analizarse | RF-01 | `tests/e2e/test_gui_camara.py::test_una_grabacion_se_elige_y_queda_configurada` | 1 PASSED | **PASSED** |
| TC-AUTO-046 | El instructor decide si las sesiones se graban, y la decisión persiste entre arranques | RF-01 | `tests/e2e/test_gui_camara.py::test_el_instructor_decide_si_se_graba_y_se_recuerda` | 1 PASSED | **PASSED** |
| TC-AUTO-047 | El impacto de una recalibración se expresa en veredictos que cambian, no en filas | RF-08 | `tests/unit/test_impacto_umbrales.py::test_el_titular_cuenta_los_cambios_sobre_las_juzgadas` | 1 PASSED | **PASSED** |
| TC-AUTO-048 | Antes de adoptar una recalibración, el sistema informa cuántas mediciones del historial cambiarían de veredicto | RF-08 | `tests/e2e/test_gui_umbrales.py::test_el_impacto_se_ve_antes_de_guardar` | 1 PASSED | **PASSED** |
| TC-AUTO-049 | El tiempo de una grabación lo dicta el video y no la velocidad a la que se analiza | RF-01, RF-05 | `tests/integration/test_marca_de_tiempo.py::test_una_pausa_en_el_analisis_no_altera_el_tiempo_de_la_grabacion` | 1 PASSED | **PASSED** |

## 5. Detalle de ejecución

### `tests/e2e/test_gui_camara.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_lista_las_camaras_detectadas_en_el_equipo` | PASSED | 368.6 |
| `test_la_fuente_elegida_se_verifica_y_persiste` | PASSED | 61.8 |
| `test_una_camara_que_no_abre_no_se_guarda` | PASSED | 56.2 |
| `test_una_camara_que_abre_pero_no_entrega_imagen_se_rechaza` | PASSED | 54.7 |
| `test_la_camara_ip_se_guarda_como_direccion_completa` | PASSED | 63.1 |
| `test_elegir_camara_ip_sin_escribir_la_direccion_avisa` | PASSED | 52.7 |
| `test_avisa_cuando_la_camara_configurada_ya_no_esta_conectada` | PASSED | 53.3 |
| `test_volver_regresa_al_panel_de_inicio` | PASSED | 61.2 |
| `test_abrir_la_pantalla_con_una_camara_ip_ya_configurada_no_inventa_un_error` | PASSED | 65.0 |
| `test_una_grabacion_se_elige_y_queda_configurada` | PASSED | 52.6 |
| `test_la_grabacion_configurada_se_precarga_al_volver_a_la_pantalla` | PASSED | 52.9 |
| `test_un_archivo_que_no_esta_se_rechaza_antes_de_intentar_abrirlo` | PASSED | 51.8 |
| `test_una_grabacion_a_medio_escribir_se_rechaza_nombrando_la_causa` | PASSED | 52.8 |
| `test_sin_archivo_escrito_el_aviso_menciona_las_tres_opciones` | PASSED | 53.3 |
| `test_elegir_una_camara_del_sistema_sigue_funcionando` | PASSED | 53.0 |
| `test_el_instructor_decide_si_se_graba_y_se_recuerda` | PASSED | 65.2 |
| `test_el_texto_explica_que_implica_el_estado_no_que_hace_el_boton` | PASSED | 52.0 |
| `test_apagar_la_grabacion_no_toca_la_fuente_de_video` | PASSED | 54.3 |

### `tests/e2e/test_gui_flow.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_arranque_pide_crear_la_cuenta_inicial` | PASSED | 39.3 |
| `test_crear_la_primera_cuenta_lleva_al_panel_de_inicio` | PASSED | 42.5 |
| `test_no_permite_crear_una_cuenta_incompleta` | PASSED | 20.7 |
| `test_login_con_credenciales_correctas` | PASSED | 40.4 |
| `test_login_con_credenciales_incorrectas_muestra_error` | PASSED | 21.0 |
| `test_elegir_un_perfil_abre_la_sesion_de_analisis` | PASSED | 250.7 |
| `test_el_video_se_embebe_en_la_ventana` | PASSED | 160.3 |
| `test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` | PASSED | 186.4 |
| `test_el_acceso_no_muestra_barra_lateral` | PASSED | 21.4 |
| `test_tras_autenticarse_aparece_la_barra_con_la_seccion_de_inicio_activa` | PASSED | 41.0 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[inicio-InicioScreen]` | PASSED | 48.9 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[vivo-LiveScreen]` | PASSED | 53.6 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[historial-HistorialScreen]` | PASSED | 46.5 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[tecnicas-TecnicasScreen]` | PASSED | 62.0 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[camara-CamaraScreen]` | PASSED | 527.6 |
| `test_la_calibracion_se_alcanza_desde_tecnicas_y_no_desde_la_barra` | PASSED | 83.7 |
| `test_la_barra_sobrevive_al_cambiar_de_seccion` | PASSED | 62.3 |
| `test_el_detalle_de_un_alumno_conserva_marcada_la_seccion_de_historial` | PASSED | 50.6 |
| `test_cerrar_sesion_de_entrenador_retira_la_barra_y_vuelve_al_acceso` | PASSED | 45.0 |
| `test_un_usuario_repetido_se_explica_en_pantalla_en_vez_de_reventar` | PASSED | 21.6 |

### `tests/e2e/test_gui_historial.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_historial_lista_a_todos_los_alumnos` | PASSED | 54.0 |
| `test_el_alumno_sin_entrenar_aparece_sin_precision` | PASSED | 57.0 |
| `test_volver_desde_el_historial_regresa_a_perfiles` | PASSED | 66.9 |
| `test_el_reporte_de_progreso_se_genera_desde_la_pantalla` | PASSED | 193.2 |
| `test_sin_evaluaciones_cerradas_se_explica_en_vez_de_generar_un_grafico_vacio` | PASSED | 50.6 |
| `test_el_perfil_muestra_el_desempeno_por_tecnica` | PASSED | 57.6 |
| `test_el_reporte_de_sesion_resume_y_ordena_los_errores` | PASSED | 55.7 |
| `test_un_reporte_de_sesion_inexistente_no_rompe_la_pantalla` | PASSED | 44.3 |
| `test_volver_desde_el_reporte_regresa_al_perfil_del_alumno` | PASSED | 65.3 |
| `test_la_biblioteca_muestra_las_tecnicas_que_el_sistema_evalua` | PASSED | 57.7 |
| `test_la_biblioteca_refleja_una_recalibracion_del_entrenador` | PASSED | 58.1 |
| `test_desde_la_biblioteca_se_llega_a_la_calibracion` | PASSED | 105.1 |
| `test_el_reporte_nombra_el_video_de_la_sesion` | PASSED | 59.4 |
| `test_una_sesion_sin_video_lo_declara_en_vez_de_omitirlo` | PASSED | 57.1 |

### `tests/e2e/test_gui_inicio.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_tras_autenticarse_se_abre_el_panel_de_inicio` | PASSED | 42.3 |
| `test_un_dojo_sin_actividad_lo_dice_en_vez_de_mostrar_cifras_en_cero` | PASSED | 41.0 |
| `test_el_panel_refleja_la_actividad_real_del_dojo` | PASSED | 51.4 |
| `test_el_panel_declara_que_no_hay_sensores_inerciales` | PASSED | 40.7 |
| `test_desde_el_inicio_se_llega_al_analisis_en_vivo_y_al_historial` | PASSED | 66.6 |
| `test_cambiar_de_perfil_pide_la_contrasena_del_sensei` | PASSED | 58.3 |
| `test_la_seleccion_lista_senseis_y_no_alumnos` | PASSED | 47.0 |
| `test_la_lista_de_senseis_nunca_expone_el_hash_de_la_contrasena` | PASSED | 4.8 |
| `test_los_alumnos_se_inscriben_desde_su_propia_seccion` | PASSED | 139.0 |
| `test_el_campo_de_grado_solo_aparece_para_cinta_cafe_o_negra` | PASSED | 89.7 |
| `test_un_formulario_invalido_no_inscribe_a_nadie` | PASSED | 95.3 |
| `test_abrir_el_registro_dos_veces_no_duplica_la_ventana` | PASSED | 88.2 |
| `test_el_reporte_señala_la_asimetria_entre_lados` | PASSED | 68.4 |
| `test_una_sesion_limpia_declara_que_no_hay_senales_de_riesgo` | PASSED | 74.5 |
| `test_el_reporte_traduce_los_errores_a_instrucciones` | PASSED | 64.5 |

### `tests/e2e/test_gui_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_pantalla_lista_todos_los_umbrales_vigentes` | PASSED | 73.2 |
| `test_recalibrar_cambia_el_criterio_del_sistema_experto` | PASSED | 89.4 |
| `test_un_campo_invalido_no_guarda_ninguno_de_los_cambios` | PASSED | 68.9 |
| `test_guardar_sin_tocar_nada_no_crea_versiones_nuevas` | PASSED | 63.6 |
| `test_descartar_devuelve_los_campos_al_valor_vigente` | PASSED | 83.3 |
| `test_sin_entrenador_la_pantalla_queda_en_solo_lectura` | PASSED | 47.4 |
| `test_el_historial_abre_una_sola_ventana_con_las_versiones_del_umbral` | PASSED | 142.4 |
| `test_una_base_sin_umbrales_lo_informa_en_vez_de_mostrar_una_tabla_vacia` | PASSED | 65.7 |
| `test_volver_regresa_al_panel_de_inicio` | PASSED | 82.2 |
| `test_el_impacto_se_ve_antes_de_guardar` | PASSED | 132.5 |
| `test_ver_el_impacto_no_guarda_el_umbral_ni_toca_las_mediciones` | PASSED | 152.4 |
| `test_un_ajuste_que_no_mueve_nada_tambien_se_informa` | PASSED | 133.2 |
| `test_sin_cambios_escritos_no_se_abre_la_ventana` | PASSED | 96.8 |
| `test_un_valor_mal_escrito_se_avisa_en_vez_de_calcular_con_el` | PASSED | 69.7 |
| `test_el_impacto_contrasta_contra_el_criterio_completo_no_solo_el_campo_editado` | PASSED | 140.1 |

### `tests/e2e/test_gui_vivo.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_sin_alumno_elegido_no_se_abre_la_camara_ni_se_crea_sesion` | PASSED | 61.3 |
| `test_el_desplegable_ofrece_a_todos_los_alumnos_inscritos` | PASSED | 164.5 |
| `test_cambiar_de_alumno_cierra_la_sesion_anterior_y_abre_otra` | PASSED | 267.5 |
| `test_elegir_al_mismo_alumno_no_abre_una_sesion_nueva` | PASSED | 164.1 |
| `test_salir_de_la_seccion_cierra_la_sesion_en_curso` | PASSED | 181.4 |
| `test_el_video_se_ajusta_al_hueco_sin_deformarse` | PASSED | 164.3 |
| `test_el_escalado_nunca_devuelve_un_tamano_nulo` | PASSED | 159.4 |
| `test_un_fotograma_grande_no_agranda_el_contenedor_del_video` | PASSED | 175.4 |
| `test_el_tamano_de_dibujado_no_altera_los_angulos_medidos` | PASSED | 160.4 |
| `test_sin_alumno_elegido_el_desplegable_no_nombra_al_primero_de_la_lista` | PASSED | 55.1 |
| `test_sin_alumnos_inscritos_el_desplegable_lo_declara` | PASSED | 55.8 |
| `test_una_sesion_en_vivo_deja_video_atado_a_la_sesion` | PASSED | 467.5 |
| `test_el_video_lleva_el_nombre_del_alumno_medido` | PASSED | 478.6 |
| `test_el_video_grabado_se_puede_volver_a_abrir_como_fuente_de_analisis` | PASSED | 478.9 |
| `test_con_la_grabacion_apagada_la_sesion_se_mide_igual_y_lo_dice` | PASSED | 384.4 |
| `test_la_pantalla_en_vivo_anuncia_si_esta_grabando` | PASSED | 165.1 |
| `test_con_la_grabacion_apagada_la_pantalla_lo_dice_en_vez_de_callarlo` | PASSED | 155.2 |
| `test_analizar_una_grabacion_no_produce_un_duplicado` | PASSED | 458.2 |
| `test_la_sesion_apunta_al_archivo_que_se_analizo` | PASSED | 316.0 |
| `test_la_pantalla_dice_que_esta_analizando_una_grabacion` | PASSED | 157.7 |

### `tests/e2e/test_navegacion_rnf04.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[medir]` | PASSED | 180.8 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[inscribir]` | PASSED | 125.5 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[progreso]` | PASSED | 108.3 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[reporte]` | PASSED | 137.9 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[grafica]` | PASSED | 248.8 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[tecnicas]` | PASSED | 112.4 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[calibrar]` | PASSED | 247.1 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[camara]` | PASSED | 86.0 |
| `test_cada_tarea_principal_se_completa_en_tres_pulsaciones[sensei]` | PASSED | 182.7 |
| `test_inscribir_un_alumno_lo_deja_registrado` | PASSED | 215.9 |
| `test_recalibrar_deja_una_version_nueva_del_umbral` | PASSED | 273.6 |
| `test_medir_abre_una_sesion_a_nombre_del_alumno_elegido` | PASSED | 181.1 |
| `test_cambiar_la_camara_la_deja_configurada` | PASSED | 93.7 |
| `test_cambiar_de_sensei_exige_la_contrasena` | PASSED | 101.5 |
| `test_el_recorrido_no_llama_a_update` | PASSED | 190.6 |
| `test_un_control_que_no_existe_hace_fallar_el_recorrido` | PASSED | 50.6 |

### `tests/integration/test_analyzer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_evalua_los_dos_brazos_de_forma_independiente` | PASSED | 0.2 |
| `test_el_angulo_medido_coincide_con_la_pose_ejecutada` | PASSED | 0.3 |
| `test_brazo_no_visible_se_informa_en_vez_de_inventar_diagnostico` | PASSED | 0.2 |
| `test_el_filtro_se_reinicia_cuando_el_brazo_desaparece` | PASSED | 0.3 |
| `test_el_suavizado_amortigua_un_salto_de_jitter` | PASSED | 0.2 |
| `test_identifica_la_postura_antes_de_evaluarla[posicion natural-175-175-POSTURA NATURAL]` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[postura de jinete-140-140-KIBA DACHI]` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[postura adelantada-100-170-ZENKUTSU]` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[postura atrasada-165-105-KOKUTSU]` | PASSED | 0.3 |
| `test_la_guardia_se_deduce_de_la_profundidad_de_los_tobillos` | PASSED | 0.2 |
| `test_una_transicion_no_se_califica_como_error` | PASSED | 0.2 |
| `test_kiba_dachi_mal_ejecutado_se_detecta_pero_se_corrige` | PASSED | 0.2 |
| `test_piernas_no_visibles_se_informan_sin_calificar` | PASSED | 0.2 |
| `test_una_patada_completa_atraviesa_el_analizador` | PASSED | 0.2 |
| `test_cada_pierna_tiene_su_propia_maquina_de_estados` | PASSED | 0.2 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_tsuki]` | PASSED | 0.2 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_stance]` | PASSED | 0.2 |
| `test_las_lineas_de_texto_no_se_encimam_en_pantalla` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[170-100]` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[165-105]` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[160-110]` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[155-115]` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[150-120]` | PASSED | 0.2 |
| `test_zenkutsu_y_kokutsu_no_se_confunden_entre_si` | PASSED | 0.2 |
| `test_la_postura_declara_con_que_tecnica_se_juzgo` | PASSED | 0.2 |
| `test_la_postura_lleva_los_dos_angulos_con_que_la_regla_la_juzgo` | PASSED | 0.2 |
| `test_los_angulos_de_la_regla_siguen_a_la_guardia_no_al_lado_de_la_pantalla` | PASSED | 0.2 |
| `test_una_transicion_no_declara_tecnica_ni_angulos_de_regla` | PASSED | 0.2 |
| `test_un_tsuki_declara_su_tecnica_y_su_unico_angulo` | PASSED | 0.2 |

### `tests/integration/test_cli_auth.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_uso_registra_al_entrenador_principal` | PASSED | 4.9 |
| `test_login_exitoso_de_un_entrenador_existente` | PASSED | 4.5 |
| `test_reintento_tras_una_contrasena_equivocada` | PASSED | 4.4 |
| `test_tras_fallar_puede_crear_una_cuenta_de_sensei_asistente` | PASSED | 4.5 |
| `test_elegir_un_perfil_existente_de_la_lista` | PASSED | 4.5 |
| `test_crear_un_perfil_nuevo_desde_la_lista` | PASSED | 4.3 |
| `test_el_grado_del_cinturon_es_opcional` | PASSED | 4.1 |
| `test_una_opcion_invalida_vuelve_a_preguntar[abc-texto en vez de n\xfamero]` | PASSED | 4.2 |
| `test_una_opcion_invalida_vuelve_a_preguntar[0-n\xfamero fuera de rango por abajo]` | PASSED | 4.3 |
| `test_una_opcion_invalida_vuelve_a_preguntar[99-n\xfamero fuera de rango por arriba]` | PASSED | 4.5 |

### `tests/integration/test_configuracion.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_preferencia_no_configurada_devuelve_el_valor_por_defecto` | PASSED | 3.8 |
| `test_la_preferencia_sobrevive_al_reinicio_del_sistema` | PASSED | 4.0 |
| `test_reconfigurar_reemplaza_en_vez_de_duplicar` | PASSED | 4.2 |
| `test_los_valores_se_guardan_como_texto` | PASSED | 3.8 |
| `test_la_migracion_no_toca_una_base_ya_existente` | PASSED | 4.1 |

### `tests/integration/test_consultas_progreso.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_precision_ignora_los_estados_transitorios` | PASSED | 7.4 |
| `test_un_alumno_sin_mediciones_aparece_con_precision_desconocida` | PASSED | 7.2 |
| `test_todos_los_alumnos_aparecen_aunque_no_hayan_entrenado` | PASSED | 7.5 |
| `test_las_sesiones_se_listan_de_la_mas_reciente_a_la_mas_antigua` | PASSED | 8.0 |
| `test_cada_sesion_trae_su_propia_precision` | PASSED | 7.6 |
| `test_una_sesion_abierta_se_distingue_de_una_cerrada` | PASSED | 7.7 |
| `test_un_alumno_sin_sesiones_devuelve_lista_vacia` | PASSED | 8.1 |
| `test_las_tecnicas_se_ordenan_de_la_mas_floja_a_la_mas_solida` | PASSED | 8.3 |
| `test_el_desempeno_puede_acotarse_a_una_sola_sesion` | PASSED | 8.1 |
| `test_el_angulo_medio_se_promedia_por_tecnica` | PASSED | 7.4 |
| `test_el_detalle_de_sesion_identifica_al_alumno_y_al_entrenador` | PASSED | 7.5 |
| `test_una_sesion_inexistente_devuelve_none` | PASSED | 7.7 |
| `test_los_errores_se_agrupan_y_ordenan_por_frecuencia` | PASSED | 7.2 |
| `test_una_sesion_sin_errores_no_reporta_correcciones` | PASSED | 8.2 |

### `tests/integration/test_database.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_primer_arranque_no_tiene_entrenadores` | PASSED | 3.6 |
| `test_registro_y_autenticacion_exitosa` | PASSED | 4.3 |
| `test_credenciales_invalidas_no_dan_acceso[sholweger-clave_incorrecta-contrase\xf1a equivocada]` | PASSED | 4.0 |
| `test_credenciales_invalidas_no_dan_acceso[usuario_inexistente-clave123-usuario que no existe]` | PASSED | 4.2 |
| `test_credenciales_invalidas_no_dan_acceso[SHOLWEGER-clave123-usuario con distinta capitalizaci\xf3n]` | PASSED | 4.4 |
| `test_credenciales_invalidas_no_dan_acceso[--credenciales vac\xedas]` | PASSED | 4.2 |
| `test_la_contrasena_nunca_se_guarda_en_texto_plano` | PASSED | 4.0 |
| `test_no_se_permiten_dos_entrenadores_con_el_mismo_usuario` | PASSED | 3.9 |
| `test_el_rol_por_defecto_es_sensei` | PASSED | 4.2 |
| `test_los_atletas_se_listan_alfabeticamente` | PASSED | 4.5 |
| `test_crear_atleta_devuelve_un_identificador_utilizable` | PASSED | 3.9 |
| `test_los_datos_opcionales_del_atleta_pueden_omitirse` | PASSED | 3.9 |
| `test_una_sesion_abierta_no_tiene_hora_de_fin` | PASSED | 4.7 |
| `test_cerrar_sesion_registra_la_hora_de_fin` | PASSED | 4.8 |
| `test_la_sesion_queda_ligada_al_atleta_y_al_entrenador` | PASSED | 4.5 |
| `test_guardar_y_recuperar_una_medicion` | PASSED | 5.2 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[True-1]` | PASSED | 4.8 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[False-0]` | PASSED | 5.8 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[None-None]` | PASSED | 5.9 |
| `test_el_historial_solo_devuelve_las_mediciones_del_atleta_consultado` | PASSED | 6.0 |
| `test_un_atleta_sin_entrenamientos_tiene_historial_vacio` | PASSED | 4.3 |
| `test_las_mediciones_sobreviven_al_cierre_de_la_aplicacion` | PASSED | 5.3 |
| `test_migra_una_base_de_datos_creada_sin_la_columna_correcto` | PASSED | 6.4 |
| `test_abrir_dos_veces_la_misma_base_no_duplica_el_esquema` | PASSED | 4.4 |

### `tests/integration/test_grabador.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_sesion_deja_un_video_reproducible_con_todos_sus_fotogramas` | PASSED | 16.3 |
| `test_los_fotogramas_retenidos_para_estimar_no_se_pierden` | PASSED | 6.2 |
| `test_una_sesion_mas_corta_que_el_tramo_de_estimacion_igual_deja_video` | PASSED | 4.9 |
| `test_una_sesion_sin_un_solo_fotograma_no_inventa_un_archivo` | PASSED | 0.7 |
| `test_la_velocidad_escrita_es_la_medida_y_no_la_nominal_de_la_camara` | PASSED | 10.1 |
| `test_un_fallo_al_escribir_apaga_la_grabacion_pero_no_levanta` | PASSED | 6.9 |
| `test_tras_un_fallo_el_resumen_explica_por_que_no_hay_video` | PASSED | 0.7 |
| `test_sin_codec_disponible_la_grabacion_se_apaga_con_su_motivo` | PASSED | 1.0 |
| `test_escribir_none_no_rompe_nada` | PASSED | 0.6 |

### `tests/integration/test_kick_state_machine.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_ciclo_completo_de_una_patada_correcta` | PASSED | 0.2 |
| `test_no_reporta_nada_mientras_el_atleta_esta_quieto` | PASSED | 0.2 |
| `test_patada_lenta_se_diagnostica_sin_explosividad` | PASSED | 0.2 |
| `test_hikiashi_incorrecto_cuando_la_pierna_cae_sin_recogerse` | PASSED | 0.2 |
| `test_mantiene_el_aviso_mientras_la_pierna_sigue_extendida` | PASSED | 0.1 |
| `test_intento_abandonado_en_carga_se_descarta_por_timeout` | PASSED | 0.2 |
| `test_kime_sostenido_demasiado_tiempo_se_descarta_por_timeout` | PASSED | 0.2 |
| `test_oclusion_breve_no_interrumpe_la_tecnica` | PASSED | 0.1 |
| `test_oclusion_prolongada_aborta_la_tecnica` | PASSED | 0.2 |
| `test_dos_patadas_seguidas_se_evaluan_de_forma_independiente` | PASSED | 0.2 |
| `test_reset_deja_la_maquina_como_recien_creada` | PASSED | 0.1 |
| `test_todo_diagnostico_trae_las_claves_que_consume_la_capa_visual` | PASSED | 0.2 |

### `tests/integration/test_marca_de_tiempo.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_pausa_en_el_analisis_no_altera_el_tiempo_de_la_grabacion` | PASSED | 1559.6 |
| `test_las_marcas_avanzan_al_ritmo_declarado_por_el_video` | PASSED | 28.0 |
| `test_la_grabacion_empieza_en_cero` | PASSED | 15.6 |
| `test_una_fuente_en_vivo_sigue_usando_el_reloj_de_pared` | PASSED | 51.4 |
| `test_una_posicion_repetida_no_detiene_la_marca` | PASSED | 0.3 |
| `test_una_posicion_que_retrocede_tampoco_detiene_la_marca` | PASSED | 0.3 |
| `test_al_rellenar_se_avanza_un_intervalo_de_fotograma_y_no_un_epsilon` | PASSED | 0.3 |

### `tests/integration/test_medicion_logger.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_treinta_frames_identicos_generan_una_sola_fila` | PASSED | 10.5 |
| `test_cada_cambio_real_de_diagnostico_se_registra` | PASSED | 8.6 |
| `test_un_diagnostico_repetido_tras_cambiar_se_vuelve_a_registrar` | PASSED | 8.1 |
| `test_las_categorias_se_rastrean_por_separado` | PASSED | 7.9 |
| `test_traduce_la_categoria_interna_a_un_nombre_legible` | PASSED | 7.6 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico0-mensaje vac\xedo (solo dibuja el n\xfamero del \xe1ngulo en pantalla)]` | PASSED | 5.6 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico1-sin categor\xeda]` | PASSED | 6.2 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico2-diccionario incompleto]` | PASSED | 5.0 |
| `test_conserva_angulo_veredicto_y_marca_de_tiempo` | PASSED | 5.3 |
| `test_registra_una_lista_completa_de_diagnosticos_de_un_frame` | PASSED | 5.6 |
| `test_la_fila_guarda_que_tecnica_se_detecto` | PASSED | 4.9 |
| `test_la_fila_guarda_los_dos_angulos_de_una_postura_de_dos_articulaciones` | PASSED | 5.0 |
| `test_una_tecnica_de_un_solo_angulo_deja_el_segundo_vacio` | PASSED | 4.9 |
| `test_una_transicion_se_guarda_sin_tecnica_ni_angulos_de_regla` | PASSED | 5.2 |
| `test_un_diagnostico_sin_los_campos_nuevos_sigue_guardandose` | PASSED | 5.4 |
| `test_las_mediciones_reevaluables_excluyen_las_que_no_se_pueden_juzgar` | PASSED | 5.3 |

### `tests/integration/test_panel_inicio.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_un_alumno_puede_inscribirse_solo_con_su_nombre` | PASSED | 4.1 |
| `test_la_ficha_completa_se_guarda_y_se_recupera` | PASSED | 4.1 |
| `test_un_alumno_inexistente_devuelve_none_en_vez_de_reventar` | PASSED | 3.8 |
| `test_la_migracion_agrega_la_ficha_a_una_base_que_ya_tenia_alumnos` | PASSED | 5.4 |
| `test_un_dojo_sin_actividad_no_reporta_cero_por_ciento` | PASSED | 4.1 |
| `test_la_ventana_de_actividad_deja_fuera_las_sesiones_viejas` | PASSED | 8.3 |
| `test_los_estados_transitorios_no_alteran_las_metricas_del_panel` | PASSED | 7.2 |
| `test_las_sesiones_recientes_abarcan_a_todo_el_dojo` | PASSED | 5.3 |
| `test_las_sesiones_recientes_respetan_el_limite` | PASSED | 6.2 |
| `test_sin_sesiones_la_lista_viene_vacia_y_no_falla` | PASSED | 3.8 |
| `test_las_tecnicas_se_ordenan_por_cuanto_se_practican` | PASSED | 9.3 |
| `test_las_tecnicas_practicadas_pueden_acotarse_a_la_ventana_reciente` | PASSED | 6.3 |
| `test_el_desempeno_se_separa_por_lado_del_cuerpo` | PASSED | 10.3 |
| `test_los_diagnosticos_sin_lado_no_se_atribuyen_a_ninguno` | PASSED | 6.9 |
| `test_se_cuentan_los_diagnosticos_que_contienen_un_fragmento` | PASSED | 10.7 |
| `test_una_sesion_sin_mediciones_devuelve_ceros_y_no_none` | PASSED | 4.7 |

### `tests/integration/test_recalibracion_retroactiva.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_correccion_de_umbral_se_aplica_a_lo_ya_medido` | PASSED | 5.3 |
| `test_una_correccion_que_no_afecta_nada_lo_dice_con_claridad` | PASSED | 5.0 |
| `test_la_recalibracion_no_reescribe_el_veredicto_registrado` | PASSED | 5.3 |
| `test_la_cobertura_avisa_cuando_el_informe_abarca_poco` | PASSED | 5.2 |

### `tests/integration/test_renderer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_sin_persona_detectada_el_video_se_devuelve_intacto` | PASSED | 0.4 |
| `test_dibuja_el_esqueleto_cuando_hay_pose` | PASSED | 0.5 |
| `test_el_mapa_anatomico_no_referencia_puntos_inexistentes` | PASSED | 0.2 |
| `test_dibuja_el_texto_del_diagnostico` | PASSED | 0.4 |
| `test_un_diagnostico_sin_angulo_no_rompe_el_dibujado` | PASSED | 0.4 |
| `test_una_lista_vacia_de_diagnosticos_deja_el_frame_igual` | PASSED | 0.3 |
| `test_el_color_del_diagnostico_llega_al_frame` | PASSED | 0.6 |

### `tests/integration/test_reportes.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_calcula_el_porcentaje_de_aciertos[veredictos0-100.0]` | PASSED | 0.2 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos1-75.0]` | PASSED | 0.2 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos2-50.0]` | PASSED | 0.2 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos3-0.0]` | PASSED | 0.2 |
| `test_los_estados_transitorios_no_alteran_el_porcentaje` | PASSED | 0.1 |
| `test_sin_evaluaciones_cerradas_no_hay_porcentaje` | PASSED | 0.1 |
| `test_no_genera_grafica_si_la_sesion_no_dejo_evaluaciones` | PASSED | 5.6 |
| `test_genera_un_png_con_el_historial_de_dos_sesiones` | PASSED | 126.8 |
| `test_crea_la_carpeta_de_evidencias_si_no_existe` | PASSED | 116.5 |
| `test_dos_reportes_seguidos_no_se_sobrescriben` | PASSED | 226.6 |

### `tests/integration/test_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_siembra_es_idempotente` | PASSED | 5.5 |
| `test_las_reglas_usan_los_umbrales_de_la_base` | PASSED | 4.5 |
| `test_recalibrar_crea_version_nueva_sin_borrar_la_anterior` | PASSED | 4.6 |
| `test_la_medicion_conserva_el_umbral_que_la_juzgo` | PASSED | 6.7 |
| `test_rechaza_un_maximo_menor_que_el_minimo` | PASSED | 4.0 |
| `test_la_maquina_de_estados_hereda_el_umbral_de_kime` | PASSED | 4.7 |
| `test_sin_base_de_datos_usa_los_valores_de_literatura` | PASSED | 0.1 |
| `test_un_umbral_sin_maximo_no_limita_por_arriba` | PASSED | 0.1 |
| `test_una_correccion_de_literatura_alcanza_a_una_base_ya_sembrada` | PASSED | 5.3 |
| `test_una_correccion_no_pisa_lo_que_el_entrenador_recalibro` | PASSED | 4.5 |
| `test_aplicar_la_correccion_dos_veces_no_crea_versiones_repetidas` | PASSED | 4.1 |

### `tests/unit/test_coaching.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_ningun_veredicto_del_motor_se_queda_sin_correccion` | PASSED | 0.5 |
| `test_la_tabla_no_esta_vacia` | PASSED | 0.1 |
| `test_la_correccion_dice_que_hacer_y_por_que` | PASSED | 0.1 |
| `test_el_lado_se_separa_del_veredicto[IZQ - TSUKI: EXCELENTE-izquierdo]` | PASSED | 0.2 |
| `test_el_lado_se_separa_del_veredicto[DER - TSUKI: EXCELENTE-derecho]` | PASSED | 0.2 |
| `test_el_lado_se_separa_del_veredicto[POSTURA: FIRME-None]` | PASSED | 0.2 |
| `test_el_lado_aparece_en_la_instruccion` | PASSED | 0.1 |
| `test_un_veredicto_desconocido_se_muestra_tal_cual_en_vez_de_inventar_consejo` | PASSED | 0.1 |
| `test_un_mensaje_vacio_no_revienta` | PASSED | 0.1 |

### `tests/unit/test_filters.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_primera_medicion_se_devuelve_intacta` | PASSED | 0.1 |
| `test_promedia_mientras_el_buffer_se_llena` | PASSED | 0.1 |
| `test_la_ventana_descarta_la_medicion_mas_antigua` | PASSED | 0.1 |
| `test_ventana_de_uno_no_suaviza` | PASSED | 0.1 |
| `test_reset_borra_el_historial` | PASSED | 0.1 |
| `test_reduce_la_dispersion_del_ruido` | PASSED | 0.2 |
| `test_conserva_el_nivel_de_una_senal_estable` | PASSED | 0.1 |
| `test_converge_tras_un_cambio_brusco_de_postura` | PASSED | 0.1 |

### `tests/unit/test_fuentes_video.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_reconoce_una_camara_de_red[http://192.168.1.50:8080/video]` | PASSED | 0.2 |
| `test_reconoce_una_camara_de_red[https://camara.dojo.local/stream]` | PASSED | 0.2 |
| `test_reconoce_una_camara_de_red[rtsp://192.168.0.10:554/live]` | PASSED | 0.2 |
| `test_reconoce_una_camara_de_red[  http://10.0.0.4:4747/video  ]` | PASSED | 0.2 |
| `test_reconoce_una_camara_de_red[HTTP://192.168.1.50:8080/video]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[0_0]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[1]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[2_0]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[0_1]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[2_1]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[camara]` | PASSED | 0.2 |
| `test_no_confunde_un_dispositivo_local_con_una_direccion[None]` | PASSED | 0.2 |
| `test_los_indices_se_convierten_a_entero[0-0_0]` | PASSED | 0.2 |
| `test_los_indices_se_convierten_a_entero[2-2_0]` | PASSED | 0.2 |
| `test_los_indices_se_convierten_a_entero[0-0_1]` | PASSED | 0.2 |
| `test_los_indices_se_convierten_a_entero[2-2_1]` | PASSED | 0.2 |
| `test_una_url_se_conserva_como_texto_y_sin_espacios` | PASSED | 0.1 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[camara]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[None]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[1.2.3]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[\xedndice dos]` | PASSED | 0.2 |
| `test_la_descripcion_distingue_red_de_dispositivo_local` | PASSED | 0.1 |
| `test_una_grabacion_se_reconoce_como_archivo[sesion.mp4]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[grabaciones/kihon.MOV]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[/Users/sebastian/tatami.avi]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[prueba.mkv]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[captura.webm]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[video.m4v]` | PASSED | 0.2 |
| `test_una_grabacion_se_reconoce_como_archivo[clip.mpeg]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[0]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[2]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[camara]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[sesion]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[notas.txt]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[carpeta.mp4/algo]` | PASSED | 0.2 |
| `test_lo_que_no_es_una_grabacion_no_se_confunde_con_una[None]` | PASSED | 0.2 |
| `test_una_transmision_de_red_con_extension_de_video_sigue_siendo_una_url` | PASSED | 0.1 |
| `test_la_descripcion_distingue_una_grabacion_de_una_camara` | PASSED | 0.1 |
| `test_el_mensaje_de_error_menciona_las_tres_formas_validas` | PASSED | 0.1 |
| `test_una_grabacion_existente_sirve_como_fuente` | PASSED | 0.9 |
| `test_un_archivo_que_no_esta_lo_dice_en_castellano` | PASSED | 0.6 |
| `test_un_archivo_vacio_se_rechaza_como_grabacion_interrumpida` | PASSED | 0.7 |
| `test_una_carpeta_no_es_una_grabacion` | PASSED | 0.7 |
| `test_un_archivo_que_no_es_video_se_rechaza_nombrando_lo_aceptado` | PASSED | 0.8 |
| `test_una_url_se_redirige_a_la_opcion_correcta` | PASSED | 0.1 |
| `test_sin_archivo_elegido_no_se_inventa_un_error_tecnico[None]` | PASSED | 0.2 |
| `test_sin_archivo_elegido_no_se_inventa_un_error_tecnico[]` | PASSED | 0.2 |
| `test_sin_archivo_elegido_no_se_inventa_un_error_tecnico[   ]` | PASSED | 0.2 |
| `test_se_prefiere_la_marca_que_declara_el_contenedor` | PASSED | 0.1 |
| `test_sin_marca_del_contenedor_se_deduce_del_indice_y_la_velocidad` | PASSED | 0.1 |
| `test_el_primer_fotograma_esta_legitimamente_en_cero` | PASSED | 0.1 |
| `test_sin_informacion_utilizable_se_devuelve_none_y_no_un_cero[None-30.0]` | PASSED | 0.2 |
| `test_sin_informacion_utilizable_se_devuelve_none_y_no_un_cero[10-None]` | PASSED | 0.2 |
| `test_sin_informacion_utilizable_se_devuelve_none_y_no_un_cero[10-0]` | PASSED | 0.2 |
| `test_sin_informacion_utilizable_se_devuelve_none_y_no_un_cero[-1-30.0]` | PASSED | 0.2 |

### `tests/unit/test_geometry.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_calcula_el_angulo_interno_conocido[angulo recto-a0-b0-c0-90.0]` | PASSED | 0.3 |
| `test_calcula_el_angulo_interno_conocido[extension total-a1-b1-c1-180.0]` | PASSED | 0.3 |
| `test_calcula_el_angulo_interno_conocido[brazo plegado-a2-b2-c2-0.0]` | PASSED | 0.3 |
| `test_calcula_el_angulo_interno_conocido[tsuki en rango correcto-a3-b3-c3-170.3]` | PASSED | 0.3 |
| `test_calcula_el_angulo_interno_conocido[angulo agudo de 45-a4-b4-c4-45.0]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[0]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[15]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[30]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[45]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[60]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[90]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[120]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[150]` | PASSED | 0.2 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[179]` | PASSED | 0.2 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[170--170-20]` | PASSED | 0.2 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[150--150-60]` | PASSED | 0.2 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[-179-179-2]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[190-170]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[270-90]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[350-10]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[0]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[37]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[90]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[143]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[180]` | PASSED | 0.2 |
| `test_es_simetrico_respecto_al_orden_de_los_extremos` | PASSED | 0.1 |
| `test_es_invariante_a_la_distancia_a_la_camara[0.5]` | PASSED | 0.2 |
| `test_es_invariante_a_la_distancia_a_la_camara[2]` | PASSED | 0.2 |
| `test_es_invariante_a_la_distancia_a_la_camara[10]` | PASSED | 0.2 |
| `test_puntos_superpuestos_no_lanzan_excepcion` | PASSED | 0.1 |

### `tests/unit/test_grabacion.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_archivo_empieza_por_la_fecha_para_que_el_listado_quede_cronologico` | PASSED | 0.1 |
| `test_el_archivo_conserva_el_nombre_del_alumno` | PASSED | 0.1 |
| `test_el_archivo_termina_con_el_id_de_sesion_que_lo_ata_a_la_base` | PASSED | 0.1 |
| `test_un_nombre_real_no_rompe_la_ruta[Jos\xe9 P\xe9rez-jose_perez]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[Ana  Mar\xeda   G\xf3mez-ana_maria_gomez]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[O'Brien-Smith-o_brien_smith]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[Ah S\xfan-ah_sun]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[   -sin_alumno]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[-sin_alumno]` | PASSED | 0.2 |
| `test_un_nombre_real_no_rompe_la_ruta[None-sin_alumno]` | PASSED | 0.2 |
| `test_un_nombre_larguisimo_se_recorta_sin_dejar_guion_colgando` | PASSED | 0.1 |
| `test_la_ruta_va_bajo_la_carpeta_de_grabaciones_y_no_bajo_evidencias` | PASSED | 0.1 |
| `test_la_carpeta_se_puede_cambiar` | PASSED | 0.7 |
| `test_la_velocidad_se_mide_por_intervalos_no_por_fotogramas` | PASSED | 0.1 |
| `test_el_costo_del_primer_fotograma_no_hunde_la_estimacion` | PASSED | 0.1 |
| `test_sin_informacion_suficiente_se_usa_un_valor_razonable[marcas0]` | PASSED | 0.2 |
| `test_sin_informacion_suficiente_se_usa_un_valor_razonable[marcas1]` | PASSED | 0.1 |
| `test_sin_informacion_suficiente_se_usa_un_valor_razonable[marcas2]` | PASSED | 0.2 |
| `test_sin_informacion_suficiente_se_usa_un_valor_razonable[marcas3]` | PASSED | 0.1 |
| `test_una_estimacion_absurdamente_alta_se_descarta` | PASSED | 0.1 |
| `test_una_estimacion_absurdamente_baja_se_descarta` | PASSED | 0.1 |
| `test_el_resumen_dice_cuanto_dura_el_video_y_a_que_velocidad` | PASSED | 0.1 |
| `test_sin_grabacion_se_dice_explicitamente_y_no_se_calla` | PASSED | 0.1 |
| `test_la_grabacion_viene_activada_por_defecto` | PASSED | 0.1 |
| `test_la_grabacion_se_puede_apagar[0]` | PASSED | 0.2 |
| `test_la_grabacion_se_puede_apagar[false]` | PASSED | 0.2 |
| `test_la_grabacion_se_puede_apagar[False]` | PASSED | 0.2 |
| `test_la_grabacion_se_puede_apagar[no]` | PASSED | 0.2 |
| `test_la_grabacion_se_puede_apagar[NO]` | PASSED | 0.1 |
| `test_la_grabacion_se_puede_apagar[off]` | PASSED | 0.2 |
| `test_la_grabacion_se_puede_apagar[ off ]` | PASSED | 0.1 |
| `test_cualquier_otro_valor_deja_la_grabacion_activada[1]` | PASSED | 0.2 |
| `test_cualquier_otro_valor_deja_la_grabacion_activada[true]` | PASSED | 0.1 |
| `test_cualquier_otro_valor_deja_la_grabacion_activada[si]` | PASSED | 0.1 |
| `test_cualquier_otro_valor_deja_la_grabacion_activada[on]` | PASSED | 0.2 |
| `test_cualquier_otro_valor_deja_la_grabacion_activada[cualquier cosa]` | PASSED | 0.2 |
| `test_sin_carpeta_configurada_se_usa_la_de_por_defecto` | PASSED | 0.1 |
| `test_la_carpeta_configurada_manda` | PASSED | 0.1 |
| `test_el_reporte_muestra_el_nombre_del_archivo_no_la_ruta_completa` | PASSED | 0.1 |
| `test_sin_video_el_reporte_declara_la_ausencia_en_vez_de_callarla[None]` | PASSED | 0.2 |
| `test_sin_video_el_reporte_declara_la_ausencia_en_vez_de_callarla[]` | PASSED | 0.1 |
| `test_sin_video_el_reporte_declara_la_ausencia_en_vez_de_callarla[   ]` | PASSED | 0.1 |
| `test_grabando_se_anuncia_con_el_punto_lleno` | PASSED | 0.1 |
| `test_sin_grabar_tambien_se_anuncia_en_vez_de_no_decir_nada` | PASSED | 0.1 |

### `tests/unit/test_impacto_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_titular_cuenta_los_cambios_sobre_las_juzgadas` | PASSED | 0.1 |
| `test_una_sola_medicion_se_redacta_en_singular` | PASSED | 0.1 |
| `test_sin_impacto_se_dice_explicitamente` | PASSED | 0.1 |
| `test_sin_mediciones_no_se_finge_un_resultado` | PASSED | 0.1 |
| `test_se_cuentan_por_separado_las_dos_direcciones` | PASSED | 0.1 |
| `test_cada_tecnica_se_cuenta_aparte` | PASSED | 0.1 |
| `test_la_linea_de_una_tecnica_nombra_las_direcciones_presentes` | PASSED | 0.1 |
| `test_cuando_parte_del_historial_queda_fuera_se_advierte` | PASSED | 0.1 |
| `test_con_cobertura_baja_se_avisa_que_el_resultado_describe_la_muestra` | PASSED | 0.1 |
| `test_con_cobertura_suficiente_no_se_repite_el_aviso` | PASSED | 0.1 |
| `test_con_el_historial_completo_no_hay_aviso` | PASSED | 0.1 |
| `test_sin_historial_no_hay_aviso_de_cobertura` | PASSED | 0.1 |
| `test_el_resumen_siempre_aclara_que_no_escribe_nada` | PASSED | 0.1 |
| `test_el_resumen_marca_si_hubo_cambios` | PASSED | 0.1 |
| `test_el_resumen_funciona_sin_datos_de_cobertura` | PASSED | 0.1 |

### `tests/unit/test_knowledge_base.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_tsuki_correcto_dentro_del_rango_de_kime[160]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[165]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[170]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[175]` | PASSED | 0.2 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[175.1]` | PASSED | 0.2 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[178]` | PASSED | 0.2 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[180]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[0]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[90]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[159.9]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[159.9-False]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[160.0-True]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[175.0-True]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[175.1-False]` | PASSED | 0.2 |
| `test_heiko_dachi_exige_rodillas_extendidas[164.9-False]` | PASSED | 0.2 |
| `test_heiko_dachi_exige_rodillas_extendidas[165.0-True]` | PASSED | 0.2 |
| `test_heiko_dachi_exige_rodillas_extendidas[172.0-True]` | PASSED | 0.2 |
| `test_heiko_dachi_exige_rodillas_extendidas[180.0-True]` | PASSED | 0.2 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[140-140-True]` | PASSED | 0.2 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[130-150-True]` | PASSED | 0.2 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[129-140-False]` | PASSED | 0.2 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[140-151-False]` | PASSED | 0.2 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[170-170-False]` | PASSED | 0.2 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[100-170-True]` | PASSED | 0.2 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[90-165-True]` | PASSED | 0.2 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[115-180-True]` | PASSED | 0.2 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[120-170-False]` | PASSED | 0.2 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[100-160-False]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[160-105-True]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[145-90-True]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[175-120-True]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[130-105-False]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[160-140-False]` | PASSED | 0.2 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[110-100-False]` | PASSED | 0.2 |
| `test_zenkutsu_y_kokutsu_no_aprueban_la_misma_ejecucion` | PASSED | 0.3 |
| `test_mae_geri_excelente_con_kime_y_explosividad` | PASSED | 0.1 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[159.9-900]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[120-900]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[90-2000]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_extension_lenta[0]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_extension_lenta[200]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_extension_lenta[399.9]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[159.9-400-False]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[160.0-400.0-True]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[170-399.9-False]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[170-400-True]` | PASSED | 0.2 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[True-True]` | PASSED | 0.2 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[False-False]` | PASSED | 0.2 |
| `test_age_uke_bloquea_solo_en_su_rango[119.9-False-DEMASIADO FLEXIONADO]` | PASSED | 0.2 |
| `test_age_uke_bloquea_solo_en_su_rango[120.0-True-EFECTIVO]` | PASSED | 0.2 |
| `test_age_uke_bloquea_solo_en_su_rango[130.0-True-EFECTIVO]` | PASSED | 0.2 |
| `test_age_uke_bloquea_solo_en_su_rango[140.0-True-EFECTIVO]` | PASSED | 0.2 |
| `test_age_uke_bloquea_solo_en_su_rango[140.1-False-DEMASIADO EXTENDIDO]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_tsuki-argumentos0]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_heiko_dachi-argumentos1]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_kiba_dachi-argumentos2]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_zenkutsu_dachi-argumentos3]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_kokutsu_dachi-argumentos4]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_mae_geri-argumentos5]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_hikiashi-argumentos6]` | PASSED | 0.2 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_age_uke-argumentos7]` | PASSED | 0.2 |

### `tests/unit/test_metrics.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_mide_cada_etapa_por_separado` | PASSED | 0.1 |
| `test_descarta_fotogramas_de_calentamiento` | PASSED | 0.1 |
| `test_estadisticas_con_valores_conocidos` | PASSED | 0.1 |
| `test_fps_se_calcula_entre_inicios_de_fotograma` | PASSED | 0.1 |
| `test_marcar_sin_iniciar_frame_falla` | PASSED | 0.1 |
| `test_sin_datos_suficientes_no_revienta` | PASSED | 0.1 |

### `tests/unit/test_navegacion.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_ninguna_tarea_pasa_de_tres_pulsaciones` | PASSED | 0.1 |
| `test_el_verificador_detecta_una_ruta_demasiado_larga` | PASSED | 0.1 |
| `test_cada_ruta_llega_a_una_pantalla_del_sistema` | PASSED | 0.1 |
| `test_las_claves_de_ruta_no_se_repiten` | PASSED | 0.1 |
| `test_ninguna_ruta_esta_vacia` | PASSED | 0.1 |
| `test_cada_paso_declara_un_tipo_de_control_conocido` | PASSED | 0.1 |
| `test_las_etiquetas_variables_estan_declaradas` | PASSED | 0.1 |
| `test_toda_ruta_arranca_en_un_control_del_panel_de_inicio` | PASSED | 0.1 |
| `test_la_calibracion_no_es_una_seccion_de_la_barra` | PASSED | 0.1 |
| `test_elegir_sensei_no_es_una_seccion_de_la_barra` | PASSED | 0.1 |
| `test_el_texto_de_cambiar_perfil_refleja_el_rol` | PASSED | 0.1 |
| `test_sin_rol_el_control_dice_sensei` | PASSED | 0.1 |
| `test_pedir_una_ruta_inexistente_falla_con_su_nombre` | PASSED | 0.2 |

### `tests/unit/test_nombres_camara.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_los_nombres_de_macos_salen_en_el_orden_en_que_el_sistema_los_reporta` | PASSED | 0.1 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[]` | PASSED | 0.2 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[   ]` | PASSED | 0.2 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[no es json]` | PASSED | 0.2 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[None]` | PASSED | 0.2 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[{}]` | PASSED | 0.2 |
| `test_una_respuesta_ilegible_no_produce_nombres_ni_excepciones[{"otra": []}]` | PASSED | 0.7 |
| `test_una_camara_sin_nombre_se_omite_en_vez_de_correr_las_demas` | PASSED | 0.1 |
| `test_se_usa_el_modelo_cuando_falta_el_nombre_amistoso` | PASSED | 0.1 |
| `test_el_nombre_de_linux_se_limpia[Integrated Camera: Integrated C\n-Integrated Camera: Integrated C]` | PASSED | 0.2 |
| `test_el_nombre_de_linux_se_limpia[  HD Pro Webcam C920  -HD Pro Webcam C920]` | PASSED | 0.2 |
| `test_el_nombre_de_linux_se_limpia[\n-None]` | PASSED | 0.2 |
| `test_el_nombre_de_linux_se_limpia[-None]` | PASSED | 0.2 |
| `test_el_nombre_de_linux_se_limpia[None-None]` | PASSED | 0.2 |
| `test_un_sistema_operativo_sin_soporte_devuelve_un_diccionario_vacio` | PASSED | 0.2 |
| `test_un_fallo_de_la_consulta_no_interrumpe_la_enumeracion` | PASSED | 0.1 |
| `test_solo_se_devuelven_los_indices_pedidos` | PASSED | 0.1 |
| `test_un_indice_fuera_de_la_lista_no_inventa_nombre` | PASSED | 0.2 |

### `tests/unit/test_panel_vivo.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_tiempo_se_lee_como_un_cronometro[0-00:00]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[999-00:00]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[1000-00:01]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[24000-00:24]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[59999-00:59]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[60000-01:00]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[605000-10:05]` | PASSED | 0.2 |
| `test_el_tiempo_se_lee_como_un_cronometro[-500-00:00]` | PASSED | 0.2 |
| `test_el_angulo_se_redondea_a_grados_enteros[170.0-170\xb0]` | PASSED | 0.2 |
| `test_el_angulo_se_redondea_a_grados_enteros[170.4-170\xb0]` | PASSED | 0.2 |
| `test_el_angulo_se_redondea_a_grados_enteros[169.6-170\xb0]` | PASSED | 0.2 |
| `test_el_angulo_se_redondea_a_grados_enteros[0.0-0\xb0]` | PASSED | 0.2 |
| `test_una_articulacion_no_visible_se_marca_con_guion_y_no_con_cero` | PASSED | 0.1 |
| `test_el_veredicto_es_binario_y_no_un_puntaje[True-Correcto]` | PASSED | 0.2 |
| `test_el_veredicto_es_binario_y_no_un_puntaje[False-Incorrecto]` | PASSED | 0.2 |
| `test_el_veredicto_es_binario_y_no_un_puntaje[None-\u2014]` | PASSED | 0.2 |
| `test_las_articulaciones_se_muestran_siempre_en_el_mismo_orden` | PASSED | 0.1 |
| `test_una_articulacion_sin_diagnostico_aparece_vacia_y_no_desaparece` | PASSED | 0.1 |
| `test_acepta_listas_anidadas_como_las_que_devuelve_el_analizador` | PASSED | 0.1 |
| `test_sin_ningun_diagnostico_la_tabla_existe_pero_viene_vacia` | PASSED | 0.1 |
| `test_una_correccion_vigente_no_se_vuelve_a_anotar` | PASSED | 0.1 |
| `test_dos_articulaciones_se_siguen_por_separado` | PASSED | 0.1 |
| `test_los_estados_transitorios_no_ensucian_la_lista` | PASSED | 0.1 |
| `test_la_lista_conserva_solo_las_mas_recientes` | PASSED | 0.1 |
| `test_registrar_informa_cuantas_correcciones_anoto` | PASSED | 0.1 |
| `test_un_fotograma_sin_persona_no_rompe_el_feed` | PASSED | 0.1 |
| `test_los_puntos_imu_estan_declarados_aunque_no_haya_hardware` | PASSED | 0.1 |
| `test_sin_alumno_elegido_el_selector_pide_elegir` | PASSED | 0.1 |
| `test_con_alumno_elegido_el_selector_lo_nombra` | PASSED | 0.1 |
| `test_sin_alumnos_inscritos_el_selector_lo_declara` | PASSED | 0.1 |
| `test_el_texto_del_selector_no_se_confunde_con_el_nombre_de_un_alumno` | PASSED | 0.1 |

### `tests/unit/test_plantilla_reporte.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_ficha_completa_se_construye_sin_errores` | PASSED | 0.1 |
| `test_acepta_el_tipo_y_la_prioridad_escritos_como_texto` | PASSED | 0.1 |
| `test_un_requisito_suelto_se_normaliza_a_tupla` | PASSED | 0.1 |
| `test_los_pasos_admiten_tuplas_ademas_de_objetos_paso` | PASSED | 0.1 |
| `test_la_ficha_es_inmutable` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-001]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[tc-auto-001]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-1]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-0001]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[justificacion_riesgo]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[componente]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[precondiciones]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[datos_entrada]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[resultado_esperado]` | PASSED | 0.2 |
| `test_rechaza_un_nombre_demasiado_corto` | PASSED | 0.1 |
| `test_rechaza_un_requisito_mal_escrito[RF-5]` | PASSED | 0.2 |
| `test_rechaza_un_requisito_mal_escrito[REQ-01]` | PASSED | 0.2 |
| `test_rechaza_un_requisito_mal_escrito[RF01]` | PASSED | 0.2 |
| `test_rechaza_un_requisito_mal_escrito[RNF-123]` | PASSED | 0.2 |
| `test_exige_trazabilidad_a_algun_requisito` | PASSED | 0.1 |
| `test_exige_un_minimo_de_pasos` | PASSED | 0.2 |
| `test_exige_al_menos_una_asercion_explicita` | PASSED | 0.1 |
| `test_un_tipo_de_prueba_inexistente_se_rechaza` | PASSED | 0.1 |
| `test_el_error_enumera_todos_los_problemas_de_una_vez` | PASSED | 0.1 |
| `test_el_markdown_contiene_todos_los_campos_del_formato` | PASSED | 0.1 |
| `test_el_markdown_marca_la_casilla_del_tipo_seleccionado` | PASSED | 0.1 |
| `test_el_markdown_declara_cuando_el_script_no_se_recolecto` | PASSED | 0.1 |
| `test_los_pasos_se_numeran_solos_en_orden` | PASSED | 0.1 |
| `test_una_serie_correlativa_no_reporta_problemas` | PASSED | 0.1 |
| `test_detecta_un_hueco_en_la_numeracion` | PASSED | 0.1 |
| `test_detecta_identificadores_repetidos` | PASSED | 0.1 |
| `test_el_decorador_impide_que_dos_pruebas_reclamen_el_mismo_id` | PASSED | 0.2 |
| `test_el_decorador_cuelga_la_ficha_sin_envolver_la_funcion` | PASSED | 0.1 |
| `test_un_hueco_real_es_incumplimiento_en_una_corrida_completa` | PASSED | 0.2 |
| `test_un_hueco_por_modulos_omitidos_es_solo_un_aviso` | PASSED | 0.2 |
| `test_un_modulo_sin_ficha_sigue_siendo_incumplimiento_aunque_haya_omitidos` | PASSED | 0.2 |
| `test_el_catalogo_no_lleva_fecha_ni_totales_que_cambien_en_cada_corrida` | PASSED | 0.2 |
| `test_dos_corridas_identicas_producen_exactamente_el_mismo_catalogo` | PASSED | 0.2 |

### `tests/unit/test_punto_de_entrada.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_linea_de_comandos_elige_la_via_correcta[argumentos0-grafico]` | PASSED | 0.4 |
| `test_la_linea_de_comandos_elige_la_via_correcta[argumentos1-consola]` | PASSED | 0.3 |
| `test_si_falta_una_dependencia_grafica_se_explica_como_seguir` | PASSED | 0.3 |

### `tests/unit/test_reevaluacion.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_corregir_el_umbral_trasero_cambia_el_veredicto_de_un_kokutsu_guardado` | PASSED | 0.1 |
| `test_reevaluar_no_toca_la_medicion_original` | PASSED | 0.1 |
| `test_un_tsuki_se_reevalua_con_su_unico_angulo` | PASSED | 0.2 |
| `test_endurecer_el_umbral_del_tsuki_vuelve_hiperextendido_lo_que_era_excelente` | PASSED | 0.1 |
| `test_el_mae_geri_no_es_reevaluable_porque_su_veredicto_usa_la_velocidad` | PASSED | 0.2 |
| `test_una_transicion_no_es_reevaluable_porque_no_se_juzgo_contra_ningun_umbral` | PASSED | 0.2 |
| `test_una_postura_de_dos_articulaciones_con_un_solo_angulo_se_rechaza` | PASSED | 0.2 |
| `test_el_informe_separa_las_que_sostienen_de_las_que_cambian` | PASSED | 0.1 |
| `test_el_informe_dice_a_que_veredicto_cambia_cada_medicion` | PASSED | 0.1 |
| `test_las_no_juzgadas_explican_el_motivo` | PASSED | 0.1 |
| `test_el_total_del_informe_cuenta_todas_las_mediciones_recibidas` | PASSED | 0.1 |
| `test_un_informe_sin_mediciones_no_revienta` | PASSED | 0.1 |

### `tests/unit/test_registro_alumno.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_grado_se_pide_desde_la_cinta_cafe[Caf\xe9]` | PASSED | 0.2 |
| `test_el_grado_se_pide_desde_la_cinta_cafe[Negra]` | PASSED | 0.2 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Blanca]` | PASSED | 0.2 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Amarilla]` | PASSED | 0.1 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Naranja]` | PASSED | 0.2 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Verde]` | PASSED | 0.1 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Azul]` | PASSED | 0.2 |
| `test_en_los_colores_iniciales_el_color_ya_determina_el_kyu[Morada]` | PASSED | 0.1 |
| `test_los_grados_ofrecidos_corresponden_al_color` | PASSED | 0.1 |
| `test_un_grado_huerfano_no_se_guarda` | PASSED | 0.1 |
| `test_el_nombre_es_el_unico_campo_obligatorio[]` | PASSED | 0.2 |
| `test_el_nombre_es_el_unico_campo_obligatorio[   ]` | PASSED | 0.2 |
| `test_el_nombre_es_el_unico_campo_obligatorio[None]` | PASSED | 0.2 |
| `test_un_alumno_puede_inscribirse_solo_con_el_nombre` | PASSED | 0.1 |
| `test_la_ficha_completa_se_traduce_a_los_argumentos_de_crear_atleta` | PASSED | 0.1 |
| `test_un_color_de_cinta_inventado_se_rechaza` | PASSED | 0.1 |
| `test_todos_los_colores_declarados_son_aceptados` | PASSED | 0.1 |
| `test_la_edad_se_interpreta_o_queda_vacia[16-16]` | PASSED | 0.2 |
| `test_la_edad_se_interpreta_o_queda_vacia[  8 -8]` | PASSED | 0.2 |
| `test_la_edad_se_interpreta_o_queda_vacia[-None]` | PASSED | 0.2 |
| `test_la_edad_se_interpreta_o_queda_vacia[   -None]` | PASSED | 0.2 |
| `test_una_edad_imposible_se_explica_en_lugar_de_guardarse[diecis\xe9is-no es un n\xfamero]` | PASSED | 0.2 |
| `test_una_edad_imposible_se_explica_en_lugar_de_guardarse[16.5-no es un n\xfamero]` | PASSED | 0.2 |
| `test_una_edad_imposible_se_explica_en_lugar_de_guardarse[2-entre 3 y 99]` | PASSED | 0.2 |
| `test_una_edad_imposible_se_explica_en_lugar_de_guardarse[150-entre 3 y 99]` | PASSED | 0.2 |
| `test_una_edad_imposible_se_explica_en_lugar_de_guardarse[-4-entre 3 y 99]` | PASSED | 0.2 |
| `test_el_peso_admite_coma_decimal[62.5-62.5]` | PASSED | 0.2 |
| `test_el_peso_admite_coma_decimal[62,5-62.5]` | PASSED | 0.2 |
| `test_el_peso_admite_coma_decimal[ 70 -70.0]` | PASSED | 0.2 |
| `test_el_peso_admite_coma_decimal[-None]` | PASSED | 0.2 |
| `test_un_peso_imposible_se_explica[sesenta-no es un n\xfamero]` | PASSED | 0.2 |
| `test_un_peso_imposible_se_explica[5-entre 10 y 250]` | PASSED | 0.2 |
| `test_un_peso_imposible_se_explica[400-entre 10 y 250]` | PASSED | 0.2 |
| `test_el_error_nombra_el_campo_para_que_el_sensei_sepa_cual_corregir` | PASSED | 0.1 |

### `tests/unit/test_riesgos.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_hiperextension_aislada_no_se_reporta` | PASSED | 0.1 |
| `test_una_hiperextension_frecuente_se_reporta_como_riesgo` | PASSED | 0.1 |
| `test_una_proporcion_baja_se_reporta_como_atencion_y_no_como_riesgo` | PASSED | 0.2 |
| `test_la_proporcion_importa_mas_que_la_cuenta` | PASSED | 0.1 |
| `test_sin_evaluaciones_no_se_afirma_nada` | PASSED | 0.1 |
| `test_la_asimetria_exige_repeticiones_suficientes_en_ambos_lados` | PASSED | 0.1 |
| `test_un_solo_lado_con_pocas_repeticiones_basta_para_callar` | PASSED | 0.1 |
| `test_una_diferencia_dentro_de_lo_normal_no_se_reporta` | PASSED | 0.1 |
| `test_la_asimetria_se_detecta_en_cualquier_direccion` | PASSED | 0.1 |
| `test_un_lado_sin_evaluaciones_cerradas_no_produce_comparacion` | PASSED | 0.1 |
| `test_un_lado_ausente_no_revienta` | PASSED | 0.1 |
| `test_una_sesion_limpia_lo_declara_en_vez_de_devolver_una_lista_vacia` | PASSED | 0.1 |
| `test_los_hallazgos_se_ordenan_del_mas_urgente_al_informativo` | PASSED | 0.1 |
| `test_el_analisis_declara_donde_termina_su_alcance` | PASSED | 0.1 |

### `tests/unit/test_validacion_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_acepta_las_formas_validas_de_escribir_un_rango[160-175-esperado0]` | PASSED | 0.2 |
| `test_acepta_las_formas_validas_de_escribir_un_rango[160.5-175.5-esperado1]` | PASSED | 0.2 |
| `test_acepta_las_formas_validas_de_escribir_un_rango[160,5-175-esperado2]` | PASSED | 0.2 |
| `test_acepta_las_formas_validas_de_escribir_un_rango[  160 - 175 -esperado3]` | PASSED | 0.2 |
| `test_acepta_las_formas_validas_de_escribir_un_rango[0-180-esperado4]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[   ]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[-]` | PASSED | 0.1 |
| `test_un_maximo_vacio_significa_sin_limite_superior[\u2014]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[sin l\xedmite]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[Sin Limite]` | PASSED | 0.1 |
| `test_un_maximo_vacio_significa_sin_limite_superior[ninguno]` | PASSED | 0.2 |
| `test_el_texto_mostrado_para_sin_limite_vuelve_a_leerse_como_sin_limite` | PASSED | 0.1 |
| `test_rechaza_los_rangos_imposibles[-175-m\xednimo es obligatorio]` | PASSED | 0.2 |
| `test_rechaza_los_rangos_imposibles[ciento sesenta-175-no es un n\xfamero]` | PASSED | 0.2 |
| `test_rechaza_los_rangos_imposibles[175-160-no puede ser menor]` | PASSED | 0.2 |
| `test_rechaza_los_rangos_imposibles[-5-10-no puede ser negativo]` | PASSED | 0.2 |
| `test_rechaza_los_rangos_imposibles[160-200-supera los 180]` | PASSED | 0.3 |
| `test_el_techo_de_180_grados_solo_aplica_a_los_angulos` | PASSED | 0.1 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[160.0-160]` | PASSED | 0.2 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[160.5-160.5]` | PASSED | 0.2 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[None-sin l\xedmite]` | PASSED | 0.5 |
