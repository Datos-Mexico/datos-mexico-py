"""Modelos Pydantic para el dataset ENIGH 2024 Nueva Serie.

Cobertura: hogares (summary, deciles, entidades), gastos por rubro,
demografía, actividades agropecuaria/no-agropecuaria/JCF, metadata y
validaciones contra cifras INEGI oficiales.

Convenciones (consistentes con CONSAR):

- Campos monetarios (``mean_*_trim``, ``mean_*_mensual``, ``oficial_*``,
  ``calculado``) usan ``Decimal`` con ``BeforeValidator(_to_decimal)``
  para preservar precisión y permitir aritmética exacta. La precisión
  importa especialmente para ``bound_delta_pct`` y ``oficial_mensual``,
  que documentan la diferencia entre el cálculo del observatorio y la
  cifra oficial INEGI.
- Porcentajes (``pct_*``, ``share_*``) también como ``Decimal``.
- Sumas y conteos (``n_*``, ``sum_*``) como ``int``.
- ``extra="allow"`` heredado del base config: si la API agrega campos,
  no rompe.
"""

from __future__ import annotations

from datos_mexico._helpers import Money
from datos_mexico.models.base import DatosMexicoModel

# ============================================================================
# Catálogo de hogares
# ============================================================================


class HogaresSummary(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/hogares/summary``.

    KPIs nacionales del padrón de hogares en la ENIGH 2024 NS: tamaño de
    muestra, factores de expansión, ingreso y gasto medios trimestrales y
    mensuales.
    """

    n_hogares_muestra: int
    n_hogares_expandido: int
    mean_ing_cor_trim: Money
    mean_ing_cor_mensual: Money
    mean_gasto_mon_trim: Money
    mean_gasto_mon_mensual: Money
    edition: str
    source: str


class DecilRow(DatosMexicoModel):
    """Fila por decil de ingreso.

    Devuelta como elemento del array ``GET /api/v1/enigh/hogares/by-decil``.
    """

    decil: int
    n_hogares_muestra: int
    n_hogares_expandido: int
    mean_ing_cor_trim: Money
    mean_ing_cor_mensual: Money
    mean_gasto_mon_trim: Money
    share_factor_pct: Money


class EntidadRow(DatosMexicoModel):
    """Fila por entidad federativa.

    Devuelta como elemento del array ``GET /api/v1/enigh/hogares/by-entidad``.
    """

    clave: str
    nombre: str
    n_hogares_muestra: int
    n_hogares_expandido: int
    mean_ing_cor_trim: Money
    mean_ing_cor_mensual: Money
    mean_gasto_mon_trim: Money


# ============================================================================
# Gastos por rubro
# ============================================================================


class RubroRow(DatosMexicoModel):
    """Fila por rubro de gasto monetario.

    Los campos ``oficial_mensual`` y ``bound_delta_pct`` documentan la
    validación contra la cifra oficial publicada por INEGI: el observatorio
    expone ambas para que el usuario pueda auditar el cálculo. Llegan como
    ``None`` cuando INEGI no publica una cifra oficial directamente
    comparable para ese rubro o decil.
    """

    slug: str
    nombre: str
    mean_gasto_trim: Money
    mean_gasto_mensual: Money
    pct_del_monetario: Money
    oficial_mensual: Money | None = None
    bound_delta_pct: Money | None = None


class RubrosResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/gastos/by-rubro``.

    Cuando ``decil`` es ``None`` la cifra es nacional; cuando es un entero
    ``1..10`` la cifra corresponde a ese decil de ingreso.
    """

    decil: int | None = None
    mean_gasto_mon_trim: Money
    rubros: list[RubroRow]


# ============================================================================
# Demografía
# ============================================================================


class SexoCount(DatosMexicoModel):
    """Conteo expandido de personas por sexo."""

    sexo: str
    n_expandido: int
    pct: Money


class EdadBucket(DatosMexicoModel):
    """Bucket de edad con conteo expandido."""

    bucket: str
    n_expandido: int
    pct: Money


class DemographicsResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/poblacion/demographics``.

    ``scope`` indica si la cifra es nacional o de una entidad específica.
    """

    scope: str
    n_personas_muestra: int
    n_personas_expandido: int
    sexo: list[SexoCount]
    edad: list[EdadBucket]


# ============================================================================
# Actividades económicas de los hogares
# ============================================================================


class ActividadDecilRow(DatosMexicoModel):
    """Distribución de hogares con una actividad por decil de ingreso."""

    decil: int
    n_hogares_muestra: int
    n_hogares_expandido: int
    pct_share_actividad: Money


class ActividadEntidadRow(DatosMexicoModel):
    """Top entidades por hogares con la actividad."""

    clave: str
    nombre: str
    n_hogares_expandido: int


class ActividadAgroResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/actividad/agro``.

    Hogares con actividad agropecuaria (cultivo, ganadería, pesca).
    """

    n_hogares_muestra: int
    n_hogares_expandido: int
    pct_del_universo: Money
    sum_ventas_trim: int
    sum_gasto_negocio_trim: int
    mean_ventas_por_hogar: Money
    por_decil: list[ActividadDecilRow]
    top_entidades: list[ActividadEntidadRow]
    note: str


class ActividadNoagroResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/actividad/noagro``.

    Hogares con actividad económica no agropecuaria (negocios, comercio,
    servicios).
    """

    n_hogares_muestra: int
    n_hogares_expandido: int
    pct_del_universo: Money
    sum_ventas_trim: int
    sum_ingreso_trim: int
    mean_ventas_por_hogar: Money
    por_decil: list[ActividadDecilRow]
    top_entidades: list[ActividadEntidadRow]
    note: str


class JcfEntidadRow(DatosMexicoModel):
    """Beneficiarios de jornal/cuenta familiar por entidad."""

    clave: str
    nombre: str
    beneficiarios_muestra: int
    beneficiarios_expandido: int


class ActividadJcfResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/actividad/jcf``.

    Hogares con actividad por jornal o cuenta familiar (autoempleo o
    trabajo familiar no remunerado formalmente).
    """

    n_beneficiarios_muestra: int
    n_beneficiarios_expandido: int
    sum_ingreso_trim: int
    mean_ingreso_trim_por_beneficiario: Money
    por_entidad: list[JcfEntidadRow]
    note: str


# ============================================================================
# Metadata y validaciones
# ============================================================================


class SourceRef(DatosMexicoModel):
    """Referencia a una fuente primaria consultada."""

    title: str
    url: str
    consulted_on: str


class EnighMetadata(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/metadata``.

    Información sobre la edición de la ENIGH, fuentes primarias y notas
    metodológicas.
    """

    edition: str
    periodicity: str
    reference_date: str
    schema_version: str
    last_updated: str
    total_hogares_muestra: int
    total_hogares_expandido: int
    total_tablas_ingestadas: int
    total_catalogos: int
    sources: list[SourceRef]
    methodology_notes: list[str]


class ValidacionRow(DatosMexicoModel):
    """Una validación individual contra una cifra oficial INEGI.

    ``passing`` es ``True`` cuando ``|delta_pct| <= tolerance_pct``.
    """

    id: str
    scope: str
    metric: str
    column: str
    unit: str
    calculado: Money
    oficial: Money
    delta_pct: Money
    tolerance_pct: Money
    passing: bool
    source: str


class ValidacionesResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/enigh/validaciones``.

    Resumen de las validaciones del observatorio contra cifras oficiales
    INEGI: ``count`` total de validaciones, ``passing`` y ``failing`` con
    el detalle en ``bounds``.
    """

    count: int
    passing: int
    failing: int
    bounds: list[ValidacionRow]
