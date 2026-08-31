"""
conftest.py (raíz) — Hace importable el paquete del proyecto durante las pruebas.

pytest inserta la carpeta rootdir en sys.path al encontrar este archivo, así
que `from expert_system.analyzer import ...` funciona sin instalar el proyecto
como paquete ni exportar PYTHONPATH a mano.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
for ruta in (RAIZ, os.path.join(RAIZ, "tests")):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
