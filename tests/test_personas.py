"""Tests del namespace personas."""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico.exceptions import NotFoundError
from datos_mexico.models.base import PaginatedResponse
from datos_mexico.models.personas import Persona

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
def test_personas_list_default(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/personas/").mock(
        return_value=httpx.Response(200, json=_load("personas_lista"))
    )
    r = client.personas.list()
    assert isinstance(r, PaginatedResponse)
    assert r.total > 0
    assert all(isinstance(p, Persona) for p in r.data)
    params = route.calls[0].request.url.params
    assert params["page"] == "1"
    assert params["per_page"] == "50"


@respx.mock
def test_personas_list_with_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/personas/").mock(
        return_value=httpx.Response(200, json=_load("personas_lista"))
    )
    client.personas.list(page=2, per_page=10, nombre="MARIA", sexo_id=1)
    params = route.calls[0].request.url.params
    assert params["page"] == "2"
    assert params["per_page"] == "10"
    assert params["nombre"] == "MARIA"
    assert params["sexo_id"] == "1"


@respx.mock
def test_personas_list_omits_none_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/personas/").mock(
        return_value=httpx.Response(200, json=_load("personas_lista"))
    )
    client.personas.list()
    params = route.calls[0].request.url.params
    assert "nombre" not in params
    assert "sexo_id" not in params


@respx.mock
def test_personas_get(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/personas/1").mock(
        return_value=httpx.Response(200, json=_load("personas_detail"))
    )
    p = client.personas.get(1)
    assert isinstance(p, Persona)
    assert p.id == 1


@respx.mock
def test_personas_get_404(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/personas/9999999").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with pytest.raises(NotFoundError):
        client.personas.get(9999999)


_LIVE = pytest.mark.skipif(
    os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1",
    reason="Integration tests deshabilitados",
)


@_LIVE
def test_live_personas_list() -> None:
    with DatosMexico() as c:
        r = c.personas.list(per_page=3)
        assert r.total > 100_000
        assert len(r.data) == 3


@_LIVE
def test_live_personas_get() -> None:
    with DatosMexico() as c:
        first = c.personas.list(per_page=1).data[0]
        detail = c.personas.get(first.id)
        assert detail.id == first.id
