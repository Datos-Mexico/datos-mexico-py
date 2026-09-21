"""Tests del namespace INEGI (cubos, tabulados, Censos Económicos, bancos de indicadores) con
mocks.
"""

from __future__ import annotations

from collections.abc import Generator
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from datos_mexico import DatosMexico

BASE = "https://api.test.local"

CATALOGO = {
    "n_cubos": 2,
    "temas": [
        {
            "clave": "economia",
            "nombre": "Economía",
            "descripcion": "x",
            "cubos": [
                {
                    "clave": "saic-censos",
                    "nombre": "Censos Económicos",
                    "tema": "economia",
                    "descripcion": "d",
                    "fuente": "INEGI",
                    "fuente_url": "https://www.inegi.org.mx",
                    "licencia": "INEGI",
                    "n_medidas": 9,
                }
            ],
        },
        {
            "clave": "poblacion",
            "nombre": "Población",
            "descripcion": "y",
            "cubos": [
                {
                    "clave": "tabulados-censo2020",
                    "nombre": "Censo 2020: tabulados básicos",
                    "tema": "poblacion",
                    "descripcion": "d",
                    "fuente": "INEGI",
                    "fuente_url": "https://www.inegi.org.mx",
                    "licencia": "INEGI",
                }
            ],
        },
    ],
}
RESULTADO = {
    "cubo": "saic-censos",
    "consulta": {
        "medidas": ["ue"],
        "columnas": ["entidad"],
        "filtros": {"anio": ["2023"]},
        "padres": False,
        "orden": None,
        "sentido": "desc",
        "limite": None,
    },
    "columnas": [
        {"clave": "entidad_id", "titulo": "Entidad", "tipo": "id", "dimension": "entidad"},
        {"clave": "entidad", "titulo": "Entidad", "tipo": "dimension", "dimension": "entidad"},
        {
            "clave": "ue",
            "titulo": "Unidades económicas",
            "tipo": "medida",
            "unidad": "unidades",
            "sumable": True,
        },
    ],
    "filas": [
        {"entidad_id": "01", "entidad": "Aguascalientes", "ue": 64549},
        {"entidad_id": "02", "entidad": "Baja California", "ue": 120000},
    ],
    "n": 2,
    "limitado": False,
    "ms": 12,
}
CUADRO = {
    "familia": "censo2020",
    "cuadro": {
        "cuadro": "cpv2020_b_eum_01_poblacion:02",
        "archivo": "cpv2020_b_eum_01_poblacion.xlsx",
        "hoja": "02",
        "titulo": "Población total por entidad federativa, sexo y grupos quinquenales de edad",
        "dimensiones": ["Entidad federativa", "Sexo", "Grupos quinquenales de edad"],
        "columnas": ["Población total"],
        "celdas": 10,
        "sha256": "ab",
        "archivo_url": "https://api.test.local/x",
    },
    "total": 1,
    "limit": 500,
    "offset": 0,
    "items": [
        {
            "d1": "Estados Unidos Mexicanos",
            "d2": "Total",
            "d3": "Total",
            "d4": "",
            "d5": "",
            "columna": "Población total",
            "valor": 126014024,
            "texto": None,
            "orden": 0,
        }
    ],
}
SAIC = {
    "anio": "2023",
    "variables": ["UE", "H001A"],
    "total": 1,
    "limit": 500,
    "offset": 0,
    "items": [
        {
            "anio": "2023",
            "cve_ent": "00",
            "cve_mun": "",
            "nivel_act": 0,
            "clave_act": "0",
            "actividad": "Total",
            "estrato": 0,
            "UE": 5468180,
            "H001A": 27965433,
        }
    ],
}


@pytest.fixture
def client() -> Generator[DatosMexico, None, None]:
    c = DatosMexico(base_url=BASE, timeout=5.0, cache_ttl=0, max_retries=0)
    yield c
    c.close()


@respx.mock
def test_cubos_catalogo(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/cubos").mock(return_value=httpx.Response(200, json=CATALOGO))
    cat = client.inegi.cubos()
    assert cat.n_cubos == 2
    assert [c.clave for c in cat.todos()] == ["saic-censos", "tabulados-censo2020"]


@respx.mock
def test_cubo_datos_arma_los_filtros(client: DatosMexico) -> None:
    ruta = respx.get(f"{BASE}/api/v1/cubos/saic-censos/datos").mock(
        return_value=httpx.Response(200, json=RESULTADO)
    )
    r = client.inegi.cubo_datos(
        "saic-censos",
        medidas=["ue"],
        columnas=["entidad"],
        filtros={"anio": ["2023"], "ambito": ["entidad"], "estrato": ["0", "1"]},
        padres=True,
        orden="ue",
        sentido="desc",
        limite=50,
    )
    q = parse_qs(urlparse(str(ruta.calls[0].request.url)).query)
    assert q["medidas"] == ["ue"] and q["columnas"] == ["entidad"]
    assert (
        q["f.anio"] == ["2023"]
        and q["f.estrato"] == ["0|1"]
        and q["padres"] == ["1"]
        and q["orden"] == ["ue"]
        and q["limite"] == ["50"]
    )
    assert r.n == 2 and sum(f["ue"] for f in r.filas) == 184549
    assert [c.clave for c in r.columnas] == ["entidad_id", "entidad", "ue"]


@respx.mock
def test_cubo_csv(client: DatosMexico) -> None:
    ruta = respx.get(f"{BASE}/api/v1/cubos/saic-censos/datos").mock(
        return_value=httpx.Response(
            200, text="﻿entidad,ue\r\nA,1\r\n", headers={"content-type": "text/csv"}
        )
    )
    texto = client.inegi.cubo_csv(
        "saic-censos", medidas=["ue"], columnas=["entidad"], filtros={"anio": ["2023"]}
    )
    assert texto.startswith("﻿") and "formato=csv" in str(ruta.calls[0].request.url)


@respx.mock
def test_tabulado_celda(client: DatosMexico) -> None:
    ruta = respx.get(
        f"{BASE}/api/v1/inegi/tabulados/censo2020/cpv2020_b_eum_01_poblacion%3A02"
    ).mock(return_value=httpx.Response(200, json=CUADRO))
    r = client.inegi.tabulado(
        "censo2020",
        "cpv2020_b_eum_01_poblacion:02",
        d1="Estados Unidos Mexicanos",
        d2="Total",
        d3="Total",
        columna="Población total",
    )
    q = parse_qs(urlparse(str(ruta.calls[0].request.url)).query)
    assert q["d1"] == ["Estados Unidos Mexicanos"] and q["columna"] == ["Población total"]
    assert r.total == 1 and r.items[0].valor == 126014024
    assert r.cuadro.dimensiones[0] == "Entidad federativa"


@respx.mock
def test_tabulado_celdas_pagina(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/inegi/tabulados/censo2020/c").mock(
        return_value=httpx.Response(200, json={**CUADRO, "total": 1, "limit": 5000})
    )
    celdas = list(client.inegi.tabulado_celdas("censo2020", "c"))
    assert len(celdas) == 1 and celdas[0].orden == 0


@respx.mock
def test_saic_datos(client: DatosMexico) -> None:
    ruta = respx.get(f"{BASE}/api/v1/inegi/saic/datos").mock(
        return_value=httpx.Response(200, json=SAIC)
    )
    r = client.inegi.saic_datos("2023", 0, cve_ent="00", variables=["UE", "H001A"])
    q = parse_qs(urlparse(str(ruta.calls[0].request.url)).query)
    assert q["anio"] == ["2023"] and q["nivel_act"] == ["0"] and q["variables"] == ["UE,H001A"]
    assert r.items[0]["UE"] == 5468180


@respx.mock
def test_indicador_observaciones(client: DatosMexico) -> None:
    respx.get(f"{BASE}/api/v1/inegi/indicadores/1002000001/observaciones").mock(
        return_value=httpx.Response(
            200,
            json={"observaciones": [{"periodo": "2020", "valor": 126014024, "geografia": "00"}]},
        )
    )
    o = client.inegi.indicador_observaciones(
        "1002000001", geografia="00", desde="2020", hasta="2020"
    )
    assert o.observaciones[0].valor == 126014024
