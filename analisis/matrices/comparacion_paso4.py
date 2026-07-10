"""Paso 4: comparación distribucional homogénea (A) vs heterogénea (B).

5,000 agentes, horizonte completo 1997-2070, escenario base, 3 semillas por
régimen. Comparación de DISTRIBUCIONES (no trayectoria-a-trayectoria: el flag
consume draws extra del RNG). Métricas sobre la cohorte que se retira 2026+.
"""

import logging
import time
from pathlib import Path

import numpy as np
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

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

REPO = Path("/Users/andrebutron/datos-mexico/datos-mexico-py")
cfg = yaml.safe_load((REPO / "motor/config.yaml").read_text())
assert cfg["simulacion"]["n_agentes"] == 5000

qx = qx_por_sexo(cargar_mortalidad())
conapo = cargar_conapo()
part = participaciones_enoe(usar_api=False)
r_hist = cargar_rendimientos_reales()
ind_sal = cargar_indice_salarial_real()

SEMILLAS = [cfg["semilla"] + k for k in range(3)]
corridas = {}   # (regimen, semilla) -> df retirados
tiempos = {}

for regimen, flag in [("A_homogenea", False), ("B_heterogenea", True)]:
    for s in SEMILLAS:
        t0 = time.time()
        res = simular(
            cfg, conapo, qx, part, escenario="base", semilla=s,
            r_historico=r_hist, indice_salarial=ind_sal,
            matriz_heterogenea=flag,
        )
        dt = time.time() - t0
        tiempos[(regimen, s)] = dt
        df = res.agentes
        corridas[(regimen, s)] = df[df["cohorte_retiro"] >= 2026].copy()
        print(f"{regimen} semilla={s}: {dt:.1f}s, "
              f"{len(corridas[(regimen, s)])} retirados 2026+", flush=True)


def metricas(df: pd.DataFrame) -> dict:
    tr = df["tasa_reemplazo"]
    tr_val = tr.dropna()
    out = {
        "n_retirados": len(df),
        "pct_pension_cero": 100 * (df["pension_mensual"] == 0).mean(),
        "pct_tasa_cero": 100 * (tr_val == 0).mean(),
        "pct_tasa_nan": 100 * tr.isna().mean(),
    }
    for q in (10, 25, 50, 75, 90):
        out[f"tr_p{q}"] = tr_val.quantile(q / 100)
    d = df["densidad_cotizacion"]
    out["dens_media"] = d.mean()
    out["dens_mediana"] = d.median()
    out["pct_sem_lt_1000"] = 100 * (df["semanas_cotizadas"] < 1000).mean()
    return out


# ---- tabla por semilla (estabilidad) ----
filas = []
for (reg, s), df in corridas.items():
    filas.append({"regimen": reg, "semilla": s} | metricas(df))
tabla = pd.DataFrame(filas)
pd.set_option("display.width", 200)
print("\n===== MÉTRICAS POR SEMILLA (estabilidad) =====")
print(tabla.round(3).to_string(index=False))

print("\n===== PROMEDIO ENTRE SEMILLAS (A vs B) =====")
prom = tabla.drop(columns="semilla").groupby("regimen").agg(["mean", "std"])
print(prom.round(3).T.to_string())

# ---- desglose de ceros del régimen B por perfil ----
b = pd.concat([corridas[("B_heterogenea", s)] for s in SEMILLAS])
b["cero"] = b["pension_mensual"] == 0
print("\n===== RÉGIMEN B: masa en cero por (género, escolaridad) — 3 semillas apiladas =====")
g = (
    b.groupby(["genero", "escolaridad"])
    .agg(
        n_retirados=("cero", "size"),
        pct_cero_del_perfil=("cero", lambda x: 100 * x.mean()),
    )
    .reset_index()
)
tot_ceros = b["cero"].sum()
g["share_de_los_ceros"] = [
    100 * b[(b["genero"] == r.genero)
            & (b["escolaridad"] == r.escolaridad)]["cero"].sum() / tot_ceros
    for r in g.itertuples()
]
print(g.round(1).to_string(index=False))

print("\n===== RÉGIMEN B: masa en cero por década de retiro =====")
b["decada"] = (b["cohorte_retiro"] // 10) * 10
print(
    b.groupby("decada")["cero"].agg(n="size", pct_cero=lambda x: 100 * x.mean())
    .round(1).to_string()
)

print("\n===== TIEMPOS =====")
for (reg, s), dt in tiempos.items():
    print(f"  {reg} semilla={s}: {dt:.1f}s")
media_b = np.mean([dt for (r, _), dt in tiempos.items() if r.startswith("B")])
media_a = np.mean([dt for (r, _), dt in tiempos.items() if r.startswith("A")])
print(f"  media A={media_a:.1f}s  media B={media_b:.1f}s (5,000 agentes, 74 años)")

# ---- figura: histogramas superpuestos (step) A vs B ----
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

AZUL, AQUA = "#2a78d6", "#1baf7a"   # slots 1-2 paleta validada (dataviz)
TINTA, TINTA2 = "#0b0b0b", "#52514e"

a = pd.concat([corridas[("A_homogenea", s)] for s in SEMILLAS])
fig, axes = plt.subplots(2, 1, figsize=(9, 8), facecolor="#fcfcfb")

# panel 1: tasa de reemplazo (incluye el pico en cero)
ax = axes[0]
bins = np.arange(0.0, 1.55, 0.05)
for df, nombre, color in [(a, "Homogénea (A)", AZUL), (b, "Heterogénea (B)", AQUA)]:
    tr = df["tasa_reemplazo"].dropna().clip(upper=1.5)
    ax.hist(tr, bins=bins, density=True, histtype="step", lw=2, color=color,
            label=nombre)
    pct0 = 100 * (df["tasa_reemplazo"].dropna() == 0).mean()
    ax.annotate(f"{pct0:.1f}% en cero", xy=(0.02, ax.get_ylim()[1]),
                xytext=(0.12, ax.get_ylim()[1] * (0.92 if color == AZUL else 0.80)),
                color=TINTA, fontsize=10,
                arrowprops={"arrowstyle": "-", "color": color, "lw": 1.5})
ax.set_title("Tasa de reemplazo, retirados 2026+ (3 semillas apiladas, recorte en 1.5)",
             color=TINTA, fontsize=11, loc="left")
ax.set_xlabel("tasa de reemplazo", color=TINTA2)
ax.set_ylabel("densidad", color=TINTA2)

# panel 2: densidad de cotización
ax = axes[1]
bins = np.arange(0.0, 1.05, 0.04)
for df, nombre, color in [(a, "Homogénea (A)", AZUL), (b, "Heterogénea (B)", AQUA)]:
    ax.hist(df["densidad_cotizacion"], bins=bins, density=True, histtype="step",
            lw=2, color=color, label=nombre)
ax.set_title("Densidad de cotización (años formales / años activos)",
             color=TINTA, fontsize=11, loc="left")
ax.set_xlabel("densidad de cotización", color=TINTA2)
ax.set_ylabel("densidad", color=TINTA2)

for ax in axes:
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", color="#e5e4e0", lw=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA2)
    ax.tick_params(colors=TINTA2)
    ax.set_facecolor("#fcfcfb")

fig.tight_layout()
dest = REPO / "analisis/matrices/fig_comparacion_homogenea_heterogenea.png"
fig.savefig(dest, dpi=150, facecolor="#fcfcfb")
print(f"\nFigura: {dest}")
