"""Namespace ``nombramientos``: tabla raw de asignaciones del padrón CDMX."""

from __future__ import annotations

from typing import Any

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.base import PaginatedResponse
from datos_mexico.models.nombramientos import Nombramiento


class NombramientosNamespace(BaseNamespace):
    """Endpoints de la tabla normalizada ``nombramientos`` del padrón CDMX.

    Un nombramiento liga una persona con un puesto, sector, tipo de
    contratación y un sueldo bruto/neto. Para una vista desnormalizada
    "lista para consumir" (con nombre del puesto y del sector ya
    resueltos), usar ``client.cdmx.servidores_lista()``.
    """

    def list(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        persona_id: int | None = None,
        sector_id: int | None = None,
    ) -> PaginatedResponse[Nombramiento]:
        """Lista paginada de nombramientos.

        Endpoint: ``GET /api/v1/nombramientos/``

        Args:
            page: Número de página (1-indexed).
            per_page: Elementos por página.
            persona_id: Filtra por ID de persona (útil para ver todos los
                nombramientos de una persona específica, p. ej. doble plaza).
            sector_id: Filtra por ID de sector. Ver
                ``client.cdmx.catalogo_sectores()`` para la lista de IDs.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if persona_id is not None:
            params["persona_id"] = persona_id
        if sector_id is not None:
            params["sector_id"] = sector_id
        return self._get_validated(
            "/api/v1/nombramientos/",
            PaginatedResponse[Nombramiento],
            params=params,
        )

    def get(self, nombramiento_id: int) -> Nombramiento:
        """Detalle de un nombramiento por ID.

        Endpoint: ``GET /api/v1/nombramientos/{nombramiento_id}``

        Raises:
            NotFoundError: Si no existe un nombramiento con ese ID.
        """
        return self._get_validated(
            f"/api/v1/nombramientos/{nombramiento_id}", Nombramiento
        )
