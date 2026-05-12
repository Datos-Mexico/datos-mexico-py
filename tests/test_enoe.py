"""Tests del namespace ENOE (Encuesta Nacional de Ocupación y Empleo)."""

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
from datos_mexico.endpoints.enoe import EnoeNamespace
from datos_mexico.models.enoe import (
    DistribucionPosicionSerie,
    DistribucionPosicionSnapshot,
    DistribucionSectorialSerie,
    DistribucionSectorialSnapshot,
    EnoeHealth,
    EnoeMetadata,
    EntidadesResponse,
    EtapasResponse,
    IndicadoresResponse,
    MicrodatosCount,
    MicrodatosListResponse,
    MicrodatosSchema,
    RankingResponse,
    SerieEntidadResponse,
    SerieNacionalResponse,
    SnapshotEntidadResponse,
    SnapshotNacionalResponse,
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
# Catálogos y metadata
# ============================================================================


@respx.mock
def test_health(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/health").mock(
        return_value=httpx.Response(200, json=_load("enoe_health"))
    )
    r = client.enoe.health()
    assert isinstance(r, EnoeHealth)
    assert r.status == "ok"
    assert r.total_microdatos > 100_000_000
    assert r.total_indicadores_agregados > 0


@respx.mock
def test_metadata(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/metadata").mock(
        return_value=httpx.Response(200, json=_load("enoe_metadata"))
    )
    r = client.enoe.metadata()
    assert isinstance(r, EnoeMetadata)
    assert r.acronimo == "ENOE"
    assert r.fuente == "INEGI"
    assert r.n_indicadores == 13
    assert r.n_entidades == 32
    assert len(r.tablas_disponibles) >= 1
    assert len(r.caveats) >= 1
    # Caveats vienen tipados
    assert all(c.slug and c.titulo for c in r.caveats)


@respx.mock
def test_indicadores_catalog(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/catalogos/indicadores").mock(
        return_value=httpx.Response(200, json=_load("enoe_indicadores"))
    )
    r = client.enoe.indicadores()
    assert isinstance(r, IndicadoresResponse)
    assert r.count == 13
    slugs = [i.slug for i in r.indicadores]
    assert "tasa_desocupacion" in slugs or "pob_15ymas" in slugs


@respx.mock
def test_entidades_catalog(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/catalogos/entidades").mock(
        return_value=httpx.Response(200, json=_load("enoe_entidades"))
    )
    r = client.enoe.entidades()
    assert isinstance(r, EntidadesResponse)
    assert r.count == 32
    # Cada entidad lleva clave de 2 dígitos
    for e in r.entidades:
        assert len(e.clave) == 2
        assert e.nombre
        assert e.abreviatura


@respx.mock
def test_etapas_catalog(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/catalogos/etapas-metodologicas").mock(
        return_value=httpx.Response(200, json=_load("enoe_etapas"))
    )
    r = client.enoe.etapas()
    assert isinstance(r, EtapasResponse)
    slugs = {e.slug for e in r.etapas}
    assert {"clasica", "etoe_telefonica", "enoe_n"}.issubset(slugs)


# ============================================================================
# Indicadores nacionales
# ============================================================================


@respx.mock
def test_serie_nacional(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/nacional/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_serie_nacional"))
    )
    r = client.enoe.serie_nacional(
        indicador="tasa_desocupacion", desde="2024T1", hasta="2025T1"
    )
    assert isinstance(r, SerieNacionalResponse)
    assert r.indicador == "tasa_desocupacion"
    assert r.cobertura.desde == "2024T1"
    assert r.cobertura.hasta == "2025T1"
    assert len(r.datos) == r.cobertura.n_observaciones
    # Query params construidos correctamente
    params = route.calls[0].request.url.params
    assert params["indicador"] == "tasa_desocupacion"
    assert params["desde"] == "2024T1"


@respx.mock
def test_serie_nacional_sin_filtros(client: DatosMexico) -> None:
    """Sólo el indicador es obligatorio; desde/hasta/etapa son opcionales."""
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/nacional/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_serie_nacional"))
    )
    client.enoe.serie_nacional(indicador="tasa_desocupacion")
    params = route.calls[0].request.url.params
    assert params["indicador"] == "tasa_desocupacion"
    assert "desde" not in params
    assert "hasta" not in params
    assert "etapa" not in params


@respx.mock
def test_serie_nacional_con_etapa(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/nacional/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_serie_nacional"))
    )
    client.enoe.serie_nacional(indicador="tasa_desocupacion", etapa="enoe_n")
    assert route.calls[0].request.url.params["etapa"] == "enoe_n"


@respx.mock
def test_snapshot_nacional(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/nacional/snapshot").mock(
        return_value=httpx.Response(200, json=_load("enoe_snapshot_nacional"))
    )
    r = client.enoe.snapshot_nacional(periodo="2025T1")
    assert isinstance(r, SnapshotNacionalResponse)
    assert r.periodo == "2025T1"
    assert r.n_indicadores == 13
    assert len(r.indicadores) == 13
    assert route.calls[0].request.url.params["periodo"] == "2025T1"


# ============================================================================
# Indicadores por entidad
# ============================================================================


@respx.mock
def test_serie_entidad_usa_param_canonico(client: DatosMexico) -> None:
    """Verifica que el SDK envía entidad_clave (post-Sub-fase 3.10c)."""
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/entidad/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_serie_entidad"))
    )
    r = client.enoe.serie_entidad(
        indicador="tasa_desocupacion",
        entidad_clave="09",
        desde="2024T1",
        hasta="2025T1",
    )
    assert isinstance(r, SerieEntidadResponse)
    assert r.entidad_clave == "09"
    assert r.entidad_nombre == "Ciudad de México"
    params = route.calls[0].request.url.params
    assert params["entidad_clave"] == "09"
    assert "entidad" not in params  # alias deprecated no debe usarse


@respx.mock
def test_snapshot_entidad(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/entidad/snapshot").mock(
        return_value=httpx.Response(200, json=_load("enoe_snapshot_entidad"))
    )
    r = client.enoe.snapshot_entidad(
        periodo="2025T1", indicador="tasa_desocupacion"
    )
    assert isinstance(r, SnapshotEntidadResponse)
    assert r.n_entidades == 32
    assert len(r.datos) == 32
    params = route.calls[0].request.url.params
    assert params["periodo"] == "2025T1"
    assert params["indicador"] == "tasa_desocupacion"


@respx.mock
def test_ranking_top5_desocupacion(client: DatosMexico) -> None:
    """Reproduce el TOP 5 publicado por INEGI 265/25 para 2025T1."""
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/entidad/ranking").mock(
        return_value=httpx.Response(200, json=_load("enoe_ranking"))
    )
    r = client.enoe.ranking(
        periodo="2025T1", indicador="tasa_desocupacion", limit=5
    )
    assert isinstance(r, RankingResponse)
    assert r.total_resultados == 5
    assert len(r.ranking) == 5
    # Tabasco lidera el ranking en 2025T1
    assert r.ranking[0].entidad_clave == "27"
    assert r.ranking[0].entidad_nombre == "Tabasco"
    # Comprobar orden por defecto
    assert route.calls[0].request.url.params["orden"] == "desc"


@respx.mock
def test_ranking_orden_asc(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/indicadores/entidad/ranking").mock(
        return_value=httpx.Response(200, json=_load("enoe_ranking"))
    )
    client.enoe.ranking(
        periodo="2025T1", indicador="tasa_desocupacion", orden="asc", limit=10
    )
    params = route.calls[0].request.url.params
    assert params["orden"] == "asc"
    assert params["limit"] == "10"


# ============================================================================
# Distribuciones sectorial + posición
# ============================================================================


@respx.mock
def test_distribucion_sectorial_snapshot_nacional(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/ocupados/por-sector/snapshot").mock(
        return_value=httpx.Response(200, json=_load("enoe_sector_snapshot"))
    )
    r = client.enoe.distribucion_sectorial_snapshot(periodo="2025T1")
    assert isinstance(r, DistribucionSectorialSnapshot)
    assert r.nivel == "nacional"
    assert r.n_sectores == 12
    # Sin entidad_clave en nacional
    assert "geo_clave" not in route.calls[0].request.url.params


@respx.mock
def test_distribucion_sectorial_snapshot_entidad_requiere_clave(
    client: DatosMexico,
) -> None:
    """Pasar nivel='entidad' sin entidad_clave debe lanzar ValueError."""
    with pytest.raises(ValueError, match="entidad_clave"):
        client.enoe.distribucion_sectorial_snapshot(
            periodo="2025T1", nivel="entidad"
        )


@respx.mock
def test_distribucion_sectorial_snapshot_entidad_pasa_geo_clave(
    client: DatosMexico,
) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/ocupados/por-sector/snapshot").mock(
        return_value=httpx.Response(200, json=_load("enoe_sector_snapshot"))
    )
    client.enoe.distribucion_sectorial_snapshot(
        periodo="2025T1", nivel="entidad", entidad_clave="09"
    )
    params = route.calls[0].request.url.params
    assert params["nivel"] == "entidad"
    assert params["geo_clave"] == "09"


@respx.mock
def test_distribucion_sectorial_serie(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/ocupados/por-sector/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_sector_serie"))
    )
    r = client.enoe.distribucion_sectorial_serie(
        sector_clave="10", desde="2024T1", hasta="2024T2"
    )
    assert isinstance(r, DistribucionSectorialSerie)
    assert r.sector_clave == "10"
    assert r.cobertura.n_observaciones == len(r.datos)
    params = route.calls[0].request.url.params
    assert params["sector_clave"] == "10"


@respx.mock
def test_distribucion_posicion_snapshot(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/ocupados/por-posicion/snapshot").mock(
        return_value=httpx.Response(200, json=_load("enoe_posicion_snapshot"))
    )
    r = client.enoe.distribucion_posicion_snapshot(periodo="2025T1")
    assert isinstance(r, DistribucionPosicionSnapshot)
    assert r.n_posiciones == 4
    # Las 4 categorías: subordinados, empleadores, cuenta propia, no remunerados
    claves = {p.pos_clave for p in r.distribucion}
    assert claves == {1, 2, 3, 4}


@respx.mock
def test_distribucion_posicion_serie(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/ocupados/por-posicion/serie").mock(
        return_value=httpx.Response(200, json=_load("enoe_posicion_serie"))
    )
    r = client.enoe.distribucion_posicion_serie(
        pos_clave=1, desde="2024T1", hasta="2024T2"
    )
    assert isinstance(r, DistribucionPosicionSerie)
    assert r.pos_clave == 1
    params = route.calls[0].request.url.params
    assert params["pos_clave"] == "1"


@respx.mock
def test_distribucion_posicion_snapshot_entidad_requiere_clave(
    client: DatosMexico,
) -> None:
    with pytest.raises(ValueError, match="entidad_clave"):
        client.enoe.distribucion_posicion_snapshot(
            periodo="2025T1", nivel="entidad"
        )


# ============================================================================
# Microdatos
# ============================================================================


@respx.mock
def test_microdatos_schema(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/schema").mock(
        return_value=httpx.Response(200, json=_load("enoe_microdatos_schema"))
    )
    r = client.enoe.microdatos_schema("sdem")
    assert isinstance(r, MicrodatosSchema)
    assert r.tabla == "microdatos_sdem"
    assert r.total_columnas > 0
    assert len(r.columnas) > 0


@respx.mock
def test_microdatos_count(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/count").mock(
        return_value=httpx.Response(200, json=_load("enoe_microdatos_count"))
    )
    r = client.enoe.microdatos_count(
        "sdem", periodo="2025T1", entidad_clave="09"
    )
    assert isinstance(r, MicrodatosCount)
    assert r.total > 0
    params = route.calls[0].request.url.params
    assert params["periodo"] == "2025T1"
    assert params["entidad_clave"] == "09"


@respx.mock
def test_microdatos_count_filtros_adicionales(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/count").mock(
        return_value=httpx.Response(200, json=_load("enoe_microdatos_count"))
    )
    client.enoe.microdatos_count(
        "sdem",
        periodo="2025T1",
        entidad_clave="09",
        sex=2,
        eda_min=25,
        eda_max=45,
    )
    params = route.calls[0].request.url.params
    assert params["sex"] == "2"
    assert params["eda_min"] == "25"
    assert params["eda_max"] == "45"


@respx.mock
def test_microdatos_page_default_include_extras_true(
    client: DatosMexico,
) -> None:
    """include_extras debe ir como True por defecto (Sub-fase 3.10b)."""
    route = respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(
            200, json=_load("enoe_microdatos_list_page1")
        )
    )
    client.enoe.microdatos_page("sdem", periodo="2025T1", per_page=3)
    params = route.calls[0].request.url.params
    assert params["include_extras"] == "true"


@respx.mock
def test_microdatos_page_include_extras_false(client: DatosMexico) -> None:
    route = respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(
            200, json=_load("enoe_microdatos_list_page1")
        )
    )
    client.enoe.microdatos_page(
        "sdem", periodo="2025T1", per_page=3, include_extras=False
    )
    assert route.calls[0].request.url.params["include_extras"] == "false"


@respx.mock
def test_microdatos_page_validates_response(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(
            200, json=_load("enoe_microdatos_list_page1")
        )
    )
    r = client.enoe.microdatos_page("sdem", periodo="2025T1")
    assert isinstance(r, MicrodatosListResponse)
    assert r.pagination.page == 1
    assert isinstance(r.data, list)
    assert len(r.data) > 0


@respx.mock
def test_microdatos_iter_paginates_until_exhausted(client: DatosMexico) -> None:
    """microdatos_iter debe pedir páginas hasta has_next=False."""
    page1 = _load("enoe_microdatos_list_page1")
    page2 = _load("enoe_microdatos_list_page2")
    expected_rows = len(page1["data"]) + len(page2["data"])

    def _handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        if page == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        side_effect=_handler
    )
    rows = list(
        client.enoe.microdatos_iter(
            "sdem", periodo="2025T1", entidad_clave="09", per_page=3
        )
    )
    assert len(rows) == expected_rows


@respx.mock
def test_microdatos_iter_respects_limit(client: DatosMexico) -> None:
    """El parámetro limit detiene la iteración aunque queden páginas."""
    page1 = _load("enoe_microdatos_list_page1")
    # Forzar has_next=True por si limit no funcionara: la primera página tiene 3 rows
    page1["pagination"]["has_next"] = True

    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(200, json=page1)
    )
    rows = list(
        client.enoe.microdatos_iter(
            "sdem", periodo="2025T1", per_page=3, limit=2
        )
    )
    assert len(rows) == 2


@respx.mock
def test_microdatos_to_pandas_returns_dataframe(client: DatosMexico) -> None:
    pd = pytest.importorskip("pandas")
    page1 = _load("enoe_microdatos_list_page1")
    page1["pagination"]["has_next"] = False
    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(200, json=page1)
    )
    df = client.enoe.microdatos_to_pandas(
        "sdem", periodo="2025T1", entidad_clave="09", include_extras=False
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(page1["data"])
    # Las columnas estables de sdem deben estar presentes
    for col in ("periodo", "ent", "eda", "sex", "fac_tri"):
        assert col in df.columns


@respx.mock
def test_microdatos_to_pandas_empty_dataframe(client: DatosMexico) -> None:
    pytest.importorskip("pandas")
    empty = _load("enoe_microdatos_list_page1")
    empty["data"] = []
    empty["pagination"]["total"] = 0
    empty["pagination"]["total_pages"] = 0
    empty["pagination"]["has_next"] = False
    respx.get(f"{BASE}/api/v1/enoe/microdatos/sdem/list").mock(
        return_value=httpx.Response(200, json=empty)
    )
    df = client.enoe.microdatos_to_pandas("sdem", periodo="9999T9")
    assert len(df) == 0


# ============================================================================
# Wiring: el namespace está expuesto en el cliente
# ============================================================================


def test_namespace_attached_to_client(client: DatosMexico) -> None:
    assert isinstance(client.enoe, EnoeNamespace)


# ============================================================================
# Integración contra API real (opt-in)
# ============================================================================


@pytest.mark.integration
def test_integration_health_real_api() -> None:
    if os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1":
        pytest.skip(
            "Activar con DATOS_MEXICO_INTEGRATION_TESTS=1 para correr "
            "tests contra el API en vivo."
        )
    with DatosMexico() as client:
        r = client.enoe.health()
        assert r.status == "ok"
        assert r.total_microdatos > 100_000_000


@pytest.mark.integration
def test_integration_inegi_265_25_reproducible() -> None:
    """Reproduce el TOP 5 desempleo 2025T1 del boletín INEGI 265/25."""
    if os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") != "1":
        pytest.skip(
            "Activar con DATOS_MEXICO_INTEGRATION_TESTS=1 para correr "
            "tests contra el API en vivo."
        )
    with DatosMexico() as client:
        r = client.enoe.ranking(
            periodo="2025T1", indicador="tasa_desocupacion", limit=5
        )
        claves = [e.entidad_clave for e in r.ranking]
        # TOP 5 publicado por INEGI en boletín 265/25:
        # 1. Tabasco (27) 2. Coahuila (05) 3. Durango (10) 4. CDMX (09) 5. Tamaulipas (28)
        assert claves == ["27", "05", "10", "09", "28"]
