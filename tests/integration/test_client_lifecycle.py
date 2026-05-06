"""Lifecycle of the :class:`DatosMexico` entry point against the live API.

Covers:

- ``with DatosMexico() as c: ...`` closes resources cleanly.
- Explicit ``close()`` is idempotent and disables further use.
- Multiple instances configured differently do not share state.
- The default User-Agent header is the canonical
  ``datos-mexico-py/{version} (https://datosmexico.org)`` string.
"""

from __future__ import annotations

import pytest

from datos_mexico import DatosMexico
from datos_mexico._constants import USER_AGENT
from datos_mexico._version import __version__

pytestmark = pytest.mark.integration


def test_context_manager_cleans_up(api_healthy: bool) -> None:
    """After a ``with`` block, the underlying httpx.Client is closed."""
    assert api_healthy
    with DatosMexico() as c:
        result = c.health()
        assert result.status == "ok"
    # After exit, the underlying httpx Client should be closed.
    # Issuing another request must raise (httpx raises RuntimeError on closed
    # clients; we accept any error type — what matters is "doesn't silently
    # succeed").
    with pytest.raises(Exception):  # noqa: B017 (broad, intentional sentinel)
        c.health()


def test_explicit_close_is_idempotent(api_healthy: bool) -> None:
    """``close()`` must be idempotent (safe to call twice)."""
    assert api_healthy
    c = DatosMexico()
    assert c.health().status == "ok"
    c.close()
    c.close()  # second call should not raise
    with pytest.raises(Exception):  # noqa: B017
        c.health()


def test_multiple_instances_independent(api_healthy: bool) -> None:
    """Two instances with different configs do not share state.

    We use very different cache TTLs and verify each one's cache reflects
    its own configuration.
    """
    assert api_healthy
    with DatosMexico(cache_ttl=600) as a, DatosMexico(cache_ttl=10) as b:
        a.cdmx.dashboard_stats()
        b.cdmx.dashboard_stats()
        # Each client owns an isolated cache instance.
        assert a._http.cache is not b._http.cache
        assert len(a._http.cache) >= 1
        assert len(b._http.cache) >= 1
        # Mutating one cache must not affect the other.
        a.clear_cache()
        assert len(a._http.cache) == 0
        assert len(b._http.cache) >= 1


def test_default_user_agent_present(api_healthy: bool) -> None:
    """The configured User-Agent contains the package version and homepage."""
    assert api_healthy
    expected = f"datos-mexico-py/{__version__} (https://datosmexico.org)"
    assert expected == USER_AGENT
    # Verify that an actual request reuses this UA via the configured
    # httpx.Client headers (the client header is the source of truth).
    with DatosMexico() as c:
        ua = c._http._client.headers.get("User-Agent")
        assert ua == USER_AGENT
        assert "datos-mexico-py/" in ua
        assert "https://datosmexico.org" in ua
