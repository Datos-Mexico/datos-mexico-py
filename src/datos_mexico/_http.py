"""Cliente HTTP base con retries, cache, logging y manejo de errores."""

from __future__ import annotations

import logging
from json import JSONDecodeError
from types import TracebackType
from typing import Any
from urllib.parse import urlencode

import httpx
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from datos_mexico._cache import TTLCache
from datos_mexico._constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF_BASE,
    DEFAULT_RETRY_BACKOFF_MAX,
    DEFAULT_TIMEOUT_SECONDS,
    RETRYABLE_STATUS_CODES,
    USER_AGENT,
)
from datos_mexico.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)


def _classify_api_error(
    *,
    endpoint: str,
    method: str,
    status_code: int,
    response_body: str | None,
    retry_after: int | None,
) -> ApiError:
    """Selecciona la subclase de ``ApiError`` apropiada según el status."""
    if status_code == 400:
        return BadRequestError(endpoint, status_code, method, response_body)
    if status_code == 401:
        return AuthenticationError(endpoint, status_code, method, response_body)
    if status_code == 403:
        return AuthorizationError(endpoint, status_code, method, response_body)
    if status_code == 404:
        return NotFoundError(endpoint, status_code, method, response_body)
    if status_code == 429:
        return RateLimitError(
            endpoint=endpoint,
            status_code=status_code,
            method=method,
            response_body=response_body,
            retry_after=retry_after,
        )
    if 500 <= status_code < 600:
        return ServerError(endpoint, status_code, method, response_body)
    return ApiError(endpoint, status_code, method, response_body)


def _parse_retry_after(value: str | None) -> int | None:
    """Parsea un header ``Retry-After`` numérico. Devuelve ``None`` si no aplica."""
    if value is None:
        return None
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return None


class HttpClient:
    """Cliente HTTP síncrono con retries, cache en memoria y logging.

    Esta clase encapsula un ``httpx.Client`` y le agrega:

    - Reintentos exponenciales para errores de red transitorios y status
      codes 5xx/429 (sólo para métodos idempotentes).
    - Cache TTL en memoria para responses ``GET``.
    - Conversión de excepciones de ``httpx`` a la jerarquía propia del
      paquete (``NetworkError``, ``TimeoutError``, ``ApiError``).
    - Logging configurable.

    Args:
        base_url: URL base de la API (sin trailing slash).
        timeout: Timeout total por request en segundos.
        cache_ttl: TTL de la caché en segundos. ``0`` la deshabilita.
        max_retries: Número máximo de reintentos por request idempotente.
        user_agent: User-Agent custom. Si es ``None`` se usa el default
            ``datos-mexico-py/<version>``.
        logger: Logger custom. Si es ``None`` se usa
            ``logging.getLogger("datos_mexico")``.

    Raises:
        ConfigurationError: Si los parámetros numéricos están fuera de rango.
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
        if timeout <= 0:
            raise ConfigurationError(f"timeout must be > 0, got {timeout}")
        if max_retries < 0:
            raise ConfigurationError(f"max_retries must be >= 0, got {max_retries}")
        if cache_ttl < 0:
            raise ConfigurationError(f"cache_ttl must be >= 0, got {cache_ttl}")

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent or USER_AGENT
        self._logger = logger or logging.getLogger("datos_mexico")
        self._cache = TTLCache(ttl_seconds=cache_ttl)

        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "application/json",
            },
        )

    @property
    def base_url(self) -> str:
        """URL base configurada (sin trailing slash)."""
        return self._base_url

    @property
    def cache(self) -> TTLCache:
        """Acceso al cache subyacente. Útil para tests e introspección."""
        return self._cache

    def _build_url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _cache_key(
        self,
        url: str,
        params: dict[str, Any] | None,
        prefix: str = "GET",
    ) -> str:
        if not params:
            return f"{prefix}:{url}"
        encoded = urlencode(sorted(params.items()), doseq=True)
        return f"{prefix}:{url}?{encoded}"

    def _log_retry(self, retry_state: RetryCallState) -> None:
        attempt = retry_state.attempt_number
        outcome = retry_state.outcome
        if outcome is None:
            return
        if outcome.failed:
            exc = outcome.exception()
            self._logger.warning(
                "Retry %d after exception: %s", attempt, type(exc).__name__
            )
        else:
            response = outcome.result()
            if isinstance(response, httpx.Response):
                self._logger.warning(
                    "Retry %d after status %d for %s",
                    attempt,
                    response.status_code,
                    response.url,
                )

    def _send_with_retries(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        def _do_request() -> httpx.Response:
            self._logger.debug("%s %s params=%s", method, url, params)
            return self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
            )

        def _on_exhausted(retry_state: RetryCallState) -> httpx.Response:
            outcome = retry_state.outcome
            if outcome is None:  # pragma: no cover
                raise RuntimeError("retry exhausted without outcome")
            if outcome.failed:
                exc = outcome.exception()
                if exc is None:  # pragma: no cover
                    raise RuntimeError("outcome.failed but exception is None")
                raise exc
            response = outcome.result()
            assert isinstance(response, httpx.Response)
            return response

        retryer = Retrying(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(
                multiplier=DEFAULT_RETRY_BACKOFF_BASE,
                max=DEFAULT_RETRY_BACKOFF_MAX,
            ),
            retry=(
                retry_if_exception_type(httpx.RequestError)
                | retry_if_result(
                    lambda r: isinstance(r, httpx.Response)
                    and r.status_code in RETRYABLE_STATUS_CODES
                )
            ),
            reraise=True,
            before_sleep=self._log_retry,
            retry_error_callback=_on_exhausted,
        )
        result: httpx.Response = retryer(_do_request)
        return result

    def _convert_request_error(self, exc: httpx.RequestError, endpoint: str) -> NetworkError:
        if isinstance(exc, httpx.TimeoutException):
            return TimeoutError(f"Timeout en {endpoint}: {exc}")
        return NetworkError(f"Error de red en {endpoint}: {exc}")

    def _parse_json_or_raise(
        self,
        response: httpx.Response,
        *,
        endpoint: str,
        method: str,
    ) -> Any:
        try:
            return response.json()
        except (JSONDecodeError, ValueError) as exc:
            raise ApiError(
                endpoint=endpoint,
                status_code=response.status_code,
                method=method,
                response_body=response.text,
                message=f"Respuesta no es JSON válido: {exc}",
            ) from exc

    def _raise_for_status(
        self,
        response: httpx.Response,
        *,
        endpoint: str,
        method: str,
    ) -> None:
        if response.status_code < 400:
            return
        retry_after = _parse_retry_after(response.headers.get("Retry-After"))
        body = response.text or None
        self._logger.error(
            "%s %s failed: HTTP %d", method, endpoint, response.status_code
        )
        raise _classify_api_error(
            endpoint=endpoint,
            method=method,
            status_code=response.status_code,
            response_body=body,
            retry_after=retry_after,
        )

    def _execute_request(
        self,
        path: str,
        params: dict[str, Any] | None,
    ) -> httpx.Response:
        """Ejecuta GET con retries y raise-on-error. Devuelve el ``httpx.Response`` crudo.

        Helper compartido por ``get()`` y ``get_text()``: ejecuta el
        request con la lógica de retries, mapea las excepciones de
        ``httpx`` a la jerarquía propia y dispara la clasificación de
        errores HTTP. **No** hace cache ni parseo del body — eso lo
        decide el caller según el tipo de payload esperado.
        """
        url = self._build_url(path)
        try:
            response = self._send_with_retries("GET", url, params=params)
        except httpx.RequestError as exc:
            raise self._convert_request_error(exc, path) from exc
        self._raise_for_status(response, endpoint=path, method="GET")
        return response

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> Any:
        """Ejecuta un ``GET`` con retries, cache y manejo de errores.

        Args:
            path: Path relativo (con o sin slash inicial).
            params: Query string params.
            use_cache: Si ``True`` (default) consulta y popula la caché.

        Returns:
            Payload JSON deserializado (``dict``, ``list``, etc.).

        Raises:
            NetworkError: Falla de red persistente tras los reintentos.
            TimeoutError: Timeout persistente tras los reintentos.
            ApiError: La API respondió con un status 4xx/5xx no transitorio.
        """
        url = self._build_url(path)
        cache_key = (
            self._cache_key(url, params, prefix="GET") if use_cache else None
        )

        if cache_key is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._logger.info("Cache hit: %s", cache_key)
                return cached

        response = self._execute_request(path, params)
        payload = self._parse_json_or_raise(response, endpoint=path, method="GET")

        if cache_key is not None:
            self._cache.set(cache_key, payload)

        return payload

    def get_text(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> str:
        """Ejecuta un ``GET`` y devuelve el body crudo como ``str``, sin parseo JSON.

        Útil para endpoints que devuelven CSV, XML, plain text o cualquier
        otro content-type distinto de JSON. Reutiliza la misma lógica de
        retries, cache, logging y manejo de errores que :meth:`get`,
        omitiendo solo la deserialización JSON.

        El cache se almacena bajo un prefijo separado (``GET_TEXT:``) para
        no colisionar con :meth:`get` cuando el mismo path soporta ambas
        representaciones.

        Args:
            path: Path relativo (con o sin slash inicial).
            params: Query string params.
            use_cache: Si ``True`` (default) consulta y popula la caché.

        Returns:
            Body del response como ``str``.

        Raises:
            NetworkError: Falla de red persistente tras los reintentos.
            TimeoutError: Timeout persistente tras los reintentos.
            ApiError: La API respondió con un status 4xx/5xx no transitorio.

        Examples:
            >>> from datos_mexico._http import HttpClient
            >>> client = HttpClient()
            >>> csv_data = client.get_text("/api/v1/export/csv")
            >>> csv_data.startswith("id,nombre")
            True
        """
        url = self._build_url(path)
        cache_key = (
            self._cache_key(url, params, prefix="GET_TEXT") if use_cache else None
        )

        if cache_key is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._logger.info("Cache hit: %s", cache_key)
                assert isinstance(cached, str)
                return cached

        response = self._execute_request(path, params)
        text = response.text

        if cache_key is not None:
            self._cache.set(cache_key, text)

        return text

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Ejecuta un ``POST``. No se cachea ni se reintenta.

        Args:
            path: Path relativo (con o sin slash inicial).
            json: Payload a enviar como body JSON.

        Returns:
            Payload JSON deserializado.

        Raises:
            NetworkError: Falla de red al enviar la request.
            TimeoutError: Timeout al esperar respuesta.
            ApiError: La API respondió con un status 4xx/5xx.
        """
        url = self._build_url(path)
        try:
            self._logger.debug("POST %s", url)
            response = self._client.request(method="POST", url=url, json=json)
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Timeout en {path}: {exc}") from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"Error de red en {path}: {exc}") from exc

        self._raise_for_status(response, endpoint=path, method="POST")
        return self._parse_json_or_raise(response, endpoint=path, method="POST")

    def clear_cache(self) -> None:
        """Vacía la caché interna."""
        self._cache.clear()

    def close(self) -> None:
        """Cierra el ``httpx.Client`` subyacente. Idempotente."""
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
