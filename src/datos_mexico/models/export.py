"""Modelos para el namespace ``export``.

El endpoint ``GET /api/v1/export/csv`` devuelve **texto CSV crudo**
(``text/csv``), no JSON, a pesar de que el OpenAPI spec lo declare
como ``application/json``. Por eso este namespace no tiene un modelo
Pydantic de "response": el método ``ExportNamespace.csv()`` devuelve
``str`` directamente con el contenido CSV listo para escribir a
archivo o pasar a ``csv.reader`` / ``pandas.read_csv``.
"""

from __future__ import annotations

__all__: list[str] = []
