"""Excepciones del cliente datos-mexico.

Jerarquía:

    DatosMexicoError (base)
    ├── ConfigurationError      (problema de setup del cliente)
    ├── NetworkError            (problemas de red, DNS, SSL)
    │   └── TimeoutError        (timeout de request)
    ├── ApiError                (HTTP error 4xx/5xx)
    │   ├── BadRequestError         (400)
    │   ├── AuthenticationError     (401)
    │   ├── AuthorizationError      (403)
    │   ├── NotFoundError           (404)
    │   ├── RateLimitError          (429, con retry_after)
    │   └── ServerError             (5xx)
    └── ValidationError         (response no matchea Pydantic schema)
"""

from __future__ import annotations

from typing import Any


class DatosMexicoError(Exception):
    """Excepción base de la librería datos-mexico.

    Todas las demás excepciones del módulo heredan de esta clase. Capturarla
    permite manejar cualquier error originado por el cliente sin tener que
    enumerar las subclases.

    Examples:
        >>> from datos_mexico import DatosMexico, DatosMexicoError
        >>> client = DatosMexico()
        >>> try:
        ...     client.health()
        ... except DatosMexicoError as e:
        ...     print(f"El cliente falló: {e}")
    """


class ConfigurationError(DatosMexicoError):
    """Se lanza cuando hay un problema con la configuración del cliente.

    Ejemplos típicos: base_url inválida, timeout negativo, max_retries < 0.
    """


class NetworkError(DatosMexicoError):
    """Se lanza cuando ocurre un problema de red al contactar la API.

    Cubre fallos de DNS, errores de SSL, conexión rechazada y similares. No
    cubre respuestas HTTP de la API (eso es ``ApiError``).
    """


class TimeoutError(NetworkError):
    """Se lanza cuando una request excede el timeout configurado.

    Subclase de ``NetworkError``. Distinta de la ``TimeoutError`` built-in de
    Python: para evitar ambigüedad importarla siempre desde
    ``datos_mexico.exceptions`` o ``datos_mexico``.
    """


class ApiError(DatosMexicoError):
    """Se lanza cuando la API responde con un código HTTP de error.

    Cubre cualquier respuesta 4xx o 5xx que no tenga una subclase más
    específica. Los atributos de la instancia exponen los detalles necesarios
    para diagnosticar y reportar el error.

    Attributes:
        endpoint: Path relativo del endpoint que falló (ej. ``"/health"``).
        status_code: Código HTTP devuelto por la API.
        method: Método HTTP usado en la request (``"GET"``, ``"POST"``, ...).
        response_body: Cuerpo crudo de la respuesta cuando estaba disponible;
            ``None`` si no se pudo leer.
    """

    def __init__(
        self,
        endpoint: str,
        status_code: int,
        method: str = "GET",
        response_body: str | None = None,
        message: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        self.method = method
        self.response_body = response_body
        self._message = message
        super().__init__(self._render_message())

    def _render_message(self) -> str:
        base = f"{self.method} {self.endpoint} → HTTP {self.status_code}"
        if self._message:
            return f"{base}: {self._message}"
        return base

    def __str__(self) -> str:
        return self._render_message()


class BadRequestError(ApiError):
    """HTTP 400. La request enviada al servidor estaba mal formada."""


class AuthenticationError(ApiError):
    """HTTP 401. La API requiere autenticación y el cliente no la proveyó."""


class AuthorizationError(ApiError):
    """HTTP 403. El cliente está autenticado pero no tiene permisos."""


class NotFoundError(ApiError):
    """HTTP 404. El endpoint o recurso solicitado no existe."""


class RateLimitError(ApiError):
    """HTTP 429. El cliente ha excedido el rate limit del servidor.

    Si la respuesta incluye un header ``Retry-After``, su valor en segundos
    queda disponible en ``retry_after``. Cuando la cabecera no es parseable
    como entero, ``retry_after`` queda en ``None``.

    Attributes:
        retry_after: Segundos sugeridos para reintentar, o ``None`` si la
            API no envió cabecera ``Retry-After``.
    """

    def __init__(
        self,
        endpoint: str,
        status_code: int = 429,
        method: str = "GET",
        response_body: str | None = None,
        retry_after: int | None = None,
        message: str | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            endpoint=endpoint,
            status_code=status_code,
            method=method,
            response_body=response_body,
            message=message,
        )

    def _render_message(self) -> str:
        base = super()._render_message()
        if self.retry_after is not None:
            return f"{base} (retry_after={self.retry_after}s)"
        return base


class ServerError(ApiError):
    """HTTP 5xx. La API tuvo un error interno al procesar la request."""


class ValidationError(DatosMexicoError):
    """La respuesta de la API no coincide con el schema Pydantic esperado.

    Indica que la API y el cliente están desincronizados: la API cambió un
    campo o tipo, o el cliente fue actualizado con un schema incorrecto.

    Attributes:
        endpoint: Path del endpoint cuya respuesta no validó.
        pydantic_errors: Lista de errores devueltos por
            ``pydantic.ValidationError.errors()``, o estructura equivalente.
        raw_payload: Payload crudo recibido (para debugging).
    """

    def __init__(
        self,
        endpoint: str,
        pydantic_errors: list[dict[str, Any]],
        raw_payload: Any,
    ) -> None:
        self.endpoint = endpoint
        self.pydantic_errors = pydantic_errors
        self.raw_payload = raw_payload
        super().__init__(self._render_message())

    def _render_message(self) -> str:
        n = len(self.pydantic_errors)
        plural = "es" if n != 1 else ""
        return f"Validación fallida en {self.endpoint}: {n} error{plural}"

    def __str__(self) -> str:
        return self._render_message()
