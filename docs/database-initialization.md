# Database Initialization

PAMP uses the PostgreSQL schema `pamp`. All tables, the migration bookkeeping
table, and the configuration documents live in that schema.

## One-command initialization (idempotent)

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/pamp"
scripts/init_db.sh
```

On Windows:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/pamp"
.\scripts\init_db.sh
```

Connection can also come from `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and
`PGDATABASE`. The wrapper selects `backend/venv` automatically and delegates to
`scripts/init_db.py`.

### What it does, in order

| Step | Source | Notes |
|------|--------|-------|
| 1. Create schema | `CREATE SCHEMA IF NOT EXISTS pamp` | Never drops existing data |
| 2. Migrations | `backend/migrations/*.sql` | Filename order; `000` migrates a legacy `eam` schema |
| 3. Table DDL | `docs/SQL/pamp_schema_ddl.sql` | `CREATE TABLE IF NOT EXISTS` |
| 4. AVDM seed | `docs/SQL/avdm_schema_seed.sql` | Concerns, viewpoints, artifacts, mappings, rules |

Every step is idempotent, so repeated runs are safe. Useful flags:

```bash
scripts/init_db.sh --skip-seed          # schema + migrations + DDL only
scripts/init_db.sh --skip-migrations    # schema + DDL + seed only
scripts/init_db.sh --ddl docs/SQL/pamp_schema_ddl.sql
```

## Manual equivalent

```bash
PG="postgresql://postgres:postgres@localhost:5432/pamp"
psql "$PG" -c "CREATE SCHEMA IF NOT EXISTS pamp;"
for f in backend/migrations/*.sql; do psql "$PG" -f "$f"; done
psql "$PG" -f docs/SQL/pamp_schema_ddl.sql
psql "$PG" -f docs/SQL/avdm_schema_seed.sql
```

The application also runs `backend/migrations/*.sql` on startup
(`backend/app/database.py: run_migrations`), tracked by the
`pamp.schema_migrations` table.

## Legacy `eam` -> `pamp` migration

`backend/migrations/000_migrate_eam_to_pamp.sql` renames a legacy `eam` schema to
`pamp` and the `eam_*` table prefix to `pamp_*`. It runs before the other
migrations and is a no-op when no `eam` schema exists.

What it moves:

* tables (`ALTER TABLE ... SET SCHEMA`, which also moves owned indexes,
  constraints, and sequences)
* views
* standalone sequences
* relocatable extensions (for example `pgcrypto`)
* functions, excluding extension members
* domains and enum types

Internal index and sequence names keep their legacy names; only the schema and
the `eam_` table prefix change.

Validate the migration against a throwaway copy of a real database:

```bash
python scripts/test_migrate_eam_to_pamp.py
```

The test copies `eam_local` to a scratch database, applies the migration, checks
that the schema is gone, the table and row counts are preserved, and
`eam_actions` became `pamp_actions`, then drops the scratch database.

## Configuration documents

Runtime configuration is stored as JSONB in `pamp.avdm_static_document`:
questionnaire sections, assessment matrices, project-type guide,
viewpoint-artifact mapping, and the AVDM classification policy. Defaults come
from application code; a row is written on first save.

The table requires a unique index on `document_key` for the `ON CONFLICT`
upsert. It is created by `backend/migrations/004_avdm_static_document_unique_key.sql`
and included in `docs/SQL/pamp_schema_ddl.sql`.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `relation "pamp.x" does not exist` | DDL/seed not applied | run `scripts/init_db.sh` |
| `no unique or exclusion constraint matching the ON CONFLICT` | missing `document_key` unique index | apply migration `004` |
| Data still under `eam` | migration `000` not applied | start the backend once or run `scripts/init_db.sh` |
| `permission denied for schema pamp` | role lacks privileges | grant usage on schema `pamp` to the app role |
