-- schema_migrations filename uniqueness
--
-- run_migrations upserts with
--   INSERT INTO pamp.schema_migrations (filename, hash) ... ON CONFLICT (filename) ...
-- which requires a unique index on pamp.schema_migrations.filename. The schema
-- snapshot used to create the table did not include it, so startup failed with
-- "no unique or exclusion constraint matching the ON CONFLICT specification"
-- when the table had been pre-created by the DDL.
--
-- The index is also declared in docs/SQL/pamp_schema_ddl.sql for fresh installs.

DO $$
BEGIN
    IF to_regclass('pamp.schema_migrations') IS NOT NULL THEN
        EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS '
             || 'schema_migrations_filename_key '
             || 'ON pamp.schema_migrations (filename)';
    END IF;
END
$$;
