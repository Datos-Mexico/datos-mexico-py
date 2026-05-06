"""Consistent error semantics across namespaces.

Covers:

- 404 from any namespace raises a subclass of :class:`DatosMexicoError`
  (specifically :class:`NotFoundError`).
- :class:`ValidationError` is raised with diagnostic info when the API
  returns a payload that does not match the expected schema. We
  exercise this with a respx-mocked response since we cannot make the
  live API return a malformed payload on demand.
- Decimal-typed fields are returned as ``Decimal`` (not float) and sum
  consistently across two different endpoints.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
import pytest
import respx

from datos_mexico import DatosMexico
from datos_mexico.exceptions import (
    DatosMexicoError,
    NotFoundError,
    ValidationError,
)

from .conftest import TOLERANCE_PCT_SISTEMA, TOLERANCE_PCT_SUM

pytestmark = pytest.mark.integration


def test_404_consistent_across_namespaces(client: DatosMexico) -> None:
    """A 404 from any namespace must raise a ``DatosMexicoError`` subclass.

    We don't hard-assert ``NotFoundError`` for every endpoint because some
    server-side handlers may return a different status code (e.g. CONSAR
    snapshots for a missing date). What matters is the SDK never leaks
    a raw ``httpx`` exception or returns a stub object.
    """
    cases: list[tuple[str, type[Exception], Exception | None]] = []

    # cdmx: a sector id that cannot exist
    try:
        client.cdmx.sector_stats(99_999_999)
    except DatosMexicoError as exc:
        cases.append(("cdmx.sector_stats(99_999_999)", type(exc), exc))
    else:
        pytest.fail("cdmx.sector_stats(99_999_999) did not raise")

    # personas: an id that cannot exist
    try:
        client.personas.get(999_999_999)
    except DatosMexicoError as exc:
        cases.append(("personas.get(999_999_999)", type(exc), exc))
    else:
        pytest.fail("personas.get(999_999_999) did not raise")

    # nombramientos: same
    try:
        client.nombramientos.get(999_999_999)
    except DatosMexicoError as exc:
        cases.append(("nombramientos.get(999_999_999)", type(exc), exc))
    else:
        pytest.fail("nombramientos.get(999_999_999) did not raise")

    # cdmx.servidor_detail: same
    try:
        client.cdmx.servidor_detail(999_999_999)
    except DatosMexicoError as exc:
        cases.append(("cdmx.servidor_detail(999_999_999)", type(exc), exc))
    else:
        pytest.fail("cdmx.servidor_detail(999_999_999) did not raise")

    # All four cases were ``DatosMexicoError`` subclasses.
    assert len(cases) == 4

    # At least one of them must be the canonical NotFoundError so we know
    # the classifier is wired up; if NONE are NotFoundError that is itself
    # a regression of error handling.
    assert any(issubclass(exc_type, NotFoundError) for _, exc_type, _ in cases), (
        "expected at least one NotFoundError across the 404 cases; "
        f"got types: {[t.__name__ for _, t, _ in cases]}"
    )


def test_validation_error_carries_diagnostics(api_healthy: bool) -> None:
    """``ValidationError`` exposes endpoint, pydantic_errors, raw_payload.

    We use respx to force a malformed payload — the live API would not
    return one on demand. The base_url goes through the in-memory mock,
    so this test does not consume a real API call.
    """
    assert api_healthy
    base = "https://api.test.local"
    with respx.mock, DatosMexico(base_url=base, max_retries=0, cache_ttl=0) as c:
        respx.get(f"{base}/api/v1/comparativo/bancarizacion").mock(
            return_value=httpx.Response(200, json={"definicion_operativa": "x"})
        )
        with pytest.raises(ValidationError) as exc_info:
            c.comparativo.bancarizacion()

    err = exc_info.value
    assert err.endpoint == "/api/v1/comparativo/bancarizacion"
    assert err.pydantic_errors, "pydantic_errors should be non-empty"
    assert err.raw_payload == {"definicion_operativa": "x"}


def test_decimal_format_validation_pcts_consistent(client: DatosMexico) -> None:
    """Percentages from two different endpoints are ``Decimal`` and sum coherently."""
    enigh_response = client.enigh.gastos_by_rubro()
    enigh_pcts = [r.pct_del_monetario for r in enigh_response.rubros]
    assert all(isinstance(p, Decimal) for p in enigh_pcts)
    enigh_total = sum(enigh_pcts, Decimal(0))
    assert abs(enigh_total - Decimal(100)) <= TOLERANCE_PCT_SUM, (
        f"ENIGH rubros pct sum: got {enigh_total}, expected ~100"
    )

    consar_response = client.consar.recursos_por_afore(fecha=date(2025, 6, 1))
    consar_pcts = [
        a.pct_sistema for a in consar_response.afores if a.pct_sistema is not None
    ]
    assert all(isinstance(p, Decimal) for p in consar_pcts)
    consar_total = sum(consar_pcts, Decimal(0))
    assert abs(consar_total - Decimal(100)) <= TOLERANCE_PCT_SISTEMA, (
        f"CONSAR pct_sistema sum: got {consar_total}, expected ~100"
    )
