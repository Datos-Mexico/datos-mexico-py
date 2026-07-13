"""Carga matrices de transición heterogéneas ENOE para el motor (Sección 6).

Dos loaders:
- cargar_matrices_anuales() — DEFINITIVO (Fase 2.5): 5x5 ANUALES directas
  del panel 1ª↔5ª entrevista (matrices_anuales_2015_2024.csv). Sin P^4.
- cargar_matrices() — v1 smoke test, OBSOLETO para el CSV anual: 4x4
  trimestrales 2024T3→T4 que anualiza con P^4. Se conserva intacto como
  referencia del pipeline v1.

Ambos devuelven {(grupo_edad, sexo_motor, escolaridad): P row-stochastic},
en la convención del motor: P[i, j] = Prob(destino=j | origen=i).

Remapeos aplicados (bitácora Fase 4, smoke test):
1. Estados CSV → índices motor (motor/motor.py:32-33):
   formal_IMSS→0, informal→1, desempleado→2, fuera_PEA→3.
2. Sexo CSV {hombre, mujer} → codificación motor {0, 1}.
3. Semántica formal: formal_IMSS (solo IMSS) se carga en FORMAL[0] del
   motor (que incluye ISSSTE). Aproximación aceptada SOLO para smoke
   test; se loguea advertencia al cargar.
4. Anualización: el CSV es UN trimestre (2024T3→T4) y el motor transita
   una vez por año → P_anual = P_trim^4 (ver docstring de cargar_matrices).
"""

import csv
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

RUTA_CSV_DEFAULT = Path(__file__).parent / "matrices_transicion_2024T3_2024T4.csv"
RUTA_CSV_ANUALES = Path(__file__).parent / "matrices_anuales_2015_2024.csv"

# Remapeo 1 (v1, 4 estados): estados CSV → índice motor (motor/motor.py:32-33)
ESTADO_A_IDX = {"formal_IMSS": 0, "informal": 1, "desempleado": 2, "fuera_PEA": 3}

# Estados ANUALES (Fase 2.5, Opción A): 5 estados, orden del contrato.
# OJO: reordena informal/desempleado/fuera respecto a los índices de 4.
ESTADOS_ANUALES = ["formal_IMSS", "formal_ISSSTE", "informal", "desempleado",
                   "fuera_PEA"]
ESTADO_A_IDX_ANUALES = {e: i for i, e in enumerate(ESTADOS_ANUALES)}

# Remapeo 2: sexo CSV/ENOE → codificación motor (0=hombre, 1=mujer)
SEXO_A_MOTOR = {"hombre": 0, "mujer": 1}


def cargar_matrices(ruta: Path = RUTA_CSV_DEFAULT, anualizar: bool = True) -> dict:
    """Devuelve {(grupo_edad, sexo_motor, escolaridad): P 4x4 row-stochastic}.

    ⚠️ OBSOLETO para el CSV anual de Fase 2.5 (matrices_anuales_2015_2024
    .csv): este loader es 4x4 y anualiza con P^4 — aplicarlo al CSV anual
    elevaría la matriz a 4 años. Usar cargar_matrices_anuales(). Se
    conserva intacto como referencia del pipeline v1 (smoke test).

    Anualización (fix Fase 4): el CSV trae transiciones de UN trimestre
    (2024T3→T4) y el motor transita una vez por AÑO, así que con
    anualizar=True (default) se devuelve P_anual = P_trim^4 (potencia de
    matriz, np.linalg.matrix_power). Supuesto: cadena de Markov de primer
    orden estacionaria dentro del año; el sesgo por dependencia de
    duración (p.ej. permanencia formal correlacionada entre trimestres)
    se absorbe en el re-anclaje contra densidad observada (Fase 5).
    anualizar=False devuelve la matriz trimestral cruda (diagnóstico).
    """
    # Remapeo 3: advertencia de semántica formal, siempre visible al cargar
    logger.warning(
        "SEMÁNTICA FORMAL: formal_IMSS del CSV (solo IMSS) se mapea a "
        "FORMAL[0] del motor (que incluye ISSSTE). Aproximación aceptada "
        "únicamente para smoke test — corregir antes de resultados finales."
    )

    matrices: dict = {}
    baja_confianza: dict = {}
    with open(ruta, newline="") as f:
        for fila in csv.DictReader(f, delimiter="|"):
            llave = (
                fila["grupo_edad"],
                SEXO_A_MOTOR[fila["sexo"]],
                fila["escolaridad"],
            )
            p = matrices.setdefault(llave, np.full((4, 4), np.nan))
            i = ESTADO_A_IDX[fila["estado_origen"]]
            j = ESTADO_A_IDX[fila["estado_destino"]]
            p[i, j] = float(fila["probabilidad"])
            if fila["baja_confianza"] == "True":
                baja_confianza.setdefault(llave, set()).add(fila["estado_origen"])

    for llave, p in matrices.items():
        if np.isnan(p).any():
            raise ValueError(f"Perfil {llave}: celdas faltantes en el CSV")
        if ((p < 0) | (p > 1)).any():
            raise ValueError(f"Perfil {llave}: probabilidades fuera de [0, 1]")
        if not np.allclose(p.sum(axis=1), 1.0, atol=1e-9):
            raise ValueError(
                f"Perfil {llave}: filas no suman 1 (sumas={p.sum(axis=1)})"
            )

    if anualizar:
        for llave, p in matrices.items():
            p_anual = np.linalg.matrix_power(p, 4)
            if not np.allclose(p_anual.sum(axis=1), 1.0, atol=1e-9):
                raise ValueError(
                    f"Perfil {llave}: P^4 no row-stochastic "
                    f"(sumas={p_anual.sum(axis=1)})"
                )
            matrices[llave] = p_anual
        logger.info("Anualización aplicada: P_anual = P_trim^4 en %d perfiles",
                    len(matrices))

    logger.info("Perfiles cargados: %d (esperado 48)", len(matrices))
    if baja_confianza:
        logger.warning(
            "Perfiles con filas de baja confianza (INCLUIDOS, no excluidos): %d",
            len(baja_confianza),
        )
        for llave in sorted(baja_confianza):
            logger.warning(
                "  baja_confianza %s — filas origen: %s",
                llave,
                sorted(baja_confianza[llave]),
            )
    return matrices


def cargar_matrices_anuales(
    ruta: Path = RUTA_CSV_ANUALES, anualizar: bool = False
) -> dict:
    """Loader DEFINITIVO (Fase 2.5): {(grupo_edad, sexo_motor, escolaridad):
    P 5x5 row-stochastic} de matrices_anuales_2015_2024.csv.

    Las matrices YA SON ANUALES: transición directa 1ª↔5ª entrevista del
    panel ENOE (t → t+4 trimestres), 27 pares apilados 2015-2024. No hay
    supuesto Markov intra-año ni P^4 — anualizar=True es un error de uso
    y levanta ValueError.

    Estados (Opción A, README_matrices_anuales.md): formal_IMSS=0,
    formal_ISSSTE=1, informal=2, desempleado=3, fuera_PEA=4.

    Validaciones: 48 perfiles exactos, sin celdas NaN, probabilidades en
    [0,1], filas suman 1 (atol 1e-9). Las filas baja_confianza (n<30) se
    loguean (esperadas: 2, origen desempleado en mujeres 60-64).
    """
    if anualizar:
        raise ValueError(
            "cargar_matrices_anuales: las matrices del CSV ya son ANUALES "
            "(par directo 1ª↔5ª entrevista); anualizar con P^4 las elevaría "
            "a una transición de 4 años."
        )

    matrices: dict = {}
    baja_confianza: dict = {}
    n_estados = len(ESTADOS_ANUALES)
    with open(ruta, newline="") as f:
        for fila in csv.DictReader(f, delimiter="|"):
            llave = (
                fila["grupo_edad"],
                SEXO_A_MOTOR[fila["sexo"]],
                fila["escolaridad"],
            )
            p = matrices.setdefault(
                llave, np.full((n_estados, n_estados), np.nan)
            )
            i = ESTADO_A_IDX_ANUALES[fila["estado_origen"]]
            j = ESTADO_A_IDX_ANUALES[fila["estado_destino"]]
            p[i, j] = float(fila["probabilidad"])
            if fila["baja_confianza"] == "True":
                baja_confianza.setdefault(llave, set()).add(fila["estado_origen"])

    if len(matrices) != 48:
        raise ValueError(f"Se esperaban 48 perfiles, hay {len(matrices)}")
    for llave, p in matrices.items():
        if np.isnan(p).any():
            raise ValueError(f"Perfil {llave}: celdas faltantes/NaN en el CSV")
        if ((p < 0) | (p > 1)).any():
            raise ValueError(f"Perfil {llave}: probabilidades fuera de [0, 1]")
        if not np.allclose(p.sum(axis=1), 1.0, atol=1e-9):
            raise ValueError(
                f"Perfil {llave}: filas no suman 1 (sumas={p.sum(axis=1)})"
            )

    logger.info("Matrices ANUALES 5x5 cargadas: %d perfiles", len(matrices))
    if baja_confianza:
        logger.warning(
            "Filas baja_confianza (n<30) en %d perfiles (INCLUIDAS, "
            "suavizadas con kappa=5):", len(baja_confianza),
        )
        for llave in sorted(baja_confianza):
            logger.warning("  %s — filas origen: %s", llave,
                           sorted(baja_confianza[llave]))
    return matrices


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print("=" * 64)
    print("VERIFICACIÓN loader ANUAL 5x5 (Fase 2.5, definitivo)")
    print("=" * 64)
    anuales = cargar_matrices_anuales()
    print(f"nº perfiles cargados: {len(anuales)}")

    llave = ("30-34", SEXO_A_MOTOR["hombre"], "superior")
    P5 = anuales[llave]
    print(f"\nPerfil de referencia {llave} (hombre, 30-34, superior):")
    print(f"shape: {P5.shape}   estados: {ESTADOS_ANUALES}")
    with np.printoptions(precision=4, suppress=True):
        print(P5)
    print(f"sumas por fila: {P5.sum(axis=1)}")
    perm = P5[ESTADO_A_IDX_ANUALES["formal_IMSS"],
              ESTADO_A_IDX_ANUALES["formal_IMSS"]]
    assert abs(perm - 0.8178) < 5e-5, f"permanencia inesperada: {perm:.6f}"
    print(f"permanencia formal_IMSS→formal_IMSS: {perm:.4f} == 0.8178 ✓")
    try:
        cargar_matrices_anuales(anualizar=True)
        raise AssertionError("anualizar=True debió levantar ValueError")
    except ValueError as e:
        print(f"anualizar=True rechazado ✓ ({e})")

    print("\n" + "=" * 64)
    print("Referencia v1 (4x4 trimestral + P^4, obsoleto para el CSV anual)")
    print("=" * 64)
    matrices = cargar_matrices()
    print(f"nº perfiles cargados: {len(matrices)}")
    P = matrices[llave]
    print(f"shape: {P.shape}  permanencia formal (P^4): {P[0, 0]:.4f}")
