"""Tests mínimos del motor (Paso 3a — escritos ANTES de tocar motor.py).

El contrato central es test_bit_identidad_homogenea: la ruta homogénea
(matriz_heterogenea=False) debe producir un df_ag bit-idéntico al de HEAD
en la adaptación a 5 estados y en cualquier cambio posterior. Si este
test falla, se rompió la línea base validada.
"""

from __future__ import annotations

import hashlib

import numpy as np

# sha256 de df_ag (columnas ordenadas, to_csv float %.17g) de la corrida
# canónica homogénea: 5,000 agentes iniciales (9,482 finales), escenario
# base, semilla de config, r_historico + indice_salarial observados.
# Calculado contra HEAD=cdc2c19 (motor.py intacto de 5a19e80) el
# 2026-07-04; determinismo verificado con doble corrida.
FINGERPRINT_HOMOGENEO = (
    "198608128bd1fc2d4a3db1f7d3ef953c13cc273061c52b96cbc7514ebecdaacd"
)


def _fingerprint(df) -> str:
    serial = df[sorted(df.columns)].to_csv(index=False, float_format="%.17g")
    return hashlib.sha256(serial.encode()).hexdigest()


def test_bit_identidad_homogenea(resultado_homogeneo):
    """La ruta homogénea es bit-idéntica a la línea base validada."""
    assert _fingerprint(resultado_homogeneo.agentes) == FINGERPRINT_HOMOGENEO


def test_tensor_row_stochastic_4x4():
    """Tensor v1 (4 estados): shape y filas estocásticas."""
    from asignacion_perfiles import construye_tensor
    from carga_matrices import cargar_matrices

    t4 = construye_tensor(cargar_matrices())
    assert t4.shape == (8, 2, 3, 4, 4)
    assert np.allclose(t4.sum(axis=-1), 1.0, atol=1e-9)


def test_tensor_row_stochastic_5x5():
    """Tensor anual (5 estados): shape, filas estocásticas, sin NaN."""
    from asignacion_perfiles import construye_tensor
    from carga_matrices import cargar_matrices_anuales

    t5 = construye_tensor(cargar_matrices_anuales())
    assert t5.shape == (8, 2, 3, 5, 5)
    assert not np.isnan(t5).any()
    assert np.allclose(t5.sum(axis=-1), 1.0, atol=1e-9)


def test_contabilidad(resultado_homogeneo):
    """ΔS = A + R - C - salidas, año a año sobre el ledger agregado.

    El check por agente ya corre dentro de simular() (ContabilidadError);
    aquí se fija como test la identidad agregada del ledger.
    """
    ledger = resultado_homogeneo.ledger
    assert (ledger["check_contable"] == "OK").all()
    saldo = ledger["saldo_total_mm"].to_numpy()
    flujo = (
        ledger["aportaciones_mm"]
        + ledger["rendimientos_mm"]
        - ledger["comisiones_mm"]
        - ledger["salidas_retiro_mm"]
        - ledger["salidas_muerte_mm"]
    ).to_numpy()
    delta = np.diff(saldo, prepend=0.0)
    np.testing.assert_allclose(delta, flujo, rtol=1e-9, atol=1e-6)
