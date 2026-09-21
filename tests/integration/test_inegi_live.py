"""Integración: el namespace INEGI reproduce cifras publicadas por el INEGI contra la API en vivo
(gated).
"""

from __future__ import annotations

import pytest

from datos_mexico import DatosMexico

pytestmark = pytest.mark.integration


def test_catalogo_de_cubos_incluye_saic_y_tabulados(client: DatosMexico) -> None:
    cat = client.inegi.cubos()
    claves = {c.clave for c in cat.todos()}
    assert (
        cat.n_cubos >= 50
        and {"saic-censos", "tabulados-censo2020", "tabulados-csi-anual"} <= claves
    )


def test_censo_2020_poblacion_total(client: DatosMexico) -> None:
    r = client.inegi.tabulado(
        "censo2020",
        "cpv2020_b_eum_01_poblacion:02",
        d1="Estados Unidos Mexicanos",
        d2="Total",
        d3="Total",
        columna="Población total",
    )
    assert r.total == 1 and r.items[0].valor == 126014024
    b = client.inegi.indicador_observaciones(
        "1002000001", geografia="00", desde="2020", hasta="2020"
    )
    assert b.observaciones[0].valor == 126014024


def test_censos_economicos_2023(client: DatosMexico) -> None:
    s = client.inegi.saic()
    anios = {a.anio: a for a in s.anios}
    assert (
        len(anios) == 5
        and all(a.completo for a in anios.values())
        and anios["2023"].unidades_economicas == 5468180
    )
    r = client.inegi.cubo_datos(
        "saic-censos",
        medidas=["ue"],
        columnas=["entidad"],
        filtros={"anio": ["2023"], "ambito": ["entidad"], "nivel": ["0"], "estrato": ["0"]},
    )
    assert r.n == 32 and sum(f["ue"] for f in r.filas) == 5468180
