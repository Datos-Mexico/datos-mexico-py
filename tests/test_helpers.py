"""Tests del helper _format_fecha."""

from __future__ import annotations

from datetime import date

import pytest

from datos_mexico._helpers import _format_fecha


def test_accepts_date() -> None:
    assert _format_fecha(date(2025, 6, 1)) == "2025-06-01"


def test_accepts_iso_string() -> None:
    assert _format_fecha("2025-06-01") == "2025-06-01"


def test_rejects_day_not_one_string() -> None:
    with pytest.raises(ValueError, match="día 01"):
        _format_fecha("2025-06-15")


def test_rejects_day_not_one_date() -> None:
    with pytest.raises(ValueError, match="día 01"):
        _format_fecha(date(2025, 6, 15))


def test_rejects_invalid_format() -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        _format_fecha("06/01/2025")


def test_rejects_invalid_type() -> None:
    with pytest.raises(TypeError, match="date o str"):
        _format_fecha(20250601)  # type: ignore[arg-type]
