"""Refresca cifras frías en docs/ y README contra la API live.

El observatorio publica cifras agregadas (e.g. "246,831 servidores") en
README y docs/. Esas cifras cambian con cada snapshot de la fuente y deben
sincronizarse antes de cortar release.

Diseño:

- Matching LITERAL, no regex. Si el documento cambió de formato y el literal
  ya no aparece, el script falla con un mensaje claro. Esto detecta cuándo
  TARGETS quedó stale antes de que silenciosamente deje de funcionar.
- Cifras pedagógicas (e.g. ejemplos en docs/conceptos/) y citas fechadas
  (e.g. ranking ENOE reproducción del boletín INEGI 265/25) están
  deliberadamente fuera de alcance. Ver docs/contributing.md.

Modos:

    python scripts/regen_docs_figures.py             # dry-run (default)
    python scripts/regen_docs_figures.py --apply     # aplica cambios
    python scripts/regen_docs_figures.py --verify    # verifica targets vivos

Exit codes:

    0 — dry-run sin drift, --apply exitoso, o --verify OK
    1 — dry-run con drift detectado (cambios pendientes)
    2 — --verify falla: algún expected_old no está en el archivo (TARGETS stale)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datos_mexico import DatosMexico

REPO_ROOT = Path(__file__).resolve().parent.parent


def _servidores_cdmx(client: DatosMexico) -> int:
    return client.cdmx.dashboard_stats().total_servidores


def _format_servidores(n: int) -> str:
    return f"{n:,} servidores"


TARGETS: list[dict] = [
    {
        "file": "README.md",
        "expected_old": "246,831 servidores",
        "endpoint_call": _servidores_cdmx,
        "format_new": _format_servidores,
        "doc_context": "Sección Datasets cubiertos",
    },
    {
        "file": "docs/tutoriales/cdmx.md",
        "expected_old": "246,831 servidores",
        "endpoint_call": _servidores_cdmx,
        "format_new": _format_servidores,
        "doc_context": "Header tutorial CDMX",
    },
]


def _print_table(rows: list[tuple[str, str, str, str, str]]) -> None:
    headers = ("file", "old", "new", "diff", "context")
    widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "  "
    print(sep.join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    print(sep.join("-" * w for w in widths))
    for row in rows:
        print(sep.join(col.ljust(w) for col, w in zip(row, widths, strict=True)))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def cmd_dry_run(targets: list[dict], client: DatosMexico) -> int:
    rows = []
    drift = False
    for target in targets:
        path = REPO_ROOT / target["file"]
        if not path.exists():
            print(f"[ERROR] archivo no existe: {target['file']}", file=sys.stderr)
            return 2
        text = _read(path)
        old = target["expected_old"]
        if old not in text:
            print(
                f"[ERROR] expected_old no encontrado en {target['file']}: {old!r}",
                file=sys.stderr,
            )
            return 2
        new_value = target["endpoint_call"](client)
        new_str = target["format_new"](new_value)
        diff_marker = "(no change)" if old == new_str else "DRIFT"
        if old != new_str:
            drift = True
        rows.append((target["file"], old, new_str, diff_marker, target["doc_context"]))
    _print_table(rows)
    print()
    if drift:
        print("Drift detectado. Correr con --apply para escribir cambios.")
        return 1
    print("Sin drift. Cifras vigentes.")
    return 0


def cmd_apply(targets: list[dict], client: DatosMexico) -> int:
    rows = []
    applied = 0
    for target in targets:
        path = REPO_ROOT / target["file"]
        if not path.exists():
            print(f"[ERROR] archivo no existe: {target['file']}", file=sys.stderr)
            return 2
        text = _read(path)
        old = target["expected_old"]
        if old not in text:
            print(
                f"[ERROR] expected_old no encontrado en {target['file']}: {old!r}",
                file=sys.stderr,
            )
            return 2
        new_value = target["endpoint_call"](client)
        new_str = target["format_new"](new_value)
        if old == new_str:
            rows.append((target["file"], old, new_str, "(no change)", target["doc_context"]))
            continue
        new_text = text.replace(old, new_str)
        _write(path, new_text)
        # Update expected_old in-memory for verification consistency
        target["expected_old"] = new_str
        applied += 1
        rows.append((target["file"], old, new_str, "APPLIED", target["doc_context"]))
    _print_table(rows)
    print()
    print(f"Aplicados: {applied} cambio(s).")
    return 0


def cmd_verify(targets: list[dict]) -> int:
    missing = []
    for target in targets:
        path = REPO_ROOT / target["file"]
        if not path.exists():
            missing.append((target["file"], "archivo no existe"))
            continue
        text = _read(path)
        if target["expected_old"] not in text:
            expected = target["expected_old"]
            missing.append((target["file"], f"expected_old no presente: {expected!r}"))
    if missing:
        for file, reason in missing:
            print(f"[FAIL] {file}: {reason}", file=sys.stderr)
        print(
            f"\nTARGETS stale: {len(missing)} target(s) ya no matchean. "
            "Actualizar scripts/regen_docs_figures.py.",
            file=sys.stderr,
        )
        return 2
    print(f"OK: los {len(targets)} TARGETS siguen presentes en los archivos.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="aplicar cambios en disco")
    group.add_argument(
        "--verify",
        action="store_true",
        help="verificar que los TARGETS sigan presentes; sin tocar la API",
    )
    args = parser.parse_args(argv)

    if args.verify:
        return cmd_verify(TARGETS)

    with DatosMexico() as client:
        if args.apply:
            return cmd_apply(TARGETS, client)
        return cmd_dry_run(TARGETS, client)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
