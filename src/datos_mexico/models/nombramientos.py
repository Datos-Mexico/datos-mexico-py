"""Modelos Pydantic del namespace ``nombramientos``.

Tabla normalizada del Patrón Único de Servidores Públicos CDMX. Un
nombramiento es la asignación de una persona a un puesto, con su sector,
sueldo y tipo de contratación específicos. Una persona puede tener
varios nombramientos (doble plaza) — cada uno es un registro.
"""

from __future__ import annotations

from datos_mexico._helpers import DateField, Money
from datos_mexico.models.base import DatosMexicoModel


class Nombramiento(DatosMexicoModel):
    """Item de ``GET /api/v1/nombramientos/`` y ``GET /api/v1/nombramientos/{id}``.

    Los IDs (``puesto_id``, ``sector_id``, etc.) referencian los catálogos
    expuestos en ``client.cdmx.catalogo_*``. Los campos monetarios
    (``sueldo_bruto``, ``sueldo_neto``) llegan como string desde la API y
    se convierten a ``Decimal`` para preservar precisión. ``fecha_ingreso``
    se parsea a ``date``.
    """

    id: int
    persona_id: int
    puesto_id: int | None = None
    sector_id: int | None = None
    tipo_nomina_id: int | None = None
    tipo_contratacion_id: int | None = None
    tipo_personal_id: int | None = None
    universo_id: int | None = None
    nivel_salarial_id: int | None = None
    fecha_ingreso: DateField | None = None
    sueldo_bruto: Money | None = None
    sueldo_neto: Money | None = None
