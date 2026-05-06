"""Cache behavior across endpoints and across get/get_text.

Covers:

- Identical calls hit the cache (no second round-trip).
- Different endpoints have different cache keys (no collision).
- ``get()`` and ``get_text()`` for the same path live under separate
  cache keys (prefix ``GET:`` vs ``GET_TEXT:``).
- ``use_cache=False`` skips the cache.
- ``clear_cache()`` invalidates entries.
"""

from __future__ import annotations

import pytest

from datos_mexico import DatosMexico

pytestmark = pytest.mark.integration


def test_same_endpoint_cached(client: DatosMexico) -> None:
    """Two consecutive identical calls populate the cache once."""
    client.clear_cache()
    assert len(client._http.cache) == 0

    first = client.cdmx.dashboard_stats()
    after_first = len(client._http.cache)
    assert after_first == 1, f"expected 1 entry after first call, got {after_first}"

    second = client.cdmx.dashboard_stats()
    after_second = len(client._http.cache)
    assert after_second == 1, (
        f"expected cache to remain at 1 entry on cache hit, got {after_second}"
    )
    assert first.total_servidores == second.total_servidores


def test_different_endpoints_no_collision(client: DatosMexico) -> None:
    """Distinct endpoints produce distinct cache entries."""
    client.clear_cache()
    client.cdmx.dashboard_stats()
    client.consar.recursos_totales()
    client.enigh.hogares_summary()
    assert len(client._http.cache) == 3


def test_get_text_separate_cache_from_get(client: DatosMexico) -> None:
    """``get()`` and ``get_text()`` for the same path use distinct keys.

    We exercise this on ``/api/v1/dashboard/stats`` (returns JSON). After
    calling both, the cache must contain two entries: one under the
    ``GET:`` prefix (parsed dict) and one under ``GET_TEXT:`` (raw text).
    """
    path = "/api/v1/dashboard/stats"
    client.clear_cache()
    assert len(client._http.cache) == 0

    parsed = client._http.get(path)
    text = client._http.get_text(path)

    assert isinstance(parsed, dict)
    assert isinstance(text, str)
    assert len(client._http.cache) == 2, (
        f"expected 2 cache entries (GET + GET_TEXT), got {len(client._http.cache)}"
    )


def test_use_cache_false_skips_cache(client: DatosMexico) -> None:
    """``use_cache=False`` on ``HttpClient.get`` must not populate cache."""
    path = "/api/v1/dashboard/stats"
    client.clear_cache()
    client._http.get(path, use_cache=False)
    assert len(client._http.cache) == 0


def test_clear_cache_works(client: DatosMexico) -> None:
    """``clear_cache()`` removes all entries; subsequent calls re-fetch."""
    client.cdmx.dashboard_stats()
    assert len(client._http.cache) >= 1
    client.clear_cache()
    assert len(client._http.cache) == 0
    client.cdmx.dashboard_stats()
    assert len(client._http.cache) == 1


def test_export_csv_cache_under_get_text_prefix(client: DatosMexico) -> None:
    """``export.csv()`` populates the cache under the ``GET_TEXT:`` prefix.

    Uses a narrow filter so the response is small (~150 bytes).
    """
    client.clear_cache()
    client.export.csv(sector_id=1, edad_min=99, edad_max=120)
    keys = list(client._http.cache._store.keys())
    assert len(keys) == 1
    assert keys[0].startswith("GET_TEXT:"), (
        f"expected GET_TEXT prefix, got key={keys[0]!r}"
    )
