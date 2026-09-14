"""
Paquete de reportería formal de la suite de pruebas.

Separa dos responsabilidades que suelen mezclarse:

* `plantilla.py` define QUÉ formato debe cumplir un caso de prueba documentado
  (el contrato) y sabe renderizarse a sí mismo.
* `plugin.py` es el complemento de pytest que RECOGE esas fichas durante la
  ejecución, las cruza con el resultado real de cada prueba y emite los
  documentos de evidencia.

La plantilla no sabe nada de pytest más allá del decorador, y el complemento no
sabe nada del formato interno de una ficha: cada uno se prueba por separado.

Se importa como `reporte.plantilla` (no `tests.reporte.plantilla`) porque el
conftest de la raíz agrega `tests/` al sys.path, igual que con `helpers.fakes`.
Usar siempre la misma ruta de importación es indispensable: el registro de
fichas es estado de módulo y dos rutas distintas crearían dos registros.
"""
from reporte.plantilla import (  # noqa: F401  (reexportación por comodidad)
    FichaCasoPrueba,
    FichaInvalida,
    Paso,
    Prioridad,
    TipoPrueba,
    ficha,
)
