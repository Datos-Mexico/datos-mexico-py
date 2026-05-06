"""Fixtures and shared constants for the integration test suite.

All tests in ``tests/integration/`` are gated:

1. Skipped unless ``DATOS_MEXICO_INTEGRATION_TESTS=1``.
2. Skipped if the API is unreachable / returns non-200 on ``/health``
   (fail-fast — one health probe per session, not per test).
3. Marked with ``@pytest.mark.integration`` for explicit ``-m`` selection.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from decimal import Decimal

import httpx
import pytest

from datos_mexico import DatosMexico
from datos_mexico._constants import DEFAULT_BASE_URL

# ---------------------------------------------------------------------------
# Tolerances for accounting / consistency assertions
# ---------------------------------------------------------------------------

#: SAR identity: |sar_total_mm (componentes) - total_sistema_mm (afores)| / x
TOLERANCE_SAR_IDENTITY: Decimal = Decimal("0.01")

#: Sum of household counts across deciles vs national total
TOLERANCE_HOGARES_DECIL: Decimal = Decimal("0.0001")

#: Sum of expenditure-rubro percentages should be ~100%
TOLERANCE_PCT_SUM: Decimal = Decimal("0.5")

#: pct_sistema across AFOREs should sum to ~100%
TOLERANCE_PCT_SISTEMA: Decimal = Decimal("0.5")


# ---------------------------------------------------------------------------
# Session-scoped enablement / health probe
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def integration_enabled() -> bool:
    """Whether integration tests are enabled via env var."""
    return os.environ.get("DATOS_MEXICO_INTEGRATION_TESTS") == "1"


@pytest.fixture(scope="session")
def api_healthy(integration_enabled: bool) -> bool:
    """Verify the API responds 200 on /health before running any tests.

    Skips the entire integration session if the env var is unset or the
    API is unreachable. One probe per session.
    """
    if not integration_enabled:
        pytest.skip("DATOS_MEXICO_INTEGRATION_TESTS not set; skipping integration suite")
    try:
        response = httpx.get(f"{DEFAULT_BASE_URL}/health", timeout=10.0)
    except httpx.RequestError as exc:
        pytest.skip(f"API unreachable: {type(exc).__name__}: {exc}")
    if response.status_code != 200:
        pytest.skip(f"API not healthy: HTTP {response.status_code}")
    return True


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(api_healthy: bool) -> Generator[DatosMexico, None, None]:
    """Fresh :class:`DatosMexico` instance for each test (not shared).

    ``max_retries`` is bumped above the default to absorb transient 429s
    that can appear when the integration suite is run in a tight loop
    against the live API (CI does not exercise this path; humans running
    locally may).
    """
    assert api_healthy
    with DatosMexico(max_retries=6) as c:
        yield c


@pytest.fixture(scope="session")
def shared_client(api_healthy: bool) -> Generator[DatosMexico, None, None]:
    """Session-scoped client. Useful for cache-related tests where state
    must persist across multiple ``cache.get(...)`` checks within one test
    or across closely related tests in the same module.
    """
    assert api_healthy
    with DatosMexico(max_retries=6) as c:
        yield c
