# scripts

Operational tooling for PAMP, grouped by purpose. All scripts resolve the
repository root themselves, so they can be run from any working directory.

```
scripts/
├── dev/        local development helpers
├── db/         database initialization and documentation
├── migration/  one-off migration and repair utilities
└── data/       business reference-data import
```

## dev/

| File | Purpose | Usage |
|------|---------|-------|
| `dev.sh` | Start the FastAPI backend and the Next.js frontend together | `scripts/dev/dev.sh` |

Requires `backend/venv` and `frontend/node_modules` to exist.

## db/

| File | Purpose | Usage |
|------|---------|-------|
| `init_db.sh` | Wrapper that runs `init_db.py` with the project's Python | `scripts/db/init_db.sh` |
| `init_db.py` | Idempotent initialization: create schema -> migrations -> DDL -> seed | `python scripts/db/init_db.py` |
| `generate_db_schema_doc.py` | Regenerate `docs/database-schema.md` from `information_schema` | `python scripts/db/generate_db_schema_doc.py` |

Connection comes from `DATABASE_URL` or the `PG*` environment variables.
`init_db.py` flags: `--skip-migrations`, `--skip-ddl`, `--skip-seed`, `--ddl`,
`--seed`, `--schema`, `--url`.

See [`../docs/database-initialization.md`](../docs/database-initialization.md)
for the full initialization and migration guide.

## migration/

One-off utilities used to perform and verify the `eam` -> `pamp` rename. They
are kept so the migration is reproducible and auditable; they are not part of
normal operation.

| File | Purpose | Usage |
|------|---------|-------|
| `rename_eam_to_pamp.py` | Rewrite `eam` identifiers to `pamp` across tracked text files | `python scripts/migration/rename_eam_to_pamp.py` (dry run), add `--apply` |
| `fix_seed_json.py` | Convert single-quoted JSON literals in the AVDM seed to valid JSON | `python scripts/migration/fix_seed_json.py [--apply]` |
| `test_migrate_eam_to_pamp.py` | Validate migration `000` against a throwaway copy of a real database | `python scripts/migration/test_migrate_eam_to_pamp.py` |

`test_migrate_eam_to_pamp.py` copies `eam_local` to a scratch database, applies
the migration, checks counts and renames, then drops the scratch database.

`rename_eam_to_pamp.py` deliberately preserves external identifiers such as the
Keycloak client id `tap-eam-...`, which must not change in the repository alone.

## data/

Business reference data. Not required for schema initialization.

| File | Purpose | Usage |
|------|---------|-------|
| `extract-apps.js` | Generate upsert SQL from an application mapping JSON export | `node scripts/data/extract-apps.js <default-data.json> > scripts/data/upsert-apps.sql` |
| `upsert-apps.sql` | Idempotent upserts for `pamp.project_app` (43 applications) | `psql "$PG" -f scripts/data/upsert-apps.sql` |

## Adding new scripts

Place the script in the folder that matches its purpose and resolve the
repository root by searching upward for the `backend` and `docs` directories
(Python) or the `backend` directory (shell), rather than counting `..` levels.
