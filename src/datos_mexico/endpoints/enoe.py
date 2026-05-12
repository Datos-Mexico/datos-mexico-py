"""Namespace ENOE: dataset Encuesta Nacional de Ocupación y Empleo (INEGI)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Literal

from datos_mexico._namespace import BaseNamespace
from datos_mexico.models.enoe import (
    DistribucionPosicionSerie,
    DistribucionPosicionSnapshot,
    DistribucionSectorialSerie,
    DistribucionSectorialSnapshot,
    EnoeHealth,
    EnoeMetadata,
    EntidadesResponse,
    EtapasResponse,
    IndicadoresResponse,
    MicrodatosCount,
    MicrodatosListResponse,
    MicrodatosSchema,
    RankingResponse,
    SerieEntidadResponse,
    SerieNacionalResponse,
    SnapshotEntidadResponse,
    SnapshotNacionalResponse,
)

if TYPE_CHECKING:
    import pandas as pd

EtapaSlug = Literal["clasica", "etoe_telefonica", "enoe_n"]
NivelGeografico = Literal["nacional", "entidad"]
OrdenRanking = Literal["desc", "asc"]
TablaMicrodatos = Literal["viv", "hog", "sdem", "coe1", "coe2"]


class EnoeNamespace(BaseNamespace):
    """Endpoints del dataset ENOE (Encuesta Nacional de Ocupación y Empleo).

    La ENOE es la fuente oficial trimestral del INEGI sobre el mercado
    laboral mexicano. El observatorio expone tres familias de endpoints:

    - **Catálogos y metadata** (5): ``health``, ``metadata``, ``indicadores``,
      ``entidades``, ``etapas``.
    - **Indicadores agregados** (5): series y snapshots nacionales y por
      entidad, ranking por indicador.
    - **Distribuciones** (4): ocupados por sector económico y por posición
      en la ocupación, snapshot y serie.
    - **Microdatos** (3): ``microdatos_schema``, ``microdatos_count``,
      ``microdatos_iter`` (sync generator) y ``microdatos_to_pandas``
      (helper opcional que requiere pandas instalado).

    Cobertura: 2005T1-2025T1 (80 trimestres, gap documental en 2020T2),
    nacional + 32 entidades federativas, ~101.5M microdatos en cinco
    tablas (``viv``, ``hog``, ``sdem``, ``coe1``, ``coe2``), 13 indicadores
    agregados y 76 mil agregados.

    Examples:
        Top 5 estados con mayor desempleo en el trimestre más reciente:

        >>> from datos_mexico import DatosMexico
        >>> with DatosMexico() as client:
        ...     r = client.enoe.ranking(
        ...         periodo="2025T1",
        ...         indicador="tasa_desocupacion",
        ...         limit=5,
        ...     )
        ...     for e in r.ranking:
        ...         print(f"{e.rank}. {e.entidad_nombre}: {e.valor:.2f}%")
        1. Tabasco: 4.97%
        2. Coahuila de Zaragoza: 3.56%
        3. Durango: 3.46%
        4. Ciudad de México: 3.45%
        5. Tamaulipas: 3.37%

    Notes:
        El observatorio mantiene un dominio operativo uniforme de
        **15 años o más** en toda la serie (re-cálculo en la etapa
        clásica pre-2020T1 que originalmente publicaba 14+). El cambio de
        marco muestral en 2020T3 y la redefinición del TCCO en 2020T1
        están documentados como caveats tipados (``slug`` ``cambio_marco_2020T3``,
        ``redefinicion_tcco_2020T1``) en cada response que los toque.

    See Also:
        Documentación INEGI: https://www.inegi.org.mx/programas/enoe/15ymas/
    """

    # ------------------------------------------------------------------
    # GRUPO 1 — Catálogos y metadata
    # ------------------------------------------------------------------

    def health(self) -> EnoeHealth:
        """Estado del dataset ENOE: último periodo, conteos, cobertura.

        Endpoint: ``GET /api/v1/enoe/health``
        """
        return self._get_validated("/api/v1/enoe/health", EnoeHealth)

    def metadata(self) -> EnoeMetadata:
        """Metadata completa del dataset: fuente, tablas y caveats.

        Endpoint: ``GET /api/v1/enoe/metadata``
        """
        return self._get_validated("/api/v1/enoe/metadata", EnoeMetadata)

    def indicadores(self) -> IndicadoresResponse:
        """Catálogo de los 13 indicadores agregados disponibles.

        Endpoint: ``GET /api/v1/enoe/catalogos/indicadores``

        Returns:
            Response con ``count`` y la lista ``indicadores`` (slug, nombre,
            unidad, fórmula, caveat aplicable).
        """
        return self._get_validated(
            "/api/v1/enoe/catalogos/indicadores", IndicadoresResponse
        )

    def entidades(self) -> EntidadesResponse:
        """Catálogo de las 32 entidades federativas con clave INEGI.

        Endpoint: ``GET /api/v1/enoe/catalogos/entidades``
        """
        return self._get_validated(
            "/api/v1/enoe/catalogos/entidades", EntidadesResponse
        )

    def etapas(self) -> EtapasResponse:
        """Catálogo de etapas metodológicas (``clasica``, ``etoe_telefonica``, ``enoe_n``).

        Endpoint: ``GET /api/v1/enoe/catalogos/etapas-metodologicas``
        """
        return self._get_validated(
            "/api/v1/enoe/catalogos/etapas-metodologicas", EtapasResponse
        )

    # ------------------------------------------------------------------
    # GRUPO 2 — Indicadores agregados
    # ------------------------------------------------------------------

    def serie_nacional(
        self,
        *,
        indicador: str,
        desde: str | None = None,
        hasta: str | None = None,
        etapa: EtapaSlug | None = None,
    ) -> SerieNacionalResponse:
        """Serie temporal nacional de un indicador.

        Endpoint: ``GET /api/v1/enoe/indicadores/nacional/serie``

        Args:
            indicador: Slug del indicador (ej. ``"tasa_desocupacion"``,
                ``"til1"``, ``"tcco"``). Ver ``indicadores()``.
            desde: Periodo inicial inclusivo en formato ``YYYYTQ``
                (ej. ``"2024T1"``).
            hasta: Periodo final inclusivo.
            etapa: Filtra por etapa metodológica. ``None`` (default) trae
                las tres etapas concatenadas.

        Raises:
            NotFoundError: Si el indicador no existe en el catálogo.
        """
        params: dict[str, Any] = {"indicador": indicador}
        if desde is not None:
            params["desde"] = desde
        if hasta is not None:
            params["hasta"] = hasta
        if etapa is not None:
            params["etapa"] = etapa
        return self._get_validated(
            "/api/v1/enoe/indicadores/nacional/serie",
            SerieNacionalResponse,
            params=params,
        )

    def snapshot_nacional(self, *, periodo: str) -> SnapshotNacionalResponse:
        """Snapshot de los 13 indicadores nacionales en un periodo.

        Endpoint: ``GET /api/v1/enoe/indicadores/nacional/snapshot``

        Args:
            periodo: Trimestre en formato ``YYYYTQ`` (ej. ``"2025T1"``).
        """
        return self._get_validated(
            "/api/v1/enoe/indicadores/nacional/snapshot",
            SnapshotNacionalResponse,
            params={"periodo": periodo},
        )

    def serie_entidad(
        self,
        *,
        indicador: str,
        entidad_clave: str,
        desde: str | None = None,
        hasta: str | None = None,
        etapa: EtapaSlug | None = None,
    ) -> SerieEntidadResponse:
        """Serie temporal por entidad federativa para un indicador.

        Endpoint: ``GET /api/v1/enoe/indicadores/entidad/serie``

        Args:
            indicador: Slug del indicador.
            entidad_clave: Clave INEGI de 2 dígitos (ej. ``"09"`` = CDMX).
            desde: Periodo inicial inclusivo.
            hasta: Periodo final inclusivo.
            etapa: Filtra por etapa metodológica.
        """
        params: dict[str, Any] = {
            "indicador": indicador,
            "entidad_clave": entidad_clave,
        }
        if desde is not None:
            params["desde"] = desde
        if hasta is not None:
            params["hasta"] = hasta
        if etapa is not None:
            params["etapa"] = etapa
        return self._get_validated(
            "/api/v1/enoe/indicadores/entidad/serie",
            SerieEntidadResponse,
            params=params,
        )

    def snapshot_entidad(
        self,
        *,
        periodo: str,
        indicador: str,
    ) -> SnapshotEntidadResponse:
        """Snapshot de un indicador para las 32 entidades en un periodo.

        Endpoint: ``GET /api/v1/enoe/indicadores/entidad/snapshot``

        Args:
            periodo: Trimestre ``YYYYTQ``.
            indicador: Slug del indicador.
        """
        return self._get_validated(
            "/api/v1/enoe/indicadores/entidad/snapshot",
            SnapshotEntidadResponse,
            params={"periodo": periodo, "indicador": indicador},
        )

    def ranking(
        self,
        *,
        periodo: str,
        indicador: str,
        orden: OrdenRanking = "desc",
        limit: int = 5,
    ) -> RankingResponse:
        """Ranking de entidades por un indicador en un periodo.

        Endpoint: ``GET /api/v1/enoe/indicadores/entidad/ranking``

        Args:
            periodo: Trimestre ``YYYYTQ``.
            indicador: Slug del indicador.
            orden: ``"desc"`` (default, mayor a menor) o ``"asc"``.
            limit: Cantidad de entidades a devolver (1..32).
        """
        return self._get_validated(
            "/api/v1/enoe/indicadores/entidad/ranking",
            RankingResponse,
            params={
                "periodo": periodo,
                "indicador": indicador,
                "orden": orden,
                "limit": limit,
            },
        )

    # ------------------------------------------------------------------
    # GRUPO 3 — Distribuciones
    # ------------------------------------------------------------------

    def distribucion_sectorial_snapshot(
        self,
        *,
        periodo: str,
        nivel: NivelGeografico = "nacional",
        entidad_clave: str | None = None,
    ) -> DistribucionSectorialSnapshot:
        """Composición de ocupados por sector económico (12 sectores SCIAN).

        Endpoint: ``GET /api/v1/enoe/ocupados/por-sector/snapshot``

        Args:
            periodo: Trimestre ``YYYYTQ``.
            nivel: ``"nacional"`` o ``"entidad"``.
            entidad_clave: Obligatorio si ``nivel="entidad"``.

        Raises:
            ValueError: Si ``nivel="entidad"`` sin ``entidad_clave``.
        """
        params: dict[str, Any] = {"periodo": periodo, "nivel": nivel}
        if nivel == "entidad":
            if entidad_clave is None:
                raise ValueError(
                    "entidad_clave es obligatorio cuando nivel='entidad'"
                )
            params["geo_clave"] = entidad_clave
        return self._get_validated(
            "/api/v1/enoe/ocupados/por-sector/snapshot",
            DistribucionSectorialSnapshot,
            params=params,
        )

    def distribucion_sectorial_serie(
        self,
        *,
        sector_clave: str,
        nivel: NivelGeografico = "nacional",
        entidad_clave: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> DistribucionSectorialSerie:
        """Serie temporal de un sector económico.

        Endpoint: ``GET /api/v1/enoe/ocupados/por-sector/serie``

        Args:
            sector_clave: Clave del sector (ej. ``"10"`` = Servicios diversos).
            nivel: ``"nacional"`` o ``"entidad"``.
            entidad_clave: Obligatorio si ``nivel="entidad"``.
            desde: Periodo inicial ``YYYYTQ``.
            hasta: Periodo final ``YYYYTQ``.

        Raises:
            ValueError: Si ``nivel="entidad"`` sin ``entidad_clave``.
        """
        params: dict[str, Any] = {
            "sector_clave": sector_clave,
            "nivel": nivel,
        }
        if nivel == "entidad":
            if entidad_clave is None:
                raise ValueError(
                    "entidad_clave es obligatorio cuando nivel='entidad'"
                )
            params["geo_clave"] = entidad_clave
        if desde is not None:
            params["desde"] = desde
        if hasta is not None:
            params["hasta"] = hasta
        return self._get_validated(
            "/api/v1/enoe/ocupados/por-sector/serie",
            DistribucionSectorialSerie,
            params=params,
        )

    def distribucion_posicion_snapshot(
        self,
        *,
        periodo: str,
        nivel: NivelGeografico = "nacional",
        entidad_clave: str | None = None,
    ) -> DistribucionPosicionSnapshot:
        """Composición de ocupados por posición en la ocupación (4 categorías).

        Endpoint: ``GET /api/v1/enoe/ocupados/por-posicion/snapshot``

        Args:
            periodo: Trimestre ``YYYYTQ``.
            nivel: ``"nacional"`` o ``"entidad"``.
            entidad_clave: Obligatorio si ``nivel="entidad"``.
        """
        params: dict[str, Any] = {"periodo": periodo, "nivel": nivel}
        if nivel == "entidad":
            if entidad_clave is None:
                raise ValueError(
                    "entidad_clave es obligatorio cuando nivel='entidad'"
                )
            params["geo_clave"] = entidad_clave
        return self._get_validated(
            "/api/v1/enoe/ocupados/por-posicion/snapshot",
            DistribucionPosicionSnapshot,
            params=params,
        )

    def distribucion_posicion_serie(
        self,
        *,
        pos_clave: int,
        nivel: NivelGeografico = "nacional",
        entidad_clave: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> DistribucionPosicionSerie:
        """Serie temporal de una posición en la ocupación.

        Endpoint: ``GET /api/v1/enoe/ocupados/por-posicion/serie``

        Args:
            pos_clave: Clave de la posición (1=subordinados, 2=empleadores,
                3=cuenta propia, 4=no remunerados).
            nivel: ``"nacional"`` o ``"entidad"``.
            entidad_clave: Obligatorio si ``nivel="entidad"``.
            desde: Periodo inicial ``YYYYTQ``.
            hasta: Periodo final ``YYYYTQ``.
        """
        params: dict[str, Any] = {"pos_clave": pos_clave, "nivel": nivel}
        if nivel == "entidad":
            if entidad_clave is None:
                raise ValueError(
                    "entidad_clave es obligatorio cuando nivel='entidad'"
                )
            params["geo_clave"] = entidad_clave
        if desde is not None:
            params["desde"] = desde
        if hasta is not None:
            params["hasta"] = hasta
        return self._get_validated(
            "/api/v1/enoe/ocupados/por-posicion/serie",
            DistribucionPosicionSerie,
            params=params,
        )

    # ------------------------------------------------------------------
    # GRUPO 4 — Microdatos
    # ------------------------------------------------------------------

    def microdatos_schema(self, tabla: TablaMicrodatos) -> MicrodatosSchema:
        """Schema (columnas y descripciones) de una tabla de microdatos.

        Endpoint: ``GET /api/v1/enoe/microdatos/{tabla}/schema``

        Args:
            tabla: ``"viv"``, ``"hog"``, ``"sdem"``, ``"coe1"`` o ``"coe2"``.
        """
        return self._get_validated(
            f"/api/v1/enoe/microdatos/{tabla}/schema",
            MicrodatosSchema,
        )

    def microdatos_count(
        self,
        tabla: TablaMicrodatos,
        *,
        periodo: str,
        entidad_clave: str | None = None,
        sex: int | None = None,
        eda_min: int | None = None,
        eda_max: int | None = None,
    ) -> MicrodatosCount:
        """Conteo de microdatos con filtros sin descargar las filas.

        Endpoint: ``GET /api/v1/enoe/microdatos/{tabla}/count``

        Args:
            tabla: ``"viv"``, ``"hog"``, ``"sdem"``, ``"coe1"`` o ``"coe2"``.
            periodo: Trimestre ``YYYYTQ`` obligatorio.
            entidad_clave: Clave INEGI de 2 dígitos.
            sex: Sexo INEGI (``1``=hombre, ``2``=mujer); aplica a sdem/coe1/coe2.
            eda_min: Edad mínima inclusiva; aplica a sdem/coe1/coe2.
            eda_max: Edad máxima inclusiva; aplica a sdem/coe1/coe2.
        """
        params: dict[str, Any] = {"periodo": periodo}
        if entidad_clave is not None:
            params["entidad_clave"] = entidad_clave
        if sex is not None:
            params["sex"] = sex
        if eda_min is not None:
            params["eda_min"] = eda_min
        if eda_max is not None:
            params["eda_max"] = eda_max
        return self._get_validated(
            f"/api/v1/enoe/microdatos/{tabla}/count",
            MicrodatosCount,
            params=params,
        )

    def microdatos_page(
        self,
        tabla: TablaMicrodatos,
        *,
        periodo: str,
        page: int = 1,
        per_page: int = 1000,
        entidad_clave: str | None = None,
        sex: int | None = None,
        eda_min: int | None = None,
        eda_max: int | None = None,
        include_extras: bool = True,
    ) -> MicrodatosListResponse:
        """Una página de microdatos con paginación explícita.

        Endpoint: ``GET /api/v1/enoe/microdatos/{tabla}/list``

        Para iterar sobre todas las páginas en orden, usar
        :meth:`microdatos_iter`. Para volcar todo a un DataFrame, usar
        :meth:`microdatos_to_pandas`.

        Args:
            tabla: Tabla de microdatos.
            periodo: Trimestre ``YYYYTQ`` obligatorio.
            page: Número de página (1-indexed).
            per_page: Filas por página (1..1000).
            entidad_clave: Filtro opcional por entidad.
            sex: Filtro opcional por sexo.
            eda_min: Edad mínima.
            eda_max: Edad máxima.
            include_extras: Si ``True`` (default), incluye ``extras_jsonb``
                con todas las variables originales no promovidas a columna.
        """
        params: dict[str, Any] = {
            "periodo": periodo,
            "page": page,
            "per_page": per_page,
            "include_extras": include_extras,
        }
        if entidad_clave is not None:
            params["entidad_clave"] = entidad_clave
        if sex is not None:
            params["sex"] = sex
        if eda_min is not None:
            params["eda_min"] = eda_min
        if eda_max is not None:
            params["eda_max"] = eda_max
        return self._get_validated(
            f"/api/v1/enoe/microdatos/{tabla}/list",
            MicrodatosListResponse,
            params=params,
        )

    def microdatos_iter(
        self,
        tabla: TablaMicrodatos,
        *,
        periodo: str,
        entidad_clave: str | None = None,
        sex: int | None = None,
        eda_min: int | None = None,
        eda_max: int | None = None,
        per_page: int = 1000,
        include_extras: bool = True,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterador síncrono sobre microdatos paginados.

        Hace requests pagina-a-pagina contra
        ``/api/v1/enoe/microdatos/{tabla}/list`` y produce un ``dict`` por
        fila. La iteración termina cuando la API marca ``has_next=False`` o
        cuando se alcanza ``limit`` (si se especifica).

        Examples:
            Iterar todos los microdatos sociodemográficos de CDMX en 2025T1:

                >>> with DatosMexico() as client:
                ...     for row in client.enoe.microdatos_iter(
                ...         "sdem", periodo="2025T1", entidad_clave="09",
                ...     ):
                ...         # procesar row sin cargar todo a memoria
                ...         ...

            Acotar a una muestra rápida (los primeros 100 registros):

                >>> with DatosMexico() as client:
                ...     filas = list(
                ...         client.enoe.microdatos_iter(
                ...             "sdem", periodo="2025T1",
                ...             entidad_clave="09", limit=100,
                ...         )
                ...     )

        Args:
            tabla: Tabla de microdatos.
            periodo: Trimestre ``YYYYTQ`` obligatorio.
            entidad_clave: Filtro opcional por entidad.
            sex: Filtro opcional por sexo (1=hombre, 2=mujer).
            eda_min: Edad mínima inclusiva.
            eda_max: Edad máxima inclusiva.
            per_page: Filas por request (1..1000). Default 1000 minimiza
                el número de requests.
            include_extras: Si ``True`` (default), incluye
                ``extras_jsonb`` con todas las variables ENOE no promovidas
                a columna. Activarlo por defecto sigue la convención de
                la Sub-fase 3.10b del observatorio: el SDK no oculta
                campos al investigador.
            limit: Máximo de filas a producir (atajo para muestras).
                ``None`` (default) itera hasta el final.

        Yields:
            ``dict`` con los campos de cada fila, esquema dependiente de
            la tabla.
        """
        page = 1
        emitted = 0
        while True:
            response = self.microdatos_page(
                tabla,
                periodo=periodo,
                page=page,
                per_page=per_page,
                entidad_clave=entidad_clave,
                sex=sex,
                eda_min=eda_min,
                eda_max=eda_max,
                include_extras=include_extras,
            )
            for row in response.data:
                yield row
                emitted += 1
                if limit is not None and emitted >= limit:
                    return
            if not response.pagination.has_next:
                return
            page += 1

    def microdatos_to_pandas(
        self,
        tabla: TablaMicrodatos,
        *,
        periodo: str,
        entidad_clave: str | None = None,
        sex: int | None = None,
        eda_min: int | None = None,
        eda_max: int | None = None,
        per_page: int = 1000,
        include_extras: bool = True,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Descarga microdatos a un ``pandas.DataFrame``.

        Construye internamente el iterador (:meth:`microdatos_iter`) y lo
        materializa en un único DataFrame. Para volúmenes grandes (>100k
        filas) considerar usar :meth:`microdatos_iter` y procesar por
        chunks.

        Examples:
            >>> with DatosMexico() as client:
            ...     df = client.enoe.microdatos_to_pandas(
            ...         "sdem", periodo="2025T1",
            ...         entidad_clave="09", limit=1000,
            ...     )
            ...     df["eda"].mean()
            ...     # 41.5

        Args:
            tabla: Tabla de microdatos.
            periodo: Trimestre ``YYYYTQ`` obligatorio.
            entidad_clave: Filtro opcional por entidad.
            sex: Filtro opcional por sexo.
            eda_min: Edad mínima.
            eda_max: Edad máxima.
            per_page: Filas por request.
            include_extras: Si ``True``, incluye ``extras_jsonb``.
            limit: Máximo de filas a descargar.

        Returns:
            ``pandas.DataFrame`` con las filas. Si no hay matches devuelve
            un DataFrame vacío.

        Raises:
            ImportError: Si ``pandas`` no está instalado. Instalar con
                ``pip install datos-mexico[examples]`` o
                ``pip install pandas``.
        """
        try:
            import pandas as pd
        except ImportError as exc:  # pragma: no cover - guard branch
            raise ImportError(
                "pandas no está instalado. Instalar con:\n"
                "    pip install datos-mexico[examples]\n"
                "o bien:\n"
                "    pip install pandas"
            ) from exc

        rows = list(
            self.microdatos_iter(
                tabla,
                periodo=periodo,
                entidad_clave=entidad_clave,
                sex=sex,
                eda_min=eda_min,
                eda_max=eda_max,
                per_page=per_page,
                include_extras=include_extras,
                limit=limit,
            )
        )
        return pd.DataFrame(rows)
