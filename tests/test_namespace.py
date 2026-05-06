"""Tests del helper BaseNamespace."""

from __future__ import annotations

from collections.abc import Generator

import httpx
import pytest
import respx

from datos_mexico._http import HttpClient
from datos_mexico._namespace import BaseNamespace
from datos_mexico.exceptions import ValidationError
from datos_mexico.models.base import DatosMexicoModel


class _Item(DatosMexicoModel):
    name: str
    count: int


@pytest.fixture
def namespace() -> Generator[BaseNamespace, None, None]:
    http = HttpClient(
        base_url="https://api.test.local",
        timeout=5.0,
        cache_ttl=0,
        max_retries=0,
    )
    try:
        yield BaseNamespace(http)
    finally:
        http.close()


@respx.mock
def test_get_raw(namespace: BaseNamespace) -> None:
    respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"x": 1})
    )
    assert namespace._get("/foo") == {"x": 1}


@respx.mock
def test_get_validated_returns_model(namespace: BaseNamespace) -> None:
    respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"name": "a", "count": 5})
    )
    result = namespace._get_validated("/foo", _Item)
    assert isinstance(result, _Item)
    assert result.name == "a"
    assert result.count == 5


@respx.mock
def test_get_validated_wraps_pydantic_error(namespace: BaseNamespace) -> None:
    respx.get("https://api.test.local/foo").mock(
        return_value=httpx.Response(200, json={"name": "a"})  # missing count
    )
    with pytest.raises(ValidationError) as exc_info:
        namespace._get_validated("/foo", _Item)
    assert exc_info.value.endpoint == "/foo"
    assert exc_info.value.raw_payload == {"name": "a"}
    assert len(exc_info.value.pydantic_errors) >= 1


@respx.mock
def test_get_validated_list_returns_models(namespace: BaseNamespace) -> None:
    respx.get("https://api.test.local/items").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"name": "a", "count": 1},
                {"name": "b", "count": 2},
            ],
        )
    )
    items = namespace._get_validated_list("/items", _Item)
    assert len(items) == 2
    assert all(isinstance(i, _Item) for i in items)
    assert items[0].name == "a"
    assert items[1].count == 2


@respx.mock
def test_get_validated_list_rejects_non_list(namespace: BaseNamespace) -> None:
    respx.get("https://api.test.local/items").mock(
        return_value=httpx.Response(200, json={"not": "a list"})
    )
    with pytest.raises(ValidationError) as exc_info:
        namespace._get_validated_list("/items", _Item)
    assert "Expected list" in exc_info.value.pydantic_errors[0]["msg"]


@respx.mock
def test_get_validated_list_wraps_element_errors(
    namespace: BaseNamespace,
) -> None:
    respx.get("https://api.test.local/items").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"name": "a", "count": 1},
                {"name": "b"},  # falta count
            ],
        )
    )
    with pytest.raises(ValidationError):
        namespace._get_validated_list("/items", _Item)
