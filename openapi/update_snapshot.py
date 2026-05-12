"""Descarga el OpenAPI spec live y escribe un snapshot normalizado.

Standalone: usa solo stdlib (urllib + json) para correr en cualquier entorno
sin instalar dependencias. Pensado para CI y uso local.

Uso:

    python openapi/update_snapshot.py                       # escribe a openapi/openapi.snapshot.json
    python openapi/update_snapshot.py /tmp/openapi.live.json  # escribe a la ruta dada

Idempotente: dos ejecuciones consecutivas producen el mismo archivo byte a byte
(salvo que la API live haya cambiado en el ínterin).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

OPENAPI_URL = "https://api.datos-itam.org/openapi.json"
DEFAULT_OUTPUT = Path(__file__).parent / "openapi.snapshot.json"


USER_AGENT = "datos-mexico-openapi-snapshot/1.0 (+https://github.com/datos-mexico/datos-mexico-py)"


def fetch_spec(url: str = OPENAPI_URL, timeout: float = 30.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def write_snapshot(spec: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False)
    output.write_text(serialized + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    output = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    spec = fetch_spec()
    write_snapshot(spec, output)
    print(f"snapshot escrito en {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
