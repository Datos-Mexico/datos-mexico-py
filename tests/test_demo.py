"""Tests del namespace demo (curso ITAM Bases de Datos)."""

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
from datos_mexico.exceptions import NotFoundError
from datos_mexico.models.demo import (
    EstudianteRow,
    EstudiantesResponse,
    ResumenResponse,
)

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
def test_demo_estudiantes(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/demo/estudiantes").mock(
        return_value=httpx.Response(200, json=_load("demo_estudiantes"))
    )
    r = client.demo.estudiantes()
    assert isinstance(r, EstudiantesResponse)
    assert r.count > 0
    assert all(isinstance(e, EstudianteRow) for e in r.estudiantes)
    assert all(isinstance(e.sueldo_diario_mxn, Decimal) for e in r.estudiantes)


@respx.mock
def test_demo_estudiante_detail(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/demo/estudiantes/12").mock(
        return_value=httpx.Response(200, json=_load("demo_estudiante_detail"))
    )
    e = client.demo.estudiante(12)
    assert isinstance(e, EstudianteRow)
    assert e.id == 12
    assert isinstance(e.sueldo_diario_mxn, Decimal)


@respx.mock
def test_demo_estudiante_404(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/demo/estudiantes/9999").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with pytest.raises(NotFoundError):
        client.demo.estudiante(9999)


@respx.mock
def test_demo_resumen(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/demo/resumen").mock(
        return_value=httpx.Response(200, json=_load("demo_resumen"))
    )
    r = client.demo.resumen()
    assert isinstance(r, ResumenResponse)
    assert r.total_empleados > 0
    assert isinstance(r.nomina_diaria_total_mxn, Decimal)
    assert (
        r.monto_distribuido_mxn + r.monto_disponible_mxn
        == r.monto_total_posible_mxn
    )


_LIVE = pytest.mark.skipif(
    os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1",
    reason="Integration tests deshabilitados",
)


@_LIVE
def test_live_demo_estudiantes() -> None:
    with DatosMexico() as c:
        r = c.demo.estudiantes()
        assert r.count > 0
        assert r.seccion


@_LIVE
def test_live_demo_resumen() -> None:
    with DatosMexico() as c:
        r = c.demo.resumen()
        assert r.bono_unitario_mxn == 50000
