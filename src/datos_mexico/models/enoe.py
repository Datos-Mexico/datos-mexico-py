"""Modelos Pydantic para el dataset ENOE (Encuesta Nacional de Ocupación y Empleo).

Cobertura del observatorio ENOE: ~101.5M microdatos en cinco tablas
(``viv``, ``hog``, ``sdem``, ``coe1``, ``coe2``) y ~76 mil indicadores
agregados (nacionales y por entidad federativa), entre 2005T1 y 2025T1.
Fuente: INEGI — `ENOE 15+`_.

.. _`ENOE 15+`: https://www.inegi.org.mx/programas/enoe/15ymas/

Convenciones (consistentes con CONSAR/ENIGH):

- Indicadores numéricos (valores de tasas, conteos expandidos, participaciones)
  llegan como ``float`` o ``int`` desde la API. Los modelos los preservan
  como ``float``/``int`` puros: para los indicadores ENOE no se hace
  aritmética monetaria exacta, así que ``Decimal`` agregaría fricción sin
  beneficio. Los conteos expandidos (``n_*``, ``total_*``) son ``int``.
- ``periodo`` es siempre ``str`` con formato ``YYYYTQ`` (ej. ``"2025T1"``).
- ``entidad_clave`` es siempre ``str`` con dos dígitos (ej. ``"09"`` para
  CDMX); seguir el contrato canónico del observatorio post-Sub-fase 3.10c.
- ``etapa`` es ``str | None`` con los slugs ``"clasica"``,
  ``"etoe_telefonica"``, o ``"enoe_n"``.
- ``extra="allow"`` heredado del base config: si la API agrega campos
  nuevos, los modelos no rompen.
"""

from __future__ import annotations

from typing import Any

from datos_mexico.models.base import DatosMexicoModel

# ============================================================================
# Metadata y health
# ============================================================================


class EnoeHealth(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/health``."""

    status: str
    ultimo_periodo: str
    ultima_carga: str
    total_microdatos: int
    total_indicadores_agregados: int
    cobertura_temporal: str


class EnoeTablaInfo(DatosMexicoModel):
    """Descripción de una tabla del dataset (microdatos o agregados)."""

    nombre: str
    descripcion: str
    n_filas: int
    has_data: bool


class CaveatMetodologico(DatosMexicoModel):
    """Caveat metodológico tipado.

    Cada caveat documenta una salvedad publicada por el observatorio: cambio
    de marco muestral en 2020T3, redefinición del TCCO post-2020T1,
    re-cálculo del dominio 15+ en la etapa clásica, gap documental en
    2020T2, etc.
    """

    slug: str
    titulo: str
    descripcion: str
    periodo_aplicable: str | None = None
    referencia: str | None = None


class EnoeMetadata(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/metadata``."""

    nombre: str
    acronimo: str
    fuente: str
    fuente_url: str
    periodicidad: str
    cobertura_temporal: str
    cobertura_geografica: str
    n_trimestres_disponibles: int
    n_indicadores: int
    n_entidades: int
    etapas_metodologicas: list[str]
    tablas_disponibles: list[EnoeTablaInfo]
    total_microdatos: int
    total_agregados: int
    caveats: list[CaveatMetodologico]


# ============================================================================
# Catálogos
# ============================================================================


class IndicadorRef(DatosMexicoModel):
    """Item del catálogo de indicadores."""

    slug: str
    nombre: str
    descripcion: str
    unidad: str
    categoria: str
    formula: str | None = None
    fuente_metodologica: str | None = None
    n_observaciones_nacional: int | None = None
    n_observaciones_entidad: int | None = None
    cobertura_temporal: str | None = None
    caveat_metodologico: str | None = None


class IndicadoresResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/catalogos/indicadores``."""

    count: int
    indicadores: list[IndicadorRef]


class EntidadRef(DatosMexicoModel):
    """Item del catálogo de entidades federativas."""

    clave: str
    nombre: str
    abreviatura: str


class EntidadesResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/catalogos/entidades``."""

    count: int
    entidades: list[EntidadRef]


class EtapaRef(DatosMexicoModel):
    """Item del catálogo de etapas metodológicas."""

    slug: str
    nombre: str
    descripcion: str
    periodo_inicio: str | None = None
    periodo_fin: str | None = None
    dominio_edad: str | None = None
    n_trimestres: int | None = None
    tiene_microdatos: bool | None = None
    caveat_aplicable: str | None = None


class EtapasResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/catalogos/etapas-metodologicas``."""

    count: int
    etapas: list[EtapaRef]


# ============================================================================
# Cobertura / paginación común
# ============================================================================


class CoberturaTemporal(DatosMexicoModel):
    """Rango temporal cubierto por una respuesta de serie."""

    desde: str
    hasta: str
    n_observaciones: int


class PuntoSerie(DatosMexicoModel):
    """Punto en una serie temporal de un indicador."""

    periodo: str
    valor: float | None = None
    etapa: str | None = None


# ============================================================================
# Indicadores nacionales
# ============================================================================


class SerieNacionalResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/indicadores/nacional/serie``."""

    indicador: str
    nombre: str
    unidad: str
    categoria: str | None = None
    cobertura: CoberturaTemporal
    datos: list[PuntoSerie]
    caveats: list[CaveatMetodologico]
    source: str
    source_url: str | None = None


class IndicadorSnapshotItem(DatosMexicoModel):
    """Un indicador dentro de un snapshot."""

    indicador: str
    nombre: str
    unidad: str
    valor: float | None = None


class SnapshotNacionalResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/indicadores/nacional/snapshot``."""

    periodo: str
    etapa: str | None = None
    n_indicadores: int
    indicadores: list[IndicadorSnapshotItem]


# ============================================================================
# Indicadores por entidad
# ============================================================================


class SerieEntidadResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/indicadores/entidad/serie``."""

    indicador: str
    nombre: str
    unidad: str
    categoria: str | None = None
    entidad_clave: str
    entidad_nombre: str
    entidad_abreviatura: str | None = None
    cobertura: CoberturaTemporal
    datos: list[PuntoSerie]
    caveats: list[CaveatMetodologico]
    source: str


class EntidadSnapshotRow(DatosMexicoModel):
    """Una entidad en un snapshot por indicador."""

    entidad_clave: str
    entidad_nombre: str
    entidad_abreviatura: str | None = None
    valor: float | None = None


class SnapshotEntidadResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/indicadores/entidad/snapshot``."""

    periodo: str
    etapa: str | None = None
    indicador: str
    nombre: str
    unidad: str
    categoria: str | None = None
    n_entidades: int
    datos: list[EntidadSnapshotRow]


class RankingEntidadRow(DatosMexicoModel):
    """Fila del ranking de entidades."""

    rank: int
    entidad_clave: str
    entidad_nombre: str
    entidad_abreviatura: str | None = None
    valor: float | None = None


class RankingResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/indicadores/entidad/ranking``."""

    periodo: str
    etapa: str | None = None
    indicador: str
    nombre: str
    unidad: str
    orden: str
    limit: int
    total_resultados: int
    ranking: list[RankingEntidadRow]
    caveats: list[CaveatMetodologico]
    source: str


# ============================================================================
# Distribuciones (sectorial + posición)
# ============================================================================


class DistribucionSectorialRow(DatosMexicoModel):
    """Fila de la distribución por sector económico."""

    periodo: str | None = None
    sector_clave: str
    sector_nombre: str
    total_ocupados: int
    participacion_porcentaje: float
    etapa: str | None = None


class DistribucionSectorialSnapshot(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/ocupados/por-sector/snapshot``."""

    periodo: str
    etapa: str | None = None
    nivel: str
    geo_clave: str | None = None
    geo_nombre: str | None = None
    total_ocupados_nivel: int
    n_sectores: int
    distribucion: list[DistribucionSectorialRow]


class DistribucionSectorialSerie(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/ocupados/por-sector/serie``."""

    sector_clave: str
    sector_nombre: str
    nivel: str
    geo_clave: str | None = None
    geo_nombre: str | None = None
    cobertura: CoberturaTemporal
    datos: list[DistribucionSectorialRow]


class DistribucionPosicionRow(DatosMexicoModel):
    """Fila de la distribución por posición en la ocupación."""

    periodo: str | None = None
    pos_clave: int
    pos_nombre: str
    total_ocupados: int
    participacion_porcentaje: float
    etapa: str | None = None


class DistribucionPosicionSnapshot(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/ocupados/por-posicion/snapshot``."""

    periodo: str
    etapa: str | None = None
    nivel: str
    geo_clave: str | None = None
    geo_nombre: str | None = None
    total_ocupados_nivel: int
    n_posiciones: int
    distribucion: list[DistribucionPosicionRow]


class DistribucionPosicionSerie(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/ocupados/por-posicion/serie``."""

    pos_clave: int
    pos_nombre: str
    nivel: str
    geo_clave: str | None = None
    geo_nombre: str | None = None
    cobertura: CoberturaTemporal
    datos: list[DistribucionPosicionRow]


# ============================================================================
# Microdatos
# ============================================================================


class MicrodatoColumna(DatosMexicoModel):
    """Una columna en el schema de una tabla de microdatos."""

    nombre: str
    tipo: str
    nullable: bool
    descripcion: str | None = None


class MicrodatosSchema(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/microdatos/{tabla}/schema``."""

    tabla: str
    total_columnas: int
    total_filas: int
    cobertura_temporal: str
    columnas: list[MicrodatoColumna]


class MicrodatosCount(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/microdatos/{tabla}/count``."""

    tabla: str
    filtros: dict[str, Any]
    total: int
    caveat_metodologico: str | None = None
    source: str


class MicrodatosPagination(DatosMexicoModel):
    """Bloque de paginación del endpoint microdatos/list."""

    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_previous: bool


class MicrodatosListResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enoe/microdatos/{tabla}/list``.

    ``data`` se preserva como ``list[dict]`` (sin tipar cada fila) porque
    cada tabla tiene un schema diferente y los nombres de columna son
    estables solo dentro de una tabla. Para análisis tipado, consultar el
    schema con :meth:`EnoeNamespace.microdatos_schema` y trabajar sobre el
    DataFrame de :meth:`EnoeNamespace.microdatos_to_pandas`.
    """

    tabla: str
    filtros: dict[str, Any]
    pagination: MicrodatosPagination
    data: list[dict[str, Any]]
    caveats: list[CaveatMetodologico] | None = None
    source: str
    tiempo_query_ms: float | None = None
