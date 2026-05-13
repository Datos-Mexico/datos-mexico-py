#!/usr/bin/env bash
# Regenera requirements-dev.txt desde uv.lock para CI reproducible.
# Correr cada vez que cambien las deps (cualquier edit a pyproject.toml o uv.lock).
#
# Path moderno de desarrollo local: uv sync + uv run.
# Path estándar de CI y reproducibilidad académica: pip install --require-hashes
# -r requirements-dev.txt && pip install -e . --no-deps.

set -euo pipefail

cd "$(dirname "$0")/.."

uv lock
uv export \
  --format requirements-txt \
  --extra dev \
  --no-emit-project \
  --output-file requirements-dev.txt

echo "requirements-dev.txt regenerado desde uv.lock"
