#!/usr/bin/env bash
# Idempotent database initialisation for PAMP.
#
# Order: create schema -> migrations -> DDL -> seed.
#
# Connection (choose one):
#   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pamp
#   # or PG* variables:
#   export PGHOST=localhost PGPORT=5432 PGUSER=postgres \
#          PGPASSWORD=postgres PGDATABASE=pamp
#
# Usage:
#   scripts/init_db.sh
#   scripts/init_db.sh --skip-seed
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
while [[ ! -d "$ROOT_DIR/backend" && "$ROOT_DIR" != "/" ]]; do
  ROOT_DIR="$(dirname "$ROOT_DIR")"
done
if [[ ! -d "$ROOT_DIR/backend" ]]; then
  echo "Could not locate repository root (no backend/ directory above $SCRIPT_DIR)" >&2
  exit 1
fi

if [[ -x "$ROOT_DIR/backend/venv/bin/python" ]]; then
  PYTHON="$ROOT_DIR/backend/venv/bin/python"
elif [[ -x "$ROOT_DIR/backend/venv/Scripts/python.exe" ]]; then
  PYTHON="$ROOT_DIR/backend/venv/Scripts/python.exe"
else
  PYTHON="$(command -v python3 || command -v python)"
fi

if [[ -z "${PYTHON:-}" ]]; then
  echo "No Python interpreter found. Create backend/venv first." >&2
  exit 1
fi

exec "$PYTHON" "$ROOT_DIR/scripts/db/init_db.py" "$@"
