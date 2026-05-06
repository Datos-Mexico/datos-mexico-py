"""Constantes compartidas del cliente datos-mexico."""

from __future__ import annotations

from datos_mexico._version import __version__

DEFAULT_BASE_URL: str = "https://api.datos-itam.org"
DEFAULT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_CACHE_TTL_SECONDS: int = 300
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_BACKOFF_BASE: float = 1.0
DEFAULT_RETRY_BACKOFF_MAX: float = 30.0

USER_AGENT: str = f"datos-mexico-py/{__version__} (https://datosmexico.org)"

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})

RETRYABLE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})
