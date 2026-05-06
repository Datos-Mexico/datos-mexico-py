"""Modelos Pydantic del namespace ``personas``.

Tabla normalizada del Patrón Único de Servidores Públicos CDMX. Cada
persona es un registro único independientemente del puesto (un servidor
con doble plaza tendría una sola persona y dos nombramientos).
"""

from __future__ import annotations

from datos_mexico.models.base import DatosMexicoModel


class Persona(DatosMexicoModel):
    """Item de ``GET /api/v1/personas/`` y ``GET /api/v1/personas/{id}``.

    El campo ``apellido_2`` puede no estar presente para personas con un
    solo apellido. ``sexo_id`` y ``edad`` pueden ser ``None`` cuando el
    dato fuente venía sin esa información.
    """

    id: int
    nombre: str
    apellido_1: str
    apellido_2: str | None = None
    sexo_id: int | None = None
    edad: int | None = None
