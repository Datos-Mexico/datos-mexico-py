"""Namespace ``export``: descarga del padrón CDMX en formato CSV."""

from __future__ import annotations

from typing import Any

from datos_mexico._namespace import BaseNamespace


class ExportNamespace(BaseNamespace):
    """Descarga del padrón CDMX en formato CSV crudo.

    El endpoint ``/api/v1/export/csv`` filtra por los mismos campos que
    ``client.cdmx.servidores_lista()`` pero devuelve **texto CSV** (no
    JSON) listo para archivar o cargar con ``pandas.read_csv``. El método
    ``csv()`` devuelve un ``str`` con el contenido completo.

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     csv_text = client.export.csv(sector_id=7, per_page=100)
        ...     # Escribir a archivo:
        ...     # Path("padron.csv").write_text(csv_text)
    """

    def csv(
        self,
        *,
        sector_id: int | None = None,
        sexo: str | None = None,
        edad_min: int | None = None,
        edad_max: int | None = None,
        sueldo_min: float | None = None,
        sueldo_max: float | None = None,
        puesto_search: str | None = None,
        tipo_contratacion_id: int | None = None,
        tipo_personal_id: int | None = None,
        universo_id: int | None = None,
        page: int | None = None,
        per_page: int | None = None,
        order_by: str | None = None,
        order: str | None = None,
        use_cache: bool = True,
    ) -> str:
        """Descarga el padrón CDMX como texto CSV.

        Endpoint: ``GET /api/v1/export/csv``

        El response es ``text/csv`` con headers ``id,nombre,apellido_1,...``
        y una fila por servidor. La API ignora ``per_page`` para algunos
        filtros y puede retornar el padrón completo (~250k filas, ~9 MB);
        si quieres paginar realmente la descarga, combina ``page`` con
        un ``per_page`` menor que el total filtrado.

        Args:
            sector_id: ID del sector. Ver ``client.cdmx.catalogo_sectores()``.
            sexo: ``"FEMENINO"``, ``"MASCULINO"`` o ``"NA"``.
            edad_min: Edad mínima inclusiva.
            edad_max: Edad máxima inclusiva.
            sueldo_min: Sueldo bruto mínimo en MXN.
            sueldo_max: Sueldo bruto máximo en MXN.
            puesto_search: Texto a buscar en el puesto.
            tipo_contratacion_id: ID de tipo de contratación.
            tipo_personal_id: ID de tipo de personal.
            universo_id: ID de universo presupuestal.
            page: Número de página (1-indexed). ``None`` deja default API.
            per_page: Filas por página. ``None`` deja default API.
            order_by: Campo para ordenar.
            order: ``"asc"`` o ``"desc"``.
            use_cache: Si ``True`` (default) consulta y popula la caché.
                El CSV puede pesar varios MB; pasar ``False`` evita
                cachear payloads grandes en memoria.

        Returns:
            ``str`` con el CSV completo (header + rows).

        Raises:
            NetworkError: Falla de red.
            TimeoutError: Timeout esperando respuesta.
            ApiError: La API respondió con status 4xx/5xx.
        """
        candidates: dict[str, Any] = {
            "sector_id": sector_id,
            "sexo": sexo,
            "edad_min": edad_min,
            "edad_max": edad_max,
            "sueldo_min": sueldo_min,
            "sueldo_max": sueldo_max,
            "puesto_search": puesto_search,
            "tipo_contratacion_id": tipo_contratacion_id,
            "tipo_personal_id": tipo_personal_id,
            "universo_id": universo_id,
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "order": order,
        }
        params = {k: v for k, v in candidates.items() if v is not None}
        return self._http.get_text(
            "/api/v1/export/csv", params=params or None, use_cache=use_cache
        )
