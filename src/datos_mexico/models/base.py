"""Modelos Pydantic base compartidos por todos los endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DatosMexicoModel(BaseModel):
    """Base model strict de Pydantic v2 con configuración común.

    Todos los modelos del SDK heredan de esta clase para asegurar consistencia
    de validación. ``extra="allow"`` permite que la API agregue campos nuevos
    sin romper a los clientes que ya tengan una versión anterior del SDK.
    """

    model_config = ConfigDict(
        strict=True,
        extra="allow",
        frozen=False,
        populate_by_name=True,
    )


class ApiResponse(DatosMexicoModel):
    """Wrapper genérico para responses estándar de la API.

    Subclase para endpoints cuyo response sea de la forma
    ``{"data": ..., "meta": ...}``. Endpoints más simples pueden heredar
    directamente de ``DatosMexicoModel``.
    """

    data: Any = None
    meta: dict[str, Any] | None = None


class PaginatedResponse(DatosMexicoModel):
    """Response paginada estándar.

    Los endpoints que devuelven listas paginadas siguen el contrato

        {"data": [...], "total": N, "page": p, "per_page": pp, "pages": P}

    Endpoints específicos pueden refinar el tipo de ``data`` en una subclase
    (por ejemplo ``data: list[ServidorPublico]``).
    """

    data: list[Any]
    total: int
    page: int
    per_page: int
    pages: int


class HealthResponse(DatosMexicoModel):
    """Respuesta del endpoint ``GET /health``.

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> client = DatosMexico()
        >>> health = client.health()
        >>> health.status
        'ok'
    """

    status: str
