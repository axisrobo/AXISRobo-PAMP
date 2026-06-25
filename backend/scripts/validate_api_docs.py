"""Validate that ``docs/api.md`` covers all OpenAPI routes.

Usage:
    cd backend && python scripts/validate_api_docs.py

Exit code 0: all routes documented.  Exit code 1: undocumented routes found.

The script extracts the list of paths from the FastAPI app's OpenAPI schema and
checks that each path appears (as a substring) in the API reference document.
It skips internal OpenAPI meta-routes (/openapi.json, /docs, /redoc).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def load_app():
    backend_dir = str(Path(__file__).resolve().parent.parent)
    sys.path.insert(0, backend_dir)
    try:
        from app.main import app
        return app
    except ImportError as exc:
        print(f"ERROR: Cannot import app: {exc}")
        print("Make sure all dependencies are installed and you're in the backend directory.")
        sys.exit(2)


def main() -> int:
    app = load_app()
    schema = app.openapi()

    api_doc_path = Path(__file__).resolve().parents[2] / "docs" / "api.md"
    if not api_doc_path.exists():
        print(f"ERROR: {api_doc_path} not found")
        return 2

    doc_text = api_doc_path.read_text(encoding="utf-8")

    skip_prefixes = {"/openapi.json", "/docs", "/redoc"}
    undocumented: list[str] = []

    for path, methods in sorted(schema.get("paths", {}).items()):
        if path in skip_prefixes:
            continue
        # Normalize both OpenAPI path and doc text: collapse all {param} → {_}
        normalized_path = re.sub(r"\{[^}]+\}", "{_}", path)
        normalized_doc = re.sub(r"\{[^}]+\}", "{_}", doc_text)
        if normalized_path in normalized_doc:
            continue
        undocumented.append(path)

    if undocumented:
        print(f"Undocumented routes ({len(undocumented)}):")
        for p in undocumented:
            print(f"  {p}")
        return 1

    total = len([p for p in schema.get("paths", {}) if p not in skip_prefixes])
    print(f"OK: all {total} API routes documented in docs/api.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
