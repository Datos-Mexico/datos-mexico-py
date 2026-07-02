"""Carga de insumos del motor.

- Estáticos locales: tabla de mortalidad CNSF EMSSA-09 y proyecciones CONAPO
  (ver motor/data/README.md para fuentes y fecha de descarga).
- Vía SDK datos-mexico (api.datos-itam.org): agregados CONSAR observados
  para la validación 2025 y participaciones ENOE para la matriz de Markov.
  Con fallback estático (valores consultados 2026-07-01) para correr offline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def cargar_mortalidad() -> pd.DataFrame:
    """Tabla EMSSA-09: columnas edad, qx_hombres, qx_mujeres (0-109)."""
    df = pd.read_csv(DATA_DIR / "cnsf_emssa09_mortalidad.csv")
    assert df["edad"].tolist() == list(range(110)), "tabla EMSSA incompleta"
    return df


def qx_por_sexo(df_mort: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "H": df_mort["qx_hombres"].to_numpy(),
        "M": df_mort["qx_mujeres"].to_numpy(),
    }


def cargar_conapo() -> pd.DataFrame:
    """Proyecciones CONAPO nacionales 2025-2070 por edad simple y sexo."""
    df = pd.read_csv(DATA_DIR / "conapo_proyecciones_nacional_2025_2070.csv")
    df["sexo"] = df["sexo"].map({"Hombres": "H", "Mujeres": "M"})
    return df


# ---------------------------------------------------------------------------
# Targets de validación 2025 (CONSAR vía SDK, con fallback estático).
# ---------------------------------------------------------------------------

# Valores observados consultados en vivo el 2026-07-01 (api.datos-itam.org):
_FALLBACK_TARGETS = {
    # RCV-IMSS dic-2025, millones MXN corrientes (consar.recursos_composicion)
    "rcv_imss_mm": 6_891_289.59,
    # Cotizantes 2024 (consar.pea_cotizantes_serie, último punto)
    "cotizantes": 29_119_328,
    # Total cuentas SAR dic-2025 (consar.cuentas_sistema total_cuentas_sar)
    "cuentas_totales": 77_772_954,
}

# Participaciones ENOE 2025T1 (client.enoe.snapshot_nacional):
_FALLBACK_ENOE = {
    "pob_15ymas": 101_527_324.0,
    "ocupados_total": 58_921_494.0,
    "desocupados_total": 1_483_994.0,
    "informales_total": 32_104_097.0,
}


def targets_validacion(usar_api: bool = True) -> dict:
    """Agregados observados 2025 contra los que valida el motor."""
    targets = dict(_FALLBACK_TARGETS)
    targets["fuente"] = "fallback estático (consultado 2026-07-01)"
    if not usar_api:
        return targets
    try:
        from datos_mexico import DatosMexico

        with DatosMexico() as client:
            comp = client.consar.recursos_composicion("2025-12-01")
            for item in comp.componentes:
                if item.tipo_codigo == "rcv_imss":
                    targets["rcv_imss_mm"] = float(item.monto_mxn_mm)
            pea = client.consar.pea_cotizantes_serie()
            targets["cotizantes"] = int(pea.serie[-1].cotizantes)
            cuentas = client.consar.cuentas_sistema(metrica="total_cuentas_sar")
            targets["cuentas_totales"] = int(cuentas.serie[-1].valor)
            targets["fuente"] = "client.consar en vivo (api.datos-itam.org)"
    except Exception as exc:  # noqa: BLE001 — offline es caso esperado
        targets["fuente"] = f"fallback estático (API no disponible: {exc})"
    return targets


def participaciones_enoe(usar_api: bool = True) -> dict[str, float]:
    """Participaciones {formal, informal, desempleado, fuera} de la población 15+.

    Derivadas del snapshot nacional ENOE 2025T1: formal = ocupados - informales.
    """
    vals = dict(_FALLBACK_ENOE)
    if usar_api:
        try:
            from datos_mexico import DatosMexico

            with DatosMexico() as client:
                snap = client.enoe.snapshot_nacional(periodo="2025T1")
                for ind in snap.indicadores:
                    if ind.indicador in vals:
                        vals[ind.indicador] = float(ind.valor)
        except Exception:  # noqa: BLE001
            pass
    pob = vals["pob_15ymas"]
    formales = vals["ocupados_total"] - vals["informales_total"]
    return {
        "formal": formales / pob,
        "informal": vals["informales_total"] / pob,
        "desempleado": vals["desocupados_total"] / pob,
        "fuera": 1.0
        - (vals["ocupados_total"] + vals["desocupados_total"]) / pob,
    }
