"""Tests del namespace CDMX (servidores públicos)."""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico.exceptions import NotFoundError, ValidationError
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

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://api.test.local"


def _load(name: str) -> Any:
    return json.loads((FIXTURES / f"cdmx_{name}.json").read_text())


@pytest.fixture
def cdmx_client() -> Generator[DatosMexico, None, None]:
    client = DatosMexico(
        base_url=BASE, timeout=5.0, cache_ttl=0, max_retries=0
    )
    try:
        yield client
    finally:
        client.close()


# ---------- Mocked unit tests ----------


@respx.mock
def test_dashboard_stats(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/dashboard/stats").mock(
        return_value=httpx.Response(200, json=_load("dashboard_stats"))
    )
    stats = cdmx_client.cdmx.dashboard_stats()
    assert isinstance(stats, DashboardStats)
    assert stats.total_servidores == 246831
    assert stats.total_sectors == 75
    assert stats.avg_salary == 13225.47
    assert len(stats.salary_distribution) == 2
    assert stats.salary_distribution[0].label.startswith("Menos")
    assert stats.bruto_neto_by_range[0].avg_bruto == 3839.61


@respx.mock
def test_servidores_stats_no_filters(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/servidores/stats").mock(
        return_value=httpx.Response(200, json=_load("servidores_stats"))
    )
    stats = cdmx_client.cdmx.servidores_stats()
    assert isinstance(stats, ServidoresStats)
    assert stats.total == 246831
    assert stats.distribucion_sueldo[0].rango == "0-5K"
    request = route.calls[0].request
    assert request.url.params == httpx.QueryParams({})


@respx.mock
def test_servidores_stats_with_filters(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/servidores/stats").mock(
        return_value=httpx.Response(200, json=_load("servidores_stats"))
    )
    cdmx_client.cdmx.servidores_stats(
        sector_id=5, sexo="FEMENINO", edad_min=30, sueldo_max=50000.0
    )
    params = route.calls[0].request.url.params
    assert params["sector_id"] == "5"
    assert params["sexo"] == "FEMENINO"
    assert params["edad_min"] == "30"
    assert params["sueldo_max"] == "50000.0"
    # los None no deben aparecer
    assert "edad_max" not in params
    assert "puesto_search" not in params


@respx.mock
def test_sectores_returns_list(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/sectores/").mock(
        return_value=httpx.Response(200, json=_load("sectores"))
    )
    sectores = cdmx_client.cdmx.sectores()
    assert all(isinstance(s, Sector) for s in sectores)
    assert len(sectores) == 2
    assert sectores[0].nombre.startswith("AGENCIA")


@respx.mock
def test_sector_stats_builds_url(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/sectores/1/stats").mock(
        return_value=httpx.Response(200, json=_load("sector_stats"))
    )
    stats = cdmx_client.cdmx.sector_stats(sector_id=1)
    assert isinstance(stats, SectorStats)
    assert stats.id == 1
    assert stats.top_puestos[0].puesto.startswith("ADMINISTRATIVO")
    assert route.called


@respx.mock
def test_sector_stats_404(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/sectores/99999/stats").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )
    with pytest.raises(NotFoundError):
        cdmx_client.cdmx.sector_stats(sector_id=99999)


@respx.mock
def test_sectores_compare_query_params(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/sectores/compare").mock(
        return_value=httpx.Response(200, json=_load("sectores_compare"))
    )
    cmp = cdmx_client.cdmx.sectores_compare(a=1, b=2)
    assert isinstance(cmp, SectoresComparison)
    assert cmp.sector_a.id == 1
    assert cmp.sector_b.id == 2
    params = route.calls[0].request.url.params
    assert params["a"] == "1"
    assert params["b"] == "2"


@respx.mock
def test_sectores_ranking(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/analytics/sectores/ranking").mock(
        return_value=httpx.Response(200, json=_load("sectores_ranking"))
    )
    ranking = cdmx_client.cdmx.sectores_ranking()
    assert all(isinstance(r, SectorRanking) for r in ranking)
    assert ranking[0].rank == 1


@respx.mock
def test_puestos_ranking_propagates_limit(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/analytics/puestos/ranking").mock(
        return_value=httpx.Response(200, json=_load("puestos_ranking"))
    )
    ranking = cdmx_client.cdmx.puestos_ranking(limit=5)
    assert all(isinstance(r, PuestoRanking) for r in ranking)
    assert ranking[0].gap_vs_next is None  # nullable
    assert ranking[1].gap_vs_next == 0.0
    assert route.calls[0].request.url.params["limit"] == "5"


@respx.mock
def test_brecha_edad(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/analytics/brecha-edad").mock(
        return_value=httpx.Response(200, json=_load("brecha_edad"))
    )
    rows = cdmx_client.cdmx.brecha_edad()
    assert all(isinstance(r, BrechaEdadRow) for r in rows)
    assert rows[0].bucket_edad == "18-25"


@respx.mock
def test_servidores_lista_decimal_conversion(
    cdmx_client: DatosMexico,
) -> None:
    respx.get(f"{BASE}/api/v1/servidores/").mock(
        return_value=httpx.Response(200, json=_load("servidores_lista"))
    )
    page = cdmx_client.cdmx.servidores_lista(page=1, per_page=2)
    assert isinstance(page, PaginatedResponse)
    assert page.total == 246831
    assert len(page.data) == 2
    primero = page.data[0]
    assert isinstance(primero, Servidor)
    assert primero.sueldo_bruto == Decimal("14915.00")
    assert primero.sueldo_neto == Decimal("13377.45")


@respx.mock
def test_servidores_lista_propagates_pagination(
    cdmx_client: DatosMexico,
) -> None:
    route = respx.get(f"{BASE}/api/v1/servidores/").mock(
        return_value=httpx.Response(200, json=_load("servidores_lista"))
    )
    cdmx_client.cdmx.servidores_lista(
        page=3, per_page=25, order_by="sueldo_bruto", order="desc", sector_id=10
    )
    params = route.calls[0].request.url.params
    assert params["page"] == "3"
    assert params["per_page"] == "25"
    assert params["order_by"] == "sueldo_bruto"
    assert params["order"] == "desc"
    assert params["sector_id"] == "10"


@respx.mock
def test_servidor_detail(cdmx_client: DatosMexico) -> None:
    from datetime import date as date_type

    respx.get(f"{BASE}/api/v1/servidores/1").mock(
        return_value=httpx.Response(200, json=_load("servidor_detail"))
    )
    s = cdmx_client.cdmx.servidor_detail(1)
    assert isinstance(s, ServidorDetail)
    assert s.id == 1
    assert isinstance(s.sueldo_bruto, Decimal)
    assert isinstance(s.fecha_ingreso, date_type)
    # Campos derivados que servidores_lista() no expone
    assert s.tipo_contratacion is not None
    assert s.universo is not None


@respx.mock
def test_servidor_detail_404(cdmx_client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/servidores/9999999").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with pytest.raises(NotFoundError):
        cdmx_client.cdmx.servidor_detail(9999999)


@respx.mock
@pytest.mark.parametrize(
    ("path", "method_name"),
    [
        ("/api/v1/catalogos/sectores", "catalogo_sectores"),
        ("/api/v1/catalogos/sexos", "catalogo_sexos"),
        ("/api/v1/catalogos/tipos-contratacion", "catalogo_tipos_contratacion"),
        ("/api/v1/catalogos/tipos-personal", "catalogo_tipos_personal"),
        ("/api/v1/catalogos/tipos-nomina", "catalogo_tipos_nomina"),
        ("/api/v1/catalogos/niveles-salariales", "catalogo_niveles_salariales"),
        ("/api/v1/catalogos/universos", "catalogo_universos"),
    ],
)
def test_catalogos_simples(
    cdmx_client: DatosMexico, path: str, method_name: str
) -> None:
    respx.get(f"{BASE}{path}").mock(
        return_value=httpx.Response(200, json=_load("catalogo"))
    )
    method = getattr(cdmx_client.cdmx, method_name)
    items = method()
    assert all(isinstance(i, CatalogItem) for i in items)
    assert items[0].id == 1
    assert items[0].count == 106040


@respx.mock
def test_catalogo_puestos_propagates_limit(cdmx_client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/catalogos/puestos").mock(
        return_value=httpx.Response(200, json=_load("catalogo"))
    )
    items = cdmx_client.cdmx.catalogo_puestos(limit=42)
    assert len(items) == 3
    assert route.calls[0].request.url.params["limit"] == "42"


@respx.mock
def test_validation_error_on_unexpected_shape(
    cdmx_client: DatosMexico,
) -> None:
    respx.get(f"{BASE}/api/v1/dashboard/stats").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    with pytest.raises(ValidationError) as exc_info:
        cdmx_client.cdmx.dashboard_stats()
    assert exc_info.value.endpoint == "/api/v1/dashboard/stats"
    assert len(exc_info.value.pydantic_errors) > 0


# ---------- Live integration tests (gated) ----------


def _live() -> bool:
    return os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") == "1"


@pytest.fixture
def live() -> Generator[DatosMexico, None, None]:
    if not _live():
        pytest.skip(
            "Integration tests deshabilitados. "
            "Activar con DATOS_MEXICO_INTEGRATION_TESTS=1."
        )
    client = DatosMexico()
    try:
        yield client
    finally:
        client.close()


def test_live_dashboard_stats_sane_total(live: DatosMexico) -> None:
    stats = live.cdmx.dashboard_stats()
    assert stats.total_servidores > 240_000
    assert stats.total_sectors >= 70


def test_live_sectores_non_empty(live: DatosMexico) -> None:
    sectores = live.cdmx.sectores()
    assert len(sectores) >= 70


def test_live_sector_stats_sector_1(live: DatosMexico) -> None:
    stats = live.cdmx.sector_stats(sector_id=1)
    assert stats.id == 1
    assert stats.total_servidores > 0


def test_live_catalogo_sectores_non_empty(live: DatosMexico) -> None:
    items = live.cdmx.catalogo_sectores()
    assert len(items) >= 70
    assert all(isinstance(i, CatalogItem) for i in items)
