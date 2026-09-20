# Evidencia de ejecución — Suite de pruebas automatizadas

> **Documento generado automáticamente.** Lo produce el complemento `tests/reporte/plugin.py` a partir de las fichas declaradas en el código con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. No editar a mano: cualquier cambio se pierde en la siguiente corrida. Para modificar una ficha hay que editar la prueba correspondiente.

## 1. Identificación de la corrida

| Campo | Valor |
|---|---|
| **Sistema bajo prueba** | Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan |
| **Framework de automatización** | pytest 9.1.1 |
| **Comando ejecutado** | `pytest --exigir-fichas --reporte-formal` |
| **Fecha y hora de inicio** | 2026-09-14 09:36:43 |
| **Duración total** | 7.92 s |
| **Entorno de ejecución** | Darwin 25.6.0 (arm64) |
| **Intérprete** | Python 3.11.0 |
| **Rama / commit** | `main` @ `d185bb3` |
| **Pruebas recolectadas** | 367 |
| **Veredicto global** | **APROBADA** |

## 2. Resumen de resultados por nivel

| Nivel | Pruebas | PASSED | FAILED | SKIPPED | Tiempo (s) |
|---|---|---|---|---|---|
| Unitaria | 193 | 193 | 0 | 0 | 0.04 |
| Integración | 125 | 125 | 0 | 0 | 0.97 |
| Interfaz (UI/E2E) | 49 | 49 | 0 | 0 | 5.68 |
| **Total** | **367** | **367** | **0** | **0** | **6.69** |

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
| TC-AUTO-013 | Al elegir un perfil de atleta se abre la pantalla de análisis en vivo y queda registrada una sesión abierta | RF-06, RNF-04 | `tests/e2e/test_gui_flow.py::test_elegir_un_perfil_abre_la_sesion_de_analisis` | 1 PASSED | **PASSED** |
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

## 5. Detalle de ejecución

### `tests/e2e/test_gui_camara.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_lista_las_camaras_detectadas_en_el_equipo` | PASSED | 945.5 |
| `test_la_fuente_elegida_se_verifica_y_persiste` | PASSED | 47.8 |
| `test_una_camara_que_no_abre_no_se_guarda` | PASSED | 43.8 |
| `test_una_camara_que_abre_pero_no_entrega_imagen_se_rechaza` | PASSED | 43.5 |
| `test_la_camara_ip_se_guarda_como_direccion_completa` | PASSED | 47.7 |
| `test_elegir_camara_ip_sin_escribir_la_direccion_avisa` | PASSED | 43.9 |
| `test_avisa_cuando_la_camara_configurada_ya_no_esta_conectada` | PASSED | 47.0 |
| `test_volver_regresa_a_la_seleccion_de_perfiles` | PASSED | 49.0 |
| `test_abrir_la_pantalla_con_una_camara_ip_ya_configurada_no_inventa_un_error` | PASSED | 50.1 |

### `tests/e2e/test_gui_flow.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_arranque_pide_crear_la_cuenta_inicial` | PASSED | 22.4 |
| `test_crear_la_primera_cuenta_lleva_a_la_seleccion_de_perfiles` | PASSED | 29.5 |
| `test_no_permite_crear_una_cuenta_incompleta` | PASSED | 21.0 |
| `test_login_con_credenciales_correctas` | PASSED | 27.3 |
| `test_login_con_credenciales_incorrectas_muestra_error` | PASSED | 21.6 |
| `test_elegir_un_perfil_abre_la_sesion_de_analisis` | PASSED | 563.2 |
| `test_el_video_se_embebe_en_la_ventana` | PASSED | 138.2 |
| `test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` | PASSED | 137.7 |
| `test_el_acceso_no_muestra_barra_lateral` | PASSED | 21.8 |
| `test_tras_autenticarse_aparece_la_barra_con_la_seccion_de_entrenar_activa` | PASSED | 27.8 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[historial-HistorialScreen]` | PASSED | 49.9 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[tecnicas-TecnicasScreen]` | PASSED | 73.9 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[umbrales-UmbralesScreen]` | PASSED | 58.4 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[camara-CamaraScreen]` | PASSED | 1402.2 |
| `test_cada_seccion_de_la_barra_abre_su_pantalla[perfiles-PerfilScreen]` | PASSED | 32.9 |
| `test_la_barra_sobrevive_al_cambiar_de_seccion` | PASSED | 61.1 |
| `test_el_detalle_de_un_alumno_conserva_marcada_la_seccion_de_historial` | PASSED | 49.5 |
| `test_cerrar_sesion_de_entrenador_retira_la_barra_y_vuelve_al_acceso` | PASSED | 32.5 |
| `test_un_usuario_repetido_se_explica_en_pantalla_en_vez_de_reventar` | PASSED | 23.6 |

### `tests/e2e/test_gui_historial.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_historial_lista_a_todos_los_alumnos` | PASSED | 52.1 |
| `test_el_alumno_sin_entrenar_aparece_sin_precision` | PASSED | 49.9 |
| `test_volver_desde_el_historial_regresa_a_perfiles` | PASSED | 57.3 |
| `test_el_reporte_de_progreso_se_genera_desde_la_pantalla` | PASSED | 198.4 |
| `test_sin_evaluaciones_cerradas_se_explica_en_vez_de_generar_un_grafico_vacio` | PASSED | 49.8 |
| `test_el_perfil_muestra_el_desempeno_por_tecnica` | PASSED | 53.5 |
| `test_el_reporte_de_sesion_resume_y_ordena_los_errores` | PASSED | 57.8 |
| `test_un_reporte_de_sesion_inexistente_no_rompe_la_pantalla` | PASSED | 45.7 |
| `test_volver_desde_el_reporte_regresa_al_perfil_del_alumno` | PASSED | 65.2 |
| `test_la_biblioteca_muestra_las_tecnicas_que_el_sistema_evalua` | PASSED | 55.1 |
| `test_la_biblioteca_refleja_una_recalibracion_del_entrenador` | PASSED | 53.8 |
| `test_desde_la_biblioteca_se_llega_a_la_calibracion` | PASSED | 76.5 |

### `tests/e2e/test_gui_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_pantalla_lista_todos_los_umbrales_vigentes` | PASSED | 58.3 |
| `test_recalibrar_cambia_el_criterio_del_sistema_experto` | PASSED | 74.6 |
| `test_un_campo_invalido_no_guarda_ninguno_de_los_cambios` | PASSED | 70.5 |
| `test_guardar_sin_tocar_nada_no_crea_versiones_nuevas` | PASSED | 55.3 |
| `test_descartar_devuelve_los_campos_al_valor_vigente` | PASSED | 77.1 |
| `test_sin_entrenador_la_pantalla_queda_en_solo_lectura` | PASSED | 49.8 |
| `test_el_historial_abre_una_sola_ventana_con_las_versiones_del_umbral` | PASSED | 200.6 |
| `test_una_base_sin_umbrales_lo_informa_en_vez_de_mostrar_una_tabla_vacia` | PASSED | 100.3 |
| `test_volver_regresa_a_la_seleccion_de_perfiles` | PASSED | 61.7 |

### `tests/integration/test_analyzer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_evalua_los_dos_brazos_de_forma_independiente` | PASSED | 0.3 |
| `test_el_angulo_medido_coincide_con_la_pose_ejecutada` | PASSED | 0.3 |
| `test_brazo_no_visible_se_informa_en_vez_de_inventar_diagnostico` | PASSED | 0.2 |
| `test_el_filtro_se_reinicia_cuando_el_brazo_desaparece` | PASSED | 0.3 |
| `test_el_suavizado_amortigua_un_salto_de_jitter` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[posicion natural-175-175-POSTURA NATURAL]` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[postura de jinete-140-140-KIBA DACHI]` | PASSED | 0.4 |
| `test_identifica_la_postura_antes_de_evaluarla[postura adelantada-100-170-ZENKUTSU]` | PASSED | 0.3 |
| `test_identifica_la_postura_antes_de_evaluarla[postura atrasada-165-105-KOKUTSU]` | PASSED | 0.3 |
| `test_la_guardia_se_deduce_de_la_profundidad_de_los_tobillos` | PASSED | 0.2 |
| `test_una_transicion_no_se_califica_como_error` | PASSED | 0.2 |
| `test_kiba_dachi_mal_ejecutado_se_detecta_pero_se_corrige` | PASSED | 0.2 |
| `test_piernas_no_visibles_se_informan_sin_calificar` | PASSED | 0.2 |
| `test_una_patada_completa_atraviesa_el_analizador` | PASSED | 0.2 |
| `test_cada_pierna_tiene_su_propia_maquina_de_estados` | PASSED | 0.2 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_tsuki]` | PASSED | 0.3 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_stance]` | PASSED | 0.2 |
| `test_las_lineas_de_texto_no_se_encimam_en_pantalla` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[170-100]` | PASSED | 0.3 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[165-105]` | PASSED | 0.3 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[160-110]` | PASSED | 0.3 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[155-115]` | PASSED | 0.2 |
| `test_un_kokutsu_real_no_se_confunde_con_una_transicion[150-120]` | PASSED | 0.2 |
| `test_zenkutsu_y_kokutsu_no_se_confunden_entre_si` | PASSED | 0.2 |

### `tests/integration/test_cli_auth.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_uso_registra_al_entrenador_principal` | PASSED | 5.2 |
| `test_login_exitoso_de_un_entrenador_existente` | PASSED | 3.9 |
| `test_reintento_tras_una_contrasena_equivocada` | PASSED | 4.2 |
| `test_tras_fallar_puede_crear_una_cuenta_de_sensei_asistente` | PASSED | 5.0 |
| `test_elegir_un_perfil_existente_de_la_lista` | PASSED | 4.4 |
| `test_crear_un_perfil_nuevo_desde_la_lista` | PASSED | 5.0 |
| `test_el_grado_del_cinturon_es_opcional` | PASSED | 4.2 |
| `test_una_opcion_invalida_vuelve_a_preguntar[abc-texto en vez de n\xfamero]` | PASSED | 4.9 |
| `test_una_opcion_invalida_vuelve_a_preguntar[0-n\xfamero fuera de rango por abajo]` | PASSED | 4.3 |
| `test_una_opcion_invalida_vuelve_a_preguntar[99-n\xfamero fuera de rango por arriba]` | PASSED | 4.1 |

### `tests/integration/test_configuracion.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_preferencia_no_configurada_devuelve_el_valor_por_defecto` | PASSED | 3.5 |
| `test_la_preferencia_sobrevive_al_reinicio_del_sistema` | PASSED | 4.3 |
| `test_reconfigurar_reemplaza_en_vez_de_duplicar` | PASSED | 4.3 |
| `test_los_valores_se_guardan_como_texto` | PASSED | 3.9 |
| `test_la_migracion_no_toca_una_base_ya_existente` | PASSED | 6.0 |

### `tests/integration/test_consultas_progreso.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_precision_ignora_los_estados_transitorios` | PASSED | 9.5 |
| `test_un_alumno_sin_mediciones_aparece_con_precision_desconocida` | PASSED | 9.8 |
| `test_todos_los_alumnos_aparecen_aunque_no_hayan_entrenado` | PASSED | 10.3 |
| `test_las_sesiones_se_listan_de_la_mas_reciente_a_la_mas_antigua` | PASSED | 10.0 |
| `test_cada_sesion_trae_su_propia_precision` | PASSED | 10.3 |
| `test_una_sesion_abierta_se_distingue_de_una_cerrada` | PASSED | 9.0 |
| `test_un_alumno_sin_sesiones_devuelve_lista_vacia` | PASSED | 9.4 |
| `test_las_tecnicas_se_ordenan_de_la_mas_floja_a_la_mas_solida` | PASSED | 9.4 |
| `test_el_desempeno_puede_acotarse_a_una_sola_sesion` | PASSED | 9.8 |
| `test_el_angulo_medio_se_promedia_por_tecnica` | PASSED | 9.7 |
| `test_el_detalle_de_sesion_identifica_al_alumno_y_al_entrenador` | PASSED | 9.3 |
| `test_una_sesion_inexistente_devuelve_none` | PASSED | 9.4 |
| `test_los_errores_se_agrupan_y_ordenan_por_frecuencia` | PASSED | 8.7 |
| `test_una_sesion_sin_errores_no_reporta_correcciones` | PASSED | 12.7 |

### `tests/integration/test_database.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_primer_arranque_no_tiene_entrenadores` | PASSED | 5.3 |
| `test_registro_y_autenticacion_exitosa` | PASSED | 4.1 |
| `test_credenciales_invalidas_no_dan_acceso[sholweger-clave_incorrecta-contrase\xf1a equivocada]` | PASSED | 3.8 |
| `test_credenciales_invalidas_no_dan_acceso[usuario_inexistente-clave123-usuario que no existe]` | PASSED | 3.8 |
| `test_credenciales_invalidas_no_dan_acceso[SHOLWEGER-clave123-usuario con distinta capitalizaci\xf3n]` | PASSED | 4.1 |
| `test_credenciales_invalidas_no_dan_acceso[--credenciales vac\xedas]` | PASSED | 4.3 |
| `test_la_contrasena_nunca_se_guarda_en_texto_plano` | PASSED | 3.8 |
| `test_no_se_permiten_dos_entrenadores_con_el_mismo_usuario` | PASSED | 4.0 |
| `test_el_rol_por_defecto_es_sensei` | PASSED | 4.2 |
| `test_los_atletas_se_listan_alfabeticamente` | PASSED | 5.2 |
| `test_crear_atleta_devuelve_un_identificador_utilizable` | PASSED | 3.7 |
| `test_los_datos_opcionales_del_atleta_pueden_omitirse` | PASSED | 3.9 |
| `test_una_sesion_abierta_no_tiene_hora_de_fin` | PASSED | 4.9 |
| `test_cerrar_sesion_registra_la_hora_de_fin` | PASSED | 5.2 |
| `test_la_sesion_queda_ligada_al_atleta_y_al_entrenador` | PASSED | 5.0 |
| `test_guardar_y_recuperar_una_medicion` | PASSED | 5.9 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[True-1]` | PASSED | 5.3 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[False-0]` | PASSED | 5.4 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[None-None]` | PASSED | 6.3 |
| `test_el_historial_solo_devuelve_las_mediciones_del_atleta_consultado` | PASSED | 6.6 |
| `test_un_atleta_sin_entrenamientos_tiene_historial_vacio` | PASSED | 4.1 |
| `test_las_mediciones_sobreviven_al_cierre_de_la_aplicacion` | PASSED | 6.4 |
| `test_migra_una_base_de_datos_creada_sin_la_columna_correcto` | PASSED | 4.6 |
| `test_abrir_dos_veces_la_misma_base_no_duplica_el_esquema` | PASSED | 4.0 |

### `tests/integration/test_kick_state_machine.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_ciclo_completo_de_una_patada_correcta` | PASSED | 0.2 |
| `test_no_reporta_nada_mientras_el_atleta_esta_quieto` | PASSED | 0.2 |
| `test_patada_lenta_se_diagnostica_sin_explosividad` | PASSED | 0.2 |
| `test_hikiashi_incorrecto_cuando_la_pierna_cae_sin_recogerse` | PASSED | 0.2 |
| `test_mantiene_el_aviso_mientras_la_pierna_sigue_extendida` | PASSED | 0.2 |
| `test_intento_abandonado_en_carga_se_descarta_por_timeout` | PASSED | 0.2 |
| `test_kime_sostenido_demasiado_tiempo_se_descarta_por_timeout` | PASSED | 0.2 |
| `test_oclusion_breve_no_interrumpe_la_tecnica` | PASSED | 0.2 |
| `test_oclusion_prolongada_aborta_la_tecnica` | PASSED | 0.2 |
| `test_dos_patadas_seguidas_se_evaluan_de_forma_independiente` | PASSED | 0.4 |
| `test_reset_deja_la_maquina_como_recien_creada` | PASSED | 0.2 |
| `test_todo_diagnostico_trae_las_claves_que_consume_la_capa_visual` | PASSED | 0.2 |

### `tests/integration/test_medicion_logger.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_treinta_frames_identicos_generan_una_sola_fila` | PASSED | 5.6 |
| `test_cada_cambio_real_de_diagnostico_se_registra` | PASSED | 5.8 |
| `test_un_diagnostico_repetido_tras_cambiar_se_vuelve_a_registrar` | PASSED | 6.5 |
| `test_las_categorias_se_rastrean_por_separado` | PASSED | 5.7 |
| `test_traduce_la_categoria_interna_a_un_nombre_legible` | PASSED | 7.0 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico0-mensaje vac\xedo (solo dibuja el n\xfamero del \xe1ngulo en pantalla)]` | PASSED | 5.7 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico1-sin categor\xeda]` | PASSED | 4.9 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico2-diccionario incompleto]` | PASSED | 5.3 |
| `test_conserva_angulo_veredicto_y_marca_de_tiempo` | PASSED | 5.9 |
| `test_registra_una_lista_completa_de_diagnosticos_de_un_frame` | PASSED | 10.9 |

### `tests/integration/test_renderer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_sin_persona_detectada_el_video_se_devuelve_intacto` | PASSED | 0.5 |
| `test_dibuja_el_esqueleto_cuando_hay_pose` | PASSED | 1.5 |
| `test_el_mapa_anatomico_no_referencia_puntos_inexistentes` | PASSED | 0.2 |
| `test_dibuja_el_texto_del_diagnostico` | PASSED | 1.1 |
| `test_un_diagnostico_sin_angulo_no_rompe_el_dibujado` | PASSED | 0.4 |
| `test_una_lista_vacia_de_diagnosticos_deja_el_frame_igual` | PASSED | 0.4 |
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
| `test_no_genera_grafica_si_la_sesion_no_dejo_evaluaciones` | PASSED | 6.1 |
| `test_genera_un_png_con_el_historial_de_dos_sesiones` | PASSED | 136.0 |
| `test_crea_la_carpeta_de_evidencias_si_no_existe` | PASSED | 137.0 |
| `test_dos_reportes_seguidos_no_se_sobrescriben` | PASSED | 249.1 |

### `tests/integration/test_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_siembra_es_idempotente` | PASSED | 5.0 |
| `test_las_reglas_usan_los_umbrales_de_la_base` | PASSED | 5.7 |
| `test_recalibrar_crea_version_nueva_sin_borrar_la_anterior` | PASSED | 4.7 |
| `test_la_medicion_conserva_el_umbral_que_la_juzgo` | PASSED | 7.2 |
| `test_rechaza_un_maximo_menor_que_el_minimo` | PASSED | 6.1 |
| `test_la_maquina_de_estados_hereda_el_umbral_de_kime` | PASSED | 4.9 |
| `test_sin_base_de_datos_usa_los_valores_de_literatura` | PASSED | 0.2 |
| `test_un_umbral_sin_maximo_no_limita_por_arriba` | PASSED | 0.2 |
| `test_una_correccion_de_literatura_alcanza_a_una_base_ya_sembrada` | PASSED | 5.2 |
| `test_una_correccion_no_pisa_lo_que_el_entrenador_recalibro` | PASSED | 5.1 |
| `test_aplicar_la_correccion_dos_veces_no_crea_versiones_repetidas` | PASSED | 4.0 |

### `tests/unit/test_filters.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_primera_medicion_se_devuelve_intacta` | PASSED | 0.2 |
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
| `test_los_indices_se_convierten_a_entero[0-0_1]` | PASSED | 0.3 |
| `test_los_indices_se_convierten_a_entero[2-2_1]` | PASSED | 0.2 |
| `test_una_url_se_conserva_como_texto_y_sin_espacios` | PASSED | 0.1 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[camara]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[None]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[1.2.3]` | PASSED | 0.2 |
| `test_una_fuente_ininteligible_se_rechaza_con_un_mensaje_util[\xedndice dos]` | PASSED | 0.2 |
| `test_la_descripcion_distingue_red_de_dispositivo_local` | PASSED | 0.1 |

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
| `test_reconstruye_cualquier_angulo_del_rango_articular[150]` | PASSED | 0.4 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[179]` | PASSED | 0.2 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[170--170-20]` | PASSED | 0.2 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[150--150-60]` | PASSED | 0.3 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[-179-179-2]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[190-170]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[270-90]` | PASSED | 0.2 |
| `test_normaliza_angulos_reflejos_al_rango_articular[350-10]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[0]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[37]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[90]` | PASSED | 0.3 |
| `test_el_resultado_nunca_sale_del_rango_0_180[143]` | PASSED | 0.2 |
| `test_el_resultado_nunca_sale_del_rango_0_180[180]` | PASSED | 0.2 |
| `test_es_simetrico_respecto_al_orden_de_los_extremos` | PASSED | 0.1 |
| `test_es_invariante_a_la_distancia_a_la_camara[0.5]` | PASSED | 0.2 |
| `test_es_invariante_a_la_distancia_a_la_camara[2]` | PASSED | 0.2 |
| `test_es_invariante_a_la_distancia_a_la_camara[10]` | PASSED | 0.2 |
| `test_puntos_superpuestos_no_lanzan_excepcion` | PASSED | 0.1 |

### `tests/unit/test_knowledge_base.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_tsuki_correcto_dentro_del_rango_de_kime[160]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[165]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[170]` | PASSED | 0.2 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[175]` | PASSED | 0.2 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[175.1]` | PASSED | 0.2 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[178]` | PASSED | 0.3 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[180]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[0]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[90]` | PASSED | 0.2 |
| `test_tsuki_flexionado_no_alcanza_el_kime[159.9]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[159.9-False]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[160.0-True]` | PASSED | 0.3 |
| `test_tsuki_fronteras_exactas[175.0-True]` | PASSED | 0.2 |
| `test_tsuki_fronteras_exactas[175.1-False]` | PASSED | 0.4 |
| `test_heiko_dachi_exige_rodillas_extendidas[164.9-False]` | PASSED | 0.3 |
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
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[160-105-True]` | PASSED | 0.3 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[145-90-True]` | PASSED | 0.3 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[175-120-True]` | PASSED | 0.3 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[130-105-False]` | PASSED | 0.3 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[160-140-False]` | PASSED | 0.3 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[110-100-False]` | PASSED | 0.9 |
| `test_zenkutsu_y_kokutsu_no_aprueban_la_misma_ejecucion` | PASSED | 0.4 |
| `test_mae_geri_excelente_con_kime_y_explosividad` | PASSED | 0.2 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[159.9-900]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[120-900]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[90-2000]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_extension_lenta[0]` | PASSED | 0.2 |
| `test_mae_geri_rechaza_extension_lenta[200]` | PASSED | 1.7 |
| `test_mae_geri_rechaza_extension_lenta[399.9]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[159.9-400-False]` | PASSED | 0.3 |
| `test_mae_geri_fronteras_exactas[160.0-400.0-True]` | PASSED | 0.2 |
| `test_mae_geri_fronteras_exactas[170-399.9-False]` | PASSED | 0.3 |
| `test_mae_geri_fronteras_exactas[170-400-True]` | PASSED | 0.3 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[True-True]` | PASSED | 0.3 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[False-False]` | PASSED | 0.3 |
| `test_age_uke_bloquea_solo_en_su_rango[119.9-False-DEMASIADO FLEXIONADO]` | PASSED | 0.3 |
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
| `test_mide_cada_etapa_por_separado` | PASSED | 0.2 |
| `test_descarta_fotogramas_de_calentamiento` | PASSED | 0.1 |
| `test_estadisticas_con_valores_conocidos` | PASSED | 0.1 |
| `test_fps_se_calcula_entre_inicios_de_fotograma` | PASSED | 0.2 |
| `test_marcar_sin_iniciar_frame_falla` | PASSED | 0.1 |
| `test_sin_datos_suficientes_no_revienta` | PASSED | 0.1 |

### `tests/unit/test_plantilla_reporte.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_ficha_completa_se_construye_sin_errores` | PASSED | 0.2 |
| `test_acepta_el_tipo_y_la_prioridad_escritos_como_texto` | PASSED | 0.2 |
| `test_un_requisito_suelto_se_normaliza_a_tupla` | PASSED | 0.2 |
| `test_los_pasos_admiten_tuplas_ademas_de_objetos_paso` | PASSED | 0.1 |
| `test_la_ficha_es_inmutable` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-001]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[tc-auto-001]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-1]` | PASSED | 0.2 |
| `test_rechaza_un_identificador_fuera_del_patron[]` | PASSED | 0.3 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-0001]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[justificacion_riesgo]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[componente]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[precondiciones]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[datos_entrada]` | PASSED | 0.2 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[resultado_esperado]` | PASSED | 0.2 |
| `test_rechaza_un_nombre_demasiado_corto` | PASSED | 0.1 |
| `test_rechaza_un_requisito_mal_escrito[RF-5]` | PASSED | 0.2 |
| `test_rechaza_un_requisito_mal_escrito[REQ-01]` | PASSED | 0.5 |
| `test_rechaza_un_requisito_mal_escrito[RF01]` | PASSED | 0.2 |
| `test_rechaza_un_requisito_mal_escrito[RNF-123]` | PASSED | 0.3 |
| `test_exige_trazabilidad_a_algun_requisito` | PASSED | 0.1 |
| `test_exige_un_minimo_de_pasos` | PASSED | 0.1 |
| `test_exige_al_menos_una_asercion_explicita` | PASSED | 0.1 |
| `test_un_tipo_de_prueba_inexistente_se_rechaza` | PASSED | 0.1 |
| `test_el_error_enumera_todos_los_problemas_de_una_vez` | PASSED | 0.2 |
| `test_el_markdown_contiene_todos_los_campos_del_formato` | PASSED | 0.2 |
| `test_el_markdown_marca_la_casilla_del_tipo_seleccionado` | PASSED | 0.2 |
| `test_el_markdown_declara_cuando_el_script_no_se_recolecto` | PASSED | 0.2 |
| `test_los_pasos_se_numeran_solos_en_orden` | PASSED | 0.2 |
| `test_una_serie_correlativa_no_reporta_problemas` | PASSED | 0.2 |
| `test_detecta_un_hueco_en_la_numeracion` | PASSED | 0.2 |
| `test_detecta_identificadores_repetidos` | PASSED | 0.1 |
| `test_el_decorador_impide_que_dos_pruebas_reclamen_el_mismo_id` | PASSED | 0.3 |
| `test_el_decorador_cuelga_la_ficha_sin_envolver_la_funcion` | PASSED | 0.2 |
| `test_un_hueco_real_es_incumplimiento_en_una_corrida_completa` | PASSED | 0.2 |
| `test_un_hueco_por_modulos_omitidos_es_solo_un_aviso` | PASSED | 0.2 |
| `test_un_modulo_sin_ficha_sigue_siendo_incumplimiento_aunque_haya_omitidos` | PASSED | 0.2 |

### `tests/unit/test_punto_de_entrada.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_linea_de_comandos_elige_la_via_correcta[argumentos0-grafico]` | PASSED | 0.5 |
| `test_la_linea_de_comandos_elige_la_via_correcta[argumentos1-consola]` | PASSED | 0.4 |
| `test_si_falta_una_dependencia_grafica_se_explica_como_seguir` | PASSED | 0.5 |

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
| `test_un_maximo_vacio_significa_sin_limite_superior[-]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[\u2014]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[sin l\xedmite]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[Sin Limite]` | PASSED | 0.2 |
| `test_un_maximo_vacio_significa_sin_limite_superior[ninguno]` | PASSED | 0.2 |
| `test_el_texto_mostrado_para_sin_limite_vuelve_a_leerse_como_sin_limite` | PASSED | 0.1 |
| `test_rechaza_los_rangos_imposibles[-175-m\xednimo es obligatorio]` | PASSED | 0.3 |
| `test_rechaza_los_rangos_imposibles[ciento sesenta-175-no es un n\xfamero]` | PASSED | 0.3 |
| `test_rechaza_los_rangos_imposibles[175-160-no puede ser menor]` | PASSED | 0.2 |
| `test_rechaza_los_rangos_imposibles[-5-10-no puede ser negativo]` | PASSED | 0.4 |
| `test_rechaza_los_rangos_imposibles[160-200-supera los 180]` | PASSED | 0.2 |
| `test_el_techo_de_180_grados_solo_aplica_a_los_angulos` | PASSED | 0.3 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[160.0-160]` | PASSED | 0.2 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[160.5-160.5]` | PASSED | 0.2 |
| `test_el_valor_mostrado_es_legible_para_el_entrenador[None-sin l\xedmite]` | PASSED | 0.4 |
