"""Cache en memoria con TTL configurable.

Implementa una caché thread-safe basada en un diccionario con timestamps
de expiración. El usuario del paquete normalmente no instancia ``TTLCache``
directamente: el ``HttpClient`` lo usa internamente para cachear respuestas
``GET``.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    """Caché thread-safe con expiración por TTL.

    Args:
        ttl_seconds: Tiempo de vida de las entradas en segundos. Si es ``0``
            la caché queda deshabilitada: ``set`` no almacena nada y ``get``
            siempre devuelve ``None``. Debe ser ``>= 0``.

    Raises:
        ValueError: Si ``ttl_seconds`` es negativo.

    Examples:
        >>> cache = TTLCache(ttl_seconds=60)
        >>> cache.set("key", {"value": 1})
        >>> cache.get("key")
        {'value': 1}
        >>> cache_disabled = TTLCache(ttl_seconds=0)
        >>> cache_disabled.set("key", "value")
        >>> cache_disabled.get("key") is None
        True
    """

    def __init__(self, ttl_seconds: int) -> None:
        if ttl_seconds < 0:
            raise ValueError(f"ttl_seconds must be >= 0, got {ttl_seconds}")
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @property
    def ttl_seconds(self) -> int:
        """TTL configurado, en segundos."""
        return self._ttl

    @property
    def enabled(self) -> bool:
        """True si la caché está activa (``ttl_seconds > 0``)."""
        return self._ttl > 0

    def get(self, key: str) -> Any | None:
        """Recupera el valor asociado a ``key`` si no expiró.

        Si la entrada expiró, se elimina y se devuelve ``None``.

        Args:
            key: Clave a consultar.

        Returns:
            Valor cacheado, o ``None`` si no existe o expiró.
        """
        if not self.enabled:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        """Almacena ``value`` bajo ``key`` con expiración relativa al TTL.

        Si la caché está deshabilitada (``ttl_seconds == 0``), la operación
        es un no-op.
        """
        if not self.enabled:
            return
        expires_at = time.monotonic() + self._ttl
        with self._lock:
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        """Elimina todas las entradas de la caché."""
        with self._lock:
            self._store.clear()

    def clear_expired(self) -> int:
        """Elimina las entradas expiradas y devuelve cuántas se eliminaron."""
        if not self.enabled:
            return 0
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (exp, _) in self._store.items() if exp <= now]
            for k in expired:
                del self._store[k]
            return len(expired)

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self.get(key) is not None
