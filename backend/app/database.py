"""Database engine and session factory."""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event, text
from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "server_settings": {"search_path": settings.DB_SCHEMA},
    },
)


@event.listens_for(engine.sync_engine, "connect")
def set_search_path(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET search_path TO {settings.DB_SCHEMA}")
    cursor.close()


AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def _split_sql_statements(sql: str) -> list[str]:
    """Split a migration file into executable SQL statements.

    asyncpg does not allow multiple SQL commands in one prepared statement, so
    migration files must be executed statement-by-statement. This splitter keeps
    semicolons inside quoted strings, comments, and PostgreSQL dollar-quoted
    blocks intact.
    """
    statements: list[str] = []
    current: list[str] = []
    index = 0
    length = len(sql)
    single_quote = False
    double_quote = False
    line_comment = False
    block_comment = False
    dollar_quote: str | None = None

    while index < length:
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < length else ""

        if line_comment:
            current.append(char)
            if char == "\n":
                line_comment = False
            index += 1
            continue

        if block_comment:
            current.append(char)
            if char == "*" and next_char == "/":
                current.append(next_char)
                block_comment = False
                index += 2
            else:
                index += 1
            continue

        if dollar_quote:
            if sql.startswith(dollar_quote, index):
                current.append(dollar_quote)
                index += len(dollar_quote)
                dollar_quote = None
            else:
                current.append(char)
                index += 1
            continue

        if single_quote:
            current.append(char)
            if char == "'":
                if next_char == "'":
                    current.append(next_char)
                    index += 2
                    continue
                single_quote = False
            index += 1
            continue

        if double_quote:
            current.append(char)
            if char == '"':
                double_quote = False
            index += 1
            continue

        if char == "-" and next_char == "-":
            current.append(char)
            current.append(next_char)
            line_comment = True
            index += 2
            continue

        if char == "/" and next_char == "*":
            current.append(char)
            current.append(next_char)
            block_comment = True
            index += 2
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
                tag = sql[index:end + 1]
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

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements


async def run_migrations() -> None:
    """Execute all SQL migration files in backend/migrations/ on startup.

    Uses a ``schema_migrations`` table to track which files have already been
    applied.  Each file is hashed; if the hash has not changed since the last
    successful application the file is skipped.  Migration failures raise
    immediately to prevent the application from starting with an inconsistent
    schema.
    """
    import hashlib

    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")
    migrations_dir = os.path.normpath(migrations_dir)
    if not os.path.isdir(migrations_dir):
        return
    sql_files = sorted(f for f in os.listdir(migrations_dir) if f.endswith(".sql"))
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.warning("PostgreSQL extension setup skipped/failed: %s", exc)

        await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.DB_SCHEMA}"'))
        await session.commit()

        await session.execute(
            text(
                f'CREATE TABLE IF NOT EXISTS "{settings.DB_SCHEMA}".schema_migrations ('
                "  id SERIAL PRIMARY KEY,"
                "  filename VARCHAR(255) NOT NULL UNIQUE,"
                "  hash VARCHAR(64) NOT NULL,"
                "  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                ")"
            )
        )
        await session.commit()

        applied_result = await session.execute(
            text(f'SELECT filename, hash FROM "{settings.DB_SCHEMA}".schema_migrations')
        )
        applied: dict[str, str] = {row.filename: row.hash for row in applied_result.mappings()}

        for filename in sql_files:
            filepath = os.path.join(migrations_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sql = f.read()
            file_hash = hashlib.sha256(sql.encode("utf-8")).hexdigest()

            if filename in applied:
                if applied[filename] == file_hash:
                    logger.info("Migration already applied (hash match): %s", filename)
                    continue
                logger.warning(
                    "Migration file %s has changed since last application! Re-applying.",
                    filename,
                )

            try:
                for statement in _split_sql_statements(sql):
                    await session.execute(text(statement))
                await session.execute(
                    text(
                        f'INSERT INTO "{settings.DB_SCHEMA}".schema_migrations (filename, hash) '
                        "VALUES (:filename, :hash) "
                        "ON CONFLICT (filename) DO UPDATE SET hash = :hash, applied_at = NOW()"
                    ),
                    {"filename": filename, "hash": file_hash},
                )
                await session.commit()
                logger.info("Migration applied: %s (hash=%s)", filename, file_hash[:16])
            except Exception:
                await session.rollback()
                logger.critical("Migration FAILED, aborting startup: %s", filename, exc_info=True)
                raise
