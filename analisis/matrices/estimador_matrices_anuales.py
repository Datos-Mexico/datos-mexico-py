"""Estimador DEFINITIVO de matrices de transición ANUALES — Fase 2.5.

Reemplaza las matrices v1 del smoke test (trimestrales 2024T3→T4, P^4).
Tres cambios sobre el pipeline de Fase 2 (estimador_matrices.py):

1. PAR ANUAL directo: 1ª↔5ª entrevista de la misma persona (t → t+4
   trimestres). Merge por la llave de Fase 1 + filtro n_ent=1 en t y
   n_ent=5 en t+4 (la llave identifica el slot muestral y se REUTILIZA
   entre hogares al rotar el panel: sin el filtro n_ent, 62% de "matches"
   espurios a 4 trimestres). Checks: sexo igual, delta-eda ∈ {0,1,2}.
   Sin supuesto Markov intra-año, sin P^4.
2. CINCO estados (Opción A): formal_IMSS, formal_ISSSTE, informal,
   desempleado, fuera_PEA. imssissste: 1=IMSS, 2=ISSSTE, 3=Otras
   instituciones (→ informal, con nota), 4=no recibe, 5=no especificado.
3. APILADO 2015-2024: los 27 pares (t, t+4) con t ∈ 2015T1-2018T4 y
   2021T3-2024T1. Excluidos los 10 pares con t o t+4 en 2020T1-2021T2
   (COVID: 2020T2 sin microdatos ENOE — ETOE telefónica; ENOE-N con
   levantamiento mixto hasta 2021T2).

Estimador idéntico a Fase 2: conteo condicional ponderado (fac_tri de t)
+ shrinkage Dirichlet por fila (kappa=5, prior = marginal 5x5 del
quinquenio sobre el panel apilado). baja_confianza si n_fila < 30.
Attrition anual (Fase 0, par 2023T1↔2024T1): máx |sesgo| 1.15 pp,
sub-representa formal_IMSS (−0.7 pp); sin IPW (umbral 2 pp).

Uso:
    python estimador_matrices_anuales.py ejemplo  # checkpoint (a)(b)(c)
    python estimador_matrices_anuales.py full     # CSV+README (tras OK)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).parent
RUTA_PICKLES = Path(
    "/private/tmp/claude-501/-Users-andrebutron-datos-mexico-datos-mexico-py/"
    "243b3eaf-791c-4f71-9a38-3c27a14becab/scratchpad"
)
CACHE_PANEL = RUTA_PICKLES / "panel_apilado_2015_2024.pkl"

LLAVE = ["cd_a", "ent", "con", "v_sel", "n_hog", "h_mud", "n_ren"]
ESTADOS = ["formal_IMSS", "formal_ISSSTE", "informal", "desempleado", "fuera_PEA"]
KAPPA = 5.0
GRUPOS_EDAD = [f"{a}-{a + 4}" for a in range(25, 65, 5)]
SEXOS = {1: "hombre", 2: "mujer"}
ESCOLARIDADES = ["basica-", "media_sup", "superior"]
NUMERICAS = ["sex", "eda", "clase1", "clase2", "imssissste", "fac_tri",
             "c_res", "r_def", "anios_esc", "n_ent"]

# 27 pares apilados; COVID_EXCLUIDOS documentado en el README
PARES_T = (
    [f"{y}T{q}" for y in range(2015, 2019) for q in (1, 2, 3, 4)]
    + ["2021T3", "2021T4"]
    + [f"{y}T{q}" for y in range(2022, 2024) for q in (1, 2, 3, 4)]
    + ["2024T1"]
)
COVID_EXCLUIDOS = (
    [f"2019T{q}" for q in (1, 2, 3, 4)]
    + [f"2020T{q}" for q in (1, 2, 3, 4)]
    + ["2021T1", "2021T2"]
)


def mas_4_trimestres(t: str) -> str:
    anio, q = int(t[:4]), int(t[-1])
    return f"{anio + 1}T{q}"


def carga_trimestre(periodo: str) -> pd.DataFrame:
    df = pd.read_pickle(RUTA_PICKLES / f"sdem_{periodo}_v3.pkl")
    for c in NUMERICAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["llave"] = df[LLAVE].astype(str).agg("|".join, axis=1)
    return df


def filtra_universo(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        df["clase1"].isin([1, 2]) & (df["r_def"] == 0) & (df["c_res"] != 3)
    ].copy()


def estado_laboral(df: pd.DataFrame) -> pd.Series:
    """Opción A, 5 estados (diccionario ENOE N, campo IMSSISSSTE).

    formal_IMSS = clase2=1 & imssissste=1; formal_ISSSTE = clase2=1 &
    imssissste=2; informal = clase2=1 & imssissste ∈ {3,4,5} (el código 3
    "Otras instituciones" va a informal, nota en README); desempleado =
    clase2=2; fuera_PEA = clase1=2. imssissste NA en ocupados → NA
    (excluido, contado en bitácora), como en Fase 2.
    """
    est = pd.Series(pd.NA, index=df.index, dtype="object")
    ocupado = df["clase2"] == 1
    est[ocupado & (df["imssissste"] == 1)] = "formal_IMSS"
    est[ocupado & (df["imssissste"] == 2)] = "formal_ISSSTE"
    est[ocupado & df["imssissste"].isin([3, 4, 5])] = "informal"
    est[df["clase2"] == 2] = "desempleado"
    est[df["clase1"] == 2] = "fuera_PEA"
    return est


def arma_par(t: str, t4: str) -> tuple[pd.DataFrame, dict]:
    """Panel de UN par (t, t+4): merge 1ª↔5ª + checks. Devuelve (panel, bit)."""
    a = filtra_universo(carga_trimestre(t))
    b = filtra_universo(carga_trimestre(t4))
    n1 = a[a["n_ent"] == 1]
    m = n1.merge(
        b.loc[b["n_ent"] == 5,
              ["llave", "sex", "eda", "clase1", "clase2", "imssissste"]],
        on="llave", how="inner", suffixes=("", "_t4"),
    )
    bit = {"par": f"{t}->{t4}", "n_ent1": len(n1), "limpios_1a5": len(m)}

    deda = m["eda_t4"] - m["eda"]
    inconsistente = (m["sex"] != m["sex_t4"]) | ~deda.isin([0, 1, 2])
    bit["descartes_inconsistencia"] = int(inconsistente.sum())
    m = m[~inconsistente].copy()
    bit["consistentes"] = len(m)
    bit["tasa_match_pct"] = round(100 * len(m) / len(n1), 2)
    bit["anomalo"] = bit["tasa_match_pct"] < 70 or bit["tasa_match_pct"] > 90

    m["estado_origen"] = estado_laboral(m)
    m["estado_destino"] = estado_laboral(
        m[["clase1_t4", "clase2_t4", "imssissste_t4"]].rename(
            columns=lambda c: c.removesuffix("_t4"))
    )
    bit["estado_na"] = int(
        m["estado_origen"].isna().sum() + m["estado_destino"].isna().sum()
    )
    m = m.dropna(subset=["estado_origen", "estado_destino"])

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
    bit["panel_25_64"] = len(m)
    m["par"] = f"{t}->{t4}"
    cols = ["par", "fac_tri", "estado_origen", "estado_destino",
            "grupo_edad", "sexo", "escolaridad"]
    return m[cols], bit


def arma_panel_apilado(usar_cache: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apila los 27 pares. Devuelve (panel, bitácora por par)."""
    if usar_cache and CACHE_PANEL.exists():
        cache = pd.read_pickle(CACHE_PANEL)
        return cache["panel"], cache["bitacora"]
    paneles, bits = [], []
    for t in PARES_T:
        t4 = mas_4_trimestres(t)
        panel, bit = arma_par(t, t4)
        paneles.append(panel)
        bits.append(bit)
        print(f"  {bit['par']}: n_ent1={bit['n_ent1']:,} "
              f"consistentes={bit['consistentes']:,} "
              f"tasa={bit['tasa_match_pct']}%"
              f"{'  *** ANÓMALO ***' if bit['anomalo'] else ''}", flush=True)
    panel = pd.concat(paneles, ignore_index=True)
    bitacora = pd.DataFrame(bits)
    pd.to_pickle({"panel": panel, "bitacora": bitacora}, CACHE_PANEL)
    return panel, bitacora


# ---------------- estimador (idéntico a Fase 2, ahora 5x5) ----------------
def matriz_cruda(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    w = df.pivot_table(index="estado_origen", columns="estado_destino",
                       values="fac_tri", aggfunc="sum", fill_value=0,
                       observed=True)
    n = df.pivot_table(index="estado_origen", columns="estado_destino",
                       values="fac_tri", aggfunc="size", fill_value=0,
                       observed=True)
    w = w.reindex(index=ESTADOS, columns=ESTADOS, fill_value=0).astype(float)
    n = n.reindex(index=ESTADOS, columns=ESTADOS, fill_value=0).astype(int)
    p = w.div(w.sum(axis=1), axis=0)
    return p, w, n


def suaviza(p_perfil: pd.DataFrame, n_perfil: pd.DataFrame,
            p_prior: pd.DataFrame, kappa: float) -> pd.DataFrame:
    n_row = n_perfil.sum(axis=1).astype(float)
    out = p_perfil.copy()
    for i in ESTADOS:
        if n_row[i] == 0:
            out.loc[i] = np.nan
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


# ---------------------------------------------------------------- modos
def ejemplo(panel: pd.DataFrame, bitacora: pd.DataFrame) -> None:
    """Checkpoint: (a) pares apilados, (b) matriz ejemplo, (c) permanencia."""
    print("\n===== (bitácora por par) =====")
    print(bitacora.to_string(index=False))
    print("\n===== (a) PARES APILADOS =====")
    print(f"pares: {len(bitacora)}  observaciones panel 25-64: {len(panel):,}")

    priors = priors_por_edad(panel)
    sel = panel[(panel["sexo"] == "hombre") & (panel["grupo_edad"] == "30-34")
                & (panel["escolaridad"] == "superior")]
    p, _, n = matriz_cruda(sel)
    ps = suaviza(p, n, priors["30-34"], KAPPA)
    valida(ps, "ejemplo")
    print(f"\n===== (b) PERFIL hombre | 30-34 | superior (n={len(sel):,}) =====")
    print("\nn sin ponderar por fila origen:")
    print(n.sum(axis=1).to_string())
    print(f"\nmatriz 5x5 suavizada (kappa={KAPPA:g}):")
    print(ps.round(4).to_string())
    print("\nmatriz cruda (sin suavizar), para referencia:")
    print(p.round(4).to_string())
    perm = ps.loc["formal_IMSS", "formal_IMSS"]
    print(f"\n===== (c) permanencia ANUAL formal_IMSS->formal_IMSS: {perm:.4f} =====")


def full(panel: pd.DataFrame, bitacora: pd.DataFrame) -> None:
    priors = priors_por_edad(panel)
    filas, filas_sens = [], []
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
    dest = AQUI / "matrices_anuales_2015_2024.csv"
    out.to_csv(dest, sep="|", index=False)

    sens = pd.DataFrame(filas_sens)
    sens["delta_1_vs_5"] = (sens["p_kappa1"] - sens["p_kappa5"]).abs()
    sens["delta_20_vs_5"] = (sens["p_kappa20"] - sens["p_kappa5"]).abs()
    dest_sens = AQUI / "sensibilidad_kappa_anuales.csv"
    sens.to_csv(dest_sens, sep="|", index=False)

    escribe_readme(bitacora, out, sens, panel)

    filas_perfil = out.drop_duplicates(
        ["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    bc = filas_perfil[filas_perfil["baja_confianza"]]
    print(f"CSV: {dest} ({len(out)} filas)")
    print(f"Sensibilidad: {dest_sens} ({len(sens)} filas)")
    print("\n===== RESUMEN =====")
    n_perf = out.groupby(["grupo_edad", "sexo", "escolaridad"], observed=True).ngroups
    print(f"perfiles: {n_perf} de 48")
    print(f"filas-perfil-origen baja_confianza (n<30): {len(bc)} de {len(filas_perfil)}")
    print("  por estado origen:")
    print(bc.groupby("estado_origen", observed=True).size().to_string())
    print(f"celdas NaN (denominador 0): {int(out.probabilidad.isna().sum())}")
    print("\n3 filas-perfil-origen con menor n sin ponderar:")
    print(filas_perfil.nsmallest(3, "n_muestra_sin_pond")[
        ["grupo_edad", "sexo", "escolaridad", "estado_origen",
         "n_muestra_sin_pond"]].to_string(index=False))
    print(f"sensibilidad: max|p_k1-p_k5|={sens.delta_1_vs_5.max():.5f}  "
          f"max|p_k20-p_k5|={sens.delta_20_vs_5.max():.5f}")


def escribe_readme(bitacora: pd.DataFrame, out: pd.DataFrame,
                   sens: pd.DataFrame, panel: pd.DataFrame) -> None:
    filas_perfil = out.drop_duplicates(
        ["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    bc_por_origen = (filas_perfil[filas_perfil["baja_confianza"]]
                     .groupby("estado_origen", observed=True).size()
                     .rename("filas_baja_confianza"))
    pares_txt = bitacora[["par", "n_ent1", "limpios_1a5", "consistentes",
                          "tasa_match_pct", "anomalo"]].to_markdown(index=False)
    texto = f"""# Matrices de transición laboral ANUALES 5x5 — ENOE 2015-2024 (Fase 2.5)

Sección 6 (Brecha 2). Entregable DEFINITIVO, generado por
`estimador_matrices_anuales.py full`. Reemplaza las matrices v1 del smoke
test (`matrices_transicion_2024T3_2024T4.csv`, trimestrales + P^4).

## Diseño: transición anual directa, panel 1ª↔5ª entrevista

Cada observación es una persona con 1ª entrevista en t y 5ª en t+4
trimestres (un año exacto). La transición anual se estima DIRECTO — sin
supuesto Markov intra-año, sin P^4. Justificación cuantificada: la
permanencia anual formal_IMSS→formal_IMSS del perfil de referencia
(hombre, 30-34, superior) es **0.82 estimada directa** vs **0.49 bajo el
P^4 de las matrices v1 trimestrales** — el supuesto Markov de primer
orden intra-año destruye la dependencia de duración (la permanencia
formal está correlacionada entre trimestres) y sobreestima la rotación.

**Hallazgo llave-slot (Fase 0)**: la llave de Fase 1 (cd_a+ent+con+v_sel+
n_hog+h_mud+n_ren) identifica el SLOT muestral, no a la persona — al
completar un hogar sus 5 entrevistas, el hogar de reemplazo hereda la
llave con n_ent reiniciado. A 4 trimestres un merge sin filtro produce
62% de matches espurios (patrones n_ent 2→1, 3→2…, 31.7% con sexo
inconsistente). Emparejamiento definitivo: llave **+ n_ent=1 en t y
n_ent=5 en t+4**, validación cruzada: 98.6% de los matches con n_ent=1
en origen cae en n_ent=5 en destino. Checks posteriores: sexo igual,
delta-eda ∈ {{0,1,2}} (97.4% de los pares limpios tiene delta = +1
exacto).

## Apilado 2015-2024 y exclusión COVID

{len(bitacora)} pares (t, t+4) apilados: t ∈ 2015T1-2018T4 y 2021T3-2024T1.
**Excluidos** los 10 pares con t o t+4 dentro de 2020T1-2021T2:
t ∈ {{{", ".join(COVID_EXCLUIDOS)}}}. Razones: 2020T2 no tiene microdatos
ENOE (ETOE telefónica); 2020T3-2021T2 es ENOE-N con levantamiento mixto en
retorno gradual. Nota adicional: el apilado cruza el rediseño muestral
post-Censo 2020 (clásica 2015-2019 vs ENOE-N 2021+) — las transiciones son
tasas condicionales, robustas al cambio de marco; el fac_tri 2021T3-T4
pre-CPV subestima niveles pero no afecta proporciones.

## Tasa de emparejamiento por par

tasa_match_pct = consistentes / n_ent=1 del trimestre t (universo
filtrado). Anómalo si <70% o >90%.

{pares_txt}

Rango observado: 73.9%–81.8%, ningún par anómalo. Los pares clásicos
(2015-2018) rondan 80-82%; los ENOE-N post-COVID bajan a 73.9-81.1% (el
mínimo es 2021T3→2022T3, retorno gradual a campo). **Nota descartes
ENOE-N**: los descartes por inconsistencia sexo/edad son ~0 en toda la
era clásica y suben a ~0.5-3.7% por par en ENOE-N (2021T3+) — artefacto
del levantamiento mixto (captura telefónica/presencial), no de la llave.

Panel apilado final (25-64, escolaridad válida): **{len(panel):,}
observaciones**.

## Attrition anual (Fase 0, par de prueba 2023T1↔2024T1)

Shares ponderados (fac_tri) del corte n_ent=1 vs panel emparejado
consistente, 5 estados: máximo |sesgo| = **1.15 pp** (fuera_PEA
sobre-representado +1.15 pp; en el universo de estimación 25-64: +0.89).
**Dirección**: el panel sub-representa formal_IMSS (−0.7 pp) — sesgo leve
hacia estabilidad/inactividad (quien se muda entre olas es más
formal/urbano). Bajo el umbral acordado de 2 pp → **sin IPW**; las
transiciones desde formal quedan estimadas sobre los que permanecen.

## Mapeo variable → estado (Opción A, 5 estados)

Fuente: INEGI, *ENOE N — Estructura de la base de datos* (2022), tabla
`ENOEN_SDEMT`, campo 97 `IMSSISSSTE`: **1 = IMSS, 2 = ISSSTE, 3 = Otras
instituciones, 4 = No recibe atención médica, 5 = No especificado**.
<https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/doc/enoe_n_fd_c_bas_amp.pdf>

| Estado | Regla |
|---|---|
| formal_IMSS | clase2 = 1 AND imssissste = 1 |
| formal_ISSSTE | clase2 = 1 AND imssissste = 2 |
| informal | clase2 = 1 AND imssissste ∈ {{3,4,5}} |
| desempleado | clase2 = 2 |
| fuera_PEA | clase1 = 2 |

**Nota código 3 ("Otras instituciones")**: va a `informal` — es atención
médica no-IMSS/ISSSTE (Pemex, Sedena, privada, etc.); su masa es chica y
no es separable en un sexto estado con n razonable. La descontaminación
relevante (36% de ISSSTE dentro de informal-superior en v1) la resuelve el
estado formal_ISSSTE explícito.

**Nota interpretativa**: transiciones como desempleado→formal_IMSS ≈ 0.32
(perfil de referencia) pueden parecer altas frente a intuiciones
trimestrales, pero son transiciones a **12 meses**: consistentes con las
duraciones cortas del desempleo en México (mediana < 3 meses), donde el
estado "desempleado" observado en t rara vez persiste un año.

## Desagregación y estimador (idéntico a Fase 2)

- 8 quinquenios 25-29…60-64 (eda en t) × 2 sexos × 3 escolaridades
  (anios_esc en t: ≤9, 10-12, ≥13; 99/NA excluido) = 48 perfiles 5x5.
- Conteo condicional ponderado con fac_tri de t. Shrinkage Dirichlet por
  fila: p = (n_fila·p_pond + kappa·P_quinquenio) / (n_fila + kappa),
  n_fila sin ponderar, prior = matriz marginal 5x5 del quinquenio sobre el
  panel apilado. **kappa = 5**. Sensibilidad kappa ∈ {{1,5,20}} en
  `sensibilidad_kappa.csv`: max|Δ| = {sens.delta_1_vs_5.max():.5f} (κ1 vs
  κ5) y {sens.delta_20_vs_5.max():.5f} (κ20 vs κ5).
- baja_confianza si n_fila < 30: {len(filas_perfil[filas_perfil["baja_confianza"]])}
  de {len(filas_perfil)} filas-perfil-origen.

{bc_por_origen.to_markdown() if len(bc_por_origen) else "(ninguna fila bajo el umbral)"}

## Archivos

- `matrices_anuales_2015_2024.csv` — {len(out)} filas (48×5×5), formato
  long `|`: grupo_edad|sexo|escolaridad|estado_origen|estado_destino|
  probabilidad|n_muestra_pond|n_muestra_sin_pond|baja_confianza.
- `sensibilidad_kappa_anuales.csv` — mismas llaves + p_kappa1|p_kappa5|
  p_kappa20 y deltas absolutos vs κ=5.
- Estimación: `estimador_matrices_anuales.py` (pickles sdem por trimestre
  en scratchpad de sesión, descarga reproducible con descarga_enoe.py
  parametrizado).
"""
    dest = AQUI / "README_matrices_anuales.md"
    dest.write_text(texto, encoding="utf-8")
    print(f"README: {dest}")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "ejemplo"
    print("Armando panel apilado (27 pares)…", flush=True)
    panel, bitacora = arma_panel_apilado()
    (ejemplo if modo == "ejemplo" else full)(panel, bitacora)
