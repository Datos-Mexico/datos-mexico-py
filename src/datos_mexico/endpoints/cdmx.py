"""Namespace CDMX: dataset Servidores Públicos del Gobierno de la Ciudad de México."""

from __future__ import annotations

from typing import Any

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.base import PaginatedResponse
from datos_mexico.models.cdmx import (
    BrechaEdadRow,
    CatalogItem,
    DashboardStats,
    PuestoRanking,
    Sector,
    SectoresComparison,
    SectorRanking,
    SectorStats,
    Servidor,
    ServidorDetail,
    ServidoresStats,
)


class CdmxNamespace(BaseNamespace):
    """Endpoints del dataset Servidores Públicos CDMX.

    Acceso al padrón de personal del Poder Ejecutivo del Gobierno de la
    Ciudad de México. La API expone tres familias de endpoints:

    - **Dashboard / Stats**: KPIs preagregados (``dashboard_stats``,
      ``servidores_stats``).
    - **Sectores**: lista, detalle, comparación, ranking
      (``sectores``, ``sector_stats``, ``sectores_compare``,
      ``sectores_ranking``).
    - **Servidores**: lista paginada con filtros (``servidores_lista``).
    - **Catálogos**: listas de referencia para construir filtros
      (``catalogo_*``).

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     stats = client.cdmx.dashboard_stats()
        ...     print(f"{stats.total_servidores:,} servidores")
        246,831 servidores
    """

    def dashboard_stats(self) -> DashboardStats:
        """KPIs preagregados del padrón de servidores públicos CDMX.

        Devuelve los KPIs principales más seis distribuciones precomputadas
        (sueldo, edad, contratación, personalidad jurídica, antigüedad,
        ranking de sectores) en una sola llamada. Pensado para alimentar
        un dashboard sin requerir cálculos del lado del cliente.

        Endpoint: ``GET /api/v1/dashboard/stats``
        """
        return self._get_validated("/api/v1/dashboard/stats", DashboardStats)

    def servidores_stats(
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
    ) -> ServidoresStats:
        """Stats agregados con filtros opcionales sobre el padrón.

        Aplica los filtros como query string y la API devuelve estadísticos
        de ese subconjunto. Todos los filtros son opcionales: sin filtros
        equivale al padrón completo.

        Endpoint: ``GET /api/v1/servidores/stats``

        Args:
            sector_id: ID del sector. Ver ``catalogo_sectores()``.
            sexo: ``"FEMENINO"``, ``"MASCULINO"`` o ``"NA"``.
            edad_min: Edad mínima inclusiva.
            edad_max: Edad máxima inclusiva.
            sueldo_min: Sueldo bruto mínimo en MXN.
            sueldo_max: Sueldo bruto máximo en MXN.
            puesto_search: Texto a buscar en el nombre del puesto.
            tipo_contratacion_id: ID de tipo de contratación.
            tipo_personal_id: ID de tipo de personal.
            universo_id: ID de universo presupuestal.
        """
        params = self._build_filter_params(
            sector_id=sector_id,
            sexo=sexo,
            edad_min=edad_min,
            edad_max=edad_max,
            sueldo_min=sueldo_min,
            sueldo_max=sueldo_max,
            puesto_search=puesto_search,
            tipo_contratacion_id=tipo_contratacion_id,
            tipo_personal_id=tipo_personal_id,
            universo_id=universo_id,
        )
        return self._get_validated(
            "/api/v1/servidores/stats", ServidoresStats, params=params
        )

    def sectores(self) -> list[Sector]:
        """Lista de sectores del Gobierno de la CDMX con resumen.

        Endpoint: ``GET /api/v1/sectores/``

        Notes:
            Puede incluir sectores de prueba con ``total_servidores == 0``;
            sus campos numéricos vendrán como ``None``. Filtrar con
            ``[s for s in sectores if s.total_servidores > 0]`` si se desea
            sólo sectores con personal asignado.
        """
        return self._get_validated_list("/api/v1/sectores/", Sector)

    def sector_stats(self, sector_id: int) -> SectorStats:
        """Detalle estadístico de un sector específico, incluye top puestos.

        Endpoint: ``GET /api/v1/sectores/{sector_id}/stats``

        Raises:
            NotFoundError: Si no existe un sector con ese ID.
        """
        return self._get_validated(
            f"/api/v1/sectores/{sector_id}/stats", SectorStats
        )

    def sectores_compare(self, a: int, b: int) -> SectoresComparison:
        """Comparación lado a lado de dos sectores.

        Endpoint: ``GET /api/v1/sectores/compare?a=..&b=..``

        Args:
            a: ID del primer sector.
            b: ID del segundo sector.
        """
        return self._get_validated(
            "/api/v1/sectores/compare",
            SectoresComparison,
            params={"a": a, "b": b},
        )

    def sectores_ranking(self) -> list[SectorRanking]:
        """Ranking de sectores ordenados por sueldo promedio descendente.

        Endpoint: ``GET /api/v1/analytics/sectores/ranking``
        """
        return self._get_validated_list(
            "/api/v1/analytics/sectores/ranking", SectorRanking
        )

    def puestos_ranking(self, *, limit: int = 20) -> list[PuestoRanking]:
        """Top puestos por sueldo promedio descendente.

        Endpoint: ``GET /api/v1/analytics/puestos/ranking``

        Args:
            limit: Cantidad de puestos a devolver.
        """
        return self._get_validated_list(
            "/api/v1/analytics/puestos/ranking",
            PuestoRanking,
            params={"limit": limit},
        )

    def brecha_edad(self) -> list[BrechaEdadRow]:
        """Brecha salarial de género por bucket de edad.

        Endpoint: ``GET /api/v1/analytics/brecha-edad``
        """
        return self._get_validated_list(
            "/api/v1/analytics/brecha-edad", BrechaEdadRow
        )

    def servidores_lista(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        order_by: str | None = None,
        order: str | None = None,
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
    ) -> PaginatedResponse[Servidor]:
        """Lista paginada de servidores con filtros.

        Endpoint: ``GET /api/v1/servidores/``

        Args:
            page: Número de página (1-indexed).
            per_page: Elementos por página.
            order_by: Campo para ordenar (ej. ``"sueldo_bruto"``).
            order: ``"asc"`` o ``"desc"``.
            sector_id: ID del sector.
            sexo: ``"FEMENINO"``, ``"MASCULINO"`` o ``"NA"``.
            edad_min: Edad mínima.
            edad_max: Edad máxima.
            sueldo_min: Sueldo bruto mínimo.
            sueldo_max: Sueldo bruto máximo.
            puesto_search: Texto a buscar en el puesto.
            tipo_contratacion_id: ID de tipo de contratación.
            tipo_personal_id: ID de tipo de personal.
            universo_id: ID de universo presupuestal.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if order_by is not None:
            params["order_by"] = order_by
        if order is not None:
            params["order"] = order
        params.update(
            self._build_filter_params(
                sector_id=sector_id,
                sexo=sexo,
                edad_min=edad_min,
                edad_max=edad_max,
                sueldo_min=sueldo_min,
                sueldo_max=sueldo_max,
                puesto_search=puesto_search,
                tipo_contratacion_id=tipo_contratacion_id,
                tipo_personal_id=tipo_personal_id,
                universo_id=universo_id,
            )
        )
        return self._get_validated(
            "/api/v1/servidores/", PaginatedResponse[Servidor], params=params
        )

    def servidor_detail(self, servidor_id: int) -> ServidorDetail:
        """Detalle completo de un servidor por ID.

        Devuelve campos derivados ya resueltos (``tipo_contratacion``,
        ``tipo_personal``, ``tipo_nomina``, ``universo``, ``fecha_ingreso``)
        que la vista de listado ``servidores_lista()`` no incluye.

        Endpoint: ``GET /api/v1/servidores/{servidor_id}``

        Raises:
            NotFoundError: Si no existe un servidor con ese ID.
        """
        return self._get_validated(
            f"/api/v1/servidores/{servidor_id}", ServidorDetail
        )

    def catalogo_sectores(self) -> list[CatalogItem]:
        """Catálogo de sectores con conteo de servidores. Útil para dropdowns.

        Endpoint: ``GET /api/v1/catalogos/sectores``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/sectores", CatalogItem
        )

    def catalogo_puestos(self, *, limit: int = 100) -> list[CatalogItem]:
        """Catálogo de puestos con conteo de servidores.

        Endpoint: ``GET /api/v1/catalogos/puestos``

        Args:
            limit: Cantidad máxima de puestos a devolver.
        """
        return self._get_validated_list(
            "/api/v1/catalogos/puestos",
            CatalogItem,
            params={"limit": limit},
        )

    def catalogo_sexos(self) -> list[CatalogItem]:
        """Catálogo de sexos disponibles en el padrón.

        Endpoint: ``GET /api/v1/catalogos/sexos``
        """
        return self._get_validated_list("/api/v1/catalogos/sexos", CatalogItem)

    def catalogo_tipos_contratacion(self) -> list[CatalogItem]:
        """Catálogo de tipos de contratación (BASE, HONORARIOS, ...).

        Endpoint: ``GET /api/v1/catalogos/tipos-contratacion``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/tipos-contratacion", CatalogItem
        )

    def catalogo_tipos_personal(self) -> list[CatalogItem]:
        """Catálogo de tipos de personal (CONFIANZA, SINDICALIZADO, ...).

        Endpoint: ``GET /api/v1/catalogos/tipos-personal``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/tipos-personal", CatalogItem
        )

    def catalogo_tipos_nomina(self) -> list[CatalogItem]:
        """Catálogo de tipos de nómina.

        Endpoint: ``GET /api/v1/catalogos/tipos-nomina``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/tipos-nomina", CatalogItem
        )

    def catalogo_niveles_salariales(self) -> list[CatalogItem]:
        """Catálogo de niveles salariales.

        Endpoint: ``GET /api/v1/catalogos/niveles-salariales``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/niveles-salariales", CatalogItem
        )

    def catalogo_universos(self) -> list[CatalogItem]:
        """Catálogo de universos presupuestales.

        Endpoint: ``GET /api/v1/catalogos/universos``
        """
        return self._get_validated_list(
            "/api/v1/catalogos/universos", CatalogItem
        )

    @staticmethod
    def _build_filter_params(
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
    ) -> dict[str, Any]:
        """Construye el dict de query params, omitiendo los que sean ``None``."""
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
        }
        return {k: v for k, v in candidates.items() if v is not None}
