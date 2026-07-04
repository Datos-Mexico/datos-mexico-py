"""Carga matrices de transición heterogéneas ENOE para el motor (Sección 6).

Lee matrices_transicion_2024T3_2024T4.csv y devuelve un dict
{(grupo_edad, sexo_motor, escolaridad): P} con P numpy 4x4 row-stochastic,
en la convención del motor: P[i, j] = Prob(destino=j | origen=i).

Remapeos aplicados (bitácora Fase 4, smoke test):
1. Estados CSV → índices motor (motor/motor.py:32-33):
   formal_IMSS→0, informal→1, desempleado→2, fuera_PEA→3.
2. Sexo CSV {hombre, mujer} → codificación motor {0, 1}.
3. Semántica formal: formal_IMSS (solo IMSS) se carga en FORMAL[0] del
   motor (que incluye ISSSTE). Aproximación aceptada SOLO para smoke
   test; se loguea advertencia al cargar.
"""

import csv
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

RUTA_CSV_DEFAULT = Path(__file__).parent / "matrices_transicion_2024T3_2024T4.csv"

# Remapeo 1: estados CSV → índice motor (filas=origen, columnas=destino)
ESTADO_A_IDX = {"formal_IMSS": 0, "informal": 1, "desempleado": 2, "fuera_PEA": 3}

# Remapeo 2: sexo CSV/ENOE → codificación motor (0=hombre, 1=mujer)
SEXO_A_MOTOR = {"hombre": 0, "mujer": 1}


def cargar_matrices(ruta: Path = RUTA_CSV_DEFAULT) -> dict:
    """Devuelve {(grupo_edad, sexo_motor, escolaridad): P 4x4 row-stochastic}."""
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    matrices = cargar_matrices()
    print(f"\nnº perfiles cargados: {len(matrices)}")

    llave = ("30-34", SEXO_A_MOTOR["hombre"], "superior")
    P = matrices[llave]
    print(f"\nPerfil {llave} (hombre, 30-34, superior):")
    print(f"shape: {P.shape}")
    with np.printoptions(precision=6, suppress=True):
        print(P)
    print(f"sumas por fila: {P.sum(axis=1)}")
