"""Tests de la jerarquía de excepciones."""

from __future__ import annotations

import pytest

from datos_mexico.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConfigurationError,
    DatosMexicoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


def test_base_error_is_exception() -> None:
    assert issubclass(DatosMexicoError, Exception)


def test_configuration_error_inherits_base() -> None:
    assert issubclass(ConfigurationError, DatosMexicoError)


def test_network_error_inherits_base() -> None:
    assert issubclass(NetworkError, DatosMexicoError)


def test_timeout_error_inherits_network() -> None:
    assert issubclass(TimeoutError, NetworkError)
    assert issubclass(TimeoutError, DatosMexicoError)


def test_api_error_message_includes_method_and_status() -> None:
    err = ApiError(endpoint="/foo", status_code=500, method="GET")
    msg = str(err)
    assert "GET" in msg
    assert "/foo" in msg
    assert "500" in msg


def test_api_error_with_message_appended() -> None:
    err = ApiError(
        endpoint="/foo",
        status_code=500,
        method="GET",
        message="boom",
    )
    assert "boom" in str(err)


def test_api_error_stores_response_body() -> None:
    err = ApiError(
        endpoint="/foo",
        status_code=500,
        method="POST",
        response_body="<html>...</html>",
    )
    assert err.response_body == "<html>...</html>"
    assert err.method == "POST"


@pytest.mark.parametrize(
    ("cls", "status"),
    [
        (BadRequestError, 400),
        (AuthenticationError, 401),
        (AuthorizationError, 403),
        (NotFoundError, 404),
        (ServerError, 500),
    ],
)
def test_api_subclasses_inherit_api_error(cls: type[ApiError], status: int) -> None:
    err = cls(endpoint="/x", status_code=status, method="GET")
    assert isinstance(err, ApiError)
    assert isinstance(err, DatosMexicoError)
    assert err.status_code == status


def test_rate_limit_error_with_retry_after() -> None:
    err = RateLimitError(
        endpoint="/x",
        status_code=429,
        method="GET",
        retry_after=42,
    )
    assert err.retry_after == 42
    assert "retry_after=42s" in str(err)


def test_rate_limit_error_without_retry_after() -> None:
    err = RateLimitError(endpoint="/x")
    assert err.retry_after is None
    assert "retry_after" not in str(err)
    assert isinstance(err, ApiError)


def test_validation_error_pluralizes() -> None:
    err = ValidationError(
        endpoint="/x",
        pydantic_errors=[{"loc": ("a",), "msg": "bad"}],
        raw_payload={"a": 1},
    )
    assert "1 error" in str(err)
    assert "errores" not in str(err)

    err2 = ValidationError(
        endpoint="/x",
        pydantic_errors=[{"loc": ("a",), "msg": "bad"}, {"loc": ("b",), "msg": "bad"}],
        raw_payload={},
    )
    assert "2 errores" in str(err2)


def test_validation_error_keeps_payload() -> None:
    payload = {"foo": "bar"}
    err = ValidationError(
        endpoint="/x",
        pydantic_errors=[],
        raw_payload=payload,
    )
    assert err.raw_payload is payload
    assert err.endpoint == "/x"
    assert isinstance(err, DatosMexicoError)


def test_catching_base_catches_all() -> None:
    """Capturar DatosMexicoError debe atrapar cualquier excepción del módulo."""
    excs: list[DatosMexicoError] = [
        ConfigurationError("bad"),
        NetworkError("dns"),
        TimeoutError("slow"),
        ApiError(endpoint="/x", status_code=500),
        BadRequestError(endpoint="/x", status_code=400),
        ServerError(endpoint="/x", status_code=502),
        RateLimitError(endpoint="/x"),
        ValidationError(endpoint="/x", pydantic_errors=[], raw_payload=None),
    ]
    for exc in excs:
        with pytest.raises(DatosMexicoError):
            raise exc
