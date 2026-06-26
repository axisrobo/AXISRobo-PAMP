"""Generate database schema documentation from PostgreSQL information_schema.

Run from the repo root:
    python scripts/generate_db_schema_doc.py
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import asyncpg


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env_file = Path(__file__).resolve().parents[1] / "backend" / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                url = line.split("=", 1)[1].strip().strip('"').strip("'")
                return url
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/axisarch"


def parse_dsn(url: str) -> dict:
    clean = url.replace("+asyncpg", "").replace("+psycopg", "").replace("postgresql://", "http://")
    clean = clean.replace("http://", "postgres://")
    pattern = r"postgres://(?:([^:]*):([^@]*)@)?([^:/]+)(?::(\d+))?/([^?]+)(?:\?(.*))?"
    m = re.match(pattern, clean)
    if not m:
        raise ValueError(f"Cannot parse DSN: {url}")
    user, password, host, port, dbname, query_str = m.groups()
    params = {
        "host": host or "localhost",
        "port": int(port) if port else 5432,
        "database": dbname or "postgres",
    }
    if user:
        params["user"] = user
    if password:
        params["password"] = password
    return params


TABLE_ORDER = [
    "avdm_pact_concern",
    "avdm_question_group",
    "avdm_question_category",
    "avdm_question_answer_type",
    "avdm_question_option_set",
    "avdm_question_option_item",
    "avdm_question",
    "avdm_question_answer_concern_mapping",
    "avdm_artifact_category",
    "avdm_artifact",
    "avdm_viewpoint",
    "avdm_viewpoint_concern_mapping",
    "avdm_viewpoint_artifact_mapping",
    "avdm_project_type_profile",
    "avdm_project_type_artifact_mapping",
    "avdm_concern_activation_rule",
    "avdm_concern_activation_rule_score",
    "avdm_questionnaire_config",
    "avdm_master_data_revision",
    "avdm_static_document",
    "avdm_project_assessment",
    "eam_request",
    "eam_request_process_log",
    "eam_request_attachment",
    "eam_meetings",
    "eam_actions",
    "eam_bigea_team_members",
    "eam_arch_ai_check",
    "eam_arch_ai_check_interaction",
    "eam_arch_ai_check_app",
    "tech_key_stack_item",
    "tech_stack_master_data",
    "tech_stack_operate_log",
    "biz_cap_map",
    "eam_project",
    "eam_team_member",
    "eam_project_app",
    "resource_pool",
    "eam_audit_log",
    "eam_file_storage",
    "local_users",
    "schema_migrations",
]


TABLE_DESCRIPTIONS = {
    "avdm_pact_concern": "PACT concern master catalog (52 architecture concerns). Defines concern keys, names, layers, risk tags.",
    "avdm_question_group": "Question groups (e.g., Scale Overall, Complexity Overall, Change Trigger, Architecture Type).",
    "avdm_question_category": "Question categories within groups (e.g., Project Scale, Technical Complexity, Business Change).",
    "avdm_question_answer_type": "Answer type definitions (radio, select, multiselect, text, textarea) with widget and storage kinds.",
    "avdm_question_option_set": "Shared option sets (e.g., Yes/No, Application Count Ranges, Project Types).",
    "avdm_question_option_item": "Individual option items within option sets (e.g., 'Yes', '5 or fewer', 'Web App').",
    "avdm_question": "Question bank items with stable IDs, text, design intent, and answer type references.",
    "avdm_question_answer_concern_mapping": "Maps question answers (or option selections) to PACT concerns with scores, severity, likelihood.",
    "avdm_artifact_category": "Artifact categories (Architecture Diagram, Business Architecture, Data Architecture, etc.).",
    "avdm_artifact": "Named artifacts (tech diagram, app collaboration, biz diagram, data model, etc.) with purpose and typical contents.",

    "avdm_viewpoint": "Architecture viewpoint definitions with L/P classification, S/B classification, purpose, examples, audience.",
    "avdm_viewpoint_concern_mapping": "Maps activated architecture concerns to viewpoints in the canonical AVDM decision chain.",
    "avdm_viewpoint_artifact_mapping": "Maps viewpoints to recommended artifacts with Mandatory/Optional status.",
    "avdm_project_type_profile": "Project type profiles (e.g., Web App, Data Project, AI/ML) with typical patterns and risks.",
    "avdm_project_type_artifact_mapping": "Maps project type profiles to default artifact recommendations.",
    "avdm_concern_activation_rule": "Conditional rules for activating concerns based on question answer combinations.",
    "avdm_concern_activation_rule_score": "Scoring entries per rule+concern combination.",
    "avdm_questionnaire_config": "JSONB-based questionnaire configuration store (config key, versioned).",
    "avdm_master_data_revision": "Revision tracking for AVDM master data domains (questionnaire, concern_mapping, artifact_catalog, etc.).",
    "avdm_static_document": "JSONB-based static document store (viewpoint_artifact_mapping, project_type_profiles, questionnaire_sections).",
    "avdm_project_assessment": "Project-level AVDM assessment records with questionnaire, risk items, evaluation, concerns, and artifact selections.",
    "eam_request": "Architecture review requests - the core entity for the EA review workflow.",
    "eam_request_process_log": "Process log tracking state transitions and workflow steps per request.",
    "eam_request_attachment": "Attachments/documents uploaded for architecture review requests.",
    "eam_meetings": "Review meeting records linked to projects/requests.",
    "eam_actions": "Action items from review meetings linked to requests.",
    "eam_bigea_team_members": "EA team member directory (itcode, name, org hierarchy).",
    "eam_arch_ai_check": "AI review check results against architecture diagrams.",
    "eam_arch_ai_check_interaction": "AI analysis of interactions between applications in a check.",
    "eam_arch_ai_check_app": "Applications referenced in AI architecture checks.",
    "tech_key_stack_item": "Technology stack items with version, compliance status, and security advice.",
    "tech_stack_master_data": "Master data for technology stack definitions (approved lists, categories).",
    "tech_stack_operate_log": "Audit log for field-level changes to tech stack items.",
    "biz_cap_map": "Business capability mapping to applications/data versions.",
    "eam_project": "Projects tracked in the project management module.",
    "eam_team_member": "Team members assigned to projects.",
    "eam_project_app": "Applications associated with projects.",
    "resource_pool": "Resource directory (itcode, name, email, org hierarchy) for autocomplete.",
    "eam_audit_log": "RBAC audit log recording all access decisions (allow/deny) with user, resource, action.",
    "eam_file_storage": "Binary file storage (S3 alternative) keyed by path.",
    "local_users": "Local authentication users (username, password hash, role). Used when AUTH_MODE=local.",
    "schema_migrations": "Migration tracking table recording applied migration filenames and hashes.",
}


async def main() -> None:
    dsn = get_database_url()
    params = parse_dsn(dsn)
    print(f"Connecting to postgres://{params.get('user','?')}@{params['host']}:{params['port']}/{params['database']}")
    conn = await asyncpg.connect(**params)
    try:
        schema = "eam"

        tables_sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = $1
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables = await conn.fetch(tables_sql, schema)
        table_names = [row["table_name"] for row in tables]

        columns_sql = """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.is_nullable,
                c.column_default,
                c.ordinal_position
            FROM information_schema.columns c
            WHERE c.table_schema = $1
            ORDER BY c.table_name, c.ordinal_position
        """
        columns = await conn.fetch(columns_sql, schema)

        fks_sql = """
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.referential_constraints rc
              ON tc.constraint_name = rc.constraint_name
              AND tc.table_schema = rc.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
              ON rc.unique_constraint_name = ccu.constraint_name
              AND rc.unique_constraint_schema = ccu.constraint_schema
            WHERE tc.table_schema = $1
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """
        fks = await conn.fetch(fks_sql, schema)

        pks_sql = """
            SELECT
                kcu.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = $1
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.table_name, kcu.ordinal_position
        """
        pks = await conn.fetch(pks_sql, schema)

    finally:
        await conn.close()

    pk_map = {}
    for row in pks:
        pk_map.setdefault(row["table_name"], set()).add(row["column_name"])

    fk_map = {}
    for row in fks:
        key = (row["source_table"], row["source_column"])
        fk_map[key] = (row["target_table"], row["target_column"], row["delete_rule"])

    col_by_table = {}
    for row in columns:
        col_by_table.setdefault(row["table_name"], []).append(dict(row))

    incoming_fks = {}
    for (st, sc), (tt, tc, dr) in fk_map.items():
        incoming_fks.setdefault(tt, []).append((st, sc, dr))

    ordered = [t for t in TABLE_ORDER if t in table_names]
    remaining = [t for t in table_names if t not in TABLE_ORDER]
    ordered.extend(sorted(remaining))

    lines = []
    lines.append("# Database Schema Documentation")
    lines.append("")
    lines.append(f"**Schema**: `{schema}`")
    lines.append(f"**Total Tables**: {len(table_names)}")
    lines.append(f"**Total Foreign Key Relationships**: {len(fk_map)}")
    lines.append("")
    lines.append("> Auto-generated from live database using `information_schema`.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for table in ordered:
        cols = col_by_table.get(table, [])
        desc = TABLE_DESCRIPTIONS.get(table, "")

        lines.append(f"## `{schema}.{table}`")
        if desc:
            lines.append("")
            lines.append(desc)
        lines.append("")
        lines.append("| Column | Type | Null | FK / PK |")
        lines.append("|--------|------|------|---------|")

        for col in cols:
            cn = col["column_name"]
            dt = col["data_type"]
            cml = col["character_maximum_length"]
            np = col["numeric_precision"]
            ns = col["numeric_scale"]

            ts = dt
            if cml:
                ts += f"({cml})"
            elif np is not None:
                if ns is not None and ns > 0:
                    ts += f"({np},{ns})"
                else:
                    ts += f"({np})"

            nl = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"

            labels = []
            if cn in pk_map.get(table, set()):
                labels.append("PK")
            fi = fk_map.get((table, cn))
            if fi:
                labels.append(f"FK -> `{fi[0]}.{fi[1]}`")
                if fi[2] != "NO ACTION":
                    labels.append(f"ON DELETE {fi[2]}")
            cd = col["column_default"]
            if cd is not None and "nextval" in str(cd).lower():
                labels.append("SERIAL")

            fk_str = ", ".join(labels) if labels else "-"
            lines.append(f"| `{cn}` | `{ts}` | {nl} | {fk_str} |")

        outgoing = []
        for c in cols:
            fi = fk_map.get((table, c["column_name"]))
            if fi:
                outgoing.append((c["column_name"], fi))

        incoming = incoming_fks.get(table, [])

        if outgoing or incoming:
            lines.append("")
            lines.append("### Relationships")
            lines.append("")

            for cn, (tt, tc, dr) in outgoing:
                dn = f" (ON DELETE {dr})" if dr != "NO ACTION" else ""
                lines.append(f"- `{schema}.{table}.{cn}` -> `{schema}.{tt}.{tc}`{dn}")

            for st, sc, dr in incoming:
                dn = f" (ON DELETE {dr})" if dr != "NO ACTION" else ""
                target_col = "id"
                lines.append(f"- `{schema}.{st}.{sc}` <- `{schema}.{table}`{dn}")

        lines.append("")
        lines.append("---")
        lines.append("")

    out = Path(__file__).resolve().parents[1] / "docs" / "database-schema.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSchema documentation written to: {out}")
    print(f"Total tables: {len(table_names)}")
    print(f"Total foreign keys: {len(fk_map)}")


if __name__ == "__main__":
    asyncio.run(main())
