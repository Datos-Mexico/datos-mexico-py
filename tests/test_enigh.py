"""Tests del namespace ENIGH 2024 NS."""

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
from datos_mexico.models.enigh import (
    ActividadAgroResponse,
    ActividadJcfResponse,
    ActividadNoagroResponse,
    DecilRow,
    DemographicsResponse,
    EnighMetadata,
    EntidadRow,
    HogaresSummary,
    RubrosResponse,
    ValidacionesResponse,
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


# ---------- Hogares ----------


@respx.mock
def test_hogares_summary(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/hogares/summary").mock(
        return_value=httpx.Response(200, json=_load("enigh_hogares_summary"))
    )
    r = client.enigh.hogares_summary()
    assert isinstance(r, HogaresSummary)
    assert r.n_hogares_expandido > 0
    assert isinstance(r.mean_ing_cor_trim, Decimal)


@respx.mock
def test_hogares_by_decil(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/hogares/by-decil").mock(
        return_value=httpx.Response(200, json=_load("enigh_hogares_by_decil"))
    )
    r = client.enigh.hogares_by_decil()
    assert all(isinstance(d, DecilRow) for d in r)
    assert r[0].decil == 1
    assert r[-1].decil == 10


@respx.mock
def test_hogares_by_entidad_no_filter(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/hogares/by-entidad").mock(
        return_value=httpx.Response(200, json=_load("enigh_hogares_by_entidad"))
    )
    r = client.enigh.hogares_by_entidad()
    assert all(isinstance(e, EntidadRow) for e in r)
    assert "entidad" not in route.calls[0].request.url.params


@respx.mock
def test_hogares_by_entidad_with_filter(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/hogares/by-entidad").mock(
        return_value=httpx.Response(200, json=_load("enigh_hogares_by_entidad"))
    )
    client.enigh.hogares_by_entidad(entidad="09")
    assert route.calls[0].request.url.params["entidad"] == "09"


# ---------- Gastos ----------


@respx.mock
def test_gastos_by_rubro_nacional(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/gastos/by-rubro").mock(
        return_value=httpx.Response(200, json=_load("enigh_gastos_by_rubro"))
    )
    r = client.enigh.gastos_by_rubro()
    assert isinstance(r, RubrosResponse)
    assert "decil" not in route.calls[0].request.url.params
    # bound_delta_pct y oficial_mensual presentes y como Decimal cuando hay
    rubros_con_bound = [
        rb for rb in r.rubros if rb.bound_delta_pct is not None
    ]
    assert all(
        isinstance(rb.bound_delta_pct, Decimal) for rb in rubros_con_bound
    )


@respx.mock
def test_gastos_by_rubro_filtered(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/gastos/by-rubro").mock(
        return_value=httpx.Response(200, json=_load("enigh_gastos_by_rubro"))
    )
    client.enigh.gastos_by_rubro(decil=5)
    assert route.calls[0].request.url.params["decil"] == "5"


@pytest.mark.parametrize("bad", [0, 11, -1])
def test_gastos_by_rubro_rejects_bad_decil(
    client: DatosMexico, bad: int
) -> None:
    with pytest.raises(ValueError, match=r"\[1, 10\]"):
        client.enigh.gastos_by_rubro(decil=bad)


# ---------- Demografía ----------


@respx.mock
def test_poblacion_demographics_nacional(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/poblacion/demographics").mock(
        return_value=httpx.Response(
            200, json=_load("enigh_poblacion_demographics")
        )
    )
    r = client.enigh.poblacion_demographics()
    assert isinstance(r, DemographicsResponse)
    assert r.scope == "nacional"
    assert "entidad" not in route.calls[0].request.url.params


@respx.mock
def test_poblacion_demographics_by_entidad(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enigh/poblacion/demographics").mock(
        return_value=httpx.Response(
            200, json=_load("enigh_poblacion_demographics")
        )
    )
    client.enigh.poblacion_demographics(entidad="09")
    assert route.calls[0].request.url.params["entidad"] == "09"


# ---------- Actividades ----------


@respx.mock
def test_actividad_agro(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/actividad/agro").mock(
        return_value=httpx.Response(200, json=_load("enigh_actividad_agro"))
    )
    r = client.enigh.actividad_agro()
    assert isinstance(r, ActividadAgroResponse)


@respx.mock
def test_actividad_noagro(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/actividad/noagro").mock(
        return_value=httpx.Response(200, json=_load("enigh_actividad_noagro"))
    )
    r = client.enigh.actividad_noagro()
    assert isinstance(r, ActividadNoagroResponse)


@respx.mock
def test_actividad_jcf(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/actividad/jcf").mock(
        return_value=httpx.Response(200, json=_load("enigh_actividad_jcf"))
    )
    r = client.enigh.actividad_jcf()
    assert isinstance(r, ActividadJcfResponse)


# ---------- Metadata + validaciones ----------


@respx.mock
def test_metadata(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/metadata").mock(
        return_value=httpx.Response(200, json=_load("enigh_metadata"))
    )
    r = client.enigh.metadata()
    assert isinstance(r, EnighMetadata)
    assert r.edition.startswith("ENIGH")


@respx.mock
def test_validaciones(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/validaciones").mock(
        return_value=httpx.Response(200, json=_load("enigh_validaciones"))
    )
    r = client.enigh.validaciones()
    assert isinstance(r, ValidacionesResponse)
    assert r.count == r.passing + r.failing
    assert isinstance(r.bounds[0].calculado, Decimal)
    assert isinstance(r.bounds[0].oficial, Decimal)


# ---------- Errores ----------


@respx.mock
def test_validation_error(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/hogares/summary").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    with pytest.raises(ValidationError):
        client.enigh.hogares_summary()


@respx.mock
def test_404_raises_not_found(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enigh/hogares/by-entidad").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )
    with pytest.raises(NotFoundError):
        client.enigh.hogares_by_entidad(entidad="999")


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
    c = DatosMexico()
    try:
        yield c
    finally:
        c.close()


def test_live_hogares_summary_sanity(live: DatosMexico) -> None:
    r = live.enigh.hogares_summary()
    assert r.n_hogares_expandido > 38_000_000


def test_live_hogares_by_decil_ten(live: DatosMexico) -> None:
    r = live.enigh.hogares_by_decil()
    assert len(r) == 10
    assert {d.decil for d in r} == set(range(1, 11))


def test_live_gastos_rubros_suman_cien(live: DatosMexico) -> None:
    r = live.enigh.gastos_by_rubro()
    suma = sum((rb.pct_del_monetario for rb in r.rubros), Decimal("0"))
    assert abs(suma - Decimal("100")) < Decimal("1.0")


def test_live_validaciones_passing(live: DatosMexico) -> None:
    r = live.enigh.validaciones()
    assert r.passing > 0
    assert r.count == r.passing + r.failing
