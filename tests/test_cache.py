"""Tests del cache TTL en memoria."""

from __future__ import annotations

import threading
import time

import pytest

from datos_mexico._cache import TTLCache


def test_set_and_get_returns_value() -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", {"v": 1})
    assert cache.get("k") == {"v": 1}


def test_get_missing_returns_none() -> None:
    cache = TTLCache(ttl_seconds=60)
    assert cache.get("missing") is None


def test_expiration_evicts_entry() -> None:
    cache = TTLCache(ttl_seconds=1)
    cache.set("k", "v")
    assert cache.get("k") == "v"
    time.sleep(1.1)
    assert cache.get("k") is None
    assert len(cache) == 0


def test_disabled_cache_is_noop() -> None:
    cache = TTLCache(ttl_seconds=0)
    assert not cache.enabled
    cache.set("k", "v")
    assert cache.get("k") is None
    assert len(cache) == 0


def test_negative_ttl_raises() -> None:
    with pytest.raises(ValueError, match="ttl_seconds must be >= 0"):
        TTLCache(ttl_seconds=-1)


def test_clear_empties_cache() -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0


def test_clear_expired_removes_only_expired() -> None:
    cache = TTLCache(ttl_seconds=1)
    cache.set("old", "x")
    time.sleep(1.1)
    cache.set("new", "y")
    removed = cache.clear_expired()
    assert removed == 1
    assert cache.get("old") is None
    assert cache.get("new") == "y"


def test_clear_expired_disabled_returns_zero() -> None:
    cache = TTLCache(ttl_seconds=0)
    assert cache.clear_expired() == 0


def test_contains_operator() -> None:
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", "v")
    assert "k" in cache
    assert "missing" not in cache
    assert 42 not in cache  # type: ignore[operator]


def test_thread_safety_basic() -> None:
    cache = TTLCache(ttl_seconds=60)
    n_threads = 20
    n_writes = 100

    def worker(prefix: str) -> None:
        for i in range(n_writes):
            cache.set(f"{prefix}-{i}", i)

    threads = [
        threading.Thread(target=worker, args=(f"t{idx}",)) for idx in range(n_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(cache) == n_threads * n_writes
