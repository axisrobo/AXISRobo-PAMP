"""Rename legacy EAM identifiers to PAMP across tracked text files.

Dry run (default):
    python scripts/rename_eam_to_pamp.py

Apply:
    python scripts/rename_eam_to_pamp.py --apply

Excluded on purpose:
* Keycloak client identifiers ``tap-eam-...`` (external IdP ids; renaming
  them here would break authentication unless Keycloak is updated too)
* binary assets, lock files, coverage data, build logs, and the gitignored
  ``backend/backup`` / ``paper`` trees

Only whole-word ``eam`` / ``eam_`` / ``eam.`` and uppercase ``EAM`` tokens are
rewritten, so words such as ``team`` and ``upstream`` are never touched.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "\x00TAPKEYCLOAK\x00"

SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".ico", ".pdf", ".woff", ".woff2", ".ttf",
    ".lock", ".coverage",
)
SKIP_PATHS = {
    "frontend/build_output.txt",
    "frontend/build.log",
    "frontend/build_log.txt",
    "frontend/tsc_errors.log",
    "frontend/tsc_output.txt",
    # These files intentionally reference the legacy `eam` identifiers: the
    # migration performs the rename and the helper scripts validate it.
    "scripts/rename_eam_to_pamp.py",
    "scripts/test_migrate_eam_to_pamp.py",
    "scripts/profile_eam_schema.py",
    "scripts/inspect_extensions.py",
    "backend/migrations/000_migrate_eam_to_pamp.sql",
}
SKIP_PREFIXES = ("backend/backup/", "paper/")

RULES = (
    (re.compile(r"\bEAM\b"), "PAMP"),
    (re.compile(r"\beam_"), "pamp_"),
    (re.compile(r"\beam\b"), "pamp"),
)


def tracked_files() -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def should_skip(relative: str) -> bool:
    if relative.startswith(SKIP_PREFIXES):
        return True
    if relative in SKIP_PATHS:
        return True
    return relative.lower().endswith(SKIP_SUFFIXES)


def rewrite(text: str) -> str:
    text = text.replace("tap-eam-", PLACEHOLDER)
    for pattern, replacement in RULES:
        text = pattern.sub(replacement, text)
    return text.replace(PLACEHOLDER, "tap-eam-")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    total_files = 0
    total_hits = 0
    report: list[tuple[str, int]] = []
    for relative in tracked_files():
        if should_skip(relative):
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        encoding = "utf-8"
        try:
            original = raw.decode("utf-8")
        except UnicodeDecodeError:
            # Keep the original bytes intact: latin-1 is a lossless byte mapping.
            encoding = "latin-1"
            original = raw.decode("latin-1")
        updated = rewrite(original)
        if updated == original:
            continue
        hits = sum(
            len(regex.findall(original)) for regex, _ in RULES
        )
        total_files += 1
        total_hits += hits
        report.append((relative, hits))
        if args.apply:
            path.write_bytes(updated.encode(encoding))

    report.sort(key=lambda item: item[1], reverse=True)
    for relative, hits in report:
        print(f"{hits:6d}  {relative}")
    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"\n{mode}: {total_files} files, {total_hits} replacements")
    if not args.apply:
        print("Re-run with --apply to write changes.")
        sys.exit(0)


if __name__ == "__main__":
    main()
