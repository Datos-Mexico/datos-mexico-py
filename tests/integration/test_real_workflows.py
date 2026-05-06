"""Investigator workflows: realistic call sequences that the SDK enables.

These tests are the strongest evidence that "the SDK works" — they
mirror the actual code an external user would write. They include the
specific cross-dataset workflow used by the paper Amafore-ITAM 2026.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from datos_mexico import DatosMexico

pytestmark = pytest.mark.integration

_SAR_SNAPSHOT = date(2025, 6, 1)


def test_workflow_servidores_distribucion(client: DatosMexico) -> None:
    """Investigator: distribución de sueldos servidores CDMX.

    1. Dashboard KPIs
    2. Lista de sectores
    3. Stats de los 3 sectores con más personal
    4. Brecha salarial por edad
    """
    dashboard = client.cdmx.dashboard_stats()
    assert dashboard.total_servidores > 0
    assert dashboard.avg_salary > 0

    sectores = client.cdmx.sectores()
    real_sectores = sorted(
        [s for s in sectores if s.total_servidores > 0],
        key=lambda s: s.total_servidores,
        reverse=True,
    )[:3]
    assert len(real_sectores) == 3

    for s in real_sectores:
        stats = client.cdmx.sector_stats(s.id)
        assert stats.id == s.id
        assert stats.total_servidores == s.total_servidores
        assert stats.count_hombres + stats.count_mujeres <= stats.total_servidores

    brecha = client.cdmx.brecha_edad()
    assert len(brecha) > 0
    for row in brecha:
        # Brecha could legitimately be near zero or even negative for some
        # buckets, but each row must report counts > 0 if averages exist.
        assert row.count_male >= 0
        assert row.count_female >= 0


def test_workflow_sar_composicion_temporal(client: DatosMexico) -> None:
    """Investigator: análisis temporal del SAR mexicano.

    1. Catálogo de afores
    2. Serie histórica del SAR total
    3. Snapshot por afore en la fecha más reciente
    4. Snapshot por componente en la misma fecha
    5. IMSS vs ISSSTE histórico
    """
    afores = client.consar.afores()
    assert len(afores.afores) > 0

    totales = client.consar.recursos_totales()
    assert totales.fecha_max >= _SAR_SNAPSHOT or totales.n_puntos > 100

    por_afore = client.consar.recursos_por_afore(fecha=_SAR_SNAPSHOT)
    assert por_afore.fecha == _SAR_SNAPSHOT
    assert por_afore.n_afores_reportando > 0

    por_componente = client.consar.recursos_por_componente(fecha=_SAR_SNAPSHOT)
    assert por_componente.fecha == _SAR_SNAPSHOT
    assert len(por_componente.componentes) > 0
    # The componentes array is hierarchical: it includes summary rows
    # (categoria == "total"), mid-level aggregates ("aggregate") and
    # leaf rows ("component" / "operativo"). Only leaf rows partition
    # sar_total_mm. The strict identity sar_total_mm vs por_afore is
    # already exercised in test_data_integrity.
    leaves = [
        c for c in por_componente.componentes
        if c.categoria in {"component", "operativo"}
    ]
    assert leaves, "expected at least one leaf component row"
    leaves_sum = sum((c.monto_mxn_mm for c in leaves), Decimal(0))
    if por_componente.sar_total_mm > 0:
        delta = abs(leaves_sum - por_componente.sar_total_mm) / por_componente.sar_total_mm
        assert delta <= Decimal("0.01"), (
            f"leaf components ({leaves_sum}) do not partition "
            f"sar_total_mm ({por_componente.sar_total_mm}); relative delta {delta}"
        )

    imss_vs_issste = client.consar.recursos_imss_vs_issste()
    assert len(imss_vs_issste.serie) > 0


def test_workflow_enigh_desigualdad(client: DatosMexico) -> None:
    """Investigator: análisis de desigualdad ENIGH 2024 NS.

    1. Resumen nacional
    2. Por decil
    3. Gastos por rubro nacional
    4. Gastos por rubro para deciles 1, 5 y 10 (extremos + mediana)
    """
    summary = client.enigh.hogares_summary()
    assert summary.n_hogares_expandido > 30_000_000

    deciles = client.enigh.hogares_by_decil()
    assert len(deciles) == 10

    nacional_rubros = client.enigh.gastos_by_rubro()
    nacional_slugs = {r.slug for r in nacional_rubros.rubros}

    for decil in (1, 5, 10):
        per_decil = client.enigh.gastos_by_rubro(decil=decil)
        assert per_decil.decil == decil
        decil_slugs = {r.slug for r in per_decil.rubros}
        assert decil_slugs == nacional_slugs, (
            f"decil {decil} expone rubros distintos al nacional: "
            f"missing={nacional_slugs - decil_slugs}, "
            f"extras={decil_slugs - nacional_slugs}"
        )


def test_workflow_comparativo_paper_amafore(client: DatosMexico) -> None:
    """Investigador: workflow específico del paper Amafore-ITAM 2026.

    Cruza CDMX (servidores), CONSAR (aportes/jubilaciones), ENIGH (deciles).
    Verifica además que los campos editoriales del observatorio (note,
    narrative, interpretacion, caveats, caveats_interpretativos) están
    presentes y son strings no vacíos.
    """
    ing = client.comparativo.ingreso_cdmx_vs_nacional()
    assert ing.note, "ingreso.note debe estar presente (campo editorial)"
    assert ing.caveats, "ingreso.caveats debe estar presente"
    assert ing.ratio_hogar_nacional_sobre_servidor > 0

    apo = client.comparativo.aportes_vs_jubilaciones_actuales()
    assert apo.interpretacion, "aportes.interpretacion debe estar presente"
    assert apo.caveats
    assert apo.cdmx_aportes_actuales.n_servidores > 100_000
    assert apo.enigh_jubilaciones_actuales.n_hogares_con_jubilacion_expandido > 0

    dec = client.comparativo.decil_servidores_cdmx()
    assert dec.narrative, "decil.narrative debe estar presente"
    assert dec.caveats_interpretativos.frontera_p50, (
        "caveats_interpretativos.frontera_p50 debe estar presente "
        "(diferenciador del observatorio)"
    )
    assert dec.caveats_interpretativos.narrativa_correcta
    assert dec.caveats_interpretativos.insight_principal
    assert dec.caveats_interpretativos.implicacion_narrativa
    assert len(dec.escenarios) >= 1
