"""Cliente principal DatosMexico — punto de entrada del SDK."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

from datos_mexico._constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
)
from datos_mexico._http import HttpClient
from datos_mexico.models.base import HealthResponse


class DatosMexico:
    """Cliente oficial para la API del Observatorio Datos México.

    Examples:
        Uso básico:

            >>> from datos_mexico import DatosMexico
            >>> client = DatosMexico()
            >>> health = client.health()
            >>> print(health.status)
            ok

        Con context manager (recomendado, cierra recursos automáticamente):

            >>> with DatosMexico() as client:
            ...     health = client.health()

        Configuración personalizada:

            >>> client = DatosMexico(
            ...     timeout=60.0,
            ...     cache_ttl=600,
            ...     max_retries=5,
            ... )
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._http = HttpClient(
            base_url=base_url,
            timeout=timeout,
            cache_ttl=cache_ttl,
            max_retries=max_retries,
            user_agent=user_agent,
            logger=logger,
        )
        # Namespaces — placeholders. Implementados en sub-prompts siguientes.
        # self.cdmx = CdmxNamespace(self._http)
        # self.consar = ConsarNamespace(self._http)
        # self.enigh = EnighNamespace(self._http)
        # self.comparativo = ComparativoNamespace(self._http)

    def health(self) -> HealthResponse:
        """Consulta ``GET /health`` para verificar que la API responde.

        El endpoint health no se cachea: cada llamada ejecuta una request
        fresca al servidor.

        Returns:
            ``HealthResponse`` con el campo ``status`` (esperado: ``"ok"``).

        Raises:
            NetworkError: Si no se puede contactar la API.
            TimeoutError: Si la API no responde dentro del timeout.
            ApiError: Si la API responde con un status code de error.
        """
        raw = self._http.get("/health", use_cache=False)
        return HealthResponse.model_validate(raw)

    def _raw_get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Acceso directo a cualquier endpoint sin validación de tipos.

        Útil para llamar endpoints que aún no tienen wrapper tipado en el
        SDK, o para debugging.

        Examples:
            >>> client = DatosMexico()
            >>> data = client._raw_get("/api/v1/endpoint/no/tipado")

        Args:
            path: Path relativo del endpoint.
            params: Query string params.

        Returns:
            Payload JSON deserializado (``dict``, ``list``, ...).
        """
        return self._http.get(path, params=params)

    def clear_cache(self) -> None:
        """Vacía la caché interna del cliente HTTP."""
        self._http.clear_cache()

    def close(self) -> None:
        """Cierra los recursos subyacentes (conexiones HTTP). Idempotente."""
        self._http.close()

    def __enter__(self) -> DatosMexico:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
