"""Modelos Pydantic para el dataset CONSAR/SAR.

Cobertura: catálogos, recursos administrados, PEA cotizantes, comisiones,
flujos, traspasos, rendimientos, precios (NAV), precios de gestión, cuentas
(número de cuentas y montos), medidas regulatorias, y activo neto por
SIEFORE.

Convenciones:

- Campos monetarios y porcentuales (``_mm``, ``_pct``, ``precio``, ``valor``
  de medidas, comisiones) se exponen como ``Decimal`` para preservar
  precisión y permitir aritmética exacta.
- Campos de fecha (``fecha``, ``desde``, ``hasta``, ``fecha_*``,
  ``desde_fecha``) se exponen como ``date``.
- Campos que pueden ser ``null`` para fechas/AFOREs sin datos están tipados
  como ``Optional[T]``.
- ``unit`` es siempre un texto descriptivo del unidad (ej. ``"MXN_mm"``,
  ``"pct"``).
"""

from __future__ import annotations

from datos_mexico._helpers import DateField, Money
from datos_mexico.models.base import DatosMexicoModel

# ============================================================================
# GRUPO 1 — Catálogos
# ============================================================================


class AforeRow(DatosMexicoModel):
    """Item del catálogo de AFOREs."""

    id: int
    codigo: str
    nombre_corto: str
    nombre_csv: str
    tipo_pension: str
    fecha_alta_serie: DateField
    activa: bool
    orden_display: int


class AforesResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/afores``."""

    count: int
    afores: list[AforeRow]
    source: str


class TipoRecursoRow(DatosMexicoModel):
    """Item del catálogo de tipos de recurso (RCV, vivienda, voluntario, etc.)."""

    id: int
    codigo: str
    columna_csv: str
    nombre_corto: str
    nombre_oficial: str
    descripcion: str | None = None
    categoria: str
    es_total_sar: bool
    orden_display: int


class TiposRecursoResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/tipos-recurso``."""

    count: int
    tipos_recurso: list[TipoRecursoRow]


class MetricaCuentaRow(DatosMexicoModel):
    """Item del catálogo de métricas de cuentas."""

    id: int
    slug: str
    columna_csv: str
    descripcion: str
    unidad: str
    desde_fecha: DateField
    orden_display: int
    notas: str | None = None


class MetricasCuentaResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/metricas-cuenta``."""

    n: int
    metricas: list[MetricaCuentaRow]
    caveats: list[str]


class MetricaSensibilidadRow(DatosMexicoModel):
    """Item del catálogo de métricas de sensibilidad."""

    id: int
    slug: str
    columna_csv: str
    descripcion: str
    unidad: str
    orden_display: int


class MetricasSensibilidadResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/metricas-sensibilidad``."""

    n: int
    metricas: list[MetricaSensibilidadRow]
    caveats: list[str]


# ============================================================================
# GRUPO 2 — Recursos administrados
# ============================================================================


class TotalSarPunto(DatosMexicoModel):
    """Punto mensual de la serie del SAR total."""

    fecha: DateField
    monto_mxn_mm: Money
    n_afores: int


class TotalesSarResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/totales``.

    Serie histórica del SAR completo en mil millones de MXN corrientes.
    """

    unit: str
    n_puntos: int
    fecha_min: DateField
    fecha_max: DateField
    serie: list[TotalSarPunto]
    caveats: list[str]
    source: str


class AforeSnapshotRow(DatosMexicoModel):
    """Fila de un snapshot por AFORE."""

    afore_codigo: str
    afore_nombre_corto: str
    sar_total_mm: Money | None = None
    recursos_trabajadores_mm: Money | None = None
    recursos_administrados_mm: Money | None = None
    pct_sistema: Money | None = None


class PorAforeResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/por-afore``."""

    fecha: DateField
    unit: str
    total_sistema_mm: Money
    n_afores_reportando: int
    afores: list[AforeSnapshotRow]
    caveats: list[str]


class ComponenteSnapshotRow(DatosMexicoModel):
    """Fila de snapshot por componente (tipo de recurso)."""

    tipo_codigo: str
    tipo_nombre_corto: str
    categoria: str
    monto_mxn_mm: Money
    pct_del_sar_total: Money | None = None


class PorComponenteResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/por-componente``."""

    fecha: DateField
    unit: str
    sar_total_mm: Money
    n_componentes: int
    componentes: list[ComponenteSnapshotRow]
    caveats: list[str]


class ComposicionItem(DatosMexicoModel):
    """Item de la composición contable del SAR para una fecha."""

    tipo_codigo: str
    tipo_nombre_corto: str
    monto_mxn_mm: Money
    pct_del_sar: Money


class ComposicionResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/composicion``.

    Verifica la identidad contable: la suma de los 8 componentes principales
    debe coincidir con el total del SAR reportado. ``cierre_al_peso`` es
    ``True`` cuando el delta absoluto es despreciable.
    """

    fecha: DateField
    unit: str
    sar_total_reportado_mm: Money
    suma_8_componentes_mm: Money
    delta_abs_mm: Money
    delta_pct: Money
    cierre_al_peso: bool
    componentes: list[ComposicionItem]
    caveats: list[str]
    identidad_caveat: str


class ImssVsIsssteePunto(DatosMexicoModel):
    """Punto mensual de la serie RCV IMSS vs ISSSTE."""

    fecha: DateField
    rcv_imss_mm: Money | None = None
    rcv_issste_mm: Money | None = None
    ratio_issste_sobre_imss: Money | None = None


class ImssVsIsssteeResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/imss-vs-issste``."""

    unit: str
    n_puntos: int
    serie: list[ImssVsIsssteePunto]
    caveats: list[str]


class SerieAforeRef(DatosMexicoModel):
    """Referencia de AFORE en una serie filtrada por afore."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class SerieTipoRecursoRef(DatosMexicoModel):
    """Referencia de tipo de recurso en una serie."""

    codigo: str
    nombre_corto: str
    nombre_oficial: str
    categoria: str


class SerieRango(DatosMexicoModel):
    """Rango temporal cubierto por una serie."""

    desde: DateField
    hasta: DateField


class SeriePunto(DatosMexicoModel):
    """Punto mensual de una serie genérica de recursos."""

    fecha: DateField
    monto_mxn_mm: Money


class SerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/recursos/serie``.

    Serie de un tipo de recurso (rcv, vivienda, voluntario, etc.).
    Si se filtra por ``afore_codigo``, ``afore`` está poblado; si no, es
    ``None`` (serie del sistema).
    """

    tipo_recurso: SerieTipoRecursoRef
    afore: SerieAforeRef | None = None
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[SeriePunto]
    caveats: list[str]


# ============================================================================
# GRUPO 3 — PEA cotizantes
# ============================================================================


class PeaCotizantesPunto(DatosMexicoModel):
    """Punto anual de cotizantes vs PEA."""

    anio: int
    cotizantes: int
    pea: int
    porcentaje_pea_afore: Money
    brecha_no_cubierta_pct: Money


class PeaCotizantesResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/pea-cotizantes/serie``."""

    n_puntos: int
    anio_min: int
    anio_max: int
    serie: list[PeaCotizantesPunto]
    cobertura_min_pct: Money
    cobertura_min_anio: int
    cobertura_max_pct: Money
    cobertura_max_anio: int
    caveats: list[str]


# ============================================================================
# GRUPO 4 — Comisiones
# ============================================================================


class ComisionAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de comisiones."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class ComisionPunto(DatosMexicoModel):
    """Punto mensual de comisión cobrada (porcentaje)."""

    fecha: DateField
    comision_pct: Money


class ComisionSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/comisiones/serie``."""

    afore: ComisionAforeRef | None = None
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[ComisionPunto]
    caveats: list[str]


class ComisionSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de comisiones por AFORE."""

    afore_codigo: str
    afore_nombre_corto: str
    tipo_pension: str
    comision_pct: Money | None = None


class ComisionSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/comisiones/snapshot``."""

    fecha: DateField
    unit: str
    n_afores_reportando: int
    promedio_simple_pct: Money
    minima_pct: Money
    maxima_pct: Money
    afores: list[ComisionSnapshotRow]
    caveats: list[str]


# ============================================================================
# GRUPO 5 — Flujos
# ============================================================================


class FlujoAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de flujos."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class FlujoPunto(DatosMexicoModel):
    """Punto mensual de flujos (entradas/salidas/neto)."""

    fecha: DateField
    montos_entradas: Money
    montos_salidas: Money
    flujo_neto: Money


class FlujoSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/flujos/serie``."""

    afore: FlujoAforeRef | None = None
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[FlujoPunto]
    caveats: list[str]


class FlujoSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de flujos por AFORE."""

    afore_codigo: str
    afore_nombre_corto: str
    tipo_pension: str
    montos_entradas: Money
    montos_salidas: Money
    flujo_neto: Money


class FlujoSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/flujos/snapshot``."""

    fecha: DateField
    unit: str
    n_afores_reportando: int
    sistema_entradas_mm: Money
    sistema_salidas_mm: Money
    sistema_flujo_neto_mm: Money
    afores: list[FlujoSnapshotRow]
    caveats: list[str]


# ============================================================================
# GRUPO 6 — Traspasos
# ============================================================================


class TraspasoAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de traspasos."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class TraspasoPunto(DatosMexicoModel):
    """Punto mensual de traspasos (cuentas)."""

    fecha: DateField
    num_tras_cedido: int | None = None
    num_tras_recibido: int | None = None
    traspaso_neto: int | None = None


class TraspasoSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/traspasos/serie``."""

    afore: TraspasoAforeRef | None = None
    n_puntos: int
    rango: SerieRango
    serie: list[TraspasoPunto]
    caveats: list[str]


class TraspasoIdentidad(DatosMexicoModel):
    """Identidad contable de traspasos: cedidos == recibidos a nivel sistema."""

    sistema_total_cedido: int
    sistema_total_recibido: int
    delta: int
    cierre_al_unidad: bool


class TraspasoSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de traspasos por AFORE."""

    afore_codigo: str
    afore_nombre_corto: str
    tipo_pension: str
    num_tras_cedido: int | None = None
    num_tras_recibido: int | None = None
    traspaso_neto: int | None = None


class TraspasoSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/traspasos/snapshot``."""

    fecha: DateField
    n_afores_reportando: int
    identidad: TraspasoIdentidad
    afores: list[TraspasoSnapshotRow]
    caveats: list[str]


# ============================================================================
# GRUPO 7 — Rendimientos
# ============================================================================


class RendimientoAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de rendimientos."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class RendimientoSieforeRef(DatosMexicoModel):
    """Referencia de SIEFORE."""

    slug: str
    nombre: str
    categoria: str


class RendimientoMappingMeta(DatosMexicoModel):
    """Provenance del mapping AFORExSIEFORE para rendimientos."""

    is_subvariant_decomposed: bool
    mapping_validated: bool | None = None
    validated_via: str | None = None


class RendimientoPunto(DatosMexicoModel):
    """Punto mensual de rendimiento (porcentaje)."""

    fecha: DateField
    rendimiento_pct: Money


class RendimientoSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/rendimientos/serie``."""

    afore: RendimientoAforeRef
    siefore: RendimientoSieforeRef
    plazo: str
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[RendimientoPunto]
    mapping_meta: RendimientoMappingMeta
    caveats: list[str]


class RendimientoSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de rendimientos."""

    afore_codigo: str
    afore_nombre_corto: str
    siefore_slug: str
    siefore_nombre: str
    siefore_categoria: str
    rendimiento_pct: Money


class RendimientoSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/rendimientos/snapshot``."""

    fecha: DateField
    plazo: str
    unit: str
    n_filas: int
    rendimiento_min: Money
    rendimiento_max: Money
    filas: list[RendimientoSnapshotRow]
    caveats: list[str]


class RendimientoSistemaPunto(DatosMexicoModel):
    """Punto mensual de rendimiento del sistema (promedio)."""

    fecha: DateField
    rendimiento_pct: Money


class RendimientoSistemaResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/rendimientos/sistema``."""

    siefore: RendimientoSieforeRef
    plazo: str
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[RendimientoSistemaPunto]
    caveats: list[str]


# ============================================================================
# GRUPO 8 — Precios (NAV) y GRUPO 9 — Precios de gestión (mismo schema)
# ============================================================================


class PrecioAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de precios."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class PrecioSieforeRef(DatosMexicoModel):
    """Referencia de SIEFORE para series de precios."""

    slug: str
    nombre: str
    categoria: str


class PrecioPunto(DatosMexicoModel):
    """Punto diario/mensual de precio (NAV)."""

    fecha: DateField
    precio: Money


class PrecioSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/precios/serie`` y precios-gestión/serie."""

    afore: PrecioAforeRef
    siefore: PrecioSieforeRef
    n_puntos: int
    rango: SerieRango
    precio_min: Money
    precio_max: Money
    serie: list[PrecioPunto]
    caveats: list[str]


class PrecioSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de precios."""

    afore_codigo: str
    afore_nombre_corto: str
    siefore_slug: str
    siefore_nombre: str
    siefore_categoria: str
    precio: Money


class PrecioSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/precios/snapshot`` y precios-gestión/snapshot."""

    fecha: DateField
    n_filas: int
    precio_min: Money
    precio_max: Money
    filas: list[PrecioSnapshotRow]
    caveats: list[str]


class PrecioComparativoSerieAfore(DatosMexicoModel):
    """Serie de precios para una AFORE en una comparación cross-AFORE."""

    afore_codigo: str
    afore_nombre_corto: str
    n_puntos: int
    serie: list[PrecioPunto]


class PrecioComparativoResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/precios/comparativo``.

    Comparación de precios de una SIEFORE entre todas las AFOREs en un
    rango de fechas.
    """

    siefore: PrecioSieforeRef
    rango: SerieRango
    n_afores: int
    series: list[PrecioComparativoSerieAfore]
    caveats: list[str]


# ============================================================================
# GRUPO 10 — Cuentas
# ============================================================================


class CuentaAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de cuentas."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class CuentaMetricaRef(DatosMexicoModel):
    """Referencia de métrica de cuentas."""

    slug: str
    descripcion: str
    unidad: str
    desde_fecha: DateField


class CuentaPunto(DatosMexicoModel):
    """Punto mensual de una métrica de cuentas (entero)."""

    fecha: DateField
    valor: int


class CuentaSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/cuentas/serie``."""

    afore: CuentaAforeRef
    metrica: CuentaMetricaRef
    n_puntos: int
    rango: SerieRango
    serie: list[CuentaPunto]
    caveats: list[str]


class CuentaSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de cuentas para una AFORE x métrica."""

    afore_codigo: str
    afore_nombre_corto: str
    metrica_slug: str
    metrica_descripcion: str
    valor: int


class CuentaSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/cuentas/snapshot``."""

    fecha: DateField
    n_filas: int
    filas: list[CuentaSnapshotRow]
    caveats: list[str]


class CuentaSistemaEtiquetaRef(DatosMexicoModel):
    """Referencia de etiqueta de cuenta a nivel sistema."""

    slug: str
    nombre_display: str
    categoria: str


class CuentaSistemaPunto(DatosMexicoModel):
    """Punto mensual del sistema completo, etiquetado por categoría."""

    fecha: DateField
    etiqueta_slug: str
    etiqueta_categoria: str
    metrica_slug: str
    valor: int


class CuentaSistemaResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/cuentas/sistema``."""

    n_puntos: int
    etiquetas: list[CuentaSistemaEtiquetaRef]
    metricas: list[CuentaMetricaRef]
    serie: list[CuentaSistemaPunto]
    caveats: list[str]


# ============================================================================
# GRUPO 11 — Medidas regulatorias
# ============================================================================


class MedidaAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de medidas."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class MedidaSieforeRef(DatosMexicoModel):
    """Referencia de SIEFORE para series de medidas."""

    slug: str
    nombre: str
    categoria: str


class MedidaMetricaRef(DatosMexicoModel):
    """Referencia de métrica regulatoria (sensibilidad, VaR, duración, etc.)."""

    slug: str
    descripcion: str
    unidad: str


class MedidaMappingMeta(DatosMexicoModel):
    """Provenance del mapping AFORExSIEFORE para medidas."""

    is_subvariant_decomposed: bool
    mapping_validated: bool | None = None
    validated_via: str | None = None


class MedidaPunto(DatosMexicoModel):
    """Punto mensual de una medida regulatoria."""

    fecha: DateField
    valor: Money


class MedidaSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/medidas/serie``."""

    afore: MedidaAforeRef
    siefore: MedidaSieforeRef
    metrica: MedidaMetricaRef
    n_puntos: int
    rango: SerieRango
    serie: list[MedidaPunto]
    mapping_meta: MedidaMappingMeta
    caveats: list[str]


class MedidaSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de medidas (AFORE x SIEFORE para una métrica)."""

    afore_codigo: str
    afore_nombre_corto: str
    siefore_slug: str
    siefore_nombre: str
    siefore_categoria: str
    valor: Money


class MedidaSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/medidas/snapshot``."""

    fecha: DateField
    metrica: MedidaMetricaRef
    n_filas: int
    valor_min: Money
    valor_max: Money
    filas: list[MedidaSnapshotRow]
    caveats: list[str]


# ============================================================================
# GRUPO 12 — Activo neto
# ============================================================================


class ActivoNetoAforeRef(DatosMexicoModel):
    """Referencia de AFORE para series de activo neto."""

    codigo: str
    nombre_corto: str
    tipo_pension: str


class ActivoNetoSieforeRef(DatosMexicoModel):
    """Referencia de SIEFORE para series de activo neto."""

    slug: str
    nombre: str
    categoria: str


class ActivoNetoMappingMeta(DatosMexicoModel):
    """Provenance del mapping AFORExSIEFORE para activo neto."""

    is_subvariant_decomposed: bool
    mapping_validated: bool | None = None
    validated_via: str | None = None


class ActivoNetoPunto(DatosMexicoModel):
    """Punto mensual de activo neto por (AFORE x SIEFORE)."""

    fecha: DateField
    monto_mxn_mm: Money | None = None


class ActivoNetoSerieResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/activo-neto/serie``."""

    afore: ActivoNetoAforeRef
    siefore: ActivoNetoSieforeRef
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[ActivoNetoPunto]
    mapping_meta: ActivoNetoMappingMeta
    caveats: list[str]


class ActivoNetoSnapshotRow(DatosMexicoModel):
    """Fila de snapshot de activo neto por (AFORE x SIEFORE)."""

    afore_codigo: str
    afore_nombre_corto: str
    siefore_slug: str
    siefore_nombre: str
    siefore_categoria: str
    monto_mxn_mm: Money | None = None


class ActivoNetoSnapshotResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/activo-neto/snapshot``."""

    fecha: DateField
    unit: str
    n_filas: int
    monto_total_mm: Money
    n_filas_null: int
    filas: list[ActivoNetoSnapshotRow]
    caveats: list[str]


class ActivoNetoAggPunto(DatosMexicoModel):
    """Punto mensual de activo neto agregado por categoría."""

    fecha: DateField
    monto_mxn_mm: Money | None = None


class ActivoNetoAggregadoResponse(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/consar/activo-neto/agregado``.

    Activo neto sumado a través de las SIEFORES de una categoría
    (ej. ``"basicas"`` agrega todas las básicas) para una AFORE.
    """

    afore: ActivoNetoAforeRef
    categoria: str
    unit: str
    n_puntos: int
    rango: SerieRango
    serie: list[ActivoNetoAggPunto]
    caveats: list[str]
