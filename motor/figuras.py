"""Figuras del entregable de la junta (brief §8, entregables 4 y 5)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paleta validada (referencia dataviz, modo claro)
AZUL = "#2a78d6"      # serie 1: simulado
AQUA = "#1baf7a"      # serie 2: observado
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": BASE,
        "axes.labelcolor": INK2,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
    }
)


def figura_validacion(df_val: pd.DataFrame, ruta: Path) -> None:
    """Figura 1 — agregados simulados vs observados 2025 (small multiples,
    una métrica por panel: las unidades difieren y NUNCA comparten eje)."""
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8))
    for ax, (_, row) in zip(axes, df_val.iterrows(), strict=True):
        vals = [row["simulado"], row["observado"]]
        bars = ax.bar(
            ["Simulado", "Observado"],
            vals,
            color=[AZUL, AQUA],
            width=0.62,
            edgecolor=SURFACE,
            linewidth=2,
        )
        for b, v in zip(bars, vals, strict=True):
            ax.text(
                b.get_x() + b.get_width() / 2,
                v,
                f"{v:,.1f}",
                ha="center",
                va="bottom",
                fontsize=10,
                color=INK,
            )
        ax.set_title(row["metrica"], fontsize=10, color=INK2, pad=10)
        ax.set_ylim(0, max(vals) * 1.22)
        ax.grid(axis="x", visible=False)
        ax.tick_params(length=0)
        razon = row["razon_sim_obs"]
        ax.text(
            0.5,
            -0.17,
            f"sim/obs = {razon:.2f}",
            transform=ax.transAxes,
            ha="center",
            fontsize=9,
            color=MUTED,
        )
    fig.suptitle(
        "Validación 2025 — motor (walking skeleton) vs CONSAR observado",
        fontsize=12,
        color=INK,
        y=1.02,
    )
    fig.text(
        0.5,
        -0.06,
        f"Observados: {df_val.attrs.get('fuente_observados', 'CONSAR')} · "
        "Skeleton Fase 1: la brecha se cierra en calibración (Fase 2)",
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def figura_tasa_reemplazo(
    df_agentes: pd.DataFrame, ruta: Path, cohorte: int = 2050, ventana: int = 2
) -> None:
    """Figura 2 — distribución de la tasa de reemplazo, cohorte 2050, base.

    Cohorte = retiros en [cohorte-ventana, cohorte+ventana] para tener masa
    suficiente con 5,000 agentes (se etiqueta explícitamente).
    """
    m = df_agentes["cohorte_retiro"].between(cohorte - ventana, cohorte + ventana)
    tr = df_agentes.loc[m, "tasa_reemplazo"].dropna()
    tr = tr[tr >= 0]
    pcts = np.percentile(tr, [10, 25, 50, 75, 90])

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.hist(
        tr.clip(upper=1.5),
        bins=36,
        color=AZUL,
        edgecolor=SURFACE,
        linewidth=0.8,
    )
    ax.set_xlabel("Tasa de reemplazo (pensión / salario promedio de cotización)")
    ax.set_ylabel("Agentes")
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    for p, v in zip([10, 50, 90], [pcts[0], pcts[2], pcts[4]], strict=True):
        ax.axvline(v, color=INK2, linewidth=1.2, linestyle="--", alpha=0.75)
        ax.text(
            v,
            ax.get_ylim()[1] * 0.97,
            f"p{p}: {v:.2f}",
            rotation=90,
            va="top",
            ha="right",
            fontsize=8.5,
            color=INK2,
        )
    ax.set_title(
        f"Distribución de tasa de reemplazo — cohorte {cohorte} "
        f"(retiros {cohorte - ventana}-{cohorte + ventana}), escenario base\n"
        f"p10={pcts[0]:.2f} · p25={pcts[1]:.2f} · p50={pcts[2]:.2f} · "
        f"p75={pcts[3]:.2f} · p90={pcts[4]:.2f} · n={len(tr)} agentes",
        fontsize=11,
        color=INK,
        loc="left",
        pad=12,
    )
    fig.text(
        0.01,
        -0.02,
        "Incluye complemento FPB. Tasa=0: retiro sin semanas suficientes "
        "(negativa de pensión). Recortado en 1.5 para lectura.",
        fontsize=8.5,
        color=MUTED,
    )
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
