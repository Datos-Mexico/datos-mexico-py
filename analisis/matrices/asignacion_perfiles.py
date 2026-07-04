"""Asignación de matrices P^(g) a agentes del motor (Fase 4, Paso 2).

Tres piezas, todas fuera de motor/motor.py:
1. grupo_edad_de: binning edad float → quinquenio del CSV, con fallbacks v1
   documentados ([15,25) → proxy "25-29"; ≥65 → None, no transitan).
2. asigna_escolaridad: muestrea escolaridad de la marginal ENOE 2024T3
   ponderada (fac_tri) por (sexo x grupo_edad) — NO uniforme.
   APROXIMACIÓN v1: asignación estática al nacer del agente; la
   escolaridad no evoluciona en el tiempo.
3. asigna_matriz: lookup (grupo_edad, sexo_motor, escolaridad) → P 4x4,
   con fallback logueado a la marginal del grupo_edad (ponderada por
   n_muestra_pond de cada fila-perfil) si el perfil no existiera.

La marginal de escolaridad se deriva del cache de microdatos de Fase 1
(pickle en scratchpad) y se persiste en marginal_escolaridad_2024T3.csv
junto a este módulo, para no depender del pickle de 52 MB en corridas
posteriores. Mismo universo y cortes que estimador_matrices.py.
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from carga_matrices import cargar_matrices

logger = logging.getLogger(__name__)

AQUI = Path(__file__).parent
RUTA_SDEM_T3 = Path(
    "/private/tmp/claude-501/-Users-andrebutron-datos-mexico-datos-mexico-py/"
    "398128e3-c9a5-48ed-ac55-59eef2d16e9a/scratchpad/sdem_2024T3_v2.pkl"
)
RUTA_MARGINAL_CSV = AQUI / "marginal_escolaridad_2024T3.csv"

GRUPOS_EDAD = [f"{a}-{a + 4}" for a in range(25, 65, 5)]
ESCOLARIDADES = ["basica-", "media_sup", "superior"]
ESC_A_IDX = {e: i for i, e in enumerate(ESCOLARIDADES)}


# ---------------------------------------------------------------- pieza 1
def grupo_edad_de(edad: float) -> str | None:
    """Mapea edad float al quinquenio string del CSV.

    Fallbacks v1 (decisión smoke test):
    - edad en [15, 25) → "25-29" como proxy (la ENOE panel estimado
      arranca en 25; los jóvenes usan el perfil más cercano).
    - edad ≥ 65 → None: no transitan (el motor ya los saca del mercado
      vía activo = edad < edad_ret). El lookup maneja None sin romperse.
    """
    if edad >= 65:
        return None
    if edad < 25:
        return GRUPOS_EDAD[0]  # proxy 15-24 → "25-29"
    return GRUPOS_EDAD[min(int((edad - 25) // 5), len(GRUPOS_EDAD) - 1)]


# ---------------------------------------------------------------- pieza 2
def marginal_escolaridad(ruta_pickle: Path = RUTA_SDEM_T3) -> pd.DataFrame:
    """Marginal ponderada (fac_tri) de escolaridad por (sexo_motor, grupo_edad).

    Universo y cortes idénticos a estimador_matrices.py: clase1 ∈ {1,2},
    r_def=0, c_res≠3, eda 25-64, anios_esc≠99. Se cachea a CSV chico.
    """
    if RUTA_MARGINAL_CSV.exists():
        m = pd.read_csv(RUTA_MARGINAL_CSV, index_col=[0, 1])
        logger.info("Marginal escolaridad cargada de cache: %s", RUTA_MARGINAL_CSV)
        return m

    df = pd.read_pickle(ruta_pickle)
    df = df[df["clase1"].isin([1, 2]) & (df["r_def"] == 0) & (df["c_res"] != 3)]
    df = df[df["eda"].between(25, 64)].copy()
    df["grupo_edad"] = pd.cut(
        df["eda"], bins=range(25, 70, 5), right=False, labels=GRUPOS_EDAD
    )
    df["sexo_motor"] = df["sex"].map({1: 0, 2: 1})
    df["escolaridad"] = pd.cut(
        df["anios_esc"].where(df["anios_esc"] != 99),
        bins=[-1, 9, 12, 90], labels=ESCOLARIDADES,
    )
    df = df.dropna(subset=["escolaridad"])
    w = df.pivot_table(
        index=["sexo_motor", "grupo_edad"], columns="escolaridad",
        values="fac_tri", aggfunc="sum", observed=True,
    )
    m = w.div(w.sum(axis=1), axis=0)[ESCOLARIDADES]
    m.to_csv(RUTA_MARGINAL_CSV)
    logger.info(
        "Marginal escolaridad derivada de %s (%d obs) y cacheada en %s",
        ruta_pickle.name, len(df), RUTA_MARGINAL_CSV,
    )
    return m


_advertencia_escolaridad_emitida = False


def asigna_escolaridad(
    edad: np.ndarray, sexo: np.ndarray, rng: np.random.Generator,
    marginal: pd.DataFrame,
) -> np.ndarray:
    """Asigna escolaridad muestreando la marginal ENOE por (sexo, grupo_edad).

    APROXIMACIÓN v1: estática al nacer del agente, no evoluciona.
    Los ≥65 usan la marginal de "60-64" (inerte: no transitan).
    """
    global _advertencia_escolaridad_emitida
    if not _advertencia_escolaridad_emitida:
        logger.warning(
            "ESCOLARIDAD v1: asignación estática al crear al agente (no "
            "evoluciona en el tiempo); [15,25) usa marginal de 25-29 (proxy)."
        )
        _advertencia_escolaridad_emitida = True
    esc = np.empty(len(edad), dtype=object)
    grupos = np.array([grupo_edad_de(e) or GRUPOS_EDAD[-1] for e in edad])
    n_65 = int((np.array([grupo_edad_de(e) for e in edad]) == None).sum())  # noqa: E711
    if n_65:
        logger.info(
            "Agentes ≥65: %d — escolaridad asignada con marginal 60-64 "
            "(inerte, no transitan)", n_65,
        )
    for sx in (0, 1):
        for g in GRUPOS_EDAD:
            sel = (sexo == sx) & (grupos == g)
            if not sel.any():
                continue
            p = marginal.loc[(sx, g)].to_numpy(dtype=float)
            esc[sel] = rng.choice(ESCOLARIDADES, size=int(sel.sum()), p=p)
    return esc


def asigna_escolaridad_idx(
    edad: np.ndarray, sexo: np.ndarray, rng: np.random.Generator,
    marginal: pd.DataFrame,
) -> np.ndarray:
    """Como asigna_escolaridad pero devuelve índices int (motor, Paso 3)."""
    esc = asigna_escolaridad(edad, sexo, rng, marginal)
    return np.array([ESC_A_IDX[e] for e in esc], dtype=int)


# ------------------------------------------------- vectorización (Paso 3)
def construye_tensor(matrices: dict) -> np.ndarray:
    """Tensor (8 grupos_edad, 2 sexos, 3 escolaridades, E, E) row-stochastic.

    E = nº de estados, inferido de las matrices (4 en v1 trimestral, 5 en
    las anuales de Fase 2.5; el orden de estados lo fija el loader que
    produjo el dict: ESTADO_A_IDX o ESTADOS_ANUALES de carga_matrices).
    Permite indexar P^(g) por agente sin romper la vectorización del motor:
    tensor[g_idx, sexo, esc_idx] es la matriz ExE del perfil.
    """
    n_estados = next(iter(matrices.values())).shape[0]
    tensor = np.empty(
        (len(GRUPOS_EDAD), 2, len(ESCOLARIDADES), n_estados, n_estados)
    )
    for gi, g in enumerate(GRUPOS_EDAD):
        for sx in (0, 1):
            for ei, esc in enumerate(ESCOLARIDADES):
                tensor[gi, sx, ei] = matrices[(g, sx, esc)]
    assert np.allclose(tensor.sum(axis=-1), 1.0, atol=1e-9)
    return tensor


def filas_transicion(
    tensor: np.ndarray, edad: np.ndarray, sexo: np.ndarray,
    esc_idx: np.ndarray, estado: np.ndarray,
) -> np.ndarray:
    """Fila origen=estado de P^(g) de cada agente, vectorizado → (n, E).

    Binning con los mismos fallbacks de grupo_edad_de:
    - edad < 25 (incluye edades negativas del backcast) → grupo 0
      (proxy "25-29"); el motor no transiciona a los <15 (activo=False).
    - edad ≥ 65 → clip al grupo 7 ("60-64"), inerte: activo=False en el
      motor (edad < edad_ret), la fila devuelta se descarta.
    """
    g_idx = np.clip(
        (np.floor(edad).astype(int) - 25) // 5, 0, len(GRUPOS_EDAD) - 1
    )
    return tensor[g_idx, sexo, esc_idx, estado]


# ---------------------------------------------------------------- pieza 3
def marginales_por_grupo(
    matrices: dict, ruta_csv: Path | None = None,
    estado_a_idx: dict[str, int] | None = None,
) -> dict[str, np.ndarray]:
    """Matriz marginal ExE por grupo_edad, para fallback del lookup.

    Promedio de los 6 perfiles (2 sexos x 3 escolaridades) del grupo,
    ponderando cada fila-origen por su n_muestra_pond en el CSV.
    Defaults = ruta y estados v1 (4x4); para las anuales 5x5 pasar
    RUTA_CSV_ANUALES y ESTADO_A_IDX_ANUALES de carga_matrices.
    """
    from carga_matrices import ESTADO_A_IDX, RUTA_CSV_DEFAULT, SEXO_A_MOTOR

    if estado_a_idx is None:
        estado_a_idx = ESTADO_A_IDX
    n_estados = len(estado_a_idx)
    df = pd.read_csv(ruta_csv or RUTA_CSV_DEFAULT, sep="|")
    pesos = df.drop_duplicates(["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    out: dict[str, np.ndarray] = {}
    for g in GRUPOS_EDAD:
        num = np.zeros((n_estados, n_estados))
        den = np.zeros(n_estados)
        sub = pesos[pesos["grupo_edad"] == g]
        for _, fila in sub.iterrows():
            llave = (g, SEXO_A_MOTOR[fila["sexo"]], fila["escolaridad"])
            i = estado_a_idx[fila["estado_origen"]]
            w = float(fila["n_muestra_pond"])
            num[i] += w * matrices[llave][i]
            den[i] += w
        m = num / den[:, None]
        m = m / m.sum(axis=1, keepdims=True)  # renormaliza redondeo
        assert np.allclose(m.sum(axis=1), 1.0, atol=1e-9)
        out[g] = m
    return out


def asigna_matriz(
    edad: float, sexo: int, escolaridad: str,
    matrices: dict, marginales: dict[str, np.ndarray],
    contadores: Counter,
) -> np.ndarray | None:
    """Devuelve P^(g) 4x4 del agente, o None si ≥65 (no transita)."""
    g = grupo_edad_de(edad)
    if g is None:
        contadores["sin_matriz_65+"] += 1
        return None
    if edad < 25:
        contadores["proxy_15-24"] += 1
    llave = (g, sexo, escolaridad)
    p = matrices.get(llave)
    if p is None:
        contadores[f"fallback_marginal_{g}"] += 1
        logger.warning(
            "Perfil %s ausente en el dict; usando marginal de %s", llave, g
        )
        return marginales[g]
    contadores["lookup_ok"] += 1
    return p


# ---------------------------------------------------------------- test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rng = np.random.default_rng(42)
    n = 5_000

    # población sintética: edades 15-70 (incluye ≥65 para probar None), 50/50
    edad = rng.uniform(15.0, 70.0, size=n)
    sexo = rng.integers(0, 2, size=n)

    marginal = marginal_escolaridad()
    print("\n== Marginal ENOE 2024T3 (fac_tri) escolaridad x (sexo, grupo_edad) ==")
    print((marginal * 100).round(1).to_string())

    esc = asigna_escolaridad(edad, sexo, rng, marginal)
    print("\n== Distribución de escolaridad ASIGNADA, por sexo (%) ==")
    tab = pd.crosstab(
        pd.Series(sexo, name="sexo_motor"), pd.Series(esc, name="escolaridad"),
        normalize="index",
    )[ESCOLARIDADES] * 100
    print(tab.round(1).to_string())

    matrices = cargar_matrices()
    marginales = marginales_por_grupo(matrices)
    contadores: Counter = Counter()
    for k in range(n):
        asigna_matriz(edad[k], int(sexo[k]), esc[k], matrices, marginales, contadores)
    print("\n== Contadores de asignación (5,000 agentes) ==")
    for nombre, c in sorted(contadores.items()):
        print(f"  {nombre}: {c}")

    print("\n== 3 agentes de ejemplo: fila FORMAL (origen=0) de su P^(g) ==")
    ejemplos = [
        ("joven proxy", lambda k: edad[k] < 22 and sexo[k] == 0),
        ("mujer 40-44 basica-", lambda k: 40 <= edad[k] < 45 and sexo[k] == 1
         and esc[k] == "basica-"),
        ("hombre 55-59 superior", lambda k: 55 <= edad[k] < 60 and sexo[k] == 0
         and esc[k] == "superior"),
    ]
    for nombre, cond in ejemplos:
        k = next(i for i in range(n) if cond(i))
        P = asigna_matriz(edad[k], int(sexo[k]), esc[k], matrices, marginales,
                          Counter())
        print(f"\n{nombre}: edad={edad[k]:.1f} sexo={sexo[k]} esc={esc[k]} "
              f"grupo={grupo_edad_de(edad[k])}")
        with np.printoptions(precision=6, suppress=True):
            print(f"  fila formal: {P[0]}  (suma={P[0].sum():.9f})")

    # ================= VERIFICACIÓN PASO 2: 5 estados =================
    print("\n" + "=" * 64)
    print("VERIFICACIÓN PASO 2: tensor y perfiles a 5 estados")
    print("=" * 64)
    from carga_matrices import (
        ESTADO_A_IDX_ANUALES,
        ESTADOS_ANUALES,
        RUTA_CSV_ANUALES,
        cargar_matrices_anuales,
    )

    # 1) tensor 5x5 anual
    anuales = cargar_matrices_anuales()
    t5 = construye_tensor(anuales)
    assert t5.shape == (8, 2, 3, 5, 5), t5.shape
    assert np.allclose(t5.sum(axis=-1), 1.0, atol=1e-9)
    print(f"tensor ANUAL: shape {t5.shape}; filas del último eje suman 1 ✓")

    # 2) tensor v1 4x4 intacto: shape y contenido celda a celda
    t4 = construye_tensor(matrices)
    assert t4.shape == (8, 2, 3, 4, 4), t4.shape
    for gi, g in enumerate(GRUPOS_EDAD):
        for sx in (0, 1):
            for ei, e5 in enumerate(ESCOLARIDADES):
                assert np.array_equal(t4[gi, sx, ei], matrices[(g, sx, e5)])
    print(f"tensor v1: shape {t4.shape}; contenido == matrices v1 celda a celda ✓")

    # 3) filas_transicion 5x5, 3 agentes de perfiles distintos
    edad3 = np.array([30.0, 52.0, 30.0])
    sexo3 = np.array([0, 1, 1])
    esc3 = np.array([ESC_A_IDX["superior"], ESC_A_IDX["basica-"],
                     ESC_A_IDX["media_sup"]])
    est3 = np.array([0, 2, 4])  # formal_IMSS, informal, fuera_PEA
    f3 = filas_transicion(t5, edad3, sexo3, esc3, est3)
    assert f3.shape == (3, 5), f3.shape
    assert np.array_equal(f3[0], anuales[("30-34", 0, "superior")][0])
    assert np.array_equal(f3[1], anuales[("50-54", 1, "basica-")][2])
    assert np.array_equal(f3[2], anuales[("30-34", 1, "media_sup")][4])
    assert not np.allclose(f3[0], f3[1]) and not np.allclose(f3[1], f3[2])
    print("filas_transicion: shape (3, 5); lookup directo coincide; filas "
          "difieren entre perfiles ✓")
    with np.printoptions(precision=4, suppress=True):
        for k, desc in enumerate([
            "H 30 superior, origen formal_IMSS",
            "M 52 basica-, origen informal",
            "M 30 media_sup, origen fuera_PEA",
        ]):
            print(f"  {desc}: {f3[k]}")

    # 4) marginales_por_grupo 5x5: row-stochastic + promedio ponderado manual
    marg5 = marginales_por_grupo(anuales, RUTA_CSV_ANUALES,
                                 ESTADO_A_IDX_ANUALES)
    assert set(marg5) == set(GRUPOS_EDAD)
    for g, m in marg5.items():
        assert m.shape == (5, 5), (g, m.shape)
        assert np.allclose(m.sum(axis=1), 1.0, atol=1e-9), g
    df_csv = pd.read_csv(RUTA_CSV_ANUALES, sep="|")
    pesos = df_csv.drop_duplicates(
        ["grupo_edad", "sexo", "escolaridad", "estado_origen"])
    sub = pesos[(pesos["grupo_edad"] == "30-34")
                & (pesos["estado_origen"] == "formal_IMSS")]
    assert len(sub) == 6  # 2 sexos x 3 escolaridades del grupo
    num = np.zeros(5)
    den = 0.0
    for _, fila in sub.iterrows():
        llave5 = ("30-34", {"hombre": 0, "mujer": 1}[fila["sexo"]],
                  fila["escolaridad"])
        num += float(fila["n_muestra_pond"]) * anuales[llave5][0]
        den += float(fila["n_muestra_pond"])
    manual = num / den
    manual = manual / manual.sum()
    assert np.allclose(manual, marg5["30-34"][0], atol=1e-12)
    print("marginales 5x5: row-stochastic los 8 grupos; fila formal_IMSS de "
          "30-34 == promedio manual sobre los 6 perfiles ✓")

    # 5) fallback 15-24 y marginal de escolaridad: sin cambios
    assert sorted(set(df_csv["grupo_edad"])) == sorted(GRUPOS_EDAD)
    assert grupo_edad_de(17.0) == "25-29"
    assert grupo_edad_de(24.9) == "25-29"
    assert grupo_edad_de(66.0) is None
    assert list(marginal.columns) == ESCOLARIDADES
    assert len(marginal) == 2 * len(GRUPOS_EDAD)
    print("fallback 15-24→'25-29' y ≥65→None intactos; CSV anual usa los "
          "mismos 8 quinquenios 25-64; marginal escolaridad sin cambios "
          f"({len(marginal)} filas = 2 sexos x 8 grupos) ✓")
    print(f"\nestados (orden del contrato): {ESTADOS_ANUALES}")
    print("VERIFICACIÓN PASO 2 COMPLETA ✓")
