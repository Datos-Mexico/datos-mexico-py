"""Namespace ENIGH: dataset Encuesta Nacional de Ingresos y Gastos de los Hogares."""

from __future__ import annotations

from typing import Any

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.enigh import (
    ActividadAgroResponse,
    ActividadJcfResponse,
    ActividadNoagroResponse,
    DecilRow,
    DemographicsResponse,
    EnighMetadata,
    EntidadRow,
    HogaresSummary,
    RubrosResponse,
    ValidacionesResponse,
)


class EnighNamespace(BaseNamespace):
    """Endpoints del dataset ENIGH 2024 Nueva Serie (INEGI).

    La ENIGH es una encuesta de corte transversal del INEGI sobre ingresos,
    gastos y demografía de los hogares mexicanos. La versión Nueva Serie
    incorpora ajustes metodológicos en la captura de ingresos respecto a
    la ENIGH Tradicional. Universo: 91,414 hogares en muestra, 38.8M
    expandidos.

    Estos endpoints exponen agregados nacionales y por decil/entidad, las
    actividades económicas de los hogares, y un panel de validaciones
    contra cifras oficiales INEGI.

    Examples:
        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     summary = client.enigh.hogares_summary()
        ...     print(f"{summary.n_hogares_expandido:,} hogares")
        38,830,230 hogares
    """

    # ------------------------------------------------------------------
    # Hogares
    # ------------------------------------------------------------------

    def hogares_summary(self) -> HogaresSummary:
        """KPIs nacionales de hogares (muestra, expandido, ingresos, gastos).

        Endpoint: ``GET /api/v1/enigh/hogares/summary``
        """
        return self._get_validated(
            "/api/v1/enigh/hogares/summary", HogaresSummary
        )

    def hogares_by_decil(self) -> list[DecilRow]:
        """Distribución de hogares por decil de ingreso (10 deciles).

        Endpoint: ``GET /api/v1/enigh/hogares/by-decil``
        """
        return self._get_validated_list(
            "/api/v1/enigh/hogares/by-decil", DecilRow
        )

    def hogares_by_entidad(
        self, entidad: str | None = None
    ) -> list[EntidadRow]:
        """Distribución por entidad federativa.

        Sin filtro retorna las 32 entidades; con filtro retorna sólo la
        entidad solicitada (lista de 1 elemento).

        Endpoint: ``GET /api/v1/enigh/hogares/by-entidad``

        Args:
            entidad: Clave de entidad federativa (ej. ``"09"`` para CDMX).
                Si es ``None`` se devuelven todas.

        Raises:
            NotFoundError: Si ``entidad`` no existe en el catálogo.
        """
        params: dict[str, Any] = {}
        if entidad is not None:
            params["entidad"] = entidad
        return self._get_validated_list(
            "/api/v1/enigh/hogares/by-entidad",
            EntidadRow,
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Gastos
    # ------------------------------------------------------------------

    def gastos_by_rubro(self, *, decil: int | None = None) -> RubrosResponse:
        """Composición del gasto monetario por rubro (9 rubros).

        Cada rubro incluye su gasto medio, su porcentaje del gasto monetario
        total, y la cifra oficial INEGI con su delta porcentual cuando hay
        comparativo directo disponible (``oficial_mensual``,
        ``bound_delta_pct``).

        Endpoint: ``GET /api/v1/enigh/gastos/by-rubro``

        Args:
            decil: Filtrar a un decil específico (1-10). ``None`` (default)
                devuelve la cifra nacional.

        Raises:
            ValueError: Si ``decil`` está fuera del rango ``[1, 10]``.
        """
        params: dict[str, Any] = {}
        if decil is not None:
            if not 1 <= decil <= 10:
                raise ValueError(
                    f"decil debe estar en rango [1, 10], recibido {decil}"
                )
            params["decil"] = decil
        return self._get_validated(
            "/api/v1/enigh/gastos/by-rubro",
            RubrosResponse,
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Demografía
    # ------------------------------------------------------------------

    def poblacion_demographics(
        self, entidad: str | None = None
    ) -> DemographicsResponse:
        """Pirámide demográfica (sexo y edad) nacional o por entidad.

        Endpoint: ``GET /api/v1/enigh/poblacion/demographics``

        Args:
            entidad: Clave de entidad federativa. ``None`` retorna nacional.
        """
        params: dict[str, Any] = {}
        if entidad is not None:
            params["entidad"] = entidad
        return self._get_validated(
            "/api/v1/enigh/poblacion/demographics",
            DemographicsResponse,
            params=params or None,
        )

    # ------------------------------------------------------------------
    # Actividades económicas de los hogares
    # ------------------------------------------------------------------

    def actividad_agro(self) -> ActividadAgroResponse:
        """Hogares con actividad agropecuaria (cultivo, ganadería, pesca).

        Endpoint: ``GET /api/v1/enigh/actividad/agro``
        """
        return self._get_validated(
            "/api/v1/enigh/actividad/agro", ActividadAgroResponse
        )

    def actividad_noagro(self) -> ActividadNoagroResponse:
        """Hogares con actividad económica no agropecuaria.

        Endpoint: ``GET /api/v1/enigh/actividad/noagro``
        """
        return self._get_validated(
            "/api/v1/enigh/actividad/noagro", ActividadNoagroResponse
        )

    def actividad_jcf(self) -> ActividadJcfResponse:
        """Hogares con actividad por jornal o cuenta familiar.

        Endpoint: ``GET /api/v1/enigh/actividad/jcf``
        """
        return self._get_validated(
            "/api/v1/enigh/actividad/jcf", ActividadJcfResponse
        )

    # ------------------------------------------------------------------
    # Metadata y validaciones
    # ------------------------------------------------------------------

    def metadata(self) -> EnighMetadata:
        """Metadata sobre la edición ENIGH (NS 2024) y notas metodológicas.

        Endpoint: ``GET /api/v1/enigh/metadata``
        """
        return self._get_validated(
            "/api/v1/enigh/metadata", EnighMetadata
        )

    def validaciones(self) -> ValidacionesResponse:
        """Validaciones del observatorio contra cifras oficiales INEGI.

        Cada bound compara una cifra calculada por el observatorio con la
        cifra oficial INEGI directamente. ``passing`` es ``True`` cuando
        la diferencia absoluta cae dentro de la tolerancia configurada.

        Endpoint: ``GET /api/v1/enigh/validaciones``
        """
        return self._get_validated(
            "/api/v1/enigh/validaciones", ValidacionesResponse
        )
