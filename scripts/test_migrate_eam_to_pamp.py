"""Validate the eam -> pamp migration against a throwaway copy of a real database."""
import asyncio
import os
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "backend" / "migrations" / "000_migrate_eam_to_pamp.sql"
SCRATCH = "pamp_mig_test"
SOURCE = "eam_local"


async def connect(database: str) -> asyncpg.Connection:
    return await asyncpg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        user=os.getenv("PGUSER", "postgres"),
        password=os.environ["PGPASSWORD"],
        database=database,
    )


async def table_count(connection: asyncpg.Connection, schema: str) -> int:
    return await connection.fetchval(
        """
        SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = $1 AND c.relkind = 'r'
        """,
        schema,
    )


async def relation_exists(connection: asyncpg.Connection, qualified: str) -> bool:
    return bool(await connection.fetchval("SELECT to_regclass($1) IS NOT NULL", qualified))


async def main() -> None:
    admin = await connect("postgres")
    await admin.execute("DROP DATABASE IF EXISTS " + SCRATCH)
    await admin.execute(f"CREATE DATABASE {SCRATCH} TEMPLATE {SOURCE}")
    await admin.close()

    connection = await connect(SCRATCH)
    before_tables = await table_count(connection, "eam")
    before_prefixed = await connection.fetchval(
        """
        SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'eam' AND c.relkind = 'r' AND c.relname LIKE 'eam\\_%'
        """
    )
    before_sample_rows = await connection.fetchval("SELECT count(*) FROM eam.eam_actions")

    # Replicate the startup sequence: DB_SCHEMA is created before migrations run.
    await connection.execute(
        "CREATE SCHEMA IF NOT EXISTS pamp;"
        "CREATE TABLE IF NOT EXISTS pamp.schema_migrations ("
        " id SERIAL PRIMARY KEY, filename VARCHAR(255) NOT NULL UNIQUE,"
        " hash VARCHAR(64) NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"
    )

    await connection.execute(MIGRATION.read_text(encoding="utf-8"))

    eam_exists = await connection.fetchval(
        "SELECT count(*) FROM pg_namespace WHERE nspname = 'eam'"
    )
    after_tables = await table_count(connection, "pamp")
    renamed = await relation_exists(connection, "pamp.pamp_actions")
    old_name = await relation_exists(connection, "pamp.eam_actions")
    non_prefixed = await relation_exists(connection, "pamp.project_app")
    after_sample_rows = await connection.fetchval("SELECT count(*) FROM pamp.pamp_actions")

    checks = {
        "eam_schema_removed": eam_exists == 0,
        "table_count_preserved": after_tables >= before_tables,
        "prefixed_table_renamed": renamed,
        "old_prefixed_table_gone": not old_name,
        "non_prefixed_table_preserved": non_prefixed,
        "row_count_preserved": before_sample_rows == after_sample_rows,
    }
    print("before tables:", before_tables, "prefixed:", before_prefixed, "rows:", before_sample_rows)
    print("after tables:", after_tables, "rows:", after_sample_rows)
    for name, ok in checks.items():
        print(("PASS " if ok else "FAIL ") + name)
    await connection.close()

    admin = await connect("postgres")
    await admin.execute("DROP DATABASE IF EXISTS " + SCRATCH)
    await admin.close()

    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
