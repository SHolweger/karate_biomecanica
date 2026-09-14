"""
Plantilla formal de un caso de prueba automatizado.

El problema que resuelve: hasta ahora la ficha de cada caso (ID, tipo,
prioridad, precondiciones, datos de entrada, pasos, criterio de salida) vivía
escrita a mano en `docs/casos_prueba_automatizados.md`, separada del script que
realmente la ejecuta. Nada obligaba a que ambos coincidieran, así que la
documentación podía envejecer sin que ninguna herramienta lo notara.

Aquí la ficha pasa a ser un objeto Python declarado JUNTO a la prueba. Como
`FichaCasoPrueba` se valida al construirse, y se construye al importar el
módulo de pruebas, una ficha incompleta o mal formada rompe la recolección de
pytest antes de ejecutar nada. En otras palabras: el formato deja de ser una
convención de redacción y pasa a ser una precondición verificada por la
herramienta.

Uso:

    from reporte.plantilla import ficha, Paso, Prioridad, TipoPrueba

    @ficha(
        id_caso="TC-AUTO-001",
        nombre="Reconstrucción exacta del ángulo interno de una articulación",
        tipo=TipoPrueba.UNITARIA,
        prioridad=Prioridad.ALTA,
        justificacion_riesgo="todo diagnóstico del sistema experto depende de este cálculo",
        componente="biomechanics/geometry.py (BiomechanicsMath)",
        requisitos="RF-05",
        precondiciones="Ninguna. BiomechanicsMath es una clase de utilidad sin estado",
        datos_entrada="Nueve ángulos del rango articular: [0, 15, ..., 179]",
        pasos=[
            Paso("Construir los tres puntos A, B, C", "Coordenadas válidas en el plano"),
            Paso("Invocar calculate_angle(A, B, C)", "assert obtenido == pytest.approx(θ, abs=0.01)"),
        ],
        resultado_esperado="PASSED sin excepciones en los nueve casos parametrizados",
    )
    def test_reconstruye_cualquier_angulo_del_rango_articular():
        ...
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Sequence

import pytest

# ---------------------------------------------------------------------------
# Reglas del formato. Están aquí arriba, como constantes con nombre, para que
# el criterio sea auditable de un vistazo y no quede enterrado en los ifs.
# ---------------------------------------------------------------------------
PATRON_ID = re.compile(r"^TC-AUTO-\d{3}$")
PATRON_REQUISITO = re.compile(r"^R(F|NF)-\d{2}$")
LARGO_MINIMO_NOMBRE = 20
LARGO_MINIMO_TEXTO = 5
PASOS_MINIMOS = 2

EVIDENCIA_POR_DEFECTO = (
    "Reporte de consola de pytest y `reporte-pruebas.xml` (JUnit XML) "
    "publicado como artefacto en GitHub Actions."
)


class FichaInvalida(ValueError):
    """
    La ficha no cumple la plantilla.

    Acumula TODOS los problemas en vez de abortar en el primero: quien escribe
    una ficha nueva prefiere ver la lista completa de lo que le falta antes que
    corregir un campo, volver a correr y descubrir el siguiente.
    """

    def __init__(self, id_caso: str, problemas: Sequence[str]):
        self.id_caso = id_caso
        self.problemas = list(problemas)
        detalle = "\n".join(f"  - {p}" for p in self.problemas)
        super().__init__(
            f"La ficha '{id_caso or '(sin ID)'}' no cumple la plantilla "
            f"({len(self.problemas)} problema(s)):\n{detalle}"
        )


class TipoPrueba(Enum):
    """Niveles de la pirámide de pruebas usados en el informe."""

    UNITARIA = "Unitaria"
    INTEGRACION = "API/Integración"
    E2E = "Interfaz (UI/E2E)"
    DESEMPENO = "Desempeño"

    @classmethod
    def desde(cls, valor: "TipoPrueba | str") -> "TipoPrueba":
        return _coercionar(cls, valor, "tipo")


class Prioridad(Enum):
    """Prioridad/riesgo del caso, en la escala de tres niveles del formato."""

    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"

    @classmethod
    def desde(cls, valor: "Prioridad | str") -> "Prioridad":
        return _coercionar(cls, valor, "prioridad")


def _coercionar(enumeracion, valor, campo: str):
    """Acepta el miembro del Enum o su nombre/valor en texto, sin más."""
    if isinstance(valor, enumeracion):
        return valor
    if isinstance(valor, str):
        clave = valor.strip().upper()
        for miembro in enumeracion:
            if clave in (miembro.name, miembro.value.upper()):
                return miembro
    validos = ", ".join(m.name for m in enumeracion)
    raise FichaInvalida("", [f"{campo}: '{valor}' no es válido (opciones: {validos})"])


@dataclass(frozen=True)
class Paso:
    """
    Un renglón de la tabla "Pasos de Ejecución Automatizada y Aserciones".

    `accion` es lo que hace el script; `asercion` es cómo se comprueba. La
    numeración no se guarda: la asigna el renderizador según la posición, para
    que reordenar pasos no obligue a renumerar a mano.
    """

    accion: str
    asercion: str


@dataclass(frozen=True)
class FichaCasoPrueba:
    """
    Contrato que debe cumplir todo caso de prueba documentado del proyecto.

    Es `frozen` a propósito: una ficha es evidencia. Si el reporte pudiera
    modificarla mientras corre la suite, dejaría de ser una declaración previa
    y pasaría a ser una narración a posteriori de lo que haya ocurrido.
    """

    id_caso: str
    nombre: str
    tipo: TipoPrueba
    prioridad: Prioridad
    justificacion_riesgo: str
    componente: str
    requisitos: tuple[str, ...]
    precondiciones: str
    datos_entrada: str
    pasos: tuple[Paso, ...]
    resultado_esperado: str
    evidencia: str = EVIDENCIA_POR_DEFECTO

    # -- normalización y validación ----------------------------------------
    def __post_init__(self) -> None:
        self._normalizar()
        problemas = self._problemas()
        if problemas:
            raise FichaInvalida(self.id_caso, problemas)

    def _fijar(self, campo: str, valor) -> None:
        """Asigna sobre una dataclass congelada (única vía permitida: __post_init__)."""
        object.__setattr__(self, campo, valor)

    def _normalizar(self) -> None:
        """
        Acepta las formas cómodas de escribir y las convierte al tipo canónico.

        Sin esto, cada ficha tendría que escribir `requisitos=("RF-05",)` con la
        coma final del singleton, un detalle de sintaxis de Python que no aporta
        nada a la documentación y que se olvida siempre.
        """
        self._fijar("tipo", TipoPrueba.desde(self.tipo))
        self._fijar("prioridad", Prioridad.desde(self.prioridad))

        requisitos = self.requisitos
        if isinstance(requisitos, str):
            requisitos = [r.strip() for r in requisitos.split(",")]
        self._fijar("requisitos", tuple(r.strip() for r in requisitos if str(r).strip()))

        pasos = tuple(p if isinstance(p, Paso) else Paso(*p) for p in self.pasos)
        self._fijar("pasos", pasos)

        for campo in ("id_caso", "nombre", "justificacion_riesgo", "componente",
                      "precondiciones", "datos_entrada", "resultado_esperado", "evidencia"):
            valor = getattr(self, campo)
            self._fijar(campo, valor.strip() if isinstance(valor, str) else valor)

    def _problemas(self) -> list[str]:
        problemas: list[str] = []

        if not PATRON_ID.match(self.id_caso):
            problemas.append(
                f"id_caso: '{self.id_caso}' no sigue el patrón TC-AUTO-### (tres dígitos)"
            )

        if len(self.nombre) < LARGO_MINIMO_NOMBRE:
            problemas.append(
                f"nombre: '{self.nombre}' es demasiado corto; debe describir la conducta "
                f"verificada en al menos {LARGO_MINIMO_NOMBRE} caracteres"
            )

        for campo in ("justificacion_riesgo", "componente", "precondiciones",
                      "datos_entrada", "resultado_esperado", "evidencia"):
            if len(getattr(self, campo)) < LARGO_MINIMO_TEXTO:
                problemas.append(f"{campo}: es obligatorio y no puede quedar vacío")

        if not self.requisitos:
            problemas.append(
                "requisitos: todo caso debe trazar al menos a un requisito (RF-## o RNF-##)"
            )
        for requisito in self.requisitos:
            if not PATRON_REQUISITO.match(requisito):
                problemas.append(
                    f"requisitos: '{requisito}' no sigue el patrón RF-## o RNF-##"
                )

        if len(self.pasos) < PASOS_MINIMOS:
            problemas.append(
                f"pasos: se exigen al menos {PASOS_MINIMOS}; hay {len(self.pasos)}"
            )
        for i, paso in enumerate(self.pasos, start=1):
            if not paso.accion.strip():
                problemas.append(f"pasos[{i}]: la acción del script está vacía")
            if not paso.asercion.strip():
                problemas.append(f"pasos[{i}]: falta el resultado esperado / aserción")

        if not any("assert" in paso.asercion for paso in self.pasos):
            problemas.append(
                "pasos: ningún paso muestra una aserción explícita (`assert ...`). "
                "Una ficha sin aserción documenta una ejecución, no una prueba"
            )

        return problemas

    # -- consultas ----------------------------------------------------------
    @property
    def numero(self) -> int:
        """Parte numérica del ID, para ordenar y detectar huecos en la serie."""
        return int(self.id_caso.rsplit("-", 1)[1])

    def con(self, **cambios) -> "FichaCasoPrueba":
        """Copia con campos sustituidos; la copia se revalida al construirse."""
        return replace(self, **cambios)

    # -- renderizado --------------------------------------------------------
    def _casillas(self, enumeracion, seleccionado) -> str:
        """Reproduce el `**[X]** Opción [ ] Otra` del formato de ficha en papel."""
        return " ".join(
            f"**[X]** {m.value}" if m is seleccionado else f"[ ] {m.value}"
            for m in enumeracion
        )

    def a_markdown(self, nodeid: str | None = None, veredicto: str | None = None) -> str:
        """
        Renderiza la ficha con la estructura exacta del formato del curso.

        `nodeid` y `veredicto` los aporta el complemento de pytest: el primero
        es la ruta real del script y el segundo el resultado observado en la
        corrida. La ficha nunca los inventa — si no se los dan, lo dice.
        """
        script = f"`{nodeid}`" if nodeid else "_(no recolectado en esta corrida)_"
        requisitos = ", ".join(self.requisitos)

        lineas = [
            f"## {self.id_caso} — {self.nombre}",
            "",
            "| Campo | Descripción / Detalle |",
            "|---|---|",
            f"| **ID del Caso de Prueba** | {self.id_caso} |",
            f"| **Nombre de la Prueba** | {self.nombre} |",
            f"| **Tipo de Prueba** | {self._casillas(TipoPrueba, self.tipo)} |",
            f"| **Prioridad / Riesgo** | {self._casillas(Prioridad, self.prioridad)} "
            f"— {self.justificacion_riesgo} |",
            f"| **Componente bajo prueba** | `{self.componente}` |",
            f"| **Requisito asociado** | {requisitos} |",
            f"| **Precondiciones** | {self.precondiciones} |",
            f"| **Datos de Entrada (Test Data)** | {self.datos_entrada} |",
            f"| **Archivo / Clase del Script** | {script} |",
            "",
            "**Pasos de Ejecución Automatizada y Aserciones**",
            "",
            "| Paso | Acción del Script | Resultado Esperado / Aserción (Assert) |",
            "|---|---|---|",
        ]
        for i, paso in enumerate(self.pasos, start=1):
            lineas.append(f"| {i} | {paso.accion} | {paso.asercion} |")

        lineas += [
            "",
            "**Criterios de Salida y Manejo de Errores**",
            f"- **Resultado Esperado Global:** {self.resultado_esperado}",
            f"- **Evidencia de Ejecución:** {self.evidencia}",
        ]
        if veredicto:
            lineas.append(f"- **Resultado Obtenido en la última corrida:** {veredicto}")

        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Registro global y decorador
# ---------------------------------------------------------------------------
# El registro existe para una sola cosa: detectar en el momento de la
# importación que dos pruebas distintas reclaman el mismo ID de caso, que es el
# error más fácil de cometer al copiar y pegar una ficha y el más difícil de
# ver después en el documento final.
_REGISTRO: dict[str, tuple[FichaCasoPrueba, str]] = {}


def fichas_registradas() -> dict[str, FichaCasoPrueba]:
    """Copia del registro, ordenada por ID. Solo lectura para quien consulte."""
    return {k: v[0] for k, v in sorted(_REGISTRO.items())}


def ficha(**campos):
    """
    Decorador que adjunta la ficha formal a una función de prueba.

    Deliberadamente no envuelve la función: pytest debe seguir viendo la misma
    función, con su firma intacta, para que la parametrización y las fixtures
    sigan funcionando igual. Solo cuelga la ficha como atributo y agrega la
    marca `ficha` para poder filtrar con `-m ficha`.
    """
    def decorador(funcion):
        ficha_caso = FichaCasoPrueba(**campos)
        origen = f"{funcion.__module__}.{funcion.__qualname__}"

        previo = _REGISTRO.get(ficha_caso.id_caso)
        if previo is not None and previo[1] != origen:
            raise FichaInvalida(ficha_caso.id_caso, [
                f"id_caso duplicado: ya lo usa {previo[1]} y ahora lo reclama {origen}"
            ])
        _REGISTRO[ficha_caso.id_caso] = (ficha_caso, origen)

        funcion.ficha_caso = ficha_caso
        return pytest.mark.ficha(ficha_caso.id_caso)(funcion)

    return decorador


def verificar_correlativos(fichas: Iterable[FichaCasoPrueba]) -> list[str]:
    """
    Comprueba la integridad de la serie de IDs: sin repetidos y sin huecos.

    Un hueco (TC-AUTO-007 seguido de TC-AUTO-009) casi siempre significa que un
    caso se borró del código pero sigue citado en el informe, o que alguien
    saltó un número al numerar. Se reporta como texto, no como excepción, para
    que quien llame decida si es un aviso o un fallo.
    """
    problemas: list[str] = []
    vistos: dict[int, str] = {}

    for f in fichas:
        if f.numero in vistos:
            problemas.append(
                f"{f.id_caso} está repetido (ya lo usaba '{vistos[f.numero]}')"
            )
        vistos[f.numero] = f.nombre

    if vistos:
        numeros = sorted(vistos)
        faltantes = sorted(set(range(1, max(numeros) + 1)) - set(numeros))
        if faltantes:
            huecos = ", ".join(f"TC-AUTO-{n:03d}" for n in faltantes)
            problemas.append(f"la serie de IDs tiene huecos: {huecos}")

    return problemas
