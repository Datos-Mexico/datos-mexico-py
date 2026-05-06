"""Clase base para namespaces de endpoints (cdmx, consar, enigh, comparativo)."""

from __future__ import annotations

from typing import Any, TypeVar, cast

import pydantic

from datos_mexico._http import HttpClient
from datos_mexico.exceptions import ValidationError
from datos_mexico.models.base import DatosMexicoModel

T = TypeVar("T", bound=DatosMexicoModel)


class BaseNamespace:
    """Base para todos los namespaces de endpoints.

    Cada namespace (CDMX, CONSAR, ENIGH, ...) hereda de esta clase y agrega
    métodos específicos para los endpoints de su dominio. Los helpers
    ``_get``, ``_get_validated`` y ``_get_validated_list`` centralizan el
    patrón "request + validar contra Pydantic + envolver errores".
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET sin validación. Devuelve el payload crudo deserializado."""
        return self._http.get(path, params=params)

    def _get_validated(
        self,
        path: str,
        model: type[T],
        params: dict[str, Any] | None = None,
    ) -> T:
        """GET y validación contra ``model``.

        Raises:
            ValidationError: Si el payload no satisface el schema del modelo.
        """
        raw = self._http.get(path, params=params)
        try:
            return model.model_validate(raw)
        except pydantic.ValidationError as e:
            raise ValidationError(
                endpoint=path,
                pydantic_errors=cast(list[dict[str, Any]], list(e.errors())),
                raw_payload=raw,
            ) from e

    def _get_validated_list(
        self,
        path: str,
        model: type[T],
        params: dict[str, Any] | None = None,
    ) -> list[T]:
        """GET de un array y validación elemento a elemento.

        Raises:
            ValidationError: Si el payload no es lista o algún elemento no
                satisface el schema del modelo.
        """
        raw = self._http.get(path, params=params)
        if not isinstance(raw, list):
            raise ValidationError(
                endpoint=path,
                pydantic_errors=[
                    {"msg": f"Expected list, got {type(raw).__name__}"}
                ],
                raw_payload=raw,
            )
        try:
            return [model.model_validate(item) for item in raw]
        except pydantic.ValidationError as e:
            raise ValidationError(
                endpoint=path,
                pydantic_errors=cast(list[dict[str, Any]], list(e.errors())),
                raw_payload=raw,
            ) from e
