"""Tests del namespace export (descarga CSV del padrón CDMX)."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://api.test.local"


def _load_csv() -> str:
    return (FIXTURES / "export_csv.csv").read_text()


@pytest.fixture
def client() -> Generator[DatosMexico, None, None]:
    c = DatosMexico(base_url=BASE, timeout=5.0, cache_ttl=0, max_retries=0)
    try:
        yield c
    finally:
        c.close()


@respx.mock
def test_export_csv_default(client: DatosMexico) -> None:
    csv_content = _load_csv()
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(
            200, text=csv_content, headers={"content-type": "text/csv"}
        )
    )
    out = client.export.csv()
    assert isinstance(out, str)
    assert out.startswith("id,nombre,apellido_1")
    # Sanity: contains expected columns
    assert "sueldo_bruto" in out
    assert "fecha_ingreso" in out


@respx.mock
def test_export_csv_with_filters(client: DatosMexico) -> None:
    csv_content = _load_csv()
    route = respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(200, text=csv_content)
    )
    client.export.csv(
        sector_id=7,
        sexo="FEMENINO",
        edad_min=30,
        edad_max=60,
        sueldo_min=10000.0,
        sueldo_max=50000.0,
        puesto_search="ANALISTA",
        tipo_contratacion_id=1,
        tipo_personal_id=1,
        universo_id=19,
        page=1,
        per_page=100,
        order_by="sueldo_bruto",
        order="desc",
    )
    params = route.calls[0].request.url.params
    assert params["sector_id"] == "7"
    assert params["sexo"] == "FEMENINO"
    assert params["edad_min"] == "30"
    assert params["puesto_search"] == "ANALISTA"
    assert params["order_by"] == "sueldo_bruto"
    assert params["order"] == "desc"


@respx.mock
def test_export_csv_omits_none_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(200, text=_load_csv())
    )
    client.export.csv()
    params = route.calls[0].request.url.params
    assert "sector_id" not in params
    assert "sexo" not in params
    assert "page" not in params


@respx.mock
def test_export_csv_404(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(404, text="not found")
    )
    with pytest.raises(NotFoundError):
        client.export.csv()


@respx.mock
def test_export_csv_400(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(400, text="bad request")
    )
    with pytest.raises(BadRequestError):
        client.export.csv()


@respx.mock
def test_export_csv_500(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(500, text="oops")
    )
    with pytest.raises(ServerError):
        client.export.csv()


@respx.mock
def test_export_csv_network_error(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    with pytest.raises(NetworkError):
        client.export.csv()


@respx.mock
def test_export_csv_timeout(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        side_effect=httpx.ReadTimeout("timeout")
    )
    with pytest.raises(TimeoutError):
        client.export.csv()


@respx.mock
@pytest.mark.parametrize(
    ("status_code", "expected_exc"),
    [
        (401, AuthenticationError),
        (403, AuthorizationError),
        (429, RateLimitError),
        (418, ApiError),
    ],
)
def test_export_csv_status_classification(
    client: DatosMexico, status_code: int, expected_exc: type[Exception]
) -> None:
    respx.get(f"{BASE}/api/v1/export/csv").mock(
        return_value=httpx.Response(status_code, text="err")
    )
    with pytest.raises(expected_exc):
        client.export.csv()


_LIVE = pytest.mark.skipif(
    os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1",
    reason="Integration tests deshabilitados",
)


@_LIVE
def test_live_export_csv_with_filter() -> None:
    # Filtro estrecho para que el response sea pequeño
    with DatosMexico() as c:
        out = c.export.csv(sector_id=1, edad_min=99, edad_max=120)
        assert out.startswith("id,nombre")
