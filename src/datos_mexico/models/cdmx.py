"""Modelos Pydantic para el dataset Servidores Públicos de la CDMX.

Cada modelo documenta el endpoint de origen. La API mezcla convenciones de
nombres entre endpoints: los endpoints de tipo "dashboard" usan camelCase
(``totalServidores``, ``avgSalary``); los demás usan snake_case
(``total_servidores``, ``sueldo_bruto_avg``). Los modelos exponen siempre
snake_case en Python; los aliases vía ``Field(alias=...)`` aceptan camelCase
desde la API.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BeforeValidator, Field

from datos_mexico._helpers import DateField
from datos_mexico.models.base import DatosMexicoModel


def _to_decimal(value: object) -> object:
    """Convierte strings monetarios (``"14915.00"``) a ``Decimal``.

    Si el valor ya es ``Decimal``, ``int`` o ``float``, se devuelve sin tocar.
    """
    if isinstance(value, str):
        return Decimal(value)
    return value


MoneyStr = Annotated[Decimal, BeforeValidator(_to_decimal)]
"""Decimal proveniente de un string monetario (``"14915.00"``)."""


class DistributionItem(DatosMexicoModel):
    """Bucket genérico ``{"label": str, "count": int}``.

    Reusado por ``salary_distribution``, ``age_distribution``,
    ``contract_types``, ``personal_types`` y ``seniority_distribution`` del
    dashboard.
    """

    label: str
    count: int


class LabeledAvg(DatosMexicoModel):
    """Bucket ``{"label": str, "avg": float}``. Usado en ``salary_by_age``."""

    label: str
    avg: float


class LabeledAvgCount(DatosMexicoModel):
    """Bucket ``{"label", "avg", "count"}``. Usado en ``salary_by_seniority``."""

    label: str
    avg: float
    count: int


class BrutoNetoBucket(DatosMexicoModel):
    """Item de ``brutoNetoByRange`` del dashboard."""

    label: str
    avg_bruto: float = Field(alias="avgBruto")
    avg_neto: float = Field(alias="avgNeto")
    count: int


class SectorAggregate(DatosMexicoModel):
    """Sector dentro del dashboard (``top15Sectors`` y ``allSectors``)."""

    name: str
    count: int
    avg_salary: float = Field(alias="avgSalary")
    avg_male: float = Field(alias="avgMale")
    avg_female: float = Field(alias="avgFemale")


class GenderGapSectorRow(DatosMexicoModel):
    """Item de ``genderGapBySector`` del dashboard."""

    name: str
    avg_male: float = Field(alias="avgMale")
    avg_female: float = Field(alias="avgFemale")
    gap: float


class TopPosition(DatosMexicoModel):
    """Item de ``topPositions`` del dashboard."""

    name: str
    count: int
    avg_salary: float = Field(alias="avgSalary")


class DashboardStats(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/dashboard/stats``.

    KPIs preagregados del padrón completo de la CDMX más seis distribuciones
    listas para graficar.
    """

    total_servidores: int = Field(alias="totalServidores")
    total_sectors: int = Field(alias="totalSectors")
    avg_salary: float = Field(alias="avgSalary")
    median_salary: float = Field(alias="medianSalary")
    min_salary: float = Field(alias="minSalary")
    max_salary: float = Field(alias="maxSalary")
    p25: float
    p50: float
    p75: float
    p90: float
    gender_gap_percent: float = Field(alias="genderGapPercent")
    hombres: int
    mujeres: int
    avg_salary_male: float = Field(alias="avgSalaryMale")
    avg_salary_female: float = Field(alias="avgSalaryFemale")
    salary_distribution: list[DistributionItem] = Field(alias="salaryDistribution")
    age_distribution: list[DistributionItem] = Field(alias="ageDistribution")
    contract_types: list[DistributionItem] = Field(alias="contractTypes")
    personal_types: list[DistributionItem] = Field(alias="personalTypes")
    salary_by_age: list[LabeledAvg] = Field(alias="salaryByAge")
    top15_sectors: list[SectorAggregate] = Field(alias="top15Sectors")
    all_sectors: list[SectorAggregate] = Field(alias="allSectors")
    gender_gap_by_sector: list[GenderGapSectorRow] = Field(alias="genderGapBySector")
    top_positions: list[TopPosition] = Field(alias="topPositions")
    seniority_distribution: list[DistributionItem] = Field(alias="seniorityDistribution")
    salary_by_seniority: list[LabeledAvgCount] = Field(alias="salaryBySeniority")
    avg_seniority: float = Field(alias="avgSeniority")
    avg_net_salary: float = Field(alias="avgNetSalary")
    avg_deduction: float = Field(alias="avgDeduction")
    avg_deduction_percent: float = Field(alias="avgDeductionPercent")
    bruto_neto_by_range: list[BrutoNetoBucket] = Field(alias="brutoNetoByRange")


class DistribucionSueldoBucket(DatosMexicoModel):
    """Bucket de ``servidores/stats``. Usa ``rango`` en vez de ``label``."""

    rango: str
    count: int


class ServidoresStats(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/servidores/stats`` (con filtros opcionales).

    Cuando los filtros aplicados producen 0 registros, los campos numéricos
    agregados (``sueldo_*``, ``edad_avg``, ``brecha_genero_pct``) llegan
    como ``null``.
    """

    total: int
    sueldo_bruto_avg: float | None = None
    sueldo_bruto_median: float | None = None
    sueldo_bruto_p25: float | None = None
    sueldo_bruto_p75: float | None = None
    sueldo_bruto_min: float | None = None
    sueldo_bruto_max: float | None = None
    sueldo_neto_avg: float | None = None
    edad_avg: float | None = None
    count_hombres: int
    count_mujeres: int
    brecha_genero_pct: float | None = None
    distribucion_sueldo: list[DistribucionSueldoBucket]


class Sector(DatosMexicoModel):
    """Item de ``GET /api/v1/sectores/`` (lista de sectores con resumen).

    Para sectores con ``total_servidores == 0`` (típicamente sectores de
    prueba o recién creados sin personal asignado), ``sueldo_bruto_avg``
    llega como ``null``.
    """

    id: int
    nombre: str
    total_servidores: int
    sueldo_bruto_avg: float | None = None
    count_hombres: int
    count_mujeres: int


class TopPuesto(DatosMexicoModel):
    """Top puesto dentro de un sector, devuelto por ``sectores/{id}/stats``."""

    puesto: str
    count: int
    sueldo_avg: float


class SectorStats(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/sectores/{sector_id}/stats``.

    Para sectores con ``total_servidores == 0`` los campos agregados
    numéricos llegan como ``null`` y ``top_puestos`` queda como lista vacía.
    """

    id: int
    nombre: str
    total_servidores: int
    sueldo_bruto_avg: float | None = None
    sueldo_bruto_median: float | None = None
    sueldo_neto_avg: float | None = None
    edad_avg: float | None = None
    count_hombres: int
    count_mujeres: int
    brecha_genero_pct: float | None = None
    top_puestos: list[TopPuesto]


class SectoresComparison(DatosMexicoModel):
    """Respuesta de ``GET /api/v1/sectores/compare?a=..&b=..``."""

    sector_a: SectorStats
    sector_b: SectorStats


class SectorRanking(DatosMexicoModel):
    """Item de ``GET /api/v1/analytics/sectores/ranking``."""

    sector_id: int
    nombre: str
    avg_sueldo: float
    count: int
    rank: int
    percent_rank: float
    avg_vs_global_pct: float


class PuestoRanking(DatosMexicoModel):
    """Item de ``GET /api/v1/analytics/puestos/ranking``.

    El campo ``gap_vs_next`` es ``None`` para el último elemento del ranking
    o cuando la API no puede calcular un delta.
    """

    puesto_id: int
    nombre: str
    avg_sueldo: float
    count: int
    rank: int
    percent_rank: float
    gap_vs_next: float | None = None


class BrechaEdadRow(DatosMexicoModel):
    """Item de ``GET /api/v1/analytics/brecha-edad``."""

    bucket_edad: str
    avg_male: float
    avg_female: float
    count_male: int
    count_female: int
    gap_pct: float
    running_avg_global: float


class Servidor(DatosMexicoModel):
    """Item de ``GET /api/v1/servidores/`` (vista resumida).

    Los campos monetarios (``sueldo_bruto``, ``sueldo_neto``) llegan como
    string desde la API y se convierten a ``Decimal`` para preservar precisión.
    El ``apellido_2`` puede no estar presente para personas con un solo apellido.
    """

    id: int
    nombre: str
    apellido_1: str
    apellido_2: str | None = None
    sexo: str
    edad: int
    sueldo_bruto: MoneyStr
    sueldo_neto: MoneyStr
    sector: str
    puesto: str


class ServidorDetail(DatosMexicoModel):
    """Detalle completo devuelto por ``GET /api/v1/servidores/{servidor_id}``.

    A diferencia de ``Servidor`` (vista de listado), incluye los campos
    derivados de ``nombramientos`` y ``catalogos`` ya resueltos por
    nombre: ``tipo_contratacion``, ``tipo_personal``, ``tipo_nomina``,
    ``universo`` y ``fecha_ingreso``. Cualquier campo puede llegar como
    ``None`` cuando el dato fuente venía sin esa información.
    """

    id: int
    nombre: str
    apellido_1: str
    apellido_2: str | None = None
    sexo: str
    edad: int | None = None
    sueldo_bruto: MoneyStr | None = None
    sueldo_neto: MoneyStr | None = None
    fecha_ingreso: DateField | None = None
    id_nivel_salarial: int | None = None
    sector: str | None = None
    puesto: str | None = None
    tipo_contratacion: str | None = None
    tipo_personal: str | None = None
    tipo_nomina: str | None = None
    universo: str | None = None


class CatalogItem(DatosMexicoModel):
    """Item común de cualquier endpoint ``/api/v1/catalogos/*``."""

    id: int
    nombre: str
    count: int
