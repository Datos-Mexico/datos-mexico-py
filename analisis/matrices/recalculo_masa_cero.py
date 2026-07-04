"""Paso 4 corregido: masa en cero sobre cotizantes IMSS (anios_formal > 0).

Mismo protocolo que comparacion_paso4.py (5k agentes, escenario base,
3 semillas por régimen), pero las métricas excluyen del denominador a
ISSSTE y nunca-formales. Solo post-procesamiento; cero cambios al motor.
"""

import logging
import time
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

logging.basicConfig(level=logging.ERROR)

REPO = Path("/Users/andrebutron/datos-mexico/datos-mexico-py")
cfg = yaml.safe_load((REPO / "motor/config.yaml").read_text())
assert cfg["simulacion"]["n_agentes"] == 5000

qx = qx_por_sexo(cargar_mortalidad())
conapo = cargar_conapo()
part = participaciones_enoe(usar_api=False)
r_hist = cargar_rendimientos_reales()
ind_sal = cargar_indice_salarial_real()

SEMILLAS = [cfg["semilla"] + k for k in range(3)]
filas = []

for regimen, flag in [("A_homogenea", False), ("B_heterogenea", True)]:
    for s in SEMILLAS:
        t0 = time.time()
        res = simular(
            cfg, conapo, qx, part, escenario="base", semilla=s,
            r_historico=r_hist, indice_salarial=ind_sal,
            matriz_heterogenea=flag,
        )
        ret = res.agentes[res.agentes["cohorte_retiro"] >= 2026]
        cot = ret[ret["anios_formal"] > 0]          # cotizantes IMSS
        nocov = ret[ret["anios_formal"] == 0]       # sin cobertura
        tr = cot["tasa_reemplazo"]
        n_nan_cot = int(tr.isna().sum())            # debe ser 0 (sanity)
        filas.append({
            "regimen": regimen,
            "semilla": s,
            "n_retirados": len(ret),
            "n_cotizantes_imss": len(cot),
            # (a) masa en cero sobre cotizantes IMSS
            "masa_en_cero_IMSS_pct": 100 * (tr == 0).mean(),
            # (b) cobertura: % de retirados que accedieron al sistema
            "cobertura_pct": 100 * len(cot) / len(ret),
            # (c) no-cobertura desglosada
            "no_cobertura_pct": 100 * len(nocov) / len(ret),
            "no_cob_issste_pct": 100 * nocov["sector_issste"].sum() / len(ret),
            "no_cob_nunca_formal_pct": 100 * (~nocov["sector_issste"]).sum() / len(ret),
            # densidad de cotización (años formales IMSS / años activos)
            "dens_media_retirados": ret["densidad_cotizacion"].mean(),
            "dens_media_cotizantes": cot["densidad_cotizacion"].mean(),
            # métricas viejas para referencia
            "vieja_pension_cero_pct": 100 * (ret["pension_mensual"] == 0).mean(),
            "vieja_tasa_cero_dropna_pct": 100
            * (ret["tasa_reemplazo"].dropna() == 0).mean(),
            "nan_TR_entre_cotizantes": n_nan_cot,
            "segundos": round(time.time() - t0, 1),
        })
        print(f"{regimen} semilla={s}: {filas[-1]['segundos']}s", flush=True)

tabla = pd.DataFrame(filas)
pd.set_option("display.width", 250)
print("\n===== POR SEMILLA =====")
print(tabla.round(2).to_string(index=False))

print("\n===== PROMEDIO ± STD ENTRE SEMILLAS =====")
prom = tabla.drop(columns=["semilla", "segundos"]).groupby("regimen").agg(
    ["mean", "std"]
)
print(prom.round(2).T.to_string())
