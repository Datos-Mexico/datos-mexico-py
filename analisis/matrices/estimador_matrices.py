"""Estimador de matrices de transición heterogéneas ENOE 2024T3→2024T4.

Sección 6, Brecha 2. Decisiones cerradas de Fase 2:
- Universo: clase1 ∈ {1,2} AND r_def=0 AND c_res≠3, en ambos trimestres.
- Estados (contrato §4): formal_IMSS = clase2=1 & imssissste=1 (solo IMSS);
  informal = clase2=1 & imssissste∈{2,3,4,5}; desempleado = clase2=2;
  fuera_PEA = clase1=2.
- Matches inconsistentes (sexo distinto o Δeda ∉ {0,1}) descartados.
- Perfiles: 8 quinquenios [25-64] × 2 sexos × 3 escolaridades = 48.
- Escolaridad (anios_esc en t): básica- ≤9, media_sup 10-12, superior ≥13;
  99/NA excluido.
- Estimador: conteo condicional ponderado (fac_tri de t) + shrinkage
  Dirichlet por fila hacia la matriz marginal del quinquenio:
  p = (n_row * p_pond + kappa * P_edad) / (n_row + kappa), con n_row el
  conteo SIN ponderar de la fila (tamaño efectivo del prior = kappa
  pseudo-observaciones).
- baja_confianza si n_sin_ponderar < 30 en la fila-perfil.

Uso:
    python estimador_matrices.py ejemplo   # matriz hombre 30-34 superior
    python estimador_matrices.py full      # CSV completo + README (tras aprobación)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRATCH = Path(__file__).parent
LLAVE = ["cd_a", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren"]
ESTADOS = ["formal_IMSS", "informal", "desempleado", "fuera_PEA"]
KAPPA = 5.0
GRUPOS_EDAD = [f"{a}-{a+4}" for a in range(25, 65, 5)]
SEXOS = {1: "hombre", 2: "mujer"}
ESCOLARIDADES = ["basica-", "media_sup", "superior"]


def filtra_universo(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        df["clase1"].isin([1, 2]) & (df["r_def"] == 0) & (df["c_res"] != 3)
    ].copy()


def estado_laboral(df: pd.DataFrame) -> pd.Series:
    """Mapeo cerrado del contrato §4 (diccionario ENOE N: imssissste 1=IMSS)."""
    est = pd.Series(pd.NA, index=df.index, dtype="object")
    ocupado = df["clase2"] == 1
    est[ocupado & (df["imssissste"] == 1)] = "formal_IMSS"
    est[ocupado & df["imssissste"].isin([2, 3, 4, 5])] = "informal"
    est[df["clase2"] == 2] = "desempleado"
    est[df["clase1"] == 2] = "fuera_PEA"
    return est


def arma_panel() -> tuple[pd.DataFrame, dict]:
    """Merge T3→T4 sobre el universo filtrado; devuelve panel y bitácora."""
    t3 = filtra_universo(pd.read_pickle(SCRATCH / "sdem_2024T3_v2.pkl"))
    t4 = filtra_universo(pd.read_pickle(SCRATCH / "sdem_2024T4.pkl"))
    for df in (t3, t4):
        df["llave"] = df[LLAVE].astype(str).agg("|".join, axis=1)
    bit = {"universo_t3": len(t3), "universo_t4": len(t4)}

    m = t3.merge(
        t4[["llave", "sex", "eda", "clase1", "clase2", "imssissste"]],
        on="llave", how="inner", suffixes=("", "_t4"),
    )
    bit["emparejadas"] = len(m)
    bit["tasa_match_pct"] = round(100 * len(m) / len(t3), 2)

    deda = m["eda_t4"] - m["eda"]
    inconsistente = (m["sex"] != m["sex_t4"]) | ~deda.isin([0, 1])
    bit["descartes_inconsistencia"] = int(inconsistente.sum())
    m = m[~inconsistente].copy()

    m["estado_origen"] = estado_laboral(m)
    m["estado_destino"] = estado_laboral(
        m[["clase1_t4", "clase2_t4", "imssissste_t4"]].rename(
            columns=lambda c: c.removesuffix("_t4"))
    )
    bit["estado_origen_na"] = int(m["estado_origen"].isna().sum())
    bit["estado_destino_na"] = int(m["estado_destino"].isna().sum())
    m = m.dropna(subset=["estado_origen", "estado_destino"])

    # perfiles sobre características en t (T3)
    m = m[m["eda"].between(25, 64)].copy()
    m["grupo_edad"] = pd.cut(
        m["eda"], bins=range(25, 70, 5), right=False, labels=GRUPOS_EDAD
    )
    m["sexo"] = m["sex"].map(SEXOS)
    m["escolaridad"] = pd.cut(
        m["anios_esc"].where(m["anios_esc"] != 99),
        bins=[-1, 9, 12, 90], labels=ESCOLARIDADES,
    )
    bit["escolaridad_na_excluida"] = int(m["escolaridad"].isna().sum())
    m = m.dropna(subset=["escolaridad"])
    bit["panel_final_25_64"] = len(m)
    return m, bit


def matriz_cruda(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve (prob ponderada, suma fac_tri, n sin ponderar) 4×4."""
    w = df.pivot_table(index="estado_origen", columns="estado_destino",
                       values="fac_tri", aggfunc="sum", fill_value=0,
                       observed=True)
    n = df.pivot_table(index="estado_origen", columns="estado_destino",
                       values="fac_tri", aggfunc="size", fill_value=0,
                       observed=True)
    w = w.reindex(index=ESTADOS, columns=ESTADOS, fill_value=0).astype(float)
    n = n.reindex(index=ESTADOS, columns=ESTADOS, fill_value=0).astype(int)
    p = w.div(w.sum(axis=1), axis=0)  # filas sin masa quedan NaN
    return p, w, n


def suaviza(p_perfil: pd.DataFrame, n_perfil: pd.DataFrame,
            p_prior: pd.DataFrame, kappa: float) -> pd.DataFrame:
    """Posterior media Dirichlet: alpha_ij = kappa * P_edad_ij."""
    n_row = n_perfil.sum(axis=1).astype(float)
    out = p_perfil.copy()
    for i in ESTADOS:
        if n_row[i] == 0:
            out.loc[i] = np.nan  # denominador 0: marcada, no rellenada
        else:
            out.loc[i] = (
                n_row[i] * p_perfil.loc[i].fillna(0) + kappa * p_prior.loc[i]
            ) / (n_row[i] + kappa)
    return out


def valida(p: pd.DataFrame, contexto: str) -> None:
    validas = p.dropna(how="all")
    sumas = validas.sum(axis=1)
    assert np.allclose(sumas, 1.0, atol=1e-9), f"{contexto}: filas no suman 1: {sumas}"
    assert ((validas >= 0) & (validas <= 1)).all().all(), f"{contexto}: fuera de [0,1]"


def priors_por_edad(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    priors = {}
    for g in GRUPOS_EDAD:
        p, _, _ = matriz_cruda(panel[panel["grupo_edad"] == g])
        valida(p, f"prior {g}")
        priors[g] = p
    return priors


def ejemplo(panel: pd.DataFrame, bit: dict) -> None:
    priors = priors_por_edad(panel)
    sel = panel[(panel["sexo"] == "hombre") & (panel["grupo_edad"] == "30-34")
                & (panel["escolaridad"] == "superior")]
    p, _, n = matriz_cruda(sel)
    print(f"bitácora: {bit}")
    print(f"\nPERFIL hombre | 30-34 | superior — n sin ponderar = {len(sel)}")
    print("\nn sin ponderar por fila:", n.sum(axis=1).to_dict())
    print("\n-- Matriz cruda ponderada (fac_tri) --")
    print(p.round(4).to_string())
    print("\n-- Prior (marginal quinquenio 30-34) --")
    print(priors["30-34"].round(4).to_string())
    for k in (1.0, 5.0, 20.0):
        ps = suaviza(p, n, priors["30-34"], k)
        valida(ps, f"ejemplo k={k}")
        tag = " <— ELEGIDO" if k == KAPPA else ""
        print(f"\n-- Suavizada kappa={k:g}{tag} --")
        print(ps.round(4).to_string())
        print(f"   sumas por fila: {ps.sum(axis=1).round(12).to_dict()}")
        dmax = (ps - p.fillna(0)).abs().max().max()
        print(f"   max |Δ| vs. cruda: {dmax:.5f}")


def sesgo_issste(panel: pd.DataFrame) -> pd.DataFrame:
    """% ponderado del estado informal (en t) con imssissste ∈ {2,3}."""
    inf = panel[panel["estado_origen"] == "informal"]
    filas = []
    for esc in ESCOLARIDADES:
        sub = inf[inf["escolaridad"] == esc]
        w_tot = sub["fac_tri"].sum()
        w_23 = sub.loc[sub["imssissste"].isin([2, 3]), "fac_tri"].sum()
        w_2 = sub.loc[sub["imssissste"] == 2, "fac_tri"].sum()
        filas.append({
            "escolaridad": esc,
            "pct_informal_imssissste_2_3": round(100 * w_23 / w_tot, 2),
            "pct_solo_issste_cod2": round(100 * w_2 / w_tot, 2),
            "n_sin_pond_informal": len(sub),
        })
    return pd.DataFrame(filas)


def full(panel: pd.DataFrame, bit: dict) -> None:
    priors = priors_por_edad(panel)
    filas = []
    filas_sens = []
    for g in GRUPOS_EDAD:
        for sx in SEXOS.values():
            for esc in ESCOLARIDADES:
                sel = panel[(panel["grupo_edad"] == g) & (panel["sexo"] == sx)
                            & (panel["escolaridad"] == esc)]
                p, w, n = matriz_cruda(sel)
                suav = {k: suaviza(p, n, priors[g], k) for k in (1.0, 5.0, 20.0)}
                for k, pk in suav.items():
                    valida(pk, f"{g}|{sx}|{esc} k={k}")
                ps = suav[KAPPA]
                n_row = n.sum(axis=1)
                w_row = w.sum(axis=1)
                for eo in ESTADOS:
                    for ed in ESTADOS:
                        filas.append({
                            "grupo_edad": g, "sexo": sx, "escolaridad": esc,
                            "estado_origen": eo, "estado_destino": ed,
                            "probabilidad": ps.loc[eo, ed],
                            "n_muestra_pond": w_row[eo],
                            "n_muestra_sin_pond": n_row[eo],
                            "baja_confianza": bool(n_row[eo] < 30),
                        })
                        filas_sens.append({
                            "grupo_edad": g, "sexo": sx, "escolaridad": esc,
                            "estado_origen": eo, "estado_destino": ed,
                            "n_muestra_sin_pond": n_row[eo],
                            "p_kappa1": suav[1.0].loc[eo, ed],
                            "p_kappa5": suav[5.0].loc[eo, ed],
                            "p_kappa20": suav[20.0].loc[eo, ed],
                        })
    out = pd.DataFrame(filas)
    dest = SCRATCH / "matrices_transicion_2024T3_2024T4.csv"
    out.to_csv(dest, sep="|", index=False)

    sens = pd.DataFrame(filas_sens)
    sens["delta_1_vs_5"] = (sens["p_kappa1"] - sens["p_kappa5"]).abs()
    sens["delta_20_vs_5"] = (sens["p_kappa20"] - sens["p_kappa5"]).abs()
    dest_sens = SCRATCH / "sensibilidad_kappa.csv"
    sens.to_csv(dest_sens, sep="|", index=False)

    issste = sesgo_issste(panel)
    escribe_readme(bit, out, sens, issste)

    # -------- RESUMEN consola --------
    perfiles = out.groupby(["grupo_edad", "sexo", "escolaridad"],
                           observed=True).ngroups
    filas_perfil = out.drop_duplicates(
        ["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    bc = filas_perfil[filas_perfil["baja_confianza"]]
    print(f"CSV: {dest} ({len(out)} filas)")
    print(f"Sensibilidad: {dest_sens} ({len(sens)} filas)")
    print("\n===== RESUMEN =====")
    print(f"perfiles estimados: {perfiles} de 48")
    print(f"filas-perfil-origen baja_confianza (n<30): {len(bc)} de "
          f"{len(filas_perfil)}")
    print("  por estado origen:")
    print(bc.groupby('estado_origen', observed=True).size().to_string())
    print(f"celdas NaN (denominador 0): {int(out.probabilidad.isna().sum())}")
    print("\nsesgo ISSSTE (% ponderado del estado informal con "
          "imssissste 2/3):")
    print(issste.to_string(index=False))
    print("\n3 filas-perfil-origen con menor n sin ponderar:")
    print(filas_perfil.nsmallest(3, "n_muestra_sin_pond")[
        ["grupo_edad", "sexo", "escolaridad", "estado_origen",
         "n_muestra_sin_pond"]].to_string(index=False))
    print(f"\nsensibilidad global: max|p_k1-p_k5|={sens.delta_1_vs_5.max():.5f}"
          f"  max|p_k20-p_k5|={sens.delta_20_vs_5.max():.5f}")
    print(f"bitácora: {bit}")


def escribe_readme(bit: dict, out: pd.DataFrame, sens: pd.DataFrame,
                   issste: pd.DataFrame) -> None:
    filas_perfil = out.drop_duplicates(
        ["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    bc_por_origen = (filas_perfil[filas_perfil["baja_confianza"]]
                     .groupby("estado_origen", observed=True).size()
                     .rename("filas_baja_confianza"))
    texto = f"""# Matrices de transición laboral heterogéneas — ENOE 2024T3→2024T4

Sección 6 (Brecha 2) del motor de microsimulación. Entregable de Fase 2,
generado por `estimador_matrices.py full`. **v1 — un solo par trimestral.**

## Rango temporal y limitación declarada

Un único par de trimestres emparejados: **2024T3 → 2024T4**. Esto implica:
(i) la **estacionalidad Q3→Q4 no está controlada** (fin de año concentra
contrataciones formales de temporada y salidas escolares hacia la PEA);
(ii) **n delgado** en las filas de origen `desempleado` y `fuera_PEA` de
varios perfiles. La matriz FINAL del paper requiere **apilar múltiples
pares trimestrales consecutivos (Fase 2.5, pendiente)**; esta v1 sirve para
validar el pipeline y la forma de la heterogeneidad.

## Mapeo variable → estado (contrato §4)

Fuente oficial: INEGI, *ENOE N — Estructura de la base de datos* (2022),
tabla `ENOEN_SDEMT`, campo 97 `IMSSISSSTE` "Instituciones de atención
médica": **1 = IMSS, 2 = ISSSTE, 3 = Otras instituciones, 4 = No recibe
atención médica, 5 = No especificado**.
<https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_fd_c_bas_amp.pdf>
(págs. 24–25).

| Estado | Regla |
|---|---|
| formal_IMSS | clase2 = 1 AND imssissste = 1 (solo IMSS) |
| informal | clase2 = 1 AND imssissste ∈ {{2,3,4,5}} |
| desempleado | clase2 = 2 |
| fuera_PEA | clase1 = 2 (incluye clase2 ∈ {{3,4}}) |

### Decisión ISSSTE (Opción B) y sesgo cuantificado

En v1 los ocupados con ISSSTE (imssissste=2) y otras instituciones (=3) se
colapsan en `informal`. Porcentaje ponderado (fac_tri) del estado informal
que en realidad tiene seguridad social institucional, por escolaridad:

{issste.to_markdown(index=False)}

**Limitación v1 declarada:** sus transiciones sectoriales quedan
aproximadas; el motor los reinyecta vía `sector_issste`.

## Universo y emparejamiento

- Universo (ambos trimestres, antes del merge): clase1 ∈ {{1,2}} AND
  r_def = 0 AND c_res ≠ 3. T3: {bit['universo_t3']:,} filas; T4:
  {bit['universo_t4']:,}.
- Llave persona: cd_a+ent+con+v_sel+n_hog+h_mud+n_ren (única en ambos
  trimestres; `h_mud` extraída de `extras_jsonb`).
- Emparejadas: {bit['emparejadas']:,} ({bit['tasa_match_pct']}% de T3).
- **Matches descartados por inconsistencia** (sexo distinto o Δeda ∉
  {{0,1}}): **{bit['descartes_inconsistencia']:,}**.
- Escolaridad no especificada (anios_esc=99) excluida:
  {bit['escolaridad_na_excluida']} filas.
- Panel final 25–64: {bit['panel_final_25_64']:,} observaciones.

## Desagregación (SPEC §6)

- Edad: quinquenios 25-29 … 60-64 sobre `eda` en t (2024T3).
- Sexo: sex 1=hombre, 2=mujer.
- Escolaridad: **`anios_esc` en t** (NIV_INS descartada: su código 4
  colapsa "medio superior y superior"). Cortes: básica- ≤ 9 años,
  media_sup 10–12, superior ≥ 13.
- 48 perfiles × matriz 4×4, formato long, separador `|`.

## Estimador y suavizamiento (SPEC §5)

Conteo condicional ponderado con `fac_tri` de t. Shrinkage Dirichlet por
fila: alpha_ij = kappa · P_marginal_edad_ij, donde P_marginal_edad es la
matriz cruda del quinquenio (colapsando sexo y escolaridad). Posterior:
p_ij = (n_fila · p_pond_ij + kappa · P_edad_ij) / (n_fila + kappa), con
n_fila el conteo SIN ponderar (kappa = pseudo-observaciones del prior).

- **kappa = 5** (elegido): imperceptible en filas robustas, estabiliza las
  delgadas sin dominarlas. Sensibilidad completa por celda bajo
  kappa ∈ {{1,5,20}} en `sensibilidad_kappa.csv`; máximo |Δp| global:
  {sens.delta_1_vs_5.max():.5f} (κ=1 vs 5) y {sens.delta_20_vs_5.max():.5f}
  (κ=20 vs 5).
- **Celdas suavizadas**: todas las filas con n_fila > 0 reciben el
  shrinkage; el efecto es material solo donde `baja_confianza=True`.
- Filas con denominador 0: probabilidad = NaN (marcadas, nunca cero
  silencioso) y baja_confianza=True.

## Baja confianza (n sin ponderar < 30 en la fila-perfil)

{len(filas_perfil[filas_perfil['baja_confianza']])} de {len(filas_perfil)}
filas-perfil-origen. Por estado de origen:

{bc_por_origen.to_markdown()}

Las 14 son filas de origen `desempleado` (mujeres 45+ y perfiles de alta
escolaridad en edades mayores). `fuera_PEA` no cae bajo el umbral en
ningún perfil: aun siendo minoritario en flujos, su stock en 25–64 es
suficientemente grande. El piso muestral está en desempleadas de 60–64
(n=4).

## Archivos

- `matrices_transicion_2024T3_2024T4.csv` — 768 filas (48×4×4), columnas
  SPEC §7: grupo_edad|sexo|escolaridad|estado_origen|estado_destino|
  probabilidad|n_muestra_pond|n_muestra_sin_pond|baja_confianza.
- `sensibilidad_kappa.csv` — mismas llaves + p_kappa1|p_kappa5|p_kappa20 y
  deltas absolutos vs κ=5.
- Attrition del panel (Fase 1): sesgo ≤ 0.3 pp por estado; sin corrección
  en v1.
"""
    dest = SCRATCH / "README_matrices.md"
    dest.write_text(texto, encoding="utf-8")
    print(f"README: {dest}")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "ejemplo"
    panel, bit = arma_panel()
    (ejemplo if modo == "ejemplo" else full)(panel, bit)
