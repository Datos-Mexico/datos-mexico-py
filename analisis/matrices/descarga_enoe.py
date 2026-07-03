"""Descarga sdem 2024T3 y 2024T4 a parquet (cache local, paralelo por entidad)."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from datos_mexico import DatosMexico

SCRATCH = Path(__file__).parent
KEEP = [
    "cd_a", "ent", "con", "v_sel", "n_hog", "n_ren",
    "sex", "eda", "clase1", "clase2", "imssissste", "fac_tri",
    "c_res", "r_def", "anios_esc", "niv_ins", "cs_p13_1",
]
VERSION = "v2"
ENTIDADES = [f"{i:02d}" for i in range(1, 33)]


def descarga_entidad(periodo: str, ent: str) -> list[dict]:
    filas = []
    with DatosMexico(timeout=120.0) as client:
        for row in client.enoe.microdatos_iter(
            "sdem", periodo=periodo, entidad_clave=ent, include_extras=True
        ):
            extras = row.get("extras_jsonb") or {}
            rec = {k: row.get(k) for k in KEEP}
            rec["h_mud"] = extras.get("h_mud")
            filas.append(rec)
    return filas


def descarga_trimestre(periodo: str) -> pd.DataFrame:
    out = SCRATCH / f"sdem_{periodo}_{VERSION}.pkl"
    if out.exists():
        print(f"[cache] {out}")
        return pd.read_pickle(out)
    todas: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(descarga_entidad, periodo, e): e for e in ENTIDADES}
        for fut in as_completed(futs):
            ent = futs[fut]
            filas = fut.result()
            todas.extend(filas)
            print(f"  {periodo} ent={ent}: {len(filas)} filas (acum {len(todas)})", flush=True)
    df = pd.DataFrame(todas)
    df.to_pickle(out)
    print(f"[guardado] {out}: {len(df)} filas")
    return df


if __name__ == "__main__":
    for t in ("2024T3",):
        df = descarga_trimestre(t)
        print(t, df.shape)
    print("descarga completa")
