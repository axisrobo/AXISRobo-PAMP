"""Idempotent database initialisation for PAMP.

Runs, in order:
  1. CREATE SCHEMA IF NOT EXISTS <schema>
  2. backend/migrations/*.sql (filename order; 000 migrates a legacy `eam` schema)
  3. docs/SQL/pamp_schema_ddl.sql
  4. docs/SQL/avdm_schema_seed.sql
  5. docs/SQL/avdm_concerns_rules_seed.sql (canonical AVDM concern/rule/mapping config)

Connection comes from PG* environment variables or --url.
Every step is idempotent, so the script can be re-run safely.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg

def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "backend").is_dir() and (candidate / "docs").is_dir():
            return candidate
    raise RuntimeError("repository root not found")


ROOT = _repo_root(Path(__file__).resolve())
DEFAULT_DDL = ROOT / "docs" / "SQL" / "pamp_schema_ddl.sql"
DEFAULT_SEED = ROOT / "docs" / "SQL" / "avdm_schema_seed.sql"
DEFAULT_CONCERNS_RULES = ROOT / "docs" / "SQL" / "avdm_concerns_rules_seed.sql"
MIGRATIONS_DIR = ROOT / "backend" / "migrations"


def split_statements(sql: str) -> list[str]:
    """Split SQL on semicolons while respecting quotes and dollar quoting."""
    statements: list[str] = []
    current: list[str] = []
    index = 0
    length = len(sql)
    single_quote = False
    double_quote = False
    dollar_quote: str | None = None
    while index < length:
        char = sql[index]
        if dollar_quote:
            if sql.startswith(dollar_quote, index):
                current.append(dollar_quote)
                index += len(dollar_quote)
                dollar_quote = None
                continue
            current.append(char)
            index += 1
            continue
        if single_quote:
            current.append(char)
            if char == "'":
                single_quote = False
            index += 1
            continue
        if double_quote:
            current.append(char)
            if char == '"':
                double_quote = False
            index += 1
            continue
        if char == "'":
            current.append(char)
            single_quote = True
            index += 1
            continue
        if char == '"':
            current.append(char)
            double_quote = True
            index += 1
            continue
        if char == "$":
            end = sql.find("$", index + 1)
            if end != -1:
                tag = sql[index : end + 1]
                if tag == "$$" or tag[1:-1].replace("_", "a").isalnum():
                    current.append(tag)
                    dollar_quote = tag
                    index = end + 1
                    continue
        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


async def run_file(connection: asyncpg.Connection, path: Path) -> int:
    """Execute a whole SQL file.

    The file is sent as one simple-query call, which PostgreSQL executes
    statement by statement. This avoids an asyncpg limitation when a
    dollar-quoted ``DO`` block is executed as a single prepared statement.
    """
    sql = path.read_text(encoding="utf-8")
    await connection.execute(sql)
    return len(split_statements(sql))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--schema", default=os.getenv("DB_SCHEMA", "pamp"))
    parser.add_argument("--ddl", type=Path, default=DEFAULT_DDL)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--concerns-rules", type=Path, default=DEFAULT_CONCERNS_RULES)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-ddl", action="store_true")
    parser.add_argument("--skip-seed", action="store_true")
    parser.add_argument("--skip-concerns-rules", action="store_true")
    args = parser.parse_args()

    if args.url:
        connection = await asyncpg.connect(args.url)
    else:
        connection = await asyncpg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", ""),
            database=os.getenv("PGDATABASE", "postgres"),
        )

    try:
        await connection.execute(f'CREATE SCHEMA IF NOT EXISTS "{args.schema}"')
        print(f"schema ready: {args.schema}")

        if not args.skip_migrations:
            for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
                count = await run_file(connection, migration)
                print(f"migration applied: {migration.name} ({count} statements)")

        if not args.skip_ddl:
            count = await run_file(connection, args.ddl)
            print(f"ddl applied: {args.ddl.name} ({count} statements)")

        if not args.skip_seed:
            count = await run_file(connection, args.seed)
            print(f"seed applied: {args.seed.name} ({count} statements)")

        if not args.skip_concerns_rules and args.concerns_rules.exists():
            count = await run_file(connection, args.concerns_rules)
            print(
                f"canonical AVDM config applied: {args.concerns_rules.name} "
                f"({count} statements)"
            )
    except Exception as exc:  # noqa: BLE001 - surface the failing step
        print(f"initialisation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        await connection.close()

    print("database initialisation complete")


if __name__ == "__main__":
    asyncio.run(main())
