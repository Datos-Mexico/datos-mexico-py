"""Integration test suite — runs against the live Datos Mexico API.

Gated by the ``DATOS_MEXICO_INTEGRATION_TESTS=1`` environment variable.
Run with::

    DATOS_MEXICO_INTEGRATION_TESTS=1 pytest tests/integration/

Each test is decorated with ``@pytest.mark.integration`` so it can be
selected (or excluded) explicitly:

    pytest tests/ -m "not integration"   # CI default — pure unit tests
    pytest tests/ -m integration         # only integration
"""
