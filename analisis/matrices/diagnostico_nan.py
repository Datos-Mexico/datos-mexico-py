"""Diagnóstico NaN en tasa de reemplazo (Paso 4) — solo caracterización.

Una corrida heterogénea, 5,000 agentes, semilla base. Caracteriza los
agentes con TR=NaN y cuadra la contabilidad cero/no-cero/NaN vs
pension_cero. Escribe analisis/matrices/diagnostico_nan.csv.
"""

import logging
from pathlib import Path

import pandas as pd
import yaml

from motor.datos import (
    cargar_conapo,
    cargar_indice_salarial_real,
    cargar_mortalidad,
    cargar_rendimientos_reales,
    participaciones_enoe,
    qx_por_sexo,
)
from motor.motor import simular

logging.basicConfig(level=logging.WARNING)

REPO = Path(__file__).resolve().parents[2]
cfg = yaml.safe_load((REPO / "motor/config.yaml").read_text())
assert cfg["simulacion"]["n_agentes"] == 5000

res = simular(
    cfg,
    cargar_conapo(),
    qx_por_sexo(cargar_mortalidad()),
    participaciones_enoe(usar_api=False),
    escenario="base",
    semilla=cfg["semilla"],
    r_historico=cargar_rendimientos_reales(),
    indice_salarial=cargar_indice_salarial_real(),
    matriz_heterogenea=True,
)
df = res.agentes
filas_csv = []


def bloque(nombre, series_dict, denom):
    print(f"\n===== {nombre} (denominador n={denom}) =====")
    for cat, n in series_dict.items():
        pct = 100 * n / denom if denom else float("nan")
        print(f"  {cat:<58s} n={n:>5d}  {pct:6.2f}%")
        filas_csv.append(
            {"bloque": nombre, "categoria": cat, "n": int(n),
             "pct": round(pct, 3), "denominador": denom}
        )


# ---------- 0. población total: dónde viven los NaN ----------
n_tot = len(df)
ret = df[df["cohorte_retiro"] >= 2026]
no_ret = df[df["cohorte_retiro"] == -1]
bloque("0_poblacion_total", {
    "agentes_totales": n_tot,
    "retirados_2026plus": len(ret),
    "sin_retirar_al_2070_muertos_pre_retiro": int((~no_ret["vivo_final"]).sum()),
    "sin_retirar_al_2070_vivos_menores_65": int(no_ret["vivo_final"].sum()),
    "nan_TR_en_retirados": int(ret["tasa_reemplazo"].isna().sum()),
    "nan_TR_en_no_retirados": int(no_ret["tasa_reemplazo"].isna().sum()),
}, n_tot)

# ---------- 2. caracterización de los NaN entre retirados 2026+ ----------
nan_ret = ret[ret["tasa_reemplazo"].isna()]
n_nan = len(nan_ret)

bloque("2a_nan_estado_laboral_al_retiro",
       nan_ret["estado_final"].value_counts().to_dict(), n_nan)

bloque("2b_nan_semanas_cotizadas", {
    "semanas_igual_0_nunca_cotizo_IMSS": int((nan_ret["semanas_cotizadas"] == 0).sum()),
    "semanas_mayor_0_cotizo_algo": int((nan_ret["semanas_cotizadas"] > 0).sum()),
    "anios_formal_igual_0": int((nan_ret["anios_formal"] == 0).sum()),
}, n_nan)

bloque("2c_nan_saldo_y_pension", {
    "pension_mayor_0": int((nan_ret["pension_mensual"] > 0).sum()),
    "pension_igual_0": int((nan_ret["pension_mensual"] == 0).sum()),
    "saldo_final_mayor_0": int((nan_ret["saldo_final"] > 0).sum()),
    "pension_mayor_0_y_salario_ref_indefinido": int(
        ((nan_ret["pension_mensual"] > 0) & (nan_ret["anios_formal"] == 0)).sum()
    ),
    "sector_issste_True": int(nan_ret["sector_issste"].sum()),
    "sector_issste_False": int((~nan_ret["sector_issste"]).sum()),
}, n_nan)

perfil = (
    nan_ret.groupby(["genero", "escolaridad"]).size().sort_values(ascending=False)
)
bloque("2d_nan_perfil_genero_escolaridad",
       {f"{g}_{e}": v for (g, e), v in perfil.items()}, n_nan)

# entre los NaN, comparar share ISSSTE vs retirados no-NaN (contexto)
no_nan_ret = ret[ret["tasa_reemplazo"].notna()]
bloque("2e_contexto_issste_retirados_no_nan", {
    "sector_issste_True": int(no_nan_ret["sector_issste"].sum()),
    "sector_issste_False": int((~no_nan_ret["sector_issste"]).sum()),
}, len(no_nan_ret))

# ---------- 3. contabilidad cero + no-cero + NaN = 100% ----------
tr = ret["tasa_reemplazo"]
n_ret = len(ret)
n_tr0 = int((tr == 0).sum())
n_trpos = int((tr > 0).sum())
n_trnan = int(tr.isna().sum())
n_p0 = int((ret["pension_mensual"] == 0).sum())
bloque("3_contabilidad_retirados_2026plus", {
    "TR_igual_0": n_tr0,
    "TR_mayor_0": n_trpos,
    "TR_NaN": n_trnan,
    "suma_tres_categorias": n_tr0 + n_trpos + n_trnan,
    "pension_igual_0": n_p0,
    "TR0_mas_NaN": n_tr0 + n_trnan,
    "pension_0_con_TR_mayor_0": int(((ret["pension_mensual"] == 0) & (tr > 0)).sum()),
    "pension_mayor_0_con_TR_0_o_NaN": int(
        ((ret["pension_mensual"] > 0) & ((tr == 0) | tr.isna())).sum()
    ),
}, n_ret)

print("\n===== 3bis: métricas como las reporta comparacion_paso4 =====")
print(f"  pct_pension_cero (sobre todos los retirados) = {100 * n_p0 / n_ret:.2f}%")
print(f"  pct_tasa_cero (sobre dropna, como el script)  = {100 * n_tr0 / (n_tr0 + n_trpos):.2f}%")
print(f"  pct_tasa_cero (sobre todos los retirados)     = {100 * n_tr0 / n_ret:.2f}%")
print(f"  pct_tasa_nan  (sobre todos los retirados)     = {100 * n_trnan / n_ret:.2f}%")
filas_csv.append({"bloque": "3bis_metricas_script", "categoria": "pct_pension_cero_sobre_todos",
                  "n": n_p0, "pct": round(100 * n_p0 / n_ret, 3), "denominador": n_ret})
filas_csv.append({"bloque": "3bis_metricas_script", "categoria": "pct_tasa_cero_sobre_dropna",
                  "n": n_tr0, "pct": round(100 * n_tr0 / (n_tr0 + n_trpos), 3),
                  "denominador": n_tr0 + n_trpos})
filas_csv.append({"bloque": "3bis_metricas_script", "categoria": "pct_tasa_nan_sobre_todos",
                  "n": n_trnan, "pct": round(100 * n_trnan / n_ret, 3), "denominador": n_ret})

dest = REPO / "analisis/matrices/diagnostico_nan.csv"
pd.DataFrame(filas_csv).to_csv(dest, index=False)
print(f"\nCSV: {dest}")
