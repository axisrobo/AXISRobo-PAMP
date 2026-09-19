# Database Initialization

PAMP uses the PostgreSQL schema `pamp`. All tables, the migration bookkeeping
table, and the configuration documents live in that schema.

## Local development database (canonical)

| Item | Value |
|------|-------|
| Database | `axisarch` |
| Schema | `pamp` |
| Host / port | `localhost:5433` (local dev cluster) |
| Role / password | `postgres` / `postgres` |
| Connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5433/axisarch` |

> **Do not use the wrong database.**
> - `eam_local` belongs to a **different project**. Never point PAMP at it,
>   never migrate it, never seed it.
> - `axis_local` has been **removed** as part of consolidating local databases.
> - Always confirm the database name in `DATABASE_URL` before running
>   migrations or seeds. When in doubt, check
>   `SELECT current_database(), current_schema();`.

## One-command initialization (idempotent)

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/axisarch"
scripts/db/init_db.sh
```

On Windows:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/axisarch"
.\scripts\init_db.sh
```

Connection can also come from `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and
`PGDATABASE`. The wrapper selects `backend/venv` automatically and delegates to
`scripts/db/init_db.py`.

### What it does, in order

| Step | Source | Notes |
|------|--------|-------|
| 1. Create schema | `CREATE SCHEMA IF NOT EXISTS pamp` | Never drops existing data |
| 2. Migrations | `backend/migrations/*.sql` | Filename order; `000` migrates a legacy `eam` schema |
| 3. Table DDL | `docs/SQL/pamp_schema_ddl.sql` | `CREATE TABLE IF NOT EXISTS` |
| 4. Base AVDM seed | `docs/SQL/avdm_schema_seed.sql` | Questions, viewpoints, artifacts, base concerns/mappings/rules |
| 5. Canonical AVDM config | `docs/SQL/avdm_concerns_rules_seed.sql` | Overrides concerns, question→concern mappings, and activation rules |

Every step is idempotent, so repeated runs are safe. Useful flags:

```bash
scripts/db/init_db.sh --skip-seed              # schema + migrations + DDL + canonical config only
scripts/db/init_db.sh --skip-migrations        # schema + DDL + seed + canonical config
scripts/db/init_db.sh --skip-concerns-rules    # everything except the canonical AVDM config
scripts/db/init_db.sh --ddl docs/SQL/pamp_schema_ddl.sql
```

## Canonical AVDM concern/rule/mapping configuration

`docs/SQL/avdm_concerns_rules_seed.sql` is the generated, idempotent source of
truth for the AVDM concern catalog, question→concern mappings, and activation
rules. It is applied after the base seed and:

* unifies concern keys on **code keys** (`DIP7`/`DIP8` → `DIN1`/`DIN2`) and
  deactivates legacy slug/DIP alias keys;
* clears `risk_tags` (activation is driven by mappings and rules only, avoiding
  the tag-averaging dilution);
* rebuilds `avdm_question_answer_concern_mapping` and
  `avdm_concern_activation_rule_score`;
* guarantees every **active** concern has at least one activation path.

The human-readable payload is `docs/SQL/avdm_config.json`.

Apply it alone (after the base schema/seed exists):

```bash
psql "$PG" -f docs/SQL/avdm_concerns_rules_seed.sql
```

## Manual equivalent

```bash
PG="postgresql://postgres:postgres@localhost:5433/axisarch"
psql "$PG" -c "CREATE SCHEMA IF NOT EXISTS pamp;"
for f in backend/migrations/*.sql; do psql "$PG" -f "$f"; done
psql "$PG" -f docs/SQL/pamp_schema_ddl.sql
psql "$PG" -f docs/SQL/avdm_schema_seed.sql
psql "$PG" -f docs/SQL/avdm_concerns_rules_seed.sql
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

> The migration is meant for **this project's own** legacy schema inside the
> PAMP database. It must never be run against `eam_local`, which is a separate
> project's database.

Validate the migration against a throwaway copy of a real database:

```bash
python scripts/migration/test_migrate_eam_to_pamp.py
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
| `relation "pamp.x" does not exist` | DDL/seed not applied | run `scripts/db/init_db.sh` |
| `no unique or exclusion constraint matching the ON CONFLICT` | missing `document_key` unique index | apply migration `004` |
| Data still under `eam` | migration `000` not applied | start the backend once or run `scripts/db/init_db.sh` |
| `permission denied for schema pamp` | role lacks privileges | grant usage on schema `pamp` to the app role |
| Changes appear in the wrong database | wrong `DATABASE_URL` | target `axisarch`; never `eam_local` |
