"""Server-side accounting / consistency checks.

These tests exercise the API for *internal consistency*: the same
fact reported by two different endpoints must agree. If any of these
fail in CI/local, the bug is upstream (server) — the SDK should not be
patched to mask it.

Covers:

- SAR identity: ``recursos_por_componente.sar_total_mm`` must equal
  ``recursos_por_afore.total_sistema_mm`` for the same date.
- ENIGH validations: every bound returned by ``validaciones()`` must
  have ``passing=True``. This is the observatory's own check vs the
  cifras oficiales INEGI.
- ENIGH deciles: the sum of ``n_hogares_expandido`` across deciles must
  equal the national total within rounding.
- ENIGH rubros: the percentages of ``gastos_by_rubro`` must sum to ~100%.
- CONSAR temporal monotonicity: the dates of ``recursos_totales().serie``
  must be strictly ascending.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from datos_mexico import DatosMexico

from .conftest import (
    TOLERANCE_HOGARES_DECIL,
    TOLERANCE_PCT_SISTEMA,
    TOLERANCE_PCT_SUM,
    TOLERANCE_SAR_IDENTITY,
)

pytestmark = pytest.mark.integration

# Most recent SAR snapshot date documented in CLAUDE.md.
_SAR_SNAPSHOT = date(2025, 6, 1)


def test_consar_recursos_identidad_contable(client: DatosMexico) -> None:
    """sar_total_mm (componentes) == total_sistema_mm (afores) at the
    same date, within ``TOLERANCE_SAR_IDENTITY`` (1%).

    Both endpoints aggregate the same underlying CONSAR snapshot from
    different angles. They must agree to the peso (or close to it).
    """
    componentes = client.consar.recursos_por_componente(fecha=_SAR_SNAPSHOT)
    afores = client.consar.recursos_por_afore(fecha=_SAR_SNAPSHOT)

    a = componentes.sar_total_mm
    b = afores.total_sistema_mm
    if a == 0:
        pytest.fail(f"sar_total_mm is zero — server returned bad snapshot for {_SAR_SNAPSHOT}")

    relative_delta = abs(a - b) / a
    assert relative_delta <= TOLERANCE_SAR_IDENTITY, (
        f"SAR identity violated for {_SAR_SNAPSHOT}: "
        f"componentes={a}, afores={b}, relative_delta={relative_delta:.6f} "
        f"> tolerance {TOLERANCE_SAR_IDENTITY}"
    )


def test_consar_pct_sistema_suman_100(client: DatosMexico) -> None:
    """Across AFOREs, ``pct_sistema`` should sum to ~100% within tolerance."""
    snapshot = client.consar.recursos_por_afore(fecha=_SAR_SNAPSHOT)
    pcts = [a.pct_sistema for a in snapshot.afores if a.pct_sistema is not None]
    assert pcts, "expected at least one AFORE with pct_sistema"

    total = sum(pcts, Decimal(0))
    assert abs(total - Decimal(100)) <= TOLERANCE_PCT_SISTEMA, (
        f"AFORE pct_sistema does not sum to 100%: total={total}, "
        f"tolerance ±{TOLERANCE_PCT_SISTEMA}"
    )


def test_enigh_validaciones_all_passing(client: DatosMexico) -> None:
    """Every bound in ``enigh.validaciones()`` must report ``passing=True``.

    If a bound fails, the test reports the failing row so the server-side
    discrepancy can be triaged immediately.
    """
    response = client.enigh.validaciones()
    assert response.count > 0, "expected at least one validation bound"

    failing = [b for b in response.bounds if not b.passing]
    if failing:
        details = "\n".join(
            f"  - {b.id} ({b.scope}/{b.metric}): "
            f"calculado={b.calculado}, oficial={b.oficial}, "
            f"delta_pct={b.delta_pct} (tolerance {b.tolerance_pct})"
            for b in failing
        )
        pytest.fail(
            f"{len(failing)}/{response.count} INEGI validations failing:\n"
            f"{details}"
        )


def test_enigh_deciles_suman_total(client: DatosMexico) -> None:
    """Sum of ``n_hogares_expandido`` across deciles ≈ national total.

    Tolerance set tight (0.01%): this is a partition of the same
    universe, so the sum should match modulo rounding.
    """
    summary = client.enigh.hogares_summary()
    deciles = client.enigh.hogares_by_decil()

    total_summary = summary.n_hogares_expandido
    total_deciles = sum(d.n_hogares_expandido for d in deciles)

    if total_summary == 0:
        pytest.fail("hogares_summary.n_hogares_expandido is zero")

    relative_delta = abs(Decimal(total_summary) - Decimal(total_deciles)) / Decimal(
        total_summary
    )
    assert relative_delta <= TOLERANCE_HOGARES_DECIL, (
        f"deciles do not partition national total: "
        f"summary={total_summary:,}, sum(deciles)={total_deciles:,}, "
        f"relative_delta={relative_delta:.6f} > tolerance {TOLERANCE_HOGARES_DECIL}"
    )


def test_enigh_rubros_suman_100pct(client: DatosMexico) -> None:
    """``gastos_by_rubro().rubros[*].pct_del_monetario`` should sum to ~100%."""
    response = client.enigh.gastos_by_rubro()
    pcts = [r.pct_del_monetario for r in response.rubros]
    assert pcts, "expected at least one rubro"

    total = sum(pcts, Decimal(0))
    assert abs(total - Decimal(100)) <= TOLERANCE_PCT_SUM, (
        f"rubros pct_del_monetario does not sum to 100%: total={total}, "
        f"tolerance ±{TOLERANCE_PCT_SUM}"
    )


def test_consar_serie_monotonia(client: DatosMexico) -> None:
    """Dates in ``recursos_totales().serie`` are strictly ascending."""
    response = client.consar.recursos_totales()
    serie = response.serie
    assert len(serie) > 1, "expected at least 2 points to test monotonicity"

    dates = [p.fecha for p in serie]
    sorted_dates = sorted(dates)
    first_disorder = next(
        (i for i in range(1, len(dates)) if dates[i] < dates[i - 1]), -1
    )
    assert dates == sorted_dates, (
        "fechas no están en orden ascendente: "
        f"primer desorden alrededor del index {first_disorder}"
    )

    # First date must precede last date and the response's declared range.
    assert response.fecha_min == dates[0]
    assert response.fecha_max == dates[-1]
