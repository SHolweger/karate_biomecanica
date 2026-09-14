# Guía de ejecución y entrega

Pasos concretos para reproducir las pruebas en tu Mac, capturar la evidencia y
armar los dos entregables del curso (informe en PDF y enlace al repositorio).

---

## 1. Ejecutar la suite en tu equipo

```bash
cd karate_biomecanica
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Deberías ver algo como `197 passed in 5.xx s`. En tu Mac sí se ejecutan las 8
pruebas E2E de la interfaz (aquí, en el entorno donde se desarrollaron, quedaron
en `SKIPPED` por no haber entorno gráfico ni MediaPipe instalados). Si alguna
E2E falla, revisa primero que el entorno virtual tenga `customtkinter`,
`mediapipe`, `opencv-python` y `pillow`, y que exista `pose_landmarker_full.task`.

---

## 2. Generar la evidencia de ejecución

**Reporte de consola con cobertura, guardado como archivo:**

```bash
pytest --cov --cov-report=term-missing -v > evidencias/pruebas_$(date +%Y%m%d).txt 2>&1
```

**Reporte de cobertura navegable (para tomar capturas de pantalla):**

```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

**Capturas recomendadas para el informe (2 o 3 bastan):**
1. La terminal con el resumen final en verde (`197 passed`).
2. La tabla de cobertura por módulo.
3. La ventana de la aplicación corriendo durante una prueba E2E, si quieres
   mostrar la interfaz real.

---

## 3. Exportar el informe a PDF (máximo 10 páginas)

El informe está en `docs/informe_tecnico_pruebas_automatizadas.md`. Tres opciones,
de más simple a más cuidada:

**Opción A — Visual Studio Code (la más rápida)**
1. Instala la extensión *Markdown PDF*.
2. Abre el archivo, clic derecho → *Markdown PDF: Export (pdf)*.

**Opción B — Pandoc (mejor tipografía)**
```bash
brew install pandoc basictex
pandoc docs/informe_tecnico_pruebas_automatizadas.md \
       -o Informe_Tecnico_Automatizacion_Pruebas.pdf \
       --pdf-engine=xelatex -V geometry:margin=2.5cm -V fontsize=11pt
```

**Opción C — Typora o Obsidian:** abrir el `.md` y usar *Exportar → PDF*.

> **Sobre el límite de 10 páginas.** El informe está calculado para entrar en ese
> límite. Las fichas de casos de prueba (`docs/casos_prueba_automatizados.md`) son
> un documento aparte y más extenso: si tu catedrático exige que TODO vaya en el
> mismo PDF de 10 páginas, incluye solo las fichas de mayor prioridad
> (TC-AUTO-001, 004, 005, 007, 009, 013) y deja el resto como anexo o como enlace
> al repositorio. Si acepta anexos, entrega los dos PDF por separado.

---

## 4. Qué entregar

| Entregable | Archivo / enlace |
|---|---|
| Informe técnico (PDF, ≤10 páginas) | `docs/informe_tecnico_pruebas_automatizadas.md` exportado a PDF |
| Fichas de casos de prueba | `docs/casos_prueba_automatizados.md` (anexo o incorporado al informe) |
| Código fuente / repositorio | `https://github.com/SHolweger/karate_biomecanica` |
| Instrucciones de ejecución (README) | `README.md`, sección **Pruebas automatizadas** |

---

## 5. Antes de entregar: revisa estos puntos

- [ ] `pytest` pasa en verde en tu equipo, con las E2E incluidas.
- [ ] La captura de pantalla del resumen está pegada en el informe.
- [ ] El PDF no pasa de 10 páginas.
- [ ] El repositorio está actualizado en GitHub (`git push`) y la rama es la
      correcta.
- [ ] Si el catedrático pedía un número mínimo específico de casos ("mínimo [X]"),
      confirma que el número está cubierto: hay **14 fichas documentadas** y
      **197 casos ejecutables**.
- [ ] Los nombres del informe (autor, curso, sección) están como los pide tu
      catedrático.

---

## 6. Preguntas que probablemente te hagan al defender

**¿Por qué no usaste Selenium o Playwright, que son las herramientas más
conocidas?**
Porque automatizan navegadores web, y este sistema es una aplicación de
escritorio sin capa HTTP ni HTML: no hay nada que esas herramientas puedan
manipular. Está desarrollado en la sección 2.2 del informe.

**¿Cómo pruebas visión por computadora sin cámara?**
No se prueba MediaPipe: se prueba cómo el sistema interpreta los landmarks que
MediaPipe entrega. Las poses sintéticas construyen esos 33 puntos por
trigonometría con una fidelidad de ±0.1°, así que la prueba declara el ángulo
exacto que quiere verificar. La precisión del modelo de pose se valida
experimentalmente, no con pruebas de software.

**¿Qué garantiza que las pruebas no dependan del orden de ejecución?**
Cada prueba recibe una base de datos SQLite nueva en un archivo temporal
(fixture `db`) y una instancia limpia del analizador. No hay estado compartido
entre casos.

**¿Por qué 99 % y no 100 % de cobertura?**
Las dos líneas sin cubrir son ramas defensivas de la máquina de estados que solo
se alcanzarían con un estado inválido imposible de producir desde la API pública.
Los módulos de cámara y de MediaPipe quedan fuera por ser envolturas de hardware:
se verifican manualmente con el equipo conectado.
