"""Re-validación Brecha 1 con el motor de 5 estados (Operación 2).

Corre la validación 2025 (saldo RCV-IMSS vs CONSAR, bitácora #25) en los
dos regímenes de transición SIN tocar motor ni matrices:

  A (homogéneo):    matriz_heterogenea=False — 4 estados, persistencias
                    hand-coded de config.yaml (la validación original 1.16).
  B (heterogéneo):  matriz_heterogenea=True — 5 estados, matrices ANUALES
                    5x5 por perfil (panel ENOE 2015-2024).

3 semillas por régimen (semilla base de config + 0/1/2), escenario base.
Truco: anio_fin=2025 EN MEMORIA — el RNG consume draws en orden cronológico
y los entrantes/mortalidad solo existen post-2025, así que el snapshot de
validación 2025 es bit-idéntico al de la corrida completa a 2070, y los
acumulados por agente (anios_formal, semanas) quedan SOLO-backcast.

Descomposición del cambio A→B (por semilla, en Δlog):
  saldo = Σ_backcast (Aportes + Rendimientos - Comisiones)   [ledger]
  Aportes = CY × S̄_eq  donde
    CY   = cotizantes-año IMSS del backcast (Σ anios_formal × W)
    S̄_eq = salario mensual promedio EQUIVALENTE por cotizante-año:
           Σ_años aportes_año/(12·tasa_a(año)) / CY — deflacta la tasa del
           año; incluye la cuota social como salario equivalente (caveat).
  CY = n_aportantes × años de aportación promedio (extensivo × intensivo)

  Δlog saldo = Δlog CY + Δlog S̄_eq + residual (rendimientos netos y timing
  de los flujos dentro del backcast).

Salida: analisis/matrices/revalidacion_brecha1.csv (3 bloques).
Uso: python revalidacion_brecha1.py  (desde la raíz del repo o con PYTHONPATH)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path("/Users/andrebutron/datos-mexico/datos-mexico-py")
sys.path.insert(0, str(RAIZ))

from motor.datos import (
    cargar_conapo,
    cargar_indice_salarial_real,
    cargar_mortalidad,
    cargar_rendimientos_reales,
    participaciones_enoe,
    qx_por_sexo,
    targets_validacion,
)
from motor.motor import simular
from motor.reglas_sar import vector_tasas_aportacion

N_SEMILLAS = 3
REGIMENES = {"A_homogeneo": False, "B_heterogeneo": True}


def main() -> int:
    cfg = yaml.safe_load((RAIZ / "motor" / "config.yaml").read_text())
    # anio_fin=2025 EN MEMORIA: snapshot 2025 idéntico, acumulados solo-backcast
    cfg["simulacion"]["anio_fin"] = cfg["simulacion"]["anio_validacion"]

    print("[1/3] Insumos…")
    mort = cargar_mortalidad()
    qx = qx_por_sexo(mort)
    conapo = cargar_conapo()
    part = participaciones_enoe(usar_api=True)
    r_hist = cargar_rendimientos_reales()
    indice_sal = cargar_indice_salarial_real()
    obs = targets_validacion(usar_api=True)
    print(f"      targets observados: {obs['fuente']}")
    print(f"      saldo RCV-IMSS obs: {obs['rcv_imss_mm'] / 1e6:.3f} bn | "
          f"cotizantes {obs['cotizantes'] / 1e6:.2f} M | "
          f"cuentas {obs['cuentas_totales'] / 1e6:.1f} M")

    tasas = vector_tasas_aportacion()

    print(f"[2/3] Corriendo {len(REGIMENES)} regímenes x {N_SEMILLAS} semillas "
          f"(escenario base, 1997-2025)…")
    filas_ratio, filas_canal = [], []
    canales: dict[tuple[str, int], dict] = {}
    for nombre, flag in REGIMENES.items():
        for rep in range(N_SEMILLAS):
            semilla = cfg["semilla"] + rep
            t0 = time.time()
            res = simular(
                cfg, conapo, qx, part, escenario="base", semilla=semilla,
                r_historico=r_hist, indice_salarial=indice_sal,
                matriz_heterogenea=flag,
            )
            v = res.validacion
            W = v["peso_agente"]
            ag = res.agentes
            led = res.ledger

            ratio_saldo = (v["saldo_rcv_simulado_mm"] / 1e6) / (obs["rcv_imss_mm"] / 1e6)
            filas_ratio.append({
                "bloque": "1_ratios",
                "regimen": nombre,
                "semilla": semilla,
                "saldo_sim_bn": round(v["saldo_rcv_simulado_mm"] / 1e6, 4),
                "saldo_obs_bn": round(obs["rcv_imss_mm"] / 1e6, 4),
                "ratio_saldo": round(ratio_saldo, 4),
                "ratio_cotizantes": round(v["cotizantes_simulados"] / obs["cotizantes"], 4),
                "ratio_cuentas": round(v["cuentas_simuladas"] / obs["cuentas_totales"], 4),
            })

            # ---- canales (backcast 1997-2025, alcance IMSS) ----
            aportantes = ag["anios_formal"] > 0
            cy = float(ag["anios_formal"].sum()) * W                  # cotizantes-año
            n_aport = int(aportantes.sum()) * W                       # personas que aportaron
            anios_prom = float(ag.loc[aportantes, "anios_formal"].mean())
            aportes = float(led["aportaciones_mm"].sum())             # mm MXN 2025
            rend_netos = float(led["rendimientos_mm"].sum() - led["comisiones_mm"].sum())
            # masa salarial equivalente: deflacta la tasa del año
            masa_eq = float(
                (led["aportaciones_mm"] / (12.0 * led["anio"].map(tasas))).sum()
            )  # mm MXN — "meses-salario equivalentes"
            sal_prom_eq = masa_eq * 1e6 / cy  # MXN mensuales por cotizante-año

            canales[(nombre, semilla)] = {
                "saldo": v["saldo_rcv_simulado_mm"], "cy": cy, "n_aport": n_aport,
                "anios_prom": anios_prom, "sal_prom_eq": sal_prom_eq,
                "aportes": aportes, "rend_netos": rend_netos,
            }
            filas_canal.append({
                "bloque": "2_canales",
                "regimen": nombre,
                "semilla": semilla,
                "cotizantes_anio_M": round(cy / 1e6, 3),
                "personas_aportantes_M": round(n_aport / 1e6, 3),
                "anios_aportacion_prom": round(anios_prom, 3),
                "salario_prom_eq_mensual": round(sal_prom_eq, 1),
                "aportes_backcast_bn": round(aportes / 1e6, 4),
                "rend_netos_backcast_bn": round(rend_netos / 1e6, 4),
            })
            print(f"      {nombre} semilla {semilla}: ratio saldo "
                  f"{ratio_saldo:.3f} ({time.time() - t0:.1f}s)")

    # ---- descomposición A→B por semilla (Δlog) ----
    filas_dec = []
    for rep in range(N_SEMILLAS):
        semilla = cfg["semilla"] + rep
        a = canales[("A_homogeneo", semilla)]
        b = canales[("B_heterogeneo", semilla)]
        dlog_saldo = np.log(b["saldo"] / a["saldo"])
        dlog_cy = np.log(b["cy"] / a["cy"])
        dlog_pers = np.log(b["n_aport"] / a["n_aport"])
        dlog_anios = np.log(b["anios_prom"] / a["anios_prom"])
        dlog_sal = np.log(b["sal_prom_eq"] / a["sal_prom_eq"])
        residual = dlog_saldo - dlog_cy - dlog_sal
        filas_dec.append({
            "bloque": "3_descomposicion_AtoB",
            "semilla": semilla,
            "dlog_saldo": round(dlog_saldo, 4),
            "dlog_cotizantes_anio": round(dlog_cy, 4),
            "dlog_personas": round(dlog_pers, 4),
            "dlog_anios_aportacion": round(dlog_anios, 4),
            "dlog_salario_prom": round(dlog_sal, 4),
            "residual_rendimientos_timing": round(residual, 4),
        })

    print("[3/3] Escribiendo CSV…")
    df = pd.concat(
        [pd.DataFrame(filas_ratio), pd.DataFrame(filas_canal), pd.DataFrame(filas_dec)],
        ignore_index=True,
    )
    destino = RAIZ / "analisis" / "matrices" / "revalidacion_brecha1.csv"
    df.to_csv(destino, index=False)
    print(f"      {destino}")
    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
