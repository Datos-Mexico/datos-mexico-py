"""Namespace ``personas``: tabla raw de personas del padrón CDMX."""

from __future__ import annotations

from typing import Any

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.base import PaginatedResponse
from datos_mexico.models.personas import Persona


class PersonasNamespace(BaseNamespace):
    """Endpoints de la tabla normalizada ``personas`` del padrón CDMX.

    Una persona es la entidad atómica del padrón: nombre, apellidos,
    sexo, edad. Para acceder al sueldo y al puesto hay que seguir la
    relación a ``nombramientos`` (una persona puede tener varios
    nombramientos, p. ej. con doble plaza).

    Para el caso común de "ver al servidor con sus campos derivados ya
    aplanados" suele ser más útil ``client.cdmx.servidores_lista()`` o
    ``client.cdmx.servidor_detail(id)``, que devuelven la vista
    desnormalizada lista para consumir.
    """

    def list(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        nombre: str | None = None,
        sexo_id: int | None = None,
    ) -> PaginatedResponse[Persona]:
        """Lista paginada de personas del padrón.

        Endpoint: ``GET /api/v1/personas/``

        Args:
            page: Número de página (1-indexed).
            per_page: Elementos por página.
            nombre: Filtro por nombre (búsqueda parcial).
            sexo_id: Filtro por ID de sexo. Ver
                ``client.cdmx.catalogo_sexos()`` para la lista de IDs.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if nombre is not None:
            params["nombre"] = nombre
        if sexo_id is not None:
            params["sexo_id"] = sexo_id
        return self._get_validated(
            "/api/v1/personas/", PaginatedResponse[Persona], params=params
        )

    def get(self, persona_id: int) -> Persona:
        """Detalle de una persona por ID.

        Endpoint: ``GET /api/v1/personas/{persona_id}``

        Raises:
            NotFoundError: Si no existe una persona con ese ID.
        """
        return self._get_validated(f"/api/v1/personas/{persona_id}", Persona)
