"""Tests del cliente HTTP base."""

from __future__ import annotations

import httpx
import pytest
import respx

from datos_mexico._constants import USER_AGENT
from datos_mexico._http import HttpClient
from datos_mexico.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)


def test_constructor_defaults() -> None:
    client = HttpClient()
    try:
        assert client.base_url == "https://api.datos-itam.org"
        assert client.cache.enabled
    finally:
        client.close()


def test_constructor_strips_trailing_slash() -> None:
    client = HttpClient(base_url="https://example.com/")
    try:
        assert client.base_url == "https://example.com"
    finally:
        client.close()


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"timeout": 0}, "timeout"),
        ({"timeout": -1.0}, "timeout"),
        ({"max_retries": -1}, "max_retries"),
        ({"cache_ttl": -1}, "cache_ttl"),
    ],
)
def test_constructor_validates_params(
    kwargs: dict[str, float | int], match: str
) -> None:
    with pytest.raises(ConfigurationError, match=match):
        HttpClient(**kwargs)  # type: ignore[arg-type]


@respx.mock
def test_get_returns_payload(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    payload = http_client.get("/health")
    assert payload == {"status": "ok"}
    assert route.called


@respx.mock
def test_get_sends_user_agent_header(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    http_client.get("/health")
    assert route.calls[0].request.headers["User-Agent"] == USER_AGENT
    assert "json" in route.calls[0].request.headers["Accept"]


@respx.mock
def test_get_caches_responses_by_default(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"value": 1})
    )
    first = http_client.get("/foo")
    second = http_client.get("/foo")
    assert first == second
    assert route.call_count == 1


@respx.mock
def test_get_use_cache_false_skips_cache(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"value": 1})
    )
    http_client.get("/foo", use_cache=False)
    http_client.get("/foo", use_cache=False)
    assert route.call_count == 2


@respx.mock
def test_get_with_params_includes_them_in_cache_key(
    http_client: HttpClient,
) -> None:
    respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"v": 1})
    )
    http_client.get("/foo", params={"a": 1})
    http_client.get("/foo", params={"a": 2})
    routes = list(respx.routes)
    total_calls = sum(r.call_count for r in routes)
    assert total_calls == 2


@respx.mock
def test_get_400_raises_bad_request(http_client: HttpClient) -> None:
    respx.get("https://api.test.local/x").mock(return_value=httpx.Response(400))
    with pytest.raises(BadRequestError) as exc_info:
        http_client.get("/x", use_cache=False)
    assert exc_info.value.status_code == 400


@respx.mock
def test_get_401_raises_authentication(http_client_no_retries: HttpClient) -> None:
    respx.get("https://api.test.local/x").mock(return_value=httpx.Response(401))
    with pytest.raises(AuthenticationError):
        http_client_no_retries.get("/x", use_cache=False)


@respx.mock
def test_get_403_raises_authorization(http_client_no_retries: HttpClient) -> None:
    respx.get("https://api.test.local/x").mock(return_value=httpx.Response(403))
    with pytest.raises(AuthorizationError):
        http_client_no_retries.get("/x", use_cache=False)


@respx.mock
def test_get_404_raises_not_found(http_client_no_retries: HttpClient) -> None:
    respx.get("https://api.test.local/x").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFoundError):
        http_client_no_retries.get("/x", use_cache=False)


@respx.mock
def test_get_429_raises_rate_limit_with_retry_after(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "30"})
    )
    with pytest.raises(RateLimitError) as exc_info:
        http_client_no_retries.get("/x", use_cache=False)
    assert exc_info.value.retry_after == 30


@respx.mock
def test_get_429_without_retry_after_header(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/x").mock(return_value=httpx.Response(429))
    with pytest.raises(RateLimitError) as exc_info:
        http_client_no_retries.get("/x", use_cache=False)
    assert exc_info.value.retry_after is None


@respx.mock
def test_get_500_raises_server_error_after_retries(
    http_client: HttpClient,
) -> None:
    """Tras agotar reintentos, un 500 persistente debe lanzar ServerError."""
    route = respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(ServerError):
        http_client.get("/x", use_cache=False)
    # max_retries=2 → 3 intentos totales
    assert route.call_count == 3


@respx.mock
def test_get_recovers_after_transient_503(http_client: HttpClient) -> None:
    """Si un 503 es seguido de 200, la respuesta exitosa debe devolverse."""
    route = respx.get("https://api.test.local/x").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    payload = http_client.get("/x", use_cache=False)
    assert payload == {"ok": True}
    assert route.call_count == 2


@respx.mock
def test_timeout_raises_module_timeout_error(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/x").mock(
        side_effect=httpx.TimeoutException("slow")
    )
    with pytest.raises(TimeoutError):
        http_client_no_retries.get("/x", use_cache=False)


@respx.mock
def test_network_error_raises_module_network_error(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/x").mock(
        side_effect=httpx.ConnectError("dns")
    )
    with pytest.raises(NetworkError) as exc_info:
        http_client_no_retries.get("/x", use_cache=False)
    assert not isinstance(exc_info.value, TimeoutError)


@respx.mock
def test_invalid_json_raises_api_error(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(200, content=b"not-json")
    )
    with pytest.raises(ApiError) as exc_info:
        http_client_no_retries.get("/x", use_cache=False)
    assert "JSON" in str(exc_info.value)


@respx.mock
def test_post_does_not_cache(http_client: HttpClient) -> None:
    route = respx.post("https://api.test.local/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    http_client.post("/x", json={"a": 1})
    http_client.post("/x", json={"a": 1})
    assert route.call_count == 2


@respx.mock
def test_post_404_raises_not_found(http_client: HttpClient) -> None:
    respx.post("https://api.test.local/x").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFoundError):
        http_client.post("/x", json={})


@respx.mock
def test_post_timeout_raises_module_timeout(http_client: HttpClient) -> None:
    respx.post("https://api.test.local/x").mock(
        side_effect=httpx.TimeoutException("slow")
    )
    with pytest.raises(TimeoutError):
        http_client.post("/x", json={})


@respx.mock
def test_post_network_error(http_client: HttpClient) -> None:
    respx.post("https://api.test.local/x").mock(
        side_effect=httpx.ConnectError("dns")
    )
    with pytest.raises(NetworkError):
        http_client.post("/x", json={})


def test_clear_cache_empties_cache(http_client: HttpClient) -> None:
    http_client.cache.set("k", "v")
    assert len(http_client.cache) == 1
    http_client.clear_cache()
    assert len(http_client.cache) == 0


@respx.mock
def test_context_manager_closes_client() -> None:
    respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    with HttpClient(base_url="https://api.test.local") as client:
        assert client.get("/x") == {"ok": True}


# ---------- get_text() ----------


@respx.mock
def test_get_text_returns_raw_body(http_client: HttpClient) -> None:
    csv = "a,b,c\n1,2,3\n4,5,6\n"
    respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(200, text=csv)
    )
    out = http_client.get_text("/export")
    assert isinstance(out, str)
    assert out == csv


@respx.mock
def test_get_text_sends_user_agent(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(200, text="ok")
    )
    http_client.get_text("/export")
    assert route.calls[0].request.headers["User-Agent"] == USER_AGENT


@respx.mock
def test_get_text_4xx_raises_api_error(
    http_client_no_retries: HttpClient,
) -> None:
    respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(404, text="missing")
    )
    with pytest.raises(NotFoundError):
        http_client_no_retries.get_text("/export", use_cache=False)


@respx.mock
def test_get_text_5xx_retries_then_raises(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(ServerError):
        http_client.get_text("/export", use_cache=False)
    assert route.call_count == 3  # max_retries=2 → 3 intentos


@respx.mock
def test_get_text_recovers_after_transient_503(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/export").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, text="csv,row\n")]
    )
    out = http_client.get_text("/export", use_cache=False)
    assert out == "csv,row\n"
    assert route.call_count == 2


@respx.mock
def test_get_text_caches_responses(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(200, text="csv,1\n")
    )
    first = http_client.get_text("/export")
    second = http_client.get_text("/export")
    assert first == second
    assert route.call_count == 1


@respx.mock
def test_get_text_use_cache_false_skips_cache(http_client: HttpClient) -> None:
    route = respx.get("https://api.test.local/export").mock(
        return_value=httpx.Response(200, text="csv,1\n")
    )
    http_client.get_text("/export", use_cache=False)
    http_client.get_text("/export", use_cache=False)
    assert route.call_count == 2


@respx.mock
def test_get_text_cache_key_separate_from_get(http_client: HttpClient) -> None:
    """get_text() y get() en el mismo path NO deben colisionar en cache."""
    respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    http_client.get("/x")
    # En el mismo path, get_text debería pegarle al server, no al cache
    # del get(): aceptamos que respx falle si get_text reusa el cache de get,
    # porque devolvería un dict en vez de un str.
    respx.get("https://api.test.local/x").mock(
        return_value=httpx.Response(200, text="raw text")
    )
    out = http_client.get_text("/x")
    assert out == "raw text"


@respx.mock
def test_get_text_timeout(http_client_no_retries: HttpClient) -> None:
    respx.get("https://api.test.local/export").mock(
        side_effect=httpx.TimeoutException("slow")
    )
    with pytest.raises(TimeoutError):
        http_client_no_retries.get_text("/export", use_cache=False)


@respx.mock
def test_get_text_network_error(http_client_no_retries: HttpClient) -> None:
    respx.get("https://api.test.local/export").mock(
        side_effect=httpx.ConnectError("dns")
    )
    with pytest.raises(NetworkError):
        http_client_no_retries.get_text("/export", use_cache=False)
