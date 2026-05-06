"""Tests del cliente principal DatosMexico."""

from __future__ import annotations

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico._constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
)
from datos_mexico.models.base import HealthResponse


def test_default_construction() -> None:
    client = DatosMexico()
    try:
        assert client._http.base_url == DEFAULT_BASE_URL
        assert client._http.cache.ttl_seconds == DEFAULT_CACHE_TTL_SECONDS
    finally:
        client.close()


def test_custom_timeout_and_cache() -> None:
    client = DatosMexico(timeout=DEFAULT_TIMEOUT_SECONDS * 2, cache_ttl=600)
    try:
        assert client._http.cache.ttl_seconds == 600
    finally:
        client.close()


@respx.mock
def test_health_returns_typed_response(datos_mexico_client: DatosMexico) -> None:
    respx.get("https://api.test.local/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    health = datos_mexico_client.health()
    assert isinstance(health, HealthResponse)
    assert health.status == "ok"


@respx.mock
def test_health_does_not_use_cache(datos_mexico_client: DatosMexico) -> None:
    """Cada llamada a health() debe pegar al servidor (use_cache=False)."""
    route = respx.get("https://api.test.local/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    datos_mexico_client.health()
    datos_mexico_client.health()
    datos_mexico_client.health()
    assert route.call_count == 3


@respx.mock
def test_raw_get_returns_payload(datos_mexico_client: DatosMexico) -> None:
    respx.get("https://api.test.local/api/v1/foo").mock(
        return_value=httpx.Response(200, json={"x": 42})
    )
    data = datos_mexico_client._raw_get("/api/v1/foo")
    assert data == {"x": 42}


@respx.mock
def test_raw_get_with_params(datos_mexico_client: DatosMexico) -> None:
    route = respx.get(
        "https://api.test.local/api/v1/foo",
        params={"page": "2"},
    ).mock(return_value=httpx.Response(200, json={"page": 2}))
    data = datos_mexico_client._raw_get("/api/v1/foo", params={"page": 2})
    assert data == {"page": 2}
    assert route.called


@respx.mock
def test_clear_cache_propagates_to_http(datos_mexico_client: DatosMexico) -> None:
    respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"v": 1})
    )
    datos_mexico_client._raw_get("/foo")
    assert len(datos_mexico_client._http.cache) == 1
    datos_mexico_client.clear_cache()
    assert len(datos_mexico_client._http.cache) == 0


@respx.mock
def test_context_manager_closes() -> None:
    respx.get("https://api.test.local/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    with DatosMexico(base_url="https://api.test.local") as client:
        assert client.health().status == "ok"


@pytest.mark.usefixtures("real_client")
def test_health_against_live_api(real_client: DatosMexico) -> None:
    """Integration test: requiere DATOS_MEXICO_INTEGRATION_TESTS=1."""
    health = real_client.health()
    assert health.status
