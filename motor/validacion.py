"""Validación 2025: agregados simulados vs observados (brief §5).

La bisagra de credibilidad: el motor debe reproducir el presente antes de
proyectar 45 años. Compara contra CONSAR vía client.consar (con fallback
estático documentado en datos.py).
"""

from __future__ import annotations

import pandas as pd

from motor.datos import targets_validacion


def comparar(validacion_sim: dict, usar_api: bool = True) -> pd.DataFrame:
    """Tabla simulado vs observado con razón sim/obs por métrica."""
    obs = targets_validacion(usar_api=usar_api)
    filas = [
        {
            "metrica": "Saldo RCV-IMSS (billones MXN)",
            "simulado": validacion_sim["saldo_rcv_simulado_mm"] / 1e6,
            "observado": obs["rcv_imss_mm"] / 1e6,
        },
        {
            "metrica": "Cotizantes (millones)",
            "simulado": validacion_sim["cotizantes_simulados"] / 1e6,
            "observado": obs["cotizantes"] / 1e6,
        },
        {
            "metrica": "Cuentas con saldo (millones)",
            "simulado": validacion_sim["cuentas_simuladas"] / 1e6,
            "observado": obs["cuentas_totales"] / 1e6,
        },
    ]
    df = pd.DataFrame(filas)
    df["razon_sim_obs"] = df["simulado"] / df["observado"]
    df.attrs["fuente_observados"] = obs["fuente"]
    return df
