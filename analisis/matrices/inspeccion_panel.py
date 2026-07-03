"""Inspección panel ENOE 2024T3→2024T4 para matrices de transición (Sección 6, Brecha 2).

Solo reporta: columnas, frecuencias, tasa de emparejamiento, checks de
consistencia y test de attrition. No estima nada.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SCRATCH = Path(__file__).parent
REQUERIDAS = [
    "cd_a", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren",
    "sex", "eda", "clase1", "clase2", "imssissste", "fac_tri",
]
LLAVE = ["cd_a", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren"]


def freq(df: pd.DataFrame, col: str) -> pd.DataFrame:
    sin = df[col].value_counts(dropna=False).rename("n")
    con = df.groupby(col, dropna=False)["fac_tri"].sum().rename("pond")
    out = pd.concat([sin, con], axis=1).fillna(0)
    out["pct_sin"] = 100 * out["n"] / out["n"].sum()
    out["pct_pond"] = 100 * out["pond"] / out["pond"].sum()
    return out.sort_index(na_position="last").round(2)


def estado_laboral(df: pd.DataFrame) -> pd.Series:
    """Mapeo PROVISIONAL a los 4 estados del contrato (Opción B: ISSSTE→formal_IMSS).

    formal_IMSS : ocupado (clase1=1, clase2=1) con imssissste ∈ {1,2,3}
    informal    : ocupado sin esa cobertura (incl. 4=otro, NA)
    desempleado : clase1=1, clase2=2
    fuera_PEA   : clase1=2 (y cualquier otro residuo)
    """
    est = pd.Series("fuera_PEA", index=df.index)
    pea = df["clase1"] == 1
    ocupado = pea & (df["clase2"] == 1)
    est[pea & (df["clase2"] == 2)] = "desempleado"
    est[ocupado] = "informal"
    est[ocupado & df["imssissste"].isin([1, 2, 3])] = "formal_IMSS"
    return est


def main() -> None:
    t3 = pd.read_pickle(SCRATCH / "sdem_2024T3.pkl")
    t4 = pd.read_pickle(SCRATCH / "sdem_2024T4.pkl")

    for nombre, df in (("2024T3", t3), ("2024T4", t4)):
        print(f"\n{'='*70}\n{nombre}: {len(df)} filas")
        print("\n-- Presencia y dtype de columnas requeridas --")
        for c in REQUERIDAS:
            if c in df.columns:
                nn = df[c].isna().sum()
                print(f"  {c:12s} {str(df[c].dtype):10s} NA={nn}")
            else:
                print(f"  {c:12s} *** AUSENTE ***")
        for col in ("clase1", "clase2", "imssissste"):
            print(f"\n-- Frecuencias {col} ({nombre}) --")
            print(freq(df, col).to_string())
        print(f"\n-- Contexto: r_def ({nombre}) --")
        print(df["r_def"].value_counts(dropna=False).to_string())
        print(f"\n-- Contexto: c_res ({nombre}) --")
        print(df["c_res"].value_counts(dropna=False).to_string())

    # ---- llave y merge ----
    print(f"\n{'='*70}\nMERGE 2024T3 -> 2024T4")
    for nombre, df in (("T3", t3), ("T4", t4)):
        df["llave"] = df[LLAVE].astype(str).agg("|".join, axis=1)
        dup = df["llave"].duplicated(keep=False).sum()
        print(f"  llaves duplicadas en {nombre}: {dup} filas "
              f"({100*dup/len(df):.3f}%)")

    m = t3.merge(t4, on="llave", how="inner", suffixes=("_t3", "_t4"))
    print(f"\n  filas T3: {len(t3)}  filas T4: {len(t4)}")
    print(f"  emparejadas: {len(m)}  tasa: {100*len(m)/len(t3):.2f}% de T3")

    # ---- checks de consistencia ----
    sex_mal = (m["sex_t3"] != m["sex_t4"]).sum()
    print(f"\n  sex NO coincide: {sex_mal} ({100*sex_mal/len(m):.2f}%)")
    deda = m["eda_t4"] - m["eda_t3"]
    retro = (deda < 0).sum()
    salta = (deda > 1).sum()
    print(f"  eda retrocede (<0): {retro} ({100*retro/len(m):.2f}%)")
    print(f"  eda salta >1: {salta} ({100*salta/len(m):.2f}%)")
    print(f"  distribución delta-eda:\n{deda.value_counts().sort_index().head(12).to_string()}")

    # ---- test de attrition ----
    print(f"\n{'='*70}\nTEST DE ATTRITION (shares ponderados con fac_tri de T3)")
    t3["estado"] = estado_laboral(t3)
    m["estado_t3"] = estado_laboral(
        m.rename(columns={c + "_t3": c for c in
                          ("clase1", "clase2", "imssissste")})
    )
    corte = t3.groupby("estado")["fac_tri"].sum()
    corte = 100 * corte / corte.sum()
    panel = m.groupby("estado_t3")["fac_tri_t3"].sum()
    panel = 100 * panel / panel.sum()
    cmp = pd.DataFrame({"corte_T3_%": corte, "panel_emparejado_%": panel})
    cmp["dif_pp"] = cmp["panel_emparejado_%"] - cmp["corte_T3_%"]
    print(cmp.round(2).to_string())


if __name__ == "__main__":
    main()
