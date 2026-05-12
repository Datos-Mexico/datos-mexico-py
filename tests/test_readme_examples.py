"""Garantiza que los bloques ```python del README sean reproducibles.

Cada bloque pasa `compile()` siempre. Los bloques que usan `DatosMexico()`
también se ejecutan contra la API real cuando `DATOS_MEXICO_INTEGRATION_TESTS=1`.

Cualquier evolución de los modelos Pydantic o de los métodos públicos que
rompa los ejemplos del README falla este test antes del merge.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

README = Path(__file__).parent.parent / "README.md"
INTEGRATION = os.getenv("DATOS_MEXICO_INTEGRATION_TESTS") == "1"

_PYTHON_BLOCK = re.compile(
    r"^```python\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)


def extract_python_blocks(md_text: str) -> list[tuple[int, str]]:
    """Devuelve [(start_line, code), ...] para cada bloque ```python del README.

    Solo matchea bloques que empiezan con ```python al inicio de línea — los
    fences ```bash, ```yaml, ```text, etc. quedan fuera.
    """
    blocks: list[tuple[int, str]] = []
    for match in _PYTHON_BLOCK.finditer(md_text):
        start_offset = match.start()
        start_line = md_text.count("\n", 0, start_offset) + 1
        code = match.group(1)
        blocks.append((start_line, code))
    return blocks


BLOCKS = extract_python_blocks(README.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("start_line", "code"),
    BLOCKS,
    ids=[f"README.md:{line}" for line, _ in BLOCKS],
)
def test_readme_block_compiles(start_line: int, code: str) -> None:
    compile(code, f"README.md:{start_line}", "exec")


_RUNNABLE = [(line, code) for line, code in BLOCKS if "DatosMexico" in code]


@pytest.mark.integration
@pytest.mark.skipif(
    not INTEGRATION,
    reason="requiere DATOS_MEXICO_INTEGRATION_TESTS=1",
)
@pytest.mark.parametrize(
    ("start_line", "code"),
    _RUNNABLE,
    ids=[f"README.md:{line}" for line, _ in _RUNNABLE],
)
def test_readme_block_runs(start_line: int, code: str) -> None:
    exec(
        compile(code, f"README.md:{start_line}", "exec"),
        {"__name__": "__main__"},
    )
