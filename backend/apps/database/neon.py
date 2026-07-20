"""Neon Postgres connection pool + migration runner for horoscope email subscriptions.

Uses the *direct* (non-pooled) Neon connection string, not the `-pooler` one: this process
already runs its own asyncpg pool, and Neon's pooled endpoint runs PgBouncer in transaction
mode, which doesn't support session-level advisory locks and has known prepared-statement
caveats with asyncpg. Going direct sidesteps that class of bug entirely.
"""

import logging
from pathlib import Path

import asyncpg

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Create the connection pool and apply any pending migrations."""
    global _pool
    _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=5)
    await run_migrations(_pool)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Postgres pool is not initialized; call init_db() first")
    return _pool


async def run_migrations(pool: asyncpg.Pool) -> None:
    """Apply numbered .sql files under migrations/ that haven't been applied yet.

    Guarded by a transaction-scoped advisory lock (safe under PgBouncer transaction
    pooling, unlike a session-scoped lock) so the API and worker processes booting
    concurrently can't double-apply or race on the same migration.
    """
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute("SELECT pg_advisory_xact_lock(hashtext('horoscope_email_migrations'))")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        applied = {
            row["filename"] for row in await conn.fetch("SELECT filename FROM schema_migrations")
        }
        for path in migration_files:
            if path.name in applied:
                continue
            await conn.execute(path.read_text())
            await conn.execute("INSERT INTO schema_migrations (filename) VALUES ($1)", path.name)
            logger.info("Applied migration %s", path.name)
