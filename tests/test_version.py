"""Test mínimo para validar que el paquete instala y la versión es accesible."""

from datos_mexico import __version__


def test_version_exists() -> None:
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
