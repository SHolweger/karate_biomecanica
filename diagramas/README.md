# Diagramas del Capítulo 3 (sección 3.8)

Los cuatro diagramas UML/MER se **generan por script** en vez de dibujarse a mano
en draw.io. La razón es de mantenimiento: cuando el código cambia (una clase nueva,
una tabla nueva), se edita el script y se regenera — el diagrama no queda desfasado
respecto al repositorio, que es el error más fácil de detectar en una defensa.

## Regenerar

```bash
cd diagramas
python3 d1_casos_uso.py
python3 d2_entidad_relacion.py
python3 d3_clases.py
python3 d4_despliegue.py
```

No requiere dependencias externas: `_svg.py` escribe el SVG directamente.

## Archivos

| Script | Salida | Sección de la tesis |
|---|---|---|
| `d1_casos_uso.py` | `3.8.1_diagrama_casos_uso.svg` | 3.8.1 Diagrama de casos de uso |
| `d2_entidad_relacion.py` | `3.8.2_diagrama_entidad_relacion.svg` | 3.8.2 Diagrama de entidad-relación |
| `d3_clases.py` | `3.8.3_diagrama_clases.svg` | 3.8.3 Diagrama de clases |
| `d4_despliegue.py` | `3.8.4_diagrama_despliegue.svg` | 3.8.4 Diagrama de despliegue físico |

## Insertarlos en el documento de Word

Word 2016 y posteriores insertan SVG como **vector**, no como imagen rasterizada:
`Insertar > Imágenes > Este dispositivo…` y elegir el `.svg`. Al ser vectorial no se
pixela al ampliar ni al imprimir, y el texto dentro del diagrama sigue siendo nítido
a cualquier tamaño.

Si la plantilla de la tesis exige PNG, se puede exportar desde el propio Word
(clic derecho sobre la imagen insertada > Guardar como imagen) o abrir el SVG en
un navegador y capturarlo.

## Convención de color (consistente en los cuatro diagramas)

- **Azul, borde continuo** → implementado y verificado en el repositorio.
- **Gris, borde punteado** → planificado (Sprint 4-5: ingesta IMU y fusión sensorial).

Esta distinción es deliberada: permite entregar el capítulo sin que el diagrama
afirme cosas que el código todavía no hace, y sin tener que rehacerlo cuando el
hardware inercial se integre.
