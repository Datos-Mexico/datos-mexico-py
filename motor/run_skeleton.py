"""Orquestador end-to-end del walking skeleton (brief §8, entregable 2).

Corre sin intervención manual:
  1. Carga insumos (EMSSA-09, CONAPO, participaciones ENOE vía SDK).
  2. Simula los 3 escenarios x 5 semillas (distribuciones, no puntos).
  3. Check contable en cada periodo (aborta si falla).
  4. Valida contra agregados CONSAR 2025 (client.consar).
  5. Genera Figura 1 (validación) y Figura 2 (tasa de reemplazo 2050).
  6. Escribe outputs con el schema de interfaz de §7.

Uso:  python -m motor.run_skeleton [--sin-api]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

from motor import figuras
from motor.datos import (
    cargar_conapo,
    cargar_mortalidad,
    cargar_rendimientos_reales,
    participaciones_enoe,
    qx_por_sexo,
)
from motor.motor import simular
from motor.reglas_sar import vector_tasas_aportacion
from motor.validacion import comparar

REPS = 5  # semillas por escenario (intervalos, no puntos — brief §6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-api", action="store_true", help="solo fallbacks estáticos")
    args = parser.parse_args()
    usar_api = not args.sin_api

    raiz = Path(__file__).parent
    outputs = raiz / "outputs"
    outputs.mkdir(exist_ok=True)

    cfg = yaml.safe_load((raiz / "config.yaml").read_text())
    print(f"[1/6] Insumos… (semilla base {cfg['semilla']})")
    mort = cargar_mortalidad()
    qx = qx_por_sexo(mort)
    conapo = cargar_conapo()
    part = participaciones_enoe(usar_api=usar_api)
    resumen_part = ", ".join(f"{k}={v:.3f}" for k, v in part.items())
    print(f"      participaciones ENOE 2025T1: {resumen_part}")
    r_hist = cargar_rendimientos_reales()
    print(f"      rendimiento real bruto observado: {min(r_hist)}-{max(r_hist)} "
          f"(media {sum(r_hist.values()) / len(r_hist):.2%}); proyección: "
          f"{cfg['economia']['rendimiento_real_anual']:.1%} constante")
    print(f"      vector aportación RCV (extracto): 2022={vector_tasas_aportacion()[2022]:.3%} "
          f"2024={vector_tasas_aportacion()[2024]:.3%} 2030={vector_tasas_aportacion()[2030]:.3%}")

    print(f"[2/6] Simulando 3 escenarios x {REPS} semillas…")
    t0 = time.time()
    agentes_all, anual_all = [], []
    validacion_base = None
    ledger_base = None
    for esc in cfg["escenarios"]:
        for rep in range(REPS):
            semilla = cfg["semilla"] + rep
            res = simular(
                cfg, conapo, qx, part, escenario=esc, semilla=semilla,
                r_historico=r_hist,
            )
            res.agentes["semilla"] = semilla
            res.anual["semilla"] = semilla
            agentes_all.append(res.agentes)
            anual_all.append(res.anual)
            if esc == "base" and rep == 0:
                validacion_base = res.validacion
                ledger_base = res.ledger
    print(f"      listo en {time.time() - t0:.1f}s — check contable ΔS=A+R-C: OK en "
          f"{len(ledger_base)} periodos x {3 * REPS} corridas")

    df_ag = pd.concat(agentes_all, ignore_index=True)
    df_anual = pd.concat(anual_all, ignore_index=True)

    print("[3/6] Validación 2025 vs CONSAR…")
    df_val = comparar(validacion_base, usar_api=usar_api)
    print(df_val.to_string(index=False))
    print(f"      observados: {df_val.attrs['fuente_observados']}")

    print("[4/6] Figuras…")
    figuras.figura_validacion(df_val, outputs / "fig1_validacion_2025.png")
    base_s0 = df_ag[(df_ag["escenario"] == "base") & (df_ag["semilla"] == cfg["semilla"])]
    figuras.figura_tasa_reemplazo(base_s0, outputs / "fig2_tasa_reemplazo_2050.png")

    print("[5/6] Outputs (schema §7)…")
    df_ag.to_csv(outputs / "agentes.csv", index=False)
    # agregado año-escenario con intervalos entre semillas
    agg = (
        df_anual.groupby(["anio", "escenario"])
        .agg(
            n_jubilados=("n_jubilados", "mean"),
            n_bajo_piso=("n_bajo_piso", "mean"),
            costo_FPB_total_mm=("costo_FPB_total_mm", "mean"),
            costo_FPB_p10_mm=("costo_FPB_total_mm", lambda s: s.quantile(0.10)),
            costo_FPB_p90_mm=("costo_FPB_total_mm", lambda s: s.quantile(0.90)),
            costo_como_pct_PIB=("costo_como_pct_PIB", "mean"),
        )
        .reset_index()
    )
    agg.to_csv(outputs / "agregados_anuales.csv", index=False)
    df_val.to_csv(outputs / "validacion_2025.csv", index=False)
    ledger_base.to_csv(outputs / "ledger_contable_base.csv", index=False)

    print("[6/6] Resumen ejecutivo:")
    tr50 = base_s0[base_s0["cohorte_retiro"].between(2048, 2052)]["tasa_reemplazo"].dropna()
    fpb_2050 = agg[(agg["anio"] == 2050) & (agg["escenario"] == "base")]
    print(f"      Tasa de reemplazo cohorte 2050 (base): "
          f"p10={tr50.quantile(0.1):.2f} p50={tr50.median():.2f} p90={tr50.quantile(0.9):.2f}")
    if not fpb_2050.empty:
        r = fpb_2050.iloc[0]
        print(f"      Costo FPB 2050 (base, solo cohortes 2026+): "
              f"{r['costo_FPB_total_mm'] / 1e6:.3f} billones MXN reales 2025 "
              f"({r['costo_como_pct_PIB']:.2f}% del PIB)")
    print(f"      Archivos en {outputs}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
