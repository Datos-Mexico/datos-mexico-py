"""Tests del namespace nombramientos."""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico.exceptions import NotFoundError
from datos_mexico.models.base import PaginatedResponse
from datos_mexico.models.nombramientos import Nombramiento

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://api.test.local"


def _load(name: str) -> Any:
    return json.loads((FIXTURES / f"{name}.json").read_text())


@pytest.fixture
def client() -> Generator[DatosMexico, None, None]:
    c = DatosMexico(base_url=BASE, timeout=5.0, cache_ttl=0, max_retries=0)
    try:
        yield c
    finally:
        c.close()


@respx.mock
def test_nombramientos_list(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/nombramientos/").mock(
        return_value=httpx.Response(200, json=_load("nombramientos_lista"))
    )
    r = client.nombramientos.list()
    assert isinstance(r, PaginatedResponse)
    assert all(isinstance(n, Nombramiento) for n in r.data)
    first = r.data[0]
    assert isinstance(first.sueldo_bruto, Decimal)
    assert isinstance(first.fecha_ingreso, date)


@respx.mock
def test_nombramientos_list_with_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/nombramientos/").mock(
        return_value=httpx.Response(200, json=_load("nombramientos_lista"))
    )
    client.nombramientos.list(
        page=3, per_page=20, persona_id=42, sector_id=7
    )
    params = route.calls[0].request.url.params
    assert params["page"] == "3"
    assert params["per_page"] == "20"
    assert params["persona_id"] == "42"
    assert params["sector_id"] == "7"


@respx.mock
def test_nombramientos_list_omits_none_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/nombramientos/").mock(
        return_value=httpx.Response(200, json=_load("nombramientos_lista"))
    )
    client.nombramientos.list()
    params = route.calls[0].request.url.params
    assert "persona_id" not in params
    assert "sector_id" not in params


@respx.mock
def test_nombramientos_get(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/nombramientos/1").mock(
        return_value=httpx.Response(200, json=_load("nombramientos_detail"))
    )
    n = client.nombramientos.get(1)
    assert isinstance(n, Nombramiento)
    assert n.id == 1
    assert n.persona_id == 1
    assert isinstance(n.sueldo_bruto, Decimal)
    assert n.sueldo_bruto == Decimal("14915.00")


@respx.mock
def test_nombramientos_get_404(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/nombramientos/9999999").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with pytest.raises(NotFoundError):
        client.nombramientos.get(9999999)


_LIVE = pytest.mark.skipif(
    os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1",
    reason="Integration tests deshabilitados",
)


@_LIVE
def test_live_nombramientos_list() -> None:
    with DatosMexico() as c:
        r = c.nombramientos.list(per_page=3)
        assert r.total > 100_000


@_LIVE
def test_live_nombramientos_filter_by_persona() -> None:
    with DatosMexico() as c:
        r = c.nombramientos.list(persona_id=1, per_page=5)
        assert all(n.persona_id == 1 for n in r.data)
