"""Tests del namespace comparativo (cross-dataset CDMX x CONSAR x ENIGH)."""

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
from datos_mexico.models.comparativo import (
    ComparativoActividad,
    ComparativoAportesVsJubilaciones,
    ComparativoBancarizacion,
    ComparativoDecilServidores,
    ComparativoGastos,
    ComparativoIngreso,
    ComparativoTopVsBottom,
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


# ---------- ingreso/cdmx-vs-nacional ----------


@respx.mock
def test_ingreso_cdmx_vs_nacional(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/ingreso/cdmx-vs-nacional").mock(
        return_value=httpx.Response(
            200, json=_load("comparativo_ingreso_cdmx_vs_nacional")
        )
    )
    r = client.comparativo.ingreso_cdmx_vs_nacional()
    assert isinstance(r, ComparativoIngreso)
    assert r.cdmx_servidor.n_servidores > 0
    assert isinstance(r.ratio_hogar_nacional_sobre_servidor, Decimal)
    assert r.ratio_hogar_nacional_sobre_servidor > 0
    assert isinstance(r.brecha_mean_servidor_vs_hogar_cdmx, Decimal)
    # Editorial fields preserved verbatim
    assert isinstance(r.note, str) and len(r.note) > 0
    assert isinstance(r.caveats, list)
    assert all(isinstance(c, str) for c in r.caveats)


# ---------- gastos/cdmx-vs-nacional ----------


@respx.mock
def test_gastos_cdmx_vs_nacional(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/gastos/cdmx-vs-nacional").mock(
        return_value=httpx.Response(
            200, json=_load("comparativo_gastos_cdmx_vs_nacional")
        )
    )
    r = client.comparativo.gastos_cdmx_vs_nacional()
    assert isinstance(r, ComparativoGastos)
    assert isinstance(r.mean_gasto_mon_mensual_cdmx, Decimal)
    assert len(r.rubros) > 0
    rubro = r.rubros[0]
    assert isinstance(rubro.delta_pct, Decimal)
    assert isinstance(rubro.pct_del_monetario_cdmx, Decimal)


# ---------- decil-servidores-cdmx ----------


@respx.mock
def test_decil_servidores_cdmx(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/decil-servidores-cdmx").mock(
        return_value=httpx.Response(
            200, json=_load("comparativo_decil_servidores_cdmx")
        )
    )
    r = client.comparativo.decil_servidores_cdmx()
    assert isinstance(r, ComparativoDecilServidores)
    # cdmx_servidor is intentionally schema-libre
    assert isinstance(r.cdmx_servidor, dict)
    assert len(r.escenarios) >= 1
    assert all(isinstance(b.lower_mensual, Decimal) for b in r.enigh_deciles_mensuales)
    # Editorial structured field preserved
    assert r.caveats_interpretativos.frontera_p50
    assert r.caveats_interpretativos.narrativa_correcta
    assert len(r.narrative) > 0


# ---------- top-vs-bottom ----------


@respx.mock
def test_top_vs_bottom(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/top-vs-bottom").mock(
        return_value=httpx.Response(200, json=_load("comparativo_top_vs_bottom"))
    )
    r = client.comparativo.top_vs_bottom()
    assert isinstance(r, ComparativoTopVsBottom)
    assert isinstance(r.top_bracket, dict)
    assert isinstance(r.bottom_bracket, dict)
    assert len(r.insights) > 0
    assert all(isinstance(s, str) for s in r.insights)


# ---------- bancarizacion ----------


@respx.mock
def test_bancarizacion(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/bancarizacion").mock(
        return_value=httpx.Response(200, json=_load("comparativo_bancarizacion"))
    )
    r = client.comparativo.bancarizacion()
    assert isinstance(r, ComparativoBancarizacion)
    assert isinstance(r.pct_nacional, Decimal)
    assert isinstance(r.pct_cdmx, Decimal)
    assert isinstance(r.delta_pp, Decimal)
    assert isinstance(r.ratio_cdmx_sobre_nacional, Decimal)
    assert r.definicion_operativa  # editorial


# ---------- actividad-cdmx-vs-nacional ----------


@respx.mock
def test_actividad_cdmx_vs_nacional(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/actividad-cdmx-vs-nacional").mock(
        return_value=httpx.Response(
            200, json=_load("comparativo_actividad_cdmx_vs_nacional")
        )
    )
    r = client.comparativo.actividad_cdmx_vs_nacional()
    assert isinstance(r, ComparativoActividad)
    assert r.agro.tipo
    assert r.noagro.tipo
    assert isinstance(r.agro.ratio_cdmx_sobre_nacional, Decimal)
    # Endpoint usa ambos: note Y nota_hipotesis (nombres heterogéneos)
    assert r.note
    assert r.nota_hipotesis


# ---------- aportes-vs-jubilaciones-actuales ----------


@respx.mock
def test_aportes_vs_jubilaciones_actuales(client: DatosMexico) -> None:
    respx.get(
        f"{BASE}/api/v1/comparativo/aportes-vs-jubilaciones-actuales"
    ).mock(
        return_value=httpx.Response(
            200, json=_load("comparativo_aportes_vs_jubilaciones")
        )
    )
    r = client.comparativo.aportes_vs_jubilaciones_actuales()
    assert isinstance(r, ComparativoAportesVsJubilaciones)
    assert r.cdmx_aportes_actuales.n_servidores > 0
    assert isinstance(r.cdmx_aportes_actuales.mean_sueldo_bruto, Decimal)
    assert isinstance(
        r.enigh_jubilaciones_actuales.pct_hogares_con_jubilacion, Decimal
    )
    # interpretacion (nombre editorial diferente a "note")
    assert r.interpretacion
    assert len(r.caveats) > 0


# ---------- error paths ----------


@respx.mock
def test_404_raises_not_found(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/comparativo/bancarizacion").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with pytest.raises(NotFoundError):
        client.comparativo.bancarizacion()


@respx.mock
def test_invalid_payload_raises_validation_error(client: DatosMexico) -> None:
    # delta_pp falta — campo requerido
    respx.get(f"{BASE}/api/v1/comparativo/bancarizacion").mock(
        return_value=httpx.Response(200, json={"definicion_operativa": "x"})
    )
    with pytest.raises(ValidationError):
        client.comparativo.bancarizacion()


# ---------- live integration (gated) ----------

_LIVE = pytest.mark.skipif(
    os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1",
    reason="Integration tests deshabilitados (DATOS_MEXICO_INTEGRATION_TESTS!=1)",
)


@_LIVE
def test_live_ingreso_cdmx_vs_nacional() -> None:
    with DatosMexico() as c:
        r = c.comparativo.ingreso_cdmx_vs_nacional()
        assert r.ratio_hogar_nacional_sobre_servidor > 0


@_LIVE
def test_live_decil_servidores_has_narrative() -> None:
    with DatosMexico() as c:
        r = c.comparativo.decil_servidores_cdmx()
        assert r.narrative
        assert r.caveats_interpretativos.frontera_p50


@_LIVE
def test_live_aportes_nested_structure() -> None:
    with DatosMexico() as c:
        r = c.comparativo.aportes_vs_jubilaciones_actuales()
        assert r.cdmx_aportes_actuales.n_servidores > 100_000
        assert r.enigh_jubilaciones_actuales.n_hogares_con_jubilacion_expandido > 0
