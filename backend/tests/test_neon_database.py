from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import apps.database.neon as neon


class FakeTransaction:
    async def __aenter__(self):
        return None

    async def __aexit__(self, *_exc_info):
        return False


class FakeAcquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *_exc_info):
        return False


def make_pool(applied_filenames=()):
    conn = SimpleNamespace(
        execute=AsyncMock(),
        fetch=AsyncMock(return_value=[{"filename": f} for f in applied_filenames]),
        transaction=Mock(return_value=FakeTransaction()),
    )
    pool = SimpleNamespace(acquire=Mock(return_value=FakeAcquire(conn)), close=AsyncMock())
    return pool, conn


@pytest.mark.asyncio
async def test_run_migrations_applies_unapplied_files_under_advisory_lock():
    pool, conn = make_pool(applied_filenames=())

    await neon.run_migrations(pool)

    executed = [call.args[0] for call in conn.execute.await_args_list]
    assert any("pg_advisory_xact_lock" in stmt for stmt in executed)
    assert any("CREATE TABLE IF NOT EXISTS schema_migrations" in stmt for stmt in executed)
    assert any("CREATE TABLE IF NOT EXISTS horoscope_subscriptions" in stmt for stmt in executed)
    insert_calls = [
        call
        for call in conn.execute.await_args_list
        if call.args[0].startswith("INSERT INTO schema_migrations")
    ]
    assert len(insert_calls) == 1
    assert insert_calls[0].args[1] == "0001_create_horoscope_email_subscription_schema.sql"


@pytest.mark.asyncio
async def test_run_migrations_skips_already_applied_files():
    pool, conn = make_pool(
        applied_filenames=("0001_create_horoscope_email_subscription_schema.sql",)
    )

    await neon.run_migrations(pool)

    executed = [call.args[0] for call in conn.execute.await_args_list]
    assert not any(
        "CREATE TABLE IF NOT EXISTS horoscope_subscriptions" in stmt for stmt in executed
    )
    assert not any(stmt.startswith("INSERT INTO schema_migrations") for stmt in executed)


@pytest.mark.asyncio
async def test_init_db_creates_pool_and_runs_migrations(monkeypatch):
    pool, _conn = make_pool()
    create_pool = AsyncMock(return_value=pool)
    monkeypatch.setattr(neon.asyncpg, "create_pool", create_pool)
    monkeypatch.setattr(neon, "_pool", None)

    await neon.init_db()

    create_pool.assert_awaited_once_with(dsn=neon.settings.database_url, min_size=1, max_size=5)
    assert neon.get_pool() is pool

    await neon.close_db()


@pytest.mark.asyncio
async def test_close_db_closes_and_clears_pool(monkeypatch):
    pool = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(neon, "_pool", pool)

    await neon.close_db()

    pool.close.assert_awaited_once()
    with pytest.raises(RuntimeError):
        neon.get_pool()


@pytest.mark.asyncio
async def test_close_db_is_a_no_op_when_never_initialized(monkeypatch):
    monkeypatch.setattr(neon, "_pool", None)

    await neon.close_db()  # must not raise


def test_get_pool_raises_before_init(monkeypatch):
    monkeypatch.setattr(neon, "_pool", None)

    with pytest.raises(RuntimeError, match="not initialized"):
        neon.get_pool()
