-- Rename the legacy `eam` schema to `pamp` and the `eam_*` table prefix to `pamp_*`.
--
-- Runs before 001-004 because migration files are applied in filename order.
-- Idempotent: a no-op when the `eam` schema is already absent.
--
-- Notes:
-- * Tables are moved with ALTER TABLE ... SET SCHEMA, which also moves owned
--   indexes, constraints, and sequences.
-- * Internal index/sequence names keep their legacy names; only the schema and
--   the `eam_` table prefix are renamed.
-- * If the target already contains a table of the same name (for example the
--   bookkeeping table created earlier in the same startup), the legacy copy is
--   dropped, because the legacy schema is the abandoned location.

DO $$
DECLARE
    r RECORD;
    new_name TEXT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'eam') THEN
        RETURN;
    END IF;

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'eam' AND c.relkind = 'r'
    LOOP
        IF to_regclass(format('pamp.%I', r.relname)) IS NULL THEN
            EXECUTE format('ALTER TABLE eam.%I SET SCHEMA pamp', r.relname);
        ELSE
            EXECUTE format('DROP TABLE IF EXISTS eam.%I CASCADE', r.relname);
        END IF;
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'eam' AND c.relkind = 'v'
    LOOP
        IF to_regclass(format('pamp.%I', r.relname)) IS NULL THEN
            EXECUTE format('ALTER VIEW eam.%I SET SCHEMA pamp', r.relname);
        ELSE
            EXECUTE format('DROP VIEW IF EXISTS eam.%I CASCADE', r.relname);
        END IF;
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'eam' AND c.relkind = 'S'
    LOOP
        IF to_regclass(format('pamp.%I', r.relname)) IS NULL THEN
            EXECUTE format('ALTER SEQUENCE eam.%I SET SCHEMA pamp', r.relname);
        ELSE
            EXECUTE format('DROP SEQUENCE IF EXISTS eam.%I', r.relname);
        END IF;
    END LOOP;

    FOR r IN
        SELECT e.extname
        FROM pg_extension e
        JOIN pg_namespace n ON n.oid = e.extnamespace
        WHERE n.nspname = 'eam' AND e.extrelocatable
    LOOP
        EXECUTE format('ALTER EXTENSION %I SET SCHEMA pamp', r.extname);
    END LOOP;

    FOR r IN
        SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'eam'
          AND NOT EXISTS (
              SELECT 1 FROM pg_depend d
              WHERE d.objid = p.oid AND d.deptype = 'e'
          )
    LOOP
        EXECUTE format('ALTER FUNCTION eam.%I(%s) SET SCHEMA pamp', r.proname, r.args);
    END LOOP;

    FOR r IN
        SELECT t.typname
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'eam' AND t.typtype IN ('d', 'e')
    LOOP
        EXECUTE format('ALTER TYPE eam.%I SET SCHEMA pamp', r.typname);
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'pamp' AND c.relkind = 'r' AND c.relname LIKE 'eam\_%'
    LOOP
        new_name := 'pamp_' || substr(r.relname, 5);
        IF to_regclass(format('pamp.%I', new_name)) IS NULL THEN
            EXECUTE format('ALTER TABLE pamp.%I RENAME TO %I', r.relname, new_name);
        END IF;
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'pamp' AND c.relkind = 'S' AND c.relname LIKE 'eam\_%'
    LOOP
        new_name := 'pamp_' || substr(r.relname, 5);
        IF to_regclass(format('pamp.%I', new_name)) IS NULL THEN
            EXECUTE format('ALTER SEQUENCE pamp.%I RENAME TO %I', r.relname, new_name);
        END IF;
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'eam'
    ) THEN
        EXECUTE 'DROP SCHEMA eam';
    END IF;
END
$$;
