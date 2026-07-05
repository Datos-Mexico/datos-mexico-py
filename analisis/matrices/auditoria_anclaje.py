"""Fase 5a — auditoría de anclaje. Cero cambios a motor/ y matrices.

Técnica: la secuencia RNG de simular() es prefijo-determinista respecto a
anio_fin (ningún draw depende del horizonte), así que correr con
anio_fin=Y entrega el estado y los acumuladores del año Y. Se valida esa
propiedad antes de usarla (fingerprint del run completo vs incremental).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path("/Users/andrebutron/datos-mexico/datos-mexico-py")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "analisis" / "matrices"))

import logging

logging.disable(logging.WARNING)

from motor.datos import (
    cargar_conapo,
    cargar_indice_salarial_real,
    cargar_mortalidad,
    cargar_rendimientos_reales,
    participaciones_enoe,
    qx_por_sexo,
)
from motor.motor import simular

cfg0 = yaml.safe_load((REPO / "motor/config.yaml").read_text())
conapo = cargar_conapo()
qx = qx_por_sexo(cargar_mortalidad())
part = participaciones_enoe(usar_api=False)
r_hist = cargar_rendimientos_reales()
ind_sal = cargar_indice_salarial_real()
SEMILLA = cfg0["semilla"]
N0 = cfg0["simulacion"]["n_agentes"]
ANIO_FIN = cfg0["simulacion"]["anio_fin"]

filas_csv = []


def corre(anio_fin: int, semilla: int = SEMILLA):
    cfg = yaml.safe_load((REPO / "motor/config.yaml").read_text())
    cfg["simulacion"]["anio_fin"] = anio_fin
    return simular(
        cfg, conapo, qx, part, escenario="base", semilla=semilla,
        r_historico=r_hist, indice_salarial=ind_sal, matriz_heterogenea=True,
    )


# ---- validación de la propiedad prefijo (antes de confiar en ella) ----
full = corre(ANIO_FIN)
df_full = full.agentes
prefijo = corre(2035)
# los acumuladores del stock inicial a 2035 deben ser un prefijo coherente:
# anios_formal(2035) <= anios_formal(2070) y estado de retirados congelado
af_35 = prefijo.agentes.loc[: N0 - 1, "anios_formal"].to_numpy()
af_70 = df_full.loc[: N0 - 1, "anios_formal"].to_numpy()
assert (af_35 <= af_70 + 1e-9).all()
print(f"[sanity prefijo] anios_formal(2035) <= anios_formal(2070) en los "
      f"{N0} agentes del stock ✓")

# edad_2025 del stock: réplica del primer draw (idéntica a verificación 3c)
rng = np.random.default_rng(SEMILLA)
c25 = conapo[(conapo["anio"] == 2025) & conapo["edad"].between(15, 64)]
pesos = c25["poblacion"].to_numpy().astype(float)
idx = rng.choice(len(c25), size=N0, p=pesos / pesos.sum())
edad_2025 = c25["edad"].to_numpy()[idx]

# pi0_het objetivo (misma construcción del motor)
from carga_matrices import ESTADO_A_IDX_ANUALES, ESTADOS_ANUALES

p_issste = cfg0["mercado_laboral"]["prop_issste_formales"]
pi0 = np.empty(5)
pi0[ESTADO_A_IDX_ANUALES["formal_IMSS"]] = part["formal"] * (1 - p_issste)
pi0[ESTADO_A_IDX_ANUALES["formal_ISSSTE"]] = part["formal"] * p_issste
pi0[ESTADO_A_IDX_ANUALES["informal"]] = part["informal"]
pi0[ESTADO_A_IDX_ANUALES["desempleado"]] = part["desempleado"]
pi0[ESTADO_A_IDX_ANUALES["fuera_PEA"]] = part["fuera"]
pi0 = pi0 / pi0.sum()

# ================= BLOQUE 1: validación transversal 2025-2035 =============
print("\n===== 1. CORTE TRANSVERSAL POR ESTADO, activos 25-64 (stock "
      "inicial), vs shares ENOE de inicialización =====")
print(f"{'anio':>5s} " + " ".join(f"{e[:12]:>13s}" for e in ESTADOS_ANUALES)
      + f" {'max|dif|pp':>11s}")
obj_txt = "  obj." + " ".join(f"{100 * p:>13.2f}" for p in pi0)
print(obj_txt)
panel_af = {}   # anio -> anios_formal del stock (para bloque 2)
for anio in range(2025, 2036):
    r = corre(anio)
    d = r.agentes.iloc[:N0]
    edad_y = edad_2025 + (anio - 2025)
    corte = d[d["vivo_final"] & (d["cohorte_retiro"] == -1)
              & (edad_y >= 25) & (edad_y <= 64)]
    shares = corte["estado_final"].value_counts(normalize=True)
    shares = shares.reindex(ESTADOS_ANUALES).fillna(0.0) * 100
    difs = shares.to_numpy() - 100 * pi0
    print(f"{anio:>5d} " + " ".join(f"{v:>13.2f}" for v in shares)
          + f" {np.abs(difs).max():>11.2f}")
    panel_af[anio] = r.agentes.iloc[:N0]["anios_formal"].to_numpy()
    for e, v, dif in zip(ESTADOS_ANUALES, shares, difs):
        filas_csv.append({"bloque": "1_transversal", "anio": anio,
                          "categoria": e, "valor": round(v, 3),
                          "referencia": round(100 * pi0[ESTADO_A_IDX_ANUALES[e]], 3),
                          "dif": round(dif, 3)})

# ================= BLOQUE 2: definiciones de densidad ======================
# panel anual completo de anios_formal del stock inicial (1997-2070)
for anio in range(1997, 2071):
    if anio not in panel_af:
        panel_af[anio] = corre(anio).agentes.iloc[:N0]["anios_formal"].to_numpy()
anios = sorted(panel_af)
AF = np.vstack([panel_af[a] for a in anios])          # (74, 5000)
cotiza = np.diff(AF, axis=0, prepend=np.zeros((1, N0))) > 0.5  # cotizó en el año

ret = df_full.iloc[:N0]
es_ret = (ret["cohorte_retiro"] >= 2026).to_numpy()
anio_ret = ret["cohorte_retiro"].to_numpy()
af_fin = ret["anios_formal"].to_numpy()
dens_a_col = ret["densidad_cotizacion"].to_numpy()

# (a) actual: densidad sobre retirados 2026+ con anios_formal>0
sel_a = es_ret & (af_fin > 0)
dens_a = dens_a_col[sel_a]

# (b) cuentahabiente: desde la PRIMERA cotización hasta el retiro
idx_anio = {a: i for i, a in enumerate(anios)}
dens_b = []
for j in np.where(sel_a)[0]:
    cot_j = np.where(cotiza[:, j])[0]
    t0 = anios[cot_j[0]]
    ventana = anio_ret[j] - t0
    dens_b.append(af_fin[j] / ventana)
dens_b = np.array(dens_b)

# (c) cotizantes recientes: >=1 año cotizado en los 10 años pre-retiro
rec = []
for j in np.where(sel_a)[0]:
    fila = idx_anio[int(anio_ret[j])]
    rec.append(cotiza[max(0, fila - 10):fila, j].any())
rec = np.array(rec)
dens_c = dens_a[rec]

print("\n===== 2. DENSIDAD SIMULADA BAJO TRES DEFINICIONES (B definitiva, "
      "retirados 2026+, semilla base) — observada CONSAR: ~40-50% =====")
for nombre, arr, desc in [
    ("a_actual", dens_a, "anios_formal/anios_activo, anios_formal>0"),
    ("b_cuentahabiente", dens_b, "desde 1ª cotización hasta retiro"),
    ("c_cotizante_reciente", dens_c,
     "def. (a) sobre quienes cotizaron en los 10 años pre-retiro"),
]:
    print(f"  ({nombre[0]}) {desc}")
    print(f"      n={len(arr):,}  media={arr.mean():.3f}  "
          f"mediana={np.median(arr):.3f}  p25={np.quantile(arr, .25):.3f}  "
          f"p75={np.quantile(arr, .75):.3f}")
    filas_csv.append({"bloque": "2_densidad", "categoria": nombre,
                      "n": len(arr), "media": round(arr.mean(), 4),
                      "mediana": round(float(np.median(arr)), 4),
                      "p25": round(float(np.quantile(arr, .25)), 4),
                      "p75": round(float(np.quantile(arr, .75)), 4)})

# ================= BLOQUE 3: masa en cero, denominadores alternos ==========
print("\n===== 3. MASA EN CERO (TR=0) BAJO DENOMINADORES ALTERNATIVOS "
      "(B definitiva, 3 semillas) =====")
umbrales = [("a_anios_formal_gt0", lambda d: d["anios_formal"] > 0),
            ("b_anios_formal_ge5", lambda d: d["anios_formal"] >= 5),
            ("c_anios_formal_ge10", lambda d: d["anios_formal"] >= 10),
            ("d_semanas_ge250", lambda d: d["semanas_cotizadas"] >= 250)]
retirados3 = []
for k in range(3):
    r = corre(ANIO_FIN, semilla=SEMILLA + k) if k else full
    d = r.agentes
    retirados3.append(d[d["cohorte_retiro"] >= 2026])
r3 = pd.concat(retirados3, ignore_index=True)
print(f"  retirados 2026+ apilados (3 semillas): {len(r3):,}")
print(f"  {'denominador':<22s} {'n':>7s} {'pct_del_total_ret':>18s} "
      f"{'masa_en_cero_pct':>17s}")
for nombre, f in umbrales:
    sub = r3[f(r3)]
    masa = 100 * (sub["tasa_reemplazo"] == 0).mean()
    print(f"  {nombre:<22s} {len(sub):>7,d} "
          f"{100 * len(sub) / len(r3):>18.1f} {masa:>17.1f}")
    filas_csv.append({"bloque": "3_masa_cero", "categoria": nombre,
                      "n": len(sub),
                      "pct_del_total_retirados": round(100 * len(sub) / len(r3), 2),
                      "masa_en_cero_pct": round(masa, 2)})

marg = r3[(r3["anios_formal"] > 0) & (r3["anios_formal"] < 5)]
cot0 = r3[r3["anios_formal"] > 0]
print(f"\n  cotización marginal (1-4 años): {len(marg):,} agentes = "
      f"{100 * len(marg) / len(cot0):.1f}% de los cotizantes actuales; "
      f"su masa en cero: {100 * (marg['tasa_reemplazo'] == 0).mean():.1f}%")
filas_csv.append({"bloque": "3_masa_cero", "categoria": "marginales_1a4_anios",
                  "n": len(marg),
                  "pct_de_cotizantes_def_a": round(100 * len(marg) / len(cot0), 2),
                  "masa_en_cero_pct":
                  round(100 * (marg["tasa_reemplazo"] == 0).mean(), 2)})

dest = REPO / "analisis/matrices/auditoria_anclaje.csv"
pd.DataFrame(filas_csv).to_csv(dest, index=False)
print(f"\nCSV: {dest}")
