"""Fixtures pytest compartidos."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest

from datos_mexico import DatosMexico
from datos_mexico._http import HttpClient


@pytest.fixture
def http_client() -> Generator[HttpClient, None, None]:
    """``HttpClient`` apuntando a una base_url ficticia para tests con respx."""
    client = HttpClient(
        base_url="https://api.test.local",
        timeout=5.0,
        cache_ttl=60,
        max_retries=2,
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def http_client_no_cache() -> Generator[HttpClient, None, None]:
    """Igual que ``http_client`` pero con cache deshabilitada."""
    client = HttpClient(
        base_url="https://api.test.local",
        timeout=5.0,
        cache_ttl=0,
        max_retries=2,
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def http_client_no_retries() -> Generator[HttpClient, None, None]:
    """``HttpClient`` con retries deshabilitados (max_retries=0)."""
    client = HttpClient(
        base_url="https://api.test.local",
        timeout=5.0,
        cache_ttl=60,
        max_retries=0,
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def datos_mexico_client() -> Generator[DatosMexico, None, None]:
    """``DatosMexico`` apuntando a base_url ficticia para tests con respx."""
    client = DatosMexico(
        base_url="https://api.test.local",
        timeout=5.0,
        cache_ttl=60,
        max_retries=2,
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def real_client() -> Generator[DatosMexico, None, None]:
    """``DatosMexico`` real apuntando a la API en vivo.

    Sólo se ejecuta si la variable de entorno
    ``DATOS_MEXICO_INTEGRATION_TESTS`` está en ``"1"``. En cualquier otro
    caso, el test que la consume queda skipped.
    """
    if os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1":
        pytest.skip(
            "Integration tests deshabilitados. "
            "Activar con DATOS_MEXICO_INTEGRATION_TESTS=1."
        )
    client = DatosMexico()
    try:
        yield client
    finally:
        client.close()
