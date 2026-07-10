"""Corrida final a escala — artefactos numéricos del paper (Fase 5).

Motor heterogéneo definitivo (5 estados, matrices anuales ENOE 2015-2024),
escenario base, 100,000 agentes, 5 semillas. Cero cambios a motor/ y matrices.

Produce en analisis/matrices/resultados_finales/:
  a) tabla_maestra_masa_cero.csv   — TR=0 bajo los dos denominadores del paper
                                     (anios_formal>0 y >=10), IC95 entre semillas
  b) cobertura.csv                 — desglose exhaustivo de cobertura al retiro
  c) tr_percentiles.csv +
     tr_histograma.csv             — distribución completa de la tasa de reemplazo
  d) perfil_sexo_escolaridad.csv +
     decada_retiro.csv             — desgloses del paper
  e) densidad_definiciones.csv     — densidad bajo las 3 definiciones de la
                                     auditoría (b y c vía panel anual de corridas
                                     prefijo, las 5 semillas)
  f) fig_*.png                     — figuras de publicación (300 dpi, español)
  metadata_corrida.csv             — parámetros, insumos y runtime

Universo de retiro: los retirados 2026+ provienen todos del stock inicial
(los entrantes cumplen 65 después de 2070), así que el panel prefijo sobre
los primeros N0 agentes cubre a todos los retirados.

Definiciones idénticas a auditoria_anclaje.py (bloques 2 y 3):
  masa en cero  = % con tasa_reemplazo == 0 dentro del denominador
  densidad (a)  = anios_formal/anios_activo, retirados 2026+ con anios_formal>0
  densidad (b)  = anios_formal / (anio_retiro - anio de PRIMERA cotización)
  densidad (c)  = def. (a) sobre quienes cotizaron en los 10 años pre-retiro

Insumos con fallback estático (usar_api=False), como la auditoría: la corrida
citable debe ser reproducible sin red; los valores usados quedan en metadata.

Uso: .venv/bin/python corrida_final_paper.py
"""

from __future__ import annotations

import contextlib
import io
import logging
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

REPO = Path("/Users/andrebutron/datos-mexico/datos-mexico-py")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "analisis" / "matrices"))
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

# ---------------------------------------------------------------- parámetros
N_AGENTES = 100_000
N_SEMILLAS = 5
OUT = REPO / "analisis" / "matrices" / "resultados_finales"
OUT.mkdir(exist_ok=True)

# Paleta de referencia validada (skill dataviz, modo claro)
INK, SEC, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, SURF = "#e1e0d9", "#c3c2b7", "#fcfcfb"
AZUL, AQUA, AZUL_OSCURO = "#2a78d6", "#1baf7a", "#104281"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "text.color": INK,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": SEC,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURF,
    "axes.facecolor": SURF,
    "savefig.facecolor": SURF,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

ORDEN_ESC = ["basica-", "media_sup", "superior"]  # etiquetas de ESCOLARIDADES
ETIQ_ESC = {"basica-": "Básica o menos", "media_sup": "Media superior",
            "superior": "Superior"}
ETIQ_SEXO = {"H": "Hombres", "M": "Mujeres"}


T_4GL = 2.7764  # t de Student al 95%, 4 grados de libertad (5 semillas)


def ic95(vals: list[float]) -> tuple[float, float, float]:
    """(media, semiancho IC95 con t de 4 gl, sd) entre semillas."""
    a = np.asarray(vals, dtype=float)
    sd = a.std(ddof=1)
    return float(a.mean()), float(T_4GL * sd / np.sqrt(len(a))), float(sd)


def main() -> int:
    t_total = time.time()
    cfg0 = yaml.safe_load((REPO / "motor" / "config.yaml").read_text())
    cfg0["simulacion"]["n_agentes"] = N_AGENTES
    ANIO_FIN = cfg0["simulacion"]["anio_fin"]
    SEMILLA0 = cfg0["semilla"]
    semillas = [SEMILLA0 + k for k in range(N_SEMILLAS)]

    print(f"[1/5] Insumos (fallback estático)… n_agentes={N_AGENTES:,}, "
          f"semillas={semillas}")
    conapo = cargar_conapo()
    qx = qx_por_sexo(cargar_mortalidad())
    part = participaciones_enoe(usar_api=False)
    r_hist = cargar_rendimientos_reales()
    ind_sal = cargar_indice_salarial_real()

    def corre(anio_fin: int, semilla: int):
        cfg = yaml.safe_load((REPO / "motor" / "config.yaml").read_text())
        cfg["simulacion"]["n_agentes"] = N_AGENTES
        cfg["simulacion"]["anio_fin"] = anio_fin
        with contextlib.redirect_stdout(io.StringIO()):
            return simular(
                cfg, conapo, qx, part, escenario="base", semilla=semilla,
                r_historico=r_hist, indice_salarial=ind_sal,
                matriz_heterogenea=True,
            )

    # ------------------------------------------------ corridas + panel anual
    print(f"[2/5] {N_SEMILLAS} corridas completas 1997-{ANIO_FIN} + panel "
          f"anual prefijo (74 corridas/semilla) para densidades b/c…")
    retirados_por_semilla: dict[int, pd.DataFrame] = {}
    dens_por_semilla: dict[int, dict[str, np.ndarray]] = {}
    runtimes = {}
    for sem in semillas:
        t0 = time.time()
        full = corre(ANIO_FIN, sem)
        d = full.agentes
        ret = d[d["cohorte_retiro"] >= 2026].copy()
        ret["semilla"] = sem
        retirados_por_semilla[sem] = ret
        # sanity: todos los retirados provienen del stock inicial
        assert ret.index.max() < N_AGENTES

        # panel anual de anios_formal del stock (propiedad prefijo, auditoría 5a)
        panel = np.empty((ANIO_FIN - 1997 + 1, N_AGENTES))
        for i, anio in enumerate(range(1997, ANIO_FIN + 1)):
            r = full if anio == ANIO_FIN else corre(anio, sem)
            panel[i] = r.agentes["anios_formal"].to_numpy()[:N_AGENTES]
        cotiza = np.diff(panel, axis=0, prepend=np.zeros((1, N_AGENTES))) > 0.5
        anios_idx = {a: i for i, a in enumerate(range(1997, ANIO_FIN + 1))}

        af_fin = d["anios_formal"].to_numpy()[:N_AGENTES]
        anio_ret = d["cohorte_retiro"].to_numpy()[:N_AGENTES]
        dens_col = d["densidad_cotizacion"].to_numpy()[:N_AGENTES]
        sel_a = (anio_ret >= 2026) & (af_fin > 0)

        dens_a = dens_col[sel_a]
        dens_b, rec = [], []
        for j in np.where(sel_a)[0]:
            cot_j = np.where(cotiza[:, j])[0]
            t_ini = 1997 + cot_j[0]
            dens_b.append(af_fin[j] / (anio_ret[j] - t_ini))
            fila = anios_idx[int(anio_ret[j])]
            rec.append(cotiza[max(0, fila - 10):fila, j].any())
        rec = np.array(rec)
        dens_por_semilla[sem] = {
            "a_actual": dens_a,
            "b_cuentahabiente": np.array(dens_b),
            "c_cotizante_reciente": dens_a[rec],
        }
        runtimes[sem] = time.time() - t0
        print(f"      semilla {sem}: {len(ret):,} retirados 2026+ "
              f"({runtimes[sem]:.0f}s con panel)")

    r_all = pd.concat(retirados_por_semilla.values(), ignore_index=True)

    # ------------------------------------------------ a) masa en cero
    print("[3/5] Tablas…")
    DENOMS = [
        ("a_anios_formal_gt0", "anios_formal > 0 (cotizó alguna vez)",
         lambda d: d["anios_formal"] > 0),
        ("c_anios_formal_ge10", "anios_formal >= 10 (cotizante sustantivo)",
         lambda d: d["anios_formal"] >= 10),
    ]
    filas = []
    for clave, desc, f in DENOMS:
        masas, shares = [], []
        for sem in semillas:
            d = retirados_por_semilla[sem]
            sub = d[f(d)]
            masas.append(100 * (sub["tasa_reemplazo"] == 0).mean())
            shares.append(100 * len(sub) / len(d))
        m, ic, sd = ic95(masas)
        ms, _, _ = ic95(shares)
        filas.append({
            "denominador": clave, "descripcion": desc,
            "masa_en_cero_pct": round(m, 2), "ic95_semiancho": round(ic, 2),
            "sd_entre_semillas": round(sd, 3),
            "pct_del_total_retirados": round(ms, 2),
            "n_agentes_pooled": len(r_all[f(r_all)]),
            **{f"semilla_{s}": round(v, 2) for s, v in zip(semillas, masas, strict=False)},
        })
    pd.DataFrame(filas).to_csv(OUT / "tabla_maestra_masa_cero.csv", index=False)

    # ------------------------------------------------ b) cobertura
    def clasifica(d: pd.DataFrame) -> pd.Series:
        cat = pd.Series("", index=d.index)
        cat[d["anios_formal"] == 0] = "nunca_cotizo"
        cat[(d["anios_formal"] > 0) & (d["pension_mensual"] == 0)] = \
            "sin_pension_saldo_en_exhibicion"
        cat[(d["pension_mensual"] > 0) & d["requiere_PG"]] = "pension_garantizada"
        cat[(d["pension_mensual"] > 0) & ~d["requiere_PG"] & d["requiere_FPB"]] = \
            "contributiva_con_complemento_FPB"
        cat[(d["pension_mensual"] > 0) & ~d["requiere_PG"] & ~d["requiere_FPB"]] = \
            "contributiva_plena"
        return cat

    ORDEN_COB = ["contributiva_plena", "contributiva_con_complemento_FPB",
                 "pension_garantizada", "sin_pension_saldo_en_exhibicion",
                 "nunca_cotizo"]
    ETIQ_COB = {
        "contributiva_plena": "Pensión contributiva plena",
        "contributiva_con_complemento_FPB": "Contributiva + complemento FPB",
        "pension_garantizada": "Pensión garantizada (PG)",
        "sin_pension_saldo_en_exhibicion": "Sin pensión (saldo en una exhibición)",
        "nunca_cotizo": "Nunca cotizó al IMSS",
    }
    filas = []
    por_sem = {s: clasifica(retirados_por_semilla[s]) for s in semillas}
    for cat in ORDEN_COB:
        vals = [100 * (por_sem[s] == cat).mean() for s in semillas]
        m, ic, sd = ic95(vals)
        filas.append({
            "categoria": cat, "etiqueta": ETIQ_COB[cat],
            "cubierto": cat in ORDEN_COB[:3],
            "pct_retirados": round(m, 2), "ic95_semiancho": round(ic, 2),
            "sd_entre_semillas": round(sd, 3),
            **{f"semilla_{s}": round(v, 2) for s, v in zip(semillas, vals, strict=False)},
        })
    cob = pd.DataFrame(filas)
    tot_cub = [100 * por_sem[s].isin(ORDEN_COB[:3]).mean() for s in semillas]
    m, ic, sd = ic95(tot_cub)
    cob = pd.concat([cob, pd.DataFrame([{
        "categoria": "TOTAL_cubiertos", "etiqueta": "Total con pensión (cobertura)",
        "cubierto": True, "pct_retirados": round(m, 2),
        "ic95_semiancho": round(ic, 2), "sd_entre_semillas": round(sd, 3),
        **{f"semilla_{s}": round(v, 2) for s, v in zip(semillas, tot_cub, strict=False)},
    }])], ignore_index=True)
    cob.to_csv(OUT / "cobertura.csv", index=False)

    # ------------------------------------------------ c) distribución de TR
    # denominador: retirados 2026+ que cotizaron alguna vez (TR definida)
    PCTS = [5, 10, 25, 50, 75, 90, 95]
    tr_sem = {s: retirados_por_semilla[s].loc[
        retirados_por_semilla[s]["anios_formal"] > 0, "tasa_reemplazo"]
        for s in semillas}
    filas = []
    for p in PCTS:
        vals = [float(np.percentile(tr_sem[s], p)) for s in semillas]
        m, ic, sd = ic95(vals)
        filas.append({"percentil": f"p{p}", "tr": round(m, 4),
                      "ic95_semiancho": round(ic, 4),
                      **{f"semilla_{s}": round(v, 4)
                         for s, v in zip(semillas, vals, strict=False)}})
    for nombre, fn in [("media", np.mean),
                       ("pct_TR_cero", lambda a: 100 * (np.asarray(a) == 0).mean()),
                       ("pct_TR_igual_1", lambda a: 100 * (np.asarray(a) == 1).mean()),
                       ("pct_TR_mayor_1.2", lambda a: 100 * (np.asarray(a) > 1.2).mean())]:
        vals = [float(fn(tr_sem[s].to_numpy())) for s in semillas]
        m, ic, sd = ic95(vals)
        filas.append({"percentil": nombre, "tr": round(m, 4),
                      "ic95_semiancho": round(ic, 4),
                      **{f"semilla_{s}": round(v, 4)
                         for s, v in zip(semillas, vals, strict=False)}})
    # condicionales a recibir pensión (pension_mensual>0): la masa en cero
    # domina hasta el p75, así que la distribución condicional es la que
    # describe a los pensionados
    for p in [10, 25, 50, 75, 90]:
        vals = []
        for s in semillas:
            d = retirados_por_semilla[s]
            a = d.loc[d["pension_mensual"] > 0, "tasa_reemplazo"].to_numpy()
            vals.append(float(np.percentile(a, p)))
        m, ic, sd = ic95(vals)
        filas.append({"percentil": f"p{p}_pensionados", "tr": round(m, 4),
                      "ic95_semiancho": round(ic, 4),
                      **{f"semilla_{s}": round(v, 4)
                         for s, v in zip(semillas, vals, strict=False)}})
    pd.DataFrame(filas).to_csv(OUT / "tr_percentiles.csv", index=False)

    # histograma: masa discreta en 0 + bins de 0.05 en (0, 1.2] + overflow
    bordes = np.arange(0.0, 1.2001, 0.05)
    filas = []
    hist_sem = []
    for s in semillas:
        a = tr_sem[s].to_numpy()
        pcts = [100 * (a == 0).mean()]
        h, _ = np.histogram(a[(a > 0) & (a <= 1.2)], bins=bordes)
        pcts += list(100 * h / len(a))
        pcts.append(100 * (a > 1.2).mean())
        hist_sem.append(pcts)
    H = np.array(hist_sem)  # (5, n_bins)
    etiquetas = (["TR = 0 (masa en cero)"]
                 + [f"({lo:.2f}, {hi:.2f}]"
                    for lo, hi in zip(bordes[:-1], bordes[1:], strict=False)]  # noqa: RUF007
                 + ["TR > 1.20"])
    for i, et in enumerate(etiquetas):
        m, ic, sd = ic95(list(H[:, i]))
        filas.append({"bin": et, "pct_retirados_cotizantes": round(m, 3),
                      "ic95_semiancho": round(ic, 3)})
    pd.DataFrame(filas).to_csv(OUT / "tr_histograma.csv", index=False)

    # ------------------------------------------------ d) perfiles y décadas
    # las etiquetas supuestas deben cubrir exactamente las del motor — un
    # typo aquí tiraría un grupo en silencio
    assert set(r_all["escolaridad"].unique()) == set(ORDEN_ESC), \
        f"escolaridades inesperadas: {sorted(r_all['escolaridad'].unique())}"

    def resumen_grupo(g: pd.DataFrame) -> dict:
        cot = g[g["anios_formal"] > 0]
        pen = g[g["pension_mensual"] > 0]
        return {
            "n_pooled": len(g),
            "pct_nunca_cotizo": round(100 * (g["anios_formal"] == 0).mean(), 2),
            "masa_cero_pct_def_a": round(
                100 * (cot["tasa_reemplazo"] == 0).mean(), 2) if len(cot) else np.nan,
            "pct_con_pension": round(100 * (g["pension_mensual"] > 0).mean(), 2),
            "pct_FPB": round(100 * g["requiere_FPB"].mean(), 2),
            "pct_PG": round(100 * g["requiere_PG"].mean(), 2),
            "densidad_media_def_a": round(
                float(cot["densidad_cotizacion"].mean()), 4) if len(cot) else np.nan,
            "tr_mediana_pensionados": round(
                float(pen["tasa_reemplazo"].median()), 4) if len(pen) else np.nan,
            "tr_p25_pensionados": round(
                float(pen["tasa_reemplazo"].quantile(.25)), 4) if len(pen) else np.nan,
            "tr_p75_pensionados": round(
                float(pen["tasa_reemplazo"].quantile(.75)), 4) if len(pen) else np.nan,
        }

    def ic_masa_cero(filtro) -> tuple[float, float, list[float]]:
        vals = []
        for s in semillas:
            d = retirados_por_semilla[s]
            cot = d[filtro(d) & (d["anios_formal"] > 0)]
            vals.append(100 * (cot["tasa_reemplazo"] == 0).mean())
        m, ic, _ = ic95(vals)
        return m, ic, vals

    filas = []
    for sexo in ["H", "M"]:
        for esc in ORDEN_ESC:
            g = r_all[(r_all["genero"] == sexo) & (r_all["escolaridad"] == esc)]
            _, ic, _ = ic_masa_cero(
                lambda d, sx=sexo, e=esc: (d["genero"] == sx)
                & (d["escolaridad"] == e))
            filas.append({"sexo": ETIQ_SEXO[sexo], "escolaridad": ETIQ_ESC[esc],
                          **resumen_grupo(g),
                          "masa_cero_ic95_semiancho": round(ic, 2)})
    pf = pd.DataFrame(filas)
    assert pf["n_pooled"].sum() == len(r_all), "grupos de perfil no cubren el total"
    pf.to_csv(OUT / "perfil_sexo_escolaridad.csv", index=False)

    DECADAS = [(2026, 2035), (2036, 2045), (2046, 2055), (2056, 2065), (2066, 2070)]
    filas = []
    for lo, hi in DECADAS:
        g = r_all[r_all["cohorte_retiro"].between(lo, hi)]
        _, ic, _ = ic_masa_cero(
            lambda d, a=lo, b=hi: d["cohorte_retiro"].between(a, b))
        et = f"{lo}-{hi}" + (" (parcial)" if hi == 2070 else "")
        filas.append({"decada_retiro": et, **resumen_grupo(g),
                      "masa_cero_ic95_semiancho": round(ic, 2)})
    dd = pd.DataFrame(filas)
    assert dd["n_pooled"].sum() == len(r_all), "décadas no cubren el total"
    dd.to_csv(OUT / "decada_retiro.csv", index=False)

    # ------------------------------------------------ e) densidad, 3 definiciones
    DEFS = [("a_actual", "anios_formal/anios_activo, anios_formal>0"),
            ("b_cuentahabiente", "desde la 1a cotización hasta el retiro"),
            ("c_cotizante_reciente",
             "def. (a) sobre quienes cotizaron en los 10 años pre-retiro")]
    filas = []
    for clave, desc in DEFS:
        stats = {"media": [], "mediana": [], "p25": [], "p75": [], "n": []}
        for s in semillas:
            arr = dens_por_semilla[s][clave]
            stats["media"].append(arr.mean())
            stats["mediana"].append(float(np.median(arr)))
            stats["p25"].append(float(np.quantile(arr, .25)))
            stats["p75"].append(float(np.quantile(arr, .75)))
            stats["n"].append(len(arr))
        fila = {"definicion": clave, "descripcion": desc,
                "n_pooled": int(sum(stats["n"]))}
        for k in ["media", "mediana", "p25", "p75"]:
            m, ic, sd = ic95(stats[k])
            fila[k] = round(m, 4)
            fila[f"{k}_ic95_semiancho"] = round(ic, 4)
        filas.append(fila)
    pd.DataFrame(filas).to_csv(OUT / "densidad_definiciones.csv", index=False)

    # ------------------------------------------------ f) figuras
    print("[4/5] Figuras…")

    # F1 — distribución de TR (LA figura central: bimodalidad 0 / piso FPB)
    hist_media = H.mean(axis=0)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = np.concatenate([[-0.05], (bordes[:-1] + bordes[1:]) / 2, [1.25]])
    colores = [AZUL_OSCURO] + [AZUL] * (len(bordes) - 1) + [AZUL]
    ax.bar(xs, hist_media, width=0.046, color=colores, zorder=3)
    ax.set_xlabel("Tasa de reemplazo al retiro")
    ax.set_ylabel("% de retirados que cotizaron alguna vez")
    ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xticks([-0.05, 0.25, 0.5, 0.75, 1.0, 1.25])
    ax.set_xticklabels(["0", "0.25", "0.50", "0.75", "1.00", ">1.2"])
    ax.grid(axis="x", visible=False)
    i0 = 0
    ax.annotate(f"Masa en cero: {hist_media[i0]:.1f}%\n(sin derecho a pensión)",
                xy=(-0.05, hist_media[i0]), xytext=(0.08, hist_media[i0] * 0.96),
                color=INK, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    i1 = 1 + int(np.argmax(hist_media[1:-1]))
    ax.annotate("Modo en TR ≈ 1:\npiso FPB = salario promedio",
                xy=(xs[i1], hist_media[i1]),
                xytext=(0.55, hist_media[i1] + 8),
                color=INK, fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Distribución bimodal de la tasa de reemplazo, retirados 2026-2070")
    fig.text(0.01, -0.04,
             f"Motor heterogéneo (5 estados, matrices ENOE 2015-2024), escenario "
             f"base, {N_AGENTES:,} agentes × {N_SEMILLAS} semillas (promedio). "
             f"Denominador: retirados con historial de cotización IMSS.",
             fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "fig_tr_distribucion.png")
    plt.close(fig)

    # F2 — masa en cero bajo los dos denominadores (IC95)
    tm = pd.read_csv(OUT / "tabla_maestra_masa_cero.csv")
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    et = ["Cotizó alguna vez\n(años formales > 0)",
          "Cotizante sustantivo\n(años formales ≥ 10)"]
    y = np.arange(len(tm))[::-1]
    ax.barh(y, tm["masa_en_cero_pct"], height=0.5, color=AZUL, zorder=3,
            xerr=tm["ic95_semiancho"], error_kw=dict(ecolor=INK, lw=1, capsize=3))
    for yi, v in zip(y, tm["masa_en_cero_pct"], strict=False):
        ax.text(v - 1.2, yi, f"{v:.1f}%", va="center", ha="right",
                color=SURF, fontweight="bold", fontsize=10)
    ax.set_yticks(y, et)
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% de retirados con TR = 0 dentro del denominador")
    ax.set_title("Masa en cero bajo los dos denominadores del paper")
    fig.text(0.01, -0.08, "Barras de error: IC95 entre 5 semillas.",
             fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "fig_masa_cero.png")
    plt.close(fig)

    # F3 — cobertura al retiro
    cb = cob[cob["categoria"] != "TOTAL_cubiertos"].iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    y = np.arange(len(cb))
    col = np.where(cb["cubierto"], AZUL, MUTED)
    ax.barh(y, cb["pct_retirados"], height=0.55, color=col, zorder=3,
            xerr=cb["ic95_semiancho"], error_kw=dict(ecolor=INK, lw=1, capsize=3))
    for yi, v in zip(y, cb["pct_retirados"], strict=False):
        ax.text(v + 1.0, yi, f"{v:.1f}%", va="center", color=INK, fontsize=9)
    ax.set_yticks(y, cb["etiqueta"])
    ax.set_xlim(0, max(cb["pct_retirados"]) * 1.22)
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("% de los retirados 2026-2070")
    tot = cob.loc[cob["categoria"] == "TOTAL_cubiertos", "pct_retirados"].iloc[0]
    ax.set_title(f"Cobertura al retiro — {tot:.1f}% recibe alguna pensión")
    fig.text(0.01, -0.06, "Azul: con pensión. Gris: sin pensión. "
             "Barras de error: IC95 entre 5 semillas.", fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "fig_cobertura.png")
    plt.close(fig)

    # F4 — masa en cero por sexo × escolaridad (dot plot, 2 series). La TR
    # mediana es 0 en todos los grupos (la masa en cero rebasa el p75), así
    # que la métrica que discrimina perfiles es la masa en cero misma.
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    y = np.arange(len(ORDEN_ESC))[::-1]
    for sexo, colr, dy in [("Hombres", AZUL, 0.14), ("Mujeres", AQUA, -0.14)]:
        sub = pf[pf["sexo"] == sexo].set_index("escolaridad").loc[
            [ETIQ_ESC[e] for e in ORDEN_ESC]]
        ax.errorbar(sub["masa_cero_pct_def_a"], y + dy,
                    xerr=sub["masa_cero_ic95_semiancho"], fmt="o", ms=7,
                    color=colr, ecolor=colr, capsize=3, lw=1.2, zorder=3,
                    label=sexo)
        for xi, yi in zip(sub["masa_cero_pct_def_a"], y + dy, strict=False):
            ax.text(xi, yi + 0.16, f"{xi:.1f}%", ha="center", fontsize=8,
                    color=SEC)
    ax.set_yticks(y, [ETIQ_ESC[e] for e in ORDEN_ESC])
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlabel("Masa en cero (% de cotizantes con TR = 0 al retiro)")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("Masa en cero por sexo y escolaridad")
    fig.text(0.01, -0.06, "Denominador: retirados 2026-2070 con historial de "
             "cotización (def. a). Barras de error: IC95 entre 5 semillas.",
             fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "fig_tr_perfil.png")
    plt.close(fig)

    # F5 — masa en cero por década de retiro (misma métrica en el tiempo)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(dd))
    ax.errorbar(x, dd["masa_cero_pct_def_a"], yerr=dd["masa_cero_ic95_semiancho"],
                fmt="-o", color=AZUL, ms=6, lw=2, capsize=3, zorder=3)
    for xi, v in zip(x, dd["masa_cero_pct_def_a"], strict=False):
        ax.text(xi, v + 2.2, f"{v:.1f}%", ha="center", fontsize=8, color=SEC)
    ax.set_xticks(x, dd["decada_retiro"], fontsize=8.5)
    ax.set_ylim(60, 100)
    ax.yaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlabel("Década de retiro")
    ax.set_ylabel("Masa en cero (% de cotizantes)")
    ax.set_title("Masa en cero por década de retiro")
    fig.text(0.01, -0.06, "La ventana de acumulación inicia en 1997 (Ley SAR): "
             "las cohortes tempranas llegan al retiro con menos años posibles "
             "de cotización. Barras de error: IC95 entre 5 semillas.",
             fontsize=7.5, color=MUTED)
    fig.savefig(OUT / "fig_tr_decada.png")
    plt.close(fig)

    # ------------------------------------------------ checks de consistencia
    print("[5/5] Checks de consistencia + metadata…")
    checks = []

    # (i) cobertura: las 5 categorías suman 100% en cada semilla
    for s in semillas:
        suma = float(sum(100 * (por_sem[s] == c).mean() for c in ORDEN_COB))
        checks.append({"check": "cobertura_suma_100", "semilla": s,
                       "valor": round(suma, 6),
                       "ok": bool(np.isclose(suma, 100.0))})

    # (ii) TR NaN entre cotizantes (anios_formal>0) == 0 en cada semilla
    for s in semillas:
        n_nan = int(tr_sem[s].isna().sum())
        checks.append({"check": "tr_nan_entre_cotizantes", "semilla": s,
                       "valor": n_nan, "ok": n_nan == 0})

    # (iii) corte transversal 2025 (semilla base, stock, activos 25-64) vs
    #       bloque 1 de auditoria_anclaje.csv — tolerancia ±0.5pp
    aud = pd.read_csv(REPO / "analisis" / "matrices" / "auditoria_anclaje.csv")
    aud25 = aud[(aud["bloque"] == "1_transversal") & (aud["anio"] == 2025)]
    ref = dict(zip(aud25["categoria"], aud25["valor"], strict=False))
    r25 = corre(2025, SEMILLA0)
    rng = np.random.default_rng(SEMILLA0)  # réplica del primer draw del motor
    c25 = conapo[(conapo["anio"] == 2025) & conapo["edad"].between(15, 64)]
    pesos = c25["poblacion"].to_numpy().astype(float)
    idx = rng.choice(len(c25), size=N_AGENTES, p=pesos / pesos.sum())
    edad_2025 = c25["edad"].to_numpy()[idx]
    d25 = r25.agentes.iloc[:N_AGENTES]
    corte = d25[d25["vivo_final"] & (d25["cohorte_retiro"] == -1)
                & (edad_2025 >= 25) & (edad_2025 <= 64)]
    shares = corte["estado_final"].value_counts(normalize=True) * 100
    for cat, v_ref in ref.items():
        v = float(shares.get(cat, 0.0))
        checks.append({"check": f"transversal_2025_{cat}", "semilla": SEMILLA0,
                       "valor": round(v, 3), "referencia_5k": v_ref,
                       "dif_pp": round(v - v_ref, 3),
                       "ok": abs(v - v_ref) <= 0.5})
    df_checks = pd.DataFrame(checks)
    df_checks.to_csv(OUT / "checks_consistencia.csv", index=False)
    n_fail = int((~df_checks["ok"]).sum())
    print(f"      checks: {len(df_checks) - n_fail}/{len(df_checks)} OK"
          + ("" if n_fail == 0 else f"  ⚠️ {n_fail} FALLAN"))
    commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    W = conapo[(conapo["anio"] == 2025)
               & conapo["edad"].between(15, 64)]["poblacion"].sum() / N_AGENTES
    meta = pd.DataFrame([
        {"clave": "n_agentes", "valor": N_AGENTES},
        {"clave": "peso_por_agente_personas", "valor": round(W, 1)},
        {"clave": "semillas", "valor": ";".join(map(str, semillas))},
        {"clave": "motor", "valor": "heterogéneo 5 estados, matrices anuales "
                                    "ENOE 2015-2024 (matriz_heterogenea=True)"},
        {"clave": "escenario", "valor": "base"},
        {"clave": "horizonte", "valor": f"1997-{ANIO_FIN}"},
        {"clave": "retirados_2026plus_pooled", "valor": len(r_all)},
        {"clave": "participaciones_enoe",
         "valor": "; ".join(f"{k}={v:.4f}" for k, v in part.items())
                  + " (fallback estático, usar_api=False)"},
        {"clave": "ic95_metodo",
         "valor": f"t de Student 4 gl ({T_4GL}) x sd/sqrt(5), entre semillas"},
        {"clave": "commit_codigo", "valor": commit},
        {"clave": "runtime_total_s", "valor": round(time.time() - t_total, 1)},
        {"clave": "runtime_por_semilla_s",
         "valor": ";".join(f"{runtimes[s]:.0f}" for s in semillas)},
    ])
    meta.to_csv(OUT / "metadata_corrida.csv", index=False)
    print(f"\nRUNTIME TOTAL: {time.time() - t_total:.1f}s")
    print(f"Artefactos en {OUT}/")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
