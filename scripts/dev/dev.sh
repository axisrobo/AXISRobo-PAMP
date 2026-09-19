#!/usr/bin/env bash
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

BACKEND_CMD=("$ROOT_DIR/backend/venv/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 4000 --app-dir "$ROOT_DIR/backend")

cleanup() {
  # Best-effort cleanup
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ ! -x "$ROOT_DIR/backend/venv/bin/python" ]]; then
  echo "backend venv not found: $ROOT_DIR/backend/venv/bin/python" >&2
  echo "Create it under backend/venv first, then re-run." >&2
  exit 1
fi

echo "Starting backend on http://localhost:4000 ..."
( cd "$ROOT_DIR/backend" && "${BACKEND_CMD[@]}" ) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:3005 ..."
cd "$ROOT_DIR/frontend"
npm run dev
