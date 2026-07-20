from datetime import UTC, date, datetime, time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from apps.services.horoscope_subscriptions.repository import SubscriptionRepository


class FakeAcquire:
    """Stands in for `pool.acquire()`'s async context manager."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *_exc_info):
        return False


def make_pool():
    conn = SimpleNamespace(fetchrow=AsyncMock(), fetch=AsyncMock(), execute=AsyncMock())
    pool = SimpleNamespace(acquire=Mock(return_value=FakeAcquire(conn)))
    return pool, conn


PREFS = {
    "birthdate": date(1990, 4, 7),
    "gender": "female",
    "language": "en",
    "timezone": "America/Los_Angeles",
    "send_time_local": time(8, 0),
}


@pytest.mark.asyncio
async def test_get_by_email_lowercases_in_query():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, "email": "a@b.com"}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.get_by_email("A@B.com")

    assert result == {"id": 1, "email": "a@b.com"}
    query, email = conn.fetchrow.await_args.args
    assert "lower(email) = lower($1)" in query
    assert email == "A@B.com"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing():
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    repo = SubscriptionRepository(pool=pool)

    assert await repo.get_by_id(999) is None


@pytest.mark.asyncio
async def test_insert_returns_new_row():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, "email": "new@example.com"}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.insert(email="new@example.com", **PREFS)

    assert result == {"id": 1, "email": "new@example.com"}
    query, *params = conn.fetchrow.await_args.args
    assert "INSERT INTO horoscope_subscriptions" in query
    assert params[0] == "new@example.com"


@pytest.mark.asyncio
async def test_update_preferences_does_not_change_status():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, **PREFS}
    repo = SubscriptionRepository(pool=pool)

    await repo.update_preferences(1, **PREFS)

    query = conn.fetchrow.await_args.args[0]
    assert "status" not in query


@pytest.mark.asyncio
async def test_update_preferences_and_reset_to_pending_sets_status():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, "status": "pending_confirmation"}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.update_preferences_and_reset_to_pending(1, **PREFS)

    assert result["status"] == "pending_confirmation"
    query = conn.fetchrow.await_args.args[0]
    assert "status = 'pending_confirmation'" in query


@pytest.mark.asyncio
async def test_update_email_and_preferences_bumps_token_version():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, "email": "new@example.com", "token_version": 2}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.update_email_and_preferences(1, new_email="new@example.com", **PREFS)

    assert result["email"] == "new@example.com"
    query = conn.fetchrow.await_args.args[0]
    assert "token_version = token_version + 1" in query
    assert "status = 'pending_confirmation'" in query


@pytest.mark.asyncio
async def test_one_raises_when_returning_star_yields_nothing():
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    repo = SubscriptionRepository(pool=pool)

    with pytest.raises(AssertionError):
        await repo.insert(email="x@example.com", **PREFS)


@pytest.mark.asyncio
async def test_confirm_returns_none_when_not_pending():
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    repo = SubscriptionRepository(pool=pool)

    assert await repo.confirm(1) is None
    query = conn.fetchrow.await_args.args[0]
    assert "status = 'pending_confirmation'" in query


@pytest.mark.asyncio
async def test_confirm_returns_row_when_transitioned():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 1, "status": "active"}
    repo = SubscriptionRepository(pool=pool)

    assert (await repo.confirm(1))["status"] == "active"


@pytest.mark.asyncio
async def test_unsubscribe_excludes_already_unsubscribed():
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    repo = SubscriptionRepository(pool=pool)

    assert await repo.unsubscribe(1) is None
    query = conn.fetchrow.await_args.args[0]
    assert "status != 'unsubscribed'" in query


@pytest.mark.asyncio
async def test_pause_updates_status():
    pool, conn = make_pool()
    repo = SubscriptionRepository(pool=pool)

    await repo.pause(1)

    query, subscription_id = conn.execute.await_args.args
    assert "status = 'paused'" in query
    assert subscription_id == 1


@pytest.mark.asyncio
async def test_list_active_filters_by_status():
    pool, conn = make_pool()
    conn.fetch.return_value = [{"id": 1}, {"id": 2}]
    repo = SubscriptionRepository(pool=pool)

    result = await repo.list_active()

    assert result == [{"id": 1}, {"id": 2}]
    assert "status = 'active'" in conn.fetch.await_args.args[0]


@pytest.mark.asyncio
async def test_claim_delivery_returns_id_on_success():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 7}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.claim_delivery(1, date(2026, 7, 19), "horoscope:1:2026-07-19")

    assert result == 7
    query = conn.fetchrow.await_args.args[0]
    assert "ON CONFLICT (subscription_id, local_date) DO NOTHING" in query


@pytest.mark.asyncio
async def test_claim_delivery_returns_none_on_conflict():
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    repo = SubscriptionRepository(pool=pool)

    assert await repo.claim_delivery(1, date(2026, 7, 19), "key") is None


@pytest.mark.asyncio
async def test_reclaim_failed_delivery_passes_max_attempts():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 9}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.reclaim_failed_delivery(1, date(2026, 7, 19), 5)

    assert result == 9
    query, subscription_id, local_date, max_attempts = conn.fetchrow.await_args.args
    assert "status = 'failed' AND attempt_count < $3" in query
    assert (subscription_id, local_date, max_attempts) == (1, date(2026, 7, 19), 5)


@pytest.mark.asyncio
async def test_mark_delivery_sent_records_message_id():
    pool, conn = make_pool()
    repo = SubscriptionRepository(pool=pool)

    await repo.mark_delivery_sent(7, "resend-msg-1")

    query, delivery_id, message_id = conn.execute.await_args.args
    assert "status = 'sent'" in query
    assert (delivery_id, message_id) == (7, "resend-msg-1")


@pytest.mark.asyncio
async def test_mark_delivery_failed_truncates_long_errors():
    pool, conn = make_pool()
    repo = SubscriptionRepository(pool=pool)

    await repo.mark_delivery_failed(7, "x" * 5000)

    _, _, stored_error = conn.execute.await_args.args
    assert len(stored_error) == 2000


@pytest.mark.asyncio
async def test_get_delivery_by_resend_message_id():
    pool, conn = make_pool()
    conn.fetchrow.return_value = {"id": 7, "resend_message_id": "resend-msg-1"}
    repo = SubscriptionRepository(pool=pool)

    result = await repo.get_delivery_by_resend_message_id("resend-msg-1")

    assert result["id"] == 7


@pytest.mark.asyncio
async def test_update_delivery_status_passes_delivered_at():
    pool, conn = make_pool()
    repo = SubscriptionRepository(pool=pool)
    delivered_at = datetime(2026, 7, 19, tzinfo=UTC)

    await repo.update_delivery_status(7, "delivered", delivered_at=delivered_at)

    query, delivery_id, status, passed_delivered_at = conn.execute.await_args.args
    assert (delivery_id, status, passed_delivered_at) == (7, "delivered", delivered_at)
    assert "COALESCE($3, delivered_at)" in query


@pytest.mark.asyncio
async def test_falls_back_to_module_pool_when_none_injected(monkeypatch):
    pool, conn = make_pool()
    conn.fetchrow.return_value = None
    monkeypatch.setattr(
        "apps.services.horoscope_subscriptions.repository.get_pool", Mock(return_value=pool)
    )
    repo = SubscriptionRepository()

    await repo.get_by_id(1)

    pool.acquire.assert_called_once()
