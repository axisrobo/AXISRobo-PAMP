"""Convert single-quoted JSON literals in the AVDM seed to valid JSON.

The seed inserts values such as ``'[''a'', ''b'']'`` and
``'[{''equals'': ''Y''}]'`` into ``json`` columns. PostgreSQL requires
double-quoted JSON, so every single-quoted SQL literal whose content starts
with ``[`` or ``{`` and contains an escaped quote (``''``) is rewritten with
``"`` instead. All other literals are left untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SEED = Path("docs/SQL/avdm_schema_seed.sql")


def convert_literals(text: str) -> tuple[str, int]:
    out: list[str] = []
    index = 0
    length = len(text)
    converted = 0
    while index < length:
        char = text[index]
        if char != "'":
            out.append(char)
            index += 1
            continue
        # Collect a single-quoted literal, treating '' as an escaped quote.
        body: list[str] = []
        index += 1
        while index < length:
            if text[index] == "'":
                if index + 1 < length and text[index + 1] == "'":
                    body.append("''")
                    index += 2
                    continue
                index += 1
                break
            body.append(text[index])
            index += 1
        content = "".join(body)
        stripped = content.lstrip()
        if stripped[:1] in ("[", "{") and "''" in content:
            out.append("'" + content.replace("''", '"') + "'")
            converted += 1
        else:
            out.append("'" + content + "'")
    return "".join(out), converted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    text = SEED.read_text(encoding="utf-8")
    updated, converted = convert_literals(text)
    print(f"json literals converted: {converted}")
    if updated == text:
        print("no changes needed")
        return
    if args.apply:
        SEED.write_text(updated, encoding="utf-8")
        print("seed rewritten")
    else:
        print("dry run; re-run with --apply")


if __name__ == "__main__":
    main()
