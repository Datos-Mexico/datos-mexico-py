"""Helpers internos compartidos por los namespaces."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BeforeValidator


def _to_decimal(value: object) -> object:
    """Convierte ``int``/``float``/``str`` a ``Decimal``.

    Para floats, usa ``str(value)`` para evitar la representación binaria
    exacta del IEEE 754 que sería ``Decimal('0.10000000000000000555...')``
    en vez de ``Decimal('0.1')``.
    """
    if value is None:
        return value
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    return value


def _to_date(value: object) -> object:
    """Convierte un string ISO ``YYYY-MM-DD`` a ``date``."""
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


Money = Annotated[Decimal, BeforeValidator(_to_decimal)]
"""Decimal proveniente de un número monetario o porcentual."""

DateField = Annotated[date, BeforeValidator(_to_date)]
"""``date`` proveniente de un string ISO."""


def _format_fecha(fecha: date | str) -> str:
    """Valida y normaliza una fecha de snapshot mensual a ``YYYY-MM-DD``.

    Las series del SAR son mensuales: cada punto tiene día = 01. Cualquier
    fecha con día distinto se rechaza para evitar requests que el servidor
    devolvería como 404.

    Args:
        fecha: ``date`` o ``str`` en formato ISO ``YYYY-MM-DD``.

    Returns:
        La fecha formateada como ``YYYY-MM-DD`` lista para query string.

    Raises:
        ValueError: Si el formato no es ``YYYY-MM-DD``, o si el día no es 01.
        TypeError: Si ``fecha`` no es ``date`` ni ``str``.

    Examples:
        >>> _format_fecha("2025-06-01")
        '2025-06-01'
        >>> from datetime import date
        >>> _format_fecha(date(2025, 6, 1))
        '2025-06-01'
        >>> _format_fecha("2025-06-15")
        Traceback (most recent call last):
            ...
        ValueError: fecha debe ser día 01 (snapshot mensual), recibido 2025-06-15
    """
    if isinstance(fecha, date):
        parsed = fecha
    elif isinstance(fecha, str):
        try:
            parsed = date.fromisoformat(fecha)
        except ValueError as exc:
            raise ValueError(
                f"fecha debe estar en formato YYYY-MM-DD: {fecha!r}"
            ) from exc
    else:
        raise TypeError(
            f"fecha debe ser date o str, recibido {type(fecha).__name__}"
        )

    if parsed.day != 1:
        raise ValueError(
            f"fecha debe ser día 01 (snapshot mensual), "
            f"recibido {parsed.isoformat()}"
        )
    return parsed.isoformat()
