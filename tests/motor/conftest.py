"""Fixtures del test suite mínimo del motor (Paso 3a, adaptación 5 estados).

Los datos se cargan de los CSV locales de motor/data (usar_api=False):
sin red, deterministas.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
RUTA_MATRICES = REPO / "analisis" / "matrices"
if str(RUTA_MATRICES) not in sys.path:
    sys.path.insert(0, str(RUTA_MATRICES))


@pytest.fixture(scope="session")
def cfg() -> dict:
    return yaml.safe_load((REPO / "motor" / "config.yaml").read_text())


@pytest.fixture(scope="session")
def datos() -> dict:
    from motor.datos import (
        cargar_conapo,
        cargar_indice_salarial_real,
        cargar_mortalidad,
        cargar_rendimientos_reales,
        participaciones_enoe,
        qx_por_sexo,
    )

    return {
        "conapo": cargar_conapo(),
        "qx": qx_por_sexo(cargar_mortalidad()),
        "part": participaciones_enoe(usar_api=False),
        "r_hist": cargar_rendimientos_reales(),
        "ind_sal": cargar_indice_salarial_real(),
    }


@pytest.fixture(scope="session")
def resultado_homogeneo(cfg, datos):
    """Corrida canónica homogénea: flag=False, semilla de config."""
    from motor.motor import simular

    return simular(
        cfg,
        datos["conapo"],
        datos["qx"],
        datos["part"],
        escenario="base",
        semilla=cfg["semilla"],
        r_historico=datos["r_hist"],
        indice_salarial=datos["ind_sal"],
        matriz_heterogenea=False,
    )
