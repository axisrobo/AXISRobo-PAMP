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

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

exec "$PYTHON" "$ROOT_DIR/scripts/init_db.py" "$@"
