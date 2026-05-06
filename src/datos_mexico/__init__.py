"""datos-mexico: Cliente Python para la API del Observatorio Datos México."""

from datos_mexico._version import __version__
from datos_mexico.client import DatosMexico
from datos_mexico.exceptions import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConfigurationError,
    DatosMexicoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "BadRequestError",
    "ConfigurationError",
    "DatosMexico",
    "DatosMexicoError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    "__version__",
]
