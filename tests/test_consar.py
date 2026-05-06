"""Tests del namespace CONSAR/SAR."""

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
from datos_mexico.exceptions import NotFoundError, ValidationError
from datos_mexico.models.consar import (
    ActivoNetoAggregadoResponse,
    ActivoNetoSerieResponse,
    ActivoNetoSnapshotResponse,
    AforesResponse,
    ComisionSerieResponse,
    ComisionSnapshotResponse,
    ComposicionResponse,
    CuentaSerieResponse,
    CuentaSistemaResponse,
    CuentaSnapshotResponse,
    FlujoSerieResponse,
    FlujoSnapshotResponse,
    ImssVsIsssteeResponse,
    MedidaSerieResponse,
    MedidaSnapshotResponse,
    MetricasCuentaResponse,
    MetricasSensibilidadResponse,
    PeaCotizantesResponse,
    PorAforeResponse,
    PorComponenteResponse,
    PrecioComparativoResponse,
    PrecioSerieResponse,
    PrecioSnapshotResponse,
    RendimientoSerieResponse,
    RendimientoSistemaResponse,
    RendimientoSnapshotResponse,
    SerieResponse,
    TiposRecursoResponse,
    TotalesSarResponse,
    TraspasoSerieResponse,
    TraspasoSnapshotResponse,
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


# ============================================================================
# GRUPO 1 — Catálogos
# ============================================================================


@respx.mock
def test_afores(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/afores").mock(
        return_value=httpx.Response(200, json=_load("consar_afores"))
    )
    r = client.consar.afores()
    assert isinstance(r, AforesResponse)
    assert r.count >= 1
    assert r.afores[0].codigo


@respx.mock
def test_tipos_recurso(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/tipos-recurso").mock(
        return_value=httpx.Response(200, json=_load("consar_tipos_recurso"))
    )
    r = client.consar.tipos_recurso()
    assert isinstance(r, TiposRecursoResponse)
    assert r.tipos_recurso[0].codigo == "rcv"


@respx.mock
def test_metricas_cuenta(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/metricas-cuenta").mock(
        return_value=httpx.Response(200, json=_load("consar_metricas_cuenta"))
    )
    r = client.consar.metricas_cuenta()
    assert isinstance(r, MetricasCuentaResponse)
    assert r.metricas[0].desde_fecha == date(2010, 1, 1)


@respx.mock
def test_metricas_sensibilidad(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/metricas-sensibilidad").mock(
        return_value=httpx.Response(
            200, json=_load("consar_metricas_sensibilidad")
        )
    )
    r = client.consar.metricas_sensibilidad()
    assert isinstance(r, MetricasSensibilidadResponse)


# ============================================================================
# GRUPO 2 — Recursos
# ============================================================================


@respx.mock
def test_recursos_totales(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/recursos/totales").mock(
        return_value=httpx.Response(200, json=_load("consar_recursos_totales"))
    )
    r = client.consar.recursos_totales()
    assert isinstance(r, TotalesSarResponse)
    assert isinstance(r.serie[0].monto_mxn_mm, Decimal)
    assert r.fecha_min < r.fecha_max


@respx.mock
def test_recursos_por_afore_with_date_object(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/recursos/por-afore").mock(
        return_value=httpx.Response(200, json=_load("consar_recursos_por_afore"))
    )
    r = client.consar.recursos_por_afore(fecha=date(2025, 6, 1))
    assert isinstance(r, PorAforeResponse)
    assert route.calls[0].request.url.params["fecha"] == "2025-06-01"


@respx.mock
def test_recursos_por_componente(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/recursos/por-componente").mock(
        return_value=httpx.Response(
            200, json=_load("consar_recursos_por_componente")
        )
    )
    r = client.consar.recursos_por_componente(fecha="2025-06-01")
    assert isinstance(r, PorComponenteResponse)
    assert r.fecha == date(2025, 6, 1)


@respx.mock
def test_recursos_composicion(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/recursos/composicion").mock(
        return_value=httpx.Response(
            200, json=_load("consar_recursos_composicion")
        )
    )
    r = client.consar.recursos_composicion(fecha="2025-06-01")
    assert isinstance(r, ComposicionResponse)
    assert r.cierre_al_peso is True


@respx.mock
def test_recursos_imss_vs_issste(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/recursos/imss-vs-issste").mock(
        return_value=httpx.Response(
            200, json=_load("consar_recursos_imss_vs_issste")
        )
    )
    r = client.consar.recursos_imss_vs_issste()
    assert isinstance(r, ImssVsIsssteeResponse)


@respx.mock
def test_recursos_serie_propagates_filters(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/recursos/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_recursos_serie"))
    )
    r = client.consar.recursos_serie(
        codigo="rcv",
        afore_codigo="PRO_FU",
        desde="2010-01-01",
        hasta="2025-06-01",
    )
    assert isinstance(r, SerieResponse)
    params = route.calls[0].request.url.params
    assert params["codigo"] == "rcv"
    assert params["afore_codigo"] == "PRO_FU"
    assert params["desde"] == "2010-01-01"
    assert params["hasta"] == "2025-06-01"


@respx.mock
def test_recursos_serie_minimal(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/recursos/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_recursos_serie"))
    )
    client.consar.recursos_serie(codigo="rcv")
    params = route.calls[0].request.url.params
    assert "codigo" in params
    assert "afore_codigo" not in params
    assert "desde" not in params


# ============================================================================
# GRUPO 3 — PEA
# ============================================================================


@respx.mock
def test_pea_cotizantes_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/pea-cotizantes/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_pea_cotizantes"))
    )
    r = client.consar.pea_cotizantes_serie()
    assert isinstance(r, PeaCotizantesResponse)


# ============================================================================
# GRUPO 4 — Comisiones
# ============================================================================


@respx.mock
def test_comisiones_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/comisiones/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_comisiones_serie"))
    )
    r = client.consar.comisiones_serie(afore_codigo="PRO_FU")
    assert isinstance(r, ComisionSerieResponse)


@respx.mock
def test_comisiones_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/comisiones/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_comisiones_snapshot"))
    )
    r = client.consar.comisiones_snapshot(fecha="2025-06-01")
    assert isinstance(r, ComisionSnapshotResponse)
    assert isinstance(r.promedio_simple_pct, Decimal)


# ============================================================================
# GRUPO 5 — Flujos
# ============================================================================


@respx.mock
def test_flujos_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/flujos/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_flujos_serie"))
    )
    r = client.consar.flujos_serie()
    assert isinstance(r, FlujoSerieResponse)


@respx.mock
def test_flujos_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/flujos/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_flujos_snapshot"))
    )
    r = client.consar.flujos_snapshot(fecha="2025-06-01")
    assert isinstance(r, FlujoSnapshotResponse)


# ============================================================================
# GRUPO 6 — Traspasos
# ============================================================================


@respx.mock
def test_traspasos_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/traspasos/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_traspasos_serie"))
    )
    r = client.consar.traspasos_serie()
    assert isinstance(r, TraspasoSerieResponse)


@respx.mock
def test_traspasos_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/traspasos/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_traspasos_snapshot"))
    )
    r = client.consar.traspasos_snapshot(fecha="2025-06-01")
    assert isinstance(r, TraspasoSnapshotResponse)
    assert r.identidad.cierre_al_unidad is True


# ============================================================================
# GRUPO 7 — Rendimientos
# ============================================================================


@respx.mock
def test_rendimientos_serie(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/rendimientos/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_rendimientos_serie"))
    )
    r = client.consar.rendimientos_serie(
        afore_codigo="PRO_FU", siefore_slug="basica-1", plazo="36meses"
    )
    assert isinstance(r, RendimientoSerieResponse)
    params = route.calls[0].request.url.params
    assert params["plazo"] == "36meses"


@respx.mock
def test_rendimientos_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/rendimientos/snapshot").mock(
        return_value=httpx.Response(
            200, json=_load("consar_rendimientos_snapshot")
        )
    )
    r = client.consar.rendimientos_snapshot(
        fecha="2025-06-01", plazo="36meses"
    )
    assert isinstance(r, RendimientoSnapshotResponse)


@respx.mock
def test_rendimientos_sistema(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/rendimientos/sistema").mock(
        return_value=httpx.Response(
            200, json=_load("consar_rendimientos_sistema")
        )
    )
    r = client.consar.rendimientos_sistema(
        siefore_slug="basica-1", plazo="36meses"
    )
    assert isinstance(r, RendimientoSistemaResponse)


# ============================================================================
# GRUPO 8 — Precios
# ============================================================================


@respx.mock
def test_precios_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/precios/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_precios_serie"))
    )
    r = client.consar.precios_serie(
        afore_codigo="PRO_FU", siefore_slug="basica-1"
    )
    assert isinstance(r, PrecioSerieResponse)
    assert isinstance(r.serie[0].precio, Decimal)


@respx.mock
def test_precios_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/precios/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_precios_snapshot"))
    )
    r = client.consar.precios_snapshot(fecha="2025-06-01")
    assert isinstance(r, PrecioSnapshotResponse)


@respx.mock
def test_precios_comparativo(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/precios/comparativo").mock(
        return_value=httpx.Response(
            200, json=_load("consar_precios_comparativo")
        )
    )
    r = client.consar.precios_comparativo(
        siefore_slug="basica-1", desde="2024-01-01", hasta="2025-06-01"
    )
    assert isinstance(r, PrecioComparativoResponse)
    params = route.calls[0].request.url.params
    assert params["desde"] == "2024-01-01"
    assert params["hasta"] == "2025-06-01"


# ============================================================================
# GRUPO 9 — Precios-gestión (mismo schema, distintos endpoints)
# ============================================================================


@respx.mock
def test_precios_gestion_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/precios-gestion/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_precios_serie"))
    )
    r = client.consar.precios_gestion_serie(
        afore_codigo="PRO_FU", siefore_slug="basica-1"
    )
    assert isinstance(r, PrecioSerieResponse)


@respx.mock
def test_precios_gestion_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/precios-gestion/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_precios_snapshot"))
    )
    r = client.consar.precios_gestion_snapshot(fecha="2025-06-01")
    assert isinstance(r, PrecioSnapshotResponse)


@respx.mock
def test_precios_gestion_comparativo(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/precios-gestion/comparativo").mock(
        return_value=httpx.Response(
            200, json=_load("consar_precios_comparativo")
        )
    )
    r = client.consar.precios_gestion_comparativo(
        siefore_slug="basica-1", desde="2024-01-01", hasta="2025-06-01"
    )
    assert isinstance(r, PrecioComparativoResponse)


# ============================================================================
# GRUPO 10 — Cuentas
# ============================================================================


@respx.mock
def test_cuentas_serie(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/consar/cuentas/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_cuentas_serie"))
    )
    r = client.consar.cuentas_serie(
        afore_codigo="PRO_FU", metrica="cuentas_admin"
    )
    assert isinstance(r, CuentaSerieResponse)
    assert route.calls[0].request.url.params["metrica"] == "cuentas_admin"


@respx.mock
def test_cuentas_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/cuentas/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_cuentas_snapshot"))
    )
    r = client.consar.cuentas_snapshot(fecha="2025-06-01")
    assert isinstance(r, CuentaSnapshotResponse)


@respx.mock
def test_cuentas_sistema(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/cuentas/sistema").mock(
        return_value=httpx.Response(200, json=_load("consar_cuentas_sistema"))
    )
    r = client.consar.cuentas_sistema(metrica="cuentas_admin")
    assert isinstance(r, CuentaSistemaResponse)


# ============================================================================
# GRUPO 11 — Medidas
# ============================================================================


@respx.mock
def test_medidas_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/medidas/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_medidas_serie"))
    )
    r = client.consar.medidas_serie(
        afore_codigo="PRO_FU", siefore_slug="basica-1", metrica="var_99"
    )
    assert isinstance(r, MedidaSerieResponse)


@respx.mock
def test_medidas_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/medidas/snapshot").mock(
        return_value=httpx.Response(200, json=_load("consar_medidas_snapshot"))
    )
    r = client.consar.medidas_snapshot(fecha="2025-06-01", metrica="var_99")
    assert isinstance(r, MedidaSnapshotResponse)


# ============================================================================
# GRUPO 12 — Activo neto
# ============================================================================


@respx.mock
def test_activo_neto_serie(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/activo-neto/serie").mock(
        return_value=httpx.Response(200, json=_load("consar_activo_neto_serie"))
    )
    r = client.consar.activo_neto_serie(
        afore_codigo="PRO_FU", siefore_slug="basica-1"
    )
    assert isinstance(r, ActivoNetoSerieResponse)


@respx.mock
def test_activo_neto_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/activo-neto/snapshot").mock(
        return_value=httpx.Response(
            200, json=_load("consar_activo_neto_snapshot")
        )
    )
    r = client.consar.activo_neto_snapshot(fecha="2025-06-01")
    assert isinstance(r, ActivoNetoSnapshotResponse)


@respx.mock
def test_activo_neto_agregado(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/activo-neto/agregado").mock(
        return_value=httpx.Response(
            200, json=_load("consar_activo_neto_agregado")
        )
    )
    r = client.consar.activo_neto_agregado(
        afore_codigo="PRO_FU", categoria="basicas"
    )
    assert isinstance(r, ActivoNetoAggregadoResponse)


# ============================================================================
# Validación cruzada
# ============================================================================


@respx.mock
def test_404_raises_not_found(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/recursos/por-afore").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )
    with pytest.raises(NotFoundError):
        client.consar.recursos_por_afore(fecha="1990-01-01")


@respx.mock
def test_validation_error_on_unexpected_shape(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/consar/afores").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    with pytest.raises(ValidationError):
        client.consar.afores()


def test_invalid_fecha_day_raises_before_request(client: DatosMexico) -> None:
    """Día != 01 debe rechazarse en el helper antes de pegar a la red."""
    with pytest.raises(ValueError, match="día 01"):
        client.consar.recursos_por_afore(fecha="2025-06-15")


# ============================================================================
# Live integration tests (gated)
# ============================================================================


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


def test_live_afores_at_least_eleven(live: DatosMexico) -> None:
    r = live.consar.afores()
    assert r.count >= 11


def test_live_recursos_totales_serie_cubre_historico(
    live: DatosMexico,
) -> None:
    r = live.consar.recursos_totales()
    assert r.fecha_min <= date(1998, 6, 1)
    assert r.fecha_max >= date(2024, 1, 1)


def test_live_recursos_por_afore_2025_06(live: DatosMexico) -> None:
    r = live.consar.recursos_por_afore(fecha="2025-06-01")
    assert r.n_afores_reportando >= 10
    assert r.total_sistema_mm > Decimal("9000000")


def test_live_first_and_last_year_available(live: DatosMexico) -> None:
    r = live.consar.recursos_totales()
    fechas = {p.fecha for p in r.serie}
    assert any(f.year == 1998 for f in fechas)
    assert any(f.year >= 2024 for f in fechas)
