# Evidencia de ejecución — Suite de pruebas automatizadas

> **Documento generado automáticamente.** Lo produce el complemento `tests/reporte/plugin.py` a partir de las fichas declaradas en el código con el decorador `@ficha(...)` de `tests/reporte/plantilla.py`. No editar a mano: cualquier cambio se pierde en la siguiente corrida. Para modificar una ficha hay que editar la prueba correspondiente.

## 1. Identificación de la corrida

| Campo | Valor |
|---|---|
| **Sistema bajo prueba** | Shotokan AI — Sistema experto de análisis biomecánico del Karate-Do Shotokan |
| **Framework de automatización** | pytest 9.1.1 |
| **Comando ejecutado** | `pytest -q --exigir-fichas --reporte-formal --cov --cov-report=term` |
| **Fecha y hora de inicio** | 2026-09-06 00:30:31 |
| **Duración total** | 3.17 s |
| **Entorno de ejecución** | Darwin 25.6.0 (arm64) |
| **Intérprete** | Python 3.11.0 |
| **Rama / commit** | `pruebas-automatizadas` @ `f280425` (con cambios sin confirmar) |
| **Pruebas recolectadas** | 245 |
| **Veredicto global** | **APROBADA** |

## 2. Resumen de resultados por nivel

| Nivel | Pruebas | PASSED | FAILED | SKIPPED | Tiempo (s) |
|---|---|---|---|---|---|
| Unitaria | 140 | 140 | 0 | 0 | 0.06 |
| Integración | 97 | 97 | 0 | 0 | 1.00 |
| Interfaz (UI/E2E) | 8 | 8 | 0 | 0 | 1.23 |
| **Total** | **245** | **245** | **0** | **0** | **2.29** |

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

## 4. Cobertura de código

Cobertura total de sentencias y ramas: **92.05 %** (medida con pytest-cov sobre los paquetes declarados en `.coveragerc`).

## 5. Detalle de ejecución

### `tests/e2e/test_gui_flow.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_arranque_pide_crear_la_cuenta_inicial` | PASSED | 452.4 |
| `test_crear_la_primera_cuenta_lleva_a_la_seleccion_de_perfiles` | PASSED | 25.4 |
| `test_no_permite_crear_una_cuenta_incompleta` | PASSED | 23.0 |
| `test_login_con_credenciales_correctas` | PASSED | 24.6 |
| `test_login_con_credenciales_incorrectas_muestra_error` | PASSED | 22.0 |
| `test_elegir_un_perfil_abre_la_sesion_de_analisis` | PASSED | 409.4 |
| `test_el_video_se_embebe_en_la_ventana` | PASSED | 139.0 |
| `test_terminar_la_sesion_cierra_el_registro_y_libera_la_camara` | PASSED | 134.9 |

### `tests/integration/test_analyzer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_evalua_los_dos_brazos_de_forma_independiente` | PASSED | 0.5 |
| `test_el_angulo_medido_coincide_con_la_pose_ejecutada` | PASSED | 0.6 |
| `test_brazo_no_visible_se_informa_en_vez_de_inventar_diagnostico` | PASSED | 0.4 |
| `test_el_filtro_se_reinicia_cuando_el_brazo_desaparece` | PASSED | 0.6 |
| `test_el_suavizado_amortigua_un_salto_de_jitter` | PASSED | 0.5 |
| `test_identifica_la_postura_antes_de_evaluarla[posicion natural-175-175-POSTURA NATURAL]` | PASSED | 0.6 |
| `test_identifica_la_postura_antes_de_evaluarla[postura de jinete-140-140-KIBA DACHI]` | PASSED | 0.6 |
| `test_identifica_la_postura_antes_de_evaluarla[postura adelantada-100-170-ZENKUTSU]` | PASSED | 0.6 |
| `test_identifica_la_postura_antes_de_evaluarla[postura atrasada-110-100-KOKUTSU]` | PASSED | 0.6 |
| `test_la_guardia_se_deduce_de_la_profundidad_de_los_tobillos` | PASSED | 0.4 |
| `test_una_transicion_no_se_califica_como_error` | PASSED | 0.6 |
| `test_kiba_dachi_mal_ejecutado_se_detecta_pero_se_corrige` | PASSED | 0.4 |
| `test_piernas_no_visibles_se_informan_sin_calificar` | PASSED | 0.3 |
| `test_una_patada_completa_atraviesa_el_analizador` | PASSED | 0.5 |
| `test_cada_pierna_tiene_su_propia_maquina_de_estados` | PASSED | 0.4 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_tsuki]` | PASSED | 0.4 |
| `test_todo_diagnostico_cumple_el_contrato_de_la_capa_visual[analyze_stance]` | PASSED | 0.4 |
| `test_las_lineas_de_texto_no_se_encimam_en_pantalla` | PASSED | 0.3 |

### `tests/integration/test_cli_auth.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_el_primer_uso_registra_al_entrenador_principal` | PASSED | 5.0 |
| `test_login_exitoso_de_un_entrenador_existente` | PASSED | 3.7 |
| `test_reintento_tras_una_contrasena_equivocada` | PASSED | 4.5 |
| `test_tras_fallar_puede_crear_una_cuenta_de_sensei_asistente` | PASSED | 3.8 |
| `test_elegir_un_perfil_existente_de_la_lista` | PASSED | 4.1 |
| `test_crear_un_perfil_nuevo_desde_la_lista` | PASSED | 3.8 |
| `test_el_grado_del_cinturon_es_opcional` | PASSED | 3.9 |
| `test_una_opcion_invalida_vuelve_a_preguntar[abc-texto en vez de n\xfamero]` | PASSED | 3.8 |
| `test_una_opcion_invalida_vuelve_a_preguntar[0-n\xfamero fuera de rango por abajo]` | PASSED | 3.8 |
| `test_una_opcion_invalida_vuelve_a_preguntar[99-n\xfamero fuera de rango por arriba]` | PASSED | 4.2 |

### `tests/integration/test_database.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_primer_arranque_no_tiene_entrenadores` | PASSED | 3.7 |
| `test_registro_y_autenticacion_exitosa` | PASSED | 3.2 |
| `test_credenciales_invalidas_no_dan_acceso[sholweger-clave_incorrecta-contrase\xf1a equivocada]` | PASSED | 4.3 |
| `test_credenciales_invalidas_no_dan_acceso[usuario_inexistente-clave123-usuario que no existe]` | PASSED | 3.7 |
| `test_credenciales_invalidas_no_dan_acceso[SHOLWEGER-clave123-usuario con distinta capitalizaci\xf3n]` | PASSED | 4.1 |
| `test_credenciales_invalidas_no_dan_acceso[--credenciales vac\xedas]` | PASSED | 3.5 |
| `test_la_contrasena_nunca_se_guarda_en_texto_plano` | PASSED | 3.5 |
| `test_no_se_permiten_dos_entrenadores_con_el_mismo_usuario` | PASSED | 3.5 |
| `test_el_rol_por_defecto_es_sensei` | PASSED | 3.9 |
| `test_los_atletas_se_listan_alfabeticamente` | PASSED | 3.8 |
| `test_crear_atleta_devuelve_un_identificador_utilizable` | PASSED | 3.2 |
| `test_los_datos_opcionales_del_atleta_pueden_omitirse` | PASSED | 4.1 |
| `test_una_sesion_abierta_no_tiene_hora_de_fin` | PASSED | 4.9 |
| `test_cerrar_sesion_registra_la_hora_de_fin` | PASSED | 4.1 |
| `test_la_sesion_queda_ligada_al_atleta_y_al_entrenador` | PASSED | 4.9 |
| `test_guardar_y_recuperar_una_medicion` | PASSED | 4.2 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[True-1]` | PASSED | 4.8 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[False-0]` | PASSED | 4.3 |
| `test_el_veredicto_se_persiste_en_los_tres_estados[None-None]` | PASSED | 4.4 |
| `test_el_historial_solo_devuelve_las_mediciones_del_atleta_consultado` | PASSED | 6.3 |
| `test_un_atleta_sin_entrenamientos_tiene_historial_vacio` | PASSED | 3.5 |
| `test_las_mediciones_sobreviven_al_cierre_de_la_aplicacion` | PASSED | 4.8 |
| `test_migra_una_base_de_datos_creada_sin_la_columna_correcto` | PASSED | 4.2 |
| `test_abrir_dos_veces_la_misma_base_no_duplica_el_esquema` | PASSED | 3.7 |

### `tests/integration/test_kick_state_machine.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_ciclo_completo_de_una_patada_correcta` | PASSED | 0.4 |
| `test_no_reporta_nada_mientras_el_atleta_esta_quieto` | PASSED | 0.3 |
| `test_patada_lenta_se_diagnostica_sin_explosividad` | PASSED | 0.3 |
| `test_hikiashi_incorrecto_cuando_la_pierna_cae_sin_recogerse` | PASSED | 0.3 |
| `test_mantiene_el_aviso_mientras_la_pierna_sigue_extendida` | PASSED | 0.3 |
| `test_intento_abandonado_en_carga_se_descarta_por_timeout` | PASSED | 0.3 |
| `test_kime_sostenido_demasiado_tiempo_se_descarta_por_timeout` | PASSED | 0.3 |
| `test_oclusion_breve_no_interrumpe_la_tecnica` | PASSED | 0.4 |
| `test_oclusion_prolongada_aborta_la_tecnica` | PASSED | 0.3 |
| `test_dos_patadas_seguidas_se_evaluan_de_forma_independiente` | PASSED | 0.3 |
| `test_reset_deja_la_maquina_como_recien_creada` | PASSED | 0.3 |
| `test_todo_diagnostico_trae_las_claves_que_consume_la_capa_visual` | PASSED | 0.3 |

### `tests/integration/test_medicion_logger.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_treinta_frames_identicos_generan_una_sola_fila` | PASSED | 5.3 |
| `test_cada_cambio_real_de_diagnostico_se_registra` | PASSED | 5.7 |
| `test_un_diagnostico_repetido_tras_cambiar_se_vuelve_a_registrar` | PASSED | 5.2 |
| `test_las_categorias_se_rastrean_por_separado` | PASSED | 5.9 |
| `test_traduce_la_categoria_interna_a_un_nombre_legible` | PASSED | 6.4 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico0-mensaje vac\xedo (solo dibuja el n\xfamero del \xe1ngulo en pantalla)]` | PASSED | 4.9 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico1-sin categor\xeda]` | PASSED | 4.3 |
| `test_ignora_entradas_que_no_son_diagnosticos_reales[diagnostico2-diccionario incompleto]` | PASSED | 4.1 |
| `test_conserva_angulo_veredicto_y_marca_de_tiempo` | PASSED | 6.6 |
| `test_registra_una_lista_completa_de_diagnosticos_de_un_frame` | PASSED | 4.7 |

### `tests/integration/test_renderer.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_sin_persona_detectada_el_video_se_devuelve_intacto` | PASSED | 1.4 |
| `test_dibuja_el_esqueleto_cuando_hay_pose` | PASSED | 2.4 |
| `test_el_mapa_anatomico_no_referencia_puntos_inexistentes` | PASSED | 0.3 |
| `test_dibuja_el_texto_del_diagnostico` | PASSED | 1.3 |
| `test_un_diagnostico_sin_angulo_no_rompe_el_dibujado` | PASSED | 0.7 |
| `test_una_lista_vacia_de_diagnosticos_deja_el_frame_igual` | PASSED | 0.5 |
| `test_el_color_del_diagnostico_llega_al_frame` | PASSED | 0.7 |

### `tests/integration/test_reportes.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_calcula_el_porcentaje_de_aciertos[veredictos0-100.0]` | PASSED | 0.4 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos1-75.0]` | PASSED | 0.4 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos2-50.0]` | PASSED | 0.3 |
| `test_calcula_el_porcentaje_de_aciertos[veredictos3-0.0]` | PASSED | 0.4 |
| `test_los_estados_transitorios_no_alteran_el_porcentaje` | PASSED | 0.3 |
| `test_sin_evaluaciones_cerradas_no_hay_porcentaje` | PASSED | 0.2 |
| `test_no_genera_grafica_si_la_sesion_no_dejo_evaluaciones` | PASSED | 285.9 |
| `test_genera_un_png_con_el_historial_de_dos_sesiones` | PASSED | 184.8 |
| `test_crea_la_carpeta_de_evidencias_si_no_existe` | PASSED | 100.7 |
| `test_dos_reportes_seguidos_no_se_sobrescriben` | PASSED | 192.3 |

### `tests/integration/test_umbrales.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_siembra_es_idempotente` | PASSED | 3.9 |
| `test_las_reglas_usan_los_umbrales_de_la_base` | PASSED | 4.8 |
| `test_recalibrar_crea_version_nueva_sin_borrar_la_anterior` | PASSED | 3.9 |
| `test_la_medicion_conserva_el_umbral_que_la_juzgo` | PASSED | 5.5 |
| `test_rechaza_un_maximo_menor_que_el_minimo` | PASSED | 4.6 |
| `test_la_maquina_de_estados_hereda_el_umbral_de_kime` | PASSED | 3.9 |
| `test_sin_base_de_datos_usa_los_valores_de_literatura` | PASSED | 0.3 |
| `test_un_umbral_sin_maximo_no_limita_por_arriba` | PASSED | 0.3 |

### `tests/unit/test_filters.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_la_primera_medicion_se_devuelve_intacta` | PASSED | 0.3 |
| `test_promedia_mientras_el_buffer_se_llena` | PASSED | 0.3 |
| `test_la_ventana_descarta_la_medicion_mas_antigua` | PASSED | 0.3 |
| `test_ventana_de_uno_no_suaviza` | PASSED | 0.3 |
| `test_reset_borra_el_historial` | PASSED | 0.3 |
| `test_reduce_la_dispersion_del_ruido` | PASSED | 0.4 |
| `test_conserva_el_nivel_de_una_senal_estable` | PASSED | 0.3 |
| `test_converge_tras_un_cambio_brusco_de_postura` | PASSED | 0.3 |

### `tests/unit/test_geometry.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_calcula_el_angulo_interno_conocido[angulo recto-a0-b0-c0-90.0]` | PASSED | 0.6 |
| `test_calcula_el_angulo_interno_conocido[extension total-a1-b1-c1-180.0]` | PASSED | 0.6 |
| `test_calcula_el_angulo_interno_conocido[brazo plegado-a2-b2-c2-0.0]` | PASSED | 0.6 |
| `test_calcula_el_angulo_interno_conocido[tsuki en rango correcto-a3-b3-c3-170.3]` | PASSED | 0.6 |
| `test_calcula_el_angulo_interno_conocido[angulo agudo de 45-a4-b4-c4-45.0]` | PASSED | 0.5 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[0]` | PASSED | 0.5 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[15]` | PASSED | 0.4 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[30]` | PASSED | 0.4 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[45]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[60]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[90]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[120]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[150]` | PASSED | 0.3 |
| `test_reconstruye_cualquier_angulo_del_rango_articular[179]` | PASSED | 0.3 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[170--170-20]` | PASSED | 0.5 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[150--150-60]` | PASSED | 0.4 |
| `test_normaliza_cuando_los_segmentos_cruzan_el_corte_angular[-179-179-2]` | PASSED | 0.4 |
| `test_normaliza_angulos_reflejos_al_rango_articular[190-170]` | PASSED | 0.4 |
| `test_normaliza_angulos_reflejos_al_rango_articular[270-90]` | PASSED | 0.4 |
| `test_normaliza_angulos_reflejos_al_rango_articular[350-10]` | PASSED | 0.4 |
| `test_el_resultado_nunca_sale_del_rango_0_180[0]` | PASSED | 0.3 |
| `test_el_resultado_nunca_sale_del_rango_0_180[37]` | PASSED | 0.3 |
| `test_el_resultado_nunca_sale_del_rango_0_180[90]` | PASSED | 0.3 |
| `test_el_resultado_nunca_sale_del_rango_0_180[143]` | PASSED | 0.3 |
| `test_el_resultado_nunca_sale_del_rango_0_180[180]` | PASSED | 0.4 |
| `test_es_simetrico_respecto_al_orden_de_los_extremos` | PASSED | 0.3 |
| `test_es_invariante_a_la_distancia_a_la_camara[0.5]` | PASSED | 0.4 |
| `test_es_invariante_a_la_distancia_a_la_camara[2]` | PASSED | 0.3 |
| `test_es_invariante_a_la_distancia_a_la_camara[10]` | PASSED | 0.3 |
| `test_puntos_superpuestos_no_lanzan_excepcion` | PASSED | 0.3 |

### `tests/unit/test_knowledge_base.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_tsuki_correcto_dentro_del_rango_de_kime[160]` | PASSED | 0.4 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[165]` | PASSED | 0.4 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[170]` | PASSED | 0.4 |
| `test_tsuki_correcto_dentro_del_rango_de_kime[175]` | PASSED | 0.6 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[175.1]` | PASSED | 0.5 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[178]` | PASSED | 0.4 |
| `test_tsuki_hiperextendido_se_marca_como_peligro[180]` | PASSED | 0.4 |
| `test_tsuki_flexionado_no_alcanza_el_kime[0]` | PASSED | 0.4 |
| `test_tsuki_flexionado_no_alcanza_el_kime[90]` | PASSED | 0.4 |
| `test_tsuki_flexionado_no_alcanza_el_kime[159.9]` | PASSED | 0.4 |
| `test_tsuki_fronteras_exactas[159.9-False]` | PASSED | 0.4 |
| `test_tsuki_fronteras_exactas[160.0-True]` | PASSED | 0.4 |
| `test_tsuki_fronteras_exactas[175.0-True]` | PASSED | 0.4 |
| `test_tsuki_fronteras_exactas[175.1-False]` | PASSED | 0.4 |
| `test_heiko_dachi_exige_rodillas_extendidas[164.9-False]` | PASSED | 0.4 |
| `test_heiko_dachi_exige_rodillas_extendidas[165.0-True]` | PASSED | 0.4 |
| `test_heiko_dachi_exige_rodillas_extendidas[172.0-True]` | PASSED | 0.4 |
| `test_heiko_dachi_exige_rodillas_extendidas[180.0-True]` | PASSED | 0.4 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[140-140-True]` | PASSED | 0.5 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[130-150-True]` | PASSED | 0.6 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[129-140-False]` | PASSED | 0.5 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[140-151-False]` | PASSED | 0.6 |
| `test_kiba_dachi_exige_simetria_en_ambas_rodillas[170-170-False]` | PASSED | 0.5 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[100-170-True]` | PASSED | 0.5 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[90-165-True]` | PASSED | 0.5 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[115-180-True]` | PASSED | 0.5 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[120-170-False]` | PASSED | 0.5 |
| `test_zenkutsu_dachi_distingue_pierna_delantera_de_trasera[100-160-False]` | PASSED | 0.6 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[110-100-True]` | PASSED | 0.5 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[100-90-True]` | PASSED | 0.6 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[120-110-True]` | PASSED | 0.5 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[130-100-False]` | PASSED | 0.5 |
| `test_kokutsu_dachi_carga_el_peso_en_la_pierna_trasera[110-130-False]` | PASSED | 0.5 |
| `test_zenkutsu_y_kokutsu_no_aprueban_la_misma_ejecucion` | PASSED | 1.0 |
| `test_mae_geri_excelente_con_kime_y_explosividad` | PASSED | 0.3 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[159.9-900]` | PASSED | 0.4 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[120-900]` | PASSED | 0.4 |
| `test_mae_geri_rechaza_kime_incompleto_aunque_sea_veloz[90-2000]` | PASSED | 0.4 |
| `test_mae_geri_rechaza_extension_lenta[0]` | PASSED | 0.4 |
| `test_mae_geri_rechaza_extension_lenta[200]` | PASSED | 0.4 |
| `test_mae_geri_rechaza_extension_lenta[399.9]` | PASSED | 0.4 |
| `test_mae_geri_fronteras_exactas[159.9-400-False]` | PASSED | 0.6 |
| `test_mae_geri_fronteras_exactas[160.0-400.0-True]` | PASSED | 0.5 |
| `test_mae_geri_fronteras_exactas[170-399.9-False]` | PASSED | 0.5 |
| `test_mae_geri_fronteras_exactas[170-400-True]` | PASSED | 0.5 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[True-True]` | PASSED | 0.4 |
| `test_hikiashi_evalua_el_recojo_de_la_pierna[False-False]` | PASSED | 0.4 |
| `test_age_uke_bloquea_solo_en_su_rango[119.9-False-DEMASIADO FLEXIONADO]` | PASSED | 0.5 |
| `test_age_uke_bloquea_solo_en_su_rango[120.0-True-EFECTIVO]` | PASSED | 0.5 |
| `test_age_uke_bloquea_solo_en_su_rango[130.0-True-EFECTIVO]` | PASSED | 0.5 |
| `test_age_uke_bloquea_solo_en_su_rango[140.0-True-EFECTIVO]` | PASSED | 0.5 |
| `test_age_uke_bloquea_solo_en_su_rango[140.1-False-DEMASIADO EXTENDIDO]` | PASSED | 0.6 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_tsuki-argumentos0]` | PASSED | 0.5 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_heiko_dachi-argumentos1]` | PASSED | 0.5 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_kiba_dachi-argumentos2]` | PASSED | 0.4 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_zenkutsu_dachi-argumentos3]` | PASSED | 0.4 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_kokutsu_dachi-argumentos4]` | PASSED | 0.4 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_mae_geri-argumentos5]` | PASSED | 0.4 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_hikiashi-argumentos6]` | PASSED | 0.4 |
| `test_toda_regla_devuelve_el_contrato_esperado[evaluate_age_uke-argumentos7]` | PASSED | 0.4 |

### `tests/unit/test_metrics.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_mide_cada_etapa_por_separado` | PASSED | 0.3 |
| `test_descarta_fotogramas_de_calentamiento` | PASSED | 0.3 |
| `test_estadisticas_con_valores_conocidos` | PASSED | 0.3 |
| `test_fps_se_calcula_entre_inicios_de_fotograma` | PASSED | 0.3 |
| `test_marcar_sin_iniciar_frame_falla` | PASSED | 0.3 |
| `test_sin_datos_suficientes_no_revienta` | PASSED | 0.3 |

### `tests/unit/test_plantilla_reporte.py`

| Prueba | Estado | Tiempo (ms) |
|---|---|---|
| `test_una_ficha_completa_se_construye_sin_errores` | PASSED | 0.3 |
| `test_acepta_el_tipo_y_la_prioridad_escritos_como_texto` | PASSED | 0.3 |
| `test_un_requisito_suelto_se_normaliza_a_tupla` | PASSED | 1.4 |
| `test_los_pasos_admiten_tuplas_ademas_de_objetos_paso` | PASSED | 0.3 |
| `test_la_ficha_es_inmutable` | PASSED | 0.3 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-001]` | PASSED | 0.4 |
| `test_rechaza_un_identificador_fuera_del_patron[tc-auto-001]` | PASSED | 0.4 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-1]` | PASSED | 0.4 |
| `test_rechaza_un_identificador_fuera_del_patron[]` | PASSED | 0.4 |
| `test_rechaza_un_identificador_fuera_del_patron[TC-AUTO-0001]` | PASSED | 0.4 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[justificacion_riesgo]` | PASSED | 0.4 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[componente]` | PASSED | 0.4 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[precondiciones]` | PASSED | 0.4 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[datos_entrada]` | PASSED | 0.6 |
| `test_ningun_campo_obligatorio_puede_quedar_vacio[resultado_esperado]` | PASSED | 0.4 |
| `test_rechaza_un_nombre_demasiado_corto` | PASSED | 0.3 |
| `test_rechaza_un_requisito_mal_escrito[RF-5]` | PASSED | 0.4 |
| `test_rechaza_un_requisito_mal_escrito[REQ-01]` | PASSED | 0.4 |
| `test_rechaza_un_requisito_mal_escrito[RF01]` | PASSED | 0.3 |
| `test_rechaza_un_requisito_mal_escrito[RNF-123]` | PASSED | 0.4 |
| `test_exige_trazabilidad_a_algun_requisito` | PASSED | 0.3 |
| `test_exige_un_minimo_de_pasos` | PASSED | 0.3 |
| `test_exige_al_menos_una_asercion_explicita` | PASSED | 0.4 |
| `test_un_tipo_de_prueba_inexistente_se_rechaza` | PASSED | 0.3 |
| `test_el_error_enumera_todos_los_problemas_de_una_vez` | PASSED | 0.3 |
| `test_el_markdown_contiene_todos_los_campos_del_formato` | PASSED | 0.4 |
| `test_el_markdown_marca_la_casilla_del_tipo_seleccionado` | PASSED | 0.3 |
| `test_el_markdown_declara_cuando_el_script_no_se_recolecto` | PASSED | 0.3 |
| `test_los_pasos_se_numeran_solos_en_orden` | PASSED | 0.3 |
| `test_una_serie_correlativa_no_reporta_problemas` | PASSED | 0.3 |
| `test_detecta_un_hueco_en_la_numeracion` | PASSED | 0.3 |
| `test_detecta_identificadores_repetidos` | PASSED | 0.3 |
| `test_el_decorador_impide_que_dos_pruebas_reclamen_el_mismo_id` | PASSED | 0.4 |
| `test_el_decorador_cuelga_la_ficha_sin_envolver_la_funcion` | PASSED | 0.4 |
