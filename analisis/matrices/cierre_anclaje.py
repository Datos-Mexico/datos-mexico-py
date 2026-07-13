"""Cierre del diagnóstico de anclaje: benchmark ENOE 25-64 + estacionaria.

1. Shares 5 estados en microdatos ENOE 2025T1 (cache v3), universo del
   corte simulado: clase1 en {1,2}, r_def=0, c_res != 3, eda 25-64,
   ponderado fac_tri, mapeo del contrato (Opción A).
2. Estacionaria de la 5x5 agregada: promedio de los 48 perfiles ponderado
   por composición demográfica CONAPO 2025 (quinquenio x sexo, 25-64) x
   marginal de escolaridad ENOE por (sexo, grupo).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SCRATCH = Path(__file__).parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "analisis" / "matrices"))

import logging

logging.disable(logging.WARNING)

from asignacion_perfiles import GRUPOS_EDAD, marginal_escolaridad
from carga_matrices import ESTADOS_ANUALES, cargar_matrices_anuales

from motor.datos import cargar_conapo

# ---------------- 1. benchmark ENOE 2025T1, 25-64, 5 estados ----------------
df = pd.read_pickle(SCRATCH / "sdem_2025T1_v3.pkl")
for c in ["clase1", "clase2", "imssissste", "r_def", "c_res", "eda", "fac_tri"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
uni = df[df["clase1"].isin([1, 2]) & (df["r_def"] == 0) & (df["c_res"] != 3)
         & df["eda"].between(25, 64)].copy()

est = pd.Series(pd.NA, index=uni.index, dtype="object")
ocup = uni["clase2"] == 1
est[ocup & (uni["imssissste"] == 1)] = "formal_IMSS"
est[ocup & (uni["imssissste"] == 2)] = "formal_ISSSTE"
est[ocup & uni["imssissste"].isin([3, 4, 5])] = "informal"
est[uni["clase2"] == 2] = "desempleado"
est[uni["clase1"] == 2] = "fuera_PEA"
uni["estado"] = est
uni = uni.dropna(subset=["estado"])
w = uni.groupby("estado")["fac_tri"].sum()
enoe = (100 * w / w.sum()).reindex(ESTADOS_ANUALES)
print(f"benchmark ENOE 2025T1 25-64: n={len(uni):,} obs, "
      f"pob ponderada={w.sum() / 1e6:.1f}M")

# ---------------- 2. estacionaria de la 5x5 agregada -----------------------
conapo = cargar_conapo()
c25 = conapo[(conapo["anio"] == 2025) & conapo["edad"].between(25, 64)].copy()
c25["grupo_edad"] = pd.cut(c25["edad"], bins=range(25, 70, 5), right=False,
                           labels=GRUPOS_EDAD)
c25["sexo_motor"] = (c25["sexo"] == "M").astype(int)
pob = c25.groupby(["grupo_edad", "sexo_motor"], observed=True)["poblacion"].sum()

marg_esc = marginal_escolaridad()
matrices = cargar_matrices_anuales()

P_agg = np.zeros((5, 5))
w_tot = 0.0
for (g, sx), p_gs in pob.items():
    for ei, esc in enumerate(["basica-", "media_sup", "superior"]):
        w_perfil = p_gs * marg_esc.loc[(sx, g)].to_numpy(dtype=float)[ei]
        P_agg += w_perfil * matrices[(g, sx, esc)]
        w_tot += w_perfil
P_agg /= w_tot
assert np.allclose(P_agg.sum(axis=1), 1.0, atol=1e-9)

vals, vecs = np.linalg.eig(P_agg.T)
v = np.real(vecs[:, np.argmax(np.real(vals))])
estac = pd.Series(100 * v / v.sum(), index=ESTADOS_ANUALES)

# ---------------- tabla única ----------------------------------------------
sim2025 = pd.Series(
    {"formal_IMSS": 24.46, "formal_ISSSTE": 4.94, "informal": 39.96,
     "desempleado": 2.15, "fuera_PEA": 28.49}
).reindex(ESTADOS_ANUALES)

tabla = pd.DataFrame({
    "ENOE_25_64_%": enoe,
    "corte_sim_2025_%": sim2025,
    "estacionaria_%": estac,
})
tabla["dif_sim_vs_ENOE_pp"] = tabla["corte_sim_2025_%"] - tabla["ENOE_25_64_%"]
tabla["dif_estac_vs_ENOE_pp"] = tabla["estacionaria_%"] - tabla["ENOE_25_64_%"]
tabla["dif_sim_vs_estac_pp"] = tabla["corte_sim_2025_%"] - tabla["estacionaria_%"]
print("\n===== TABLA ÚNICA: benchmark correcto =====")
print(tabla.round(2).to_string())

# ---------------- anexar al CSV de auditoría -------------------------------
dest = REPO / "analisis/matrices/auditoria_anclaje.csv"
aud = pd.read_csv(dest)
nuevas = []
for e in ESTADOS_ANUALES:
    nuevas.append({
        "bloque": "4_benchmark_correcto", "categoria": e,
        "valor": round(sim2025[e], 3),                # corte simulado 2025
        "referencia": round(enoe[e], 3),              # ENOE 25-64
        "dif": round(sim2025[e] - enoe[e], 3),
        "estacionaria": round(estac[e], 3),
        "dif_estac_vs_enoe": round(estac[e] - enoe[e], 3),
    })
aud = pd.concat([aud, pd.DataFrame(nuevas)], ignore_index=True)
aud.to_csv(dest, index=False)
print(f"\nCSV actualizado: {dest} (+{len(nuevas)} filas, bloque "
      f"4_benchmark_correcto)")
