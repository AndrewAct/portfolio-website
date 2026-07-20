import asyncio
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import apps.workers.horoscope_email as horoscope_email
from apps.workers.horoscope_email import TickResult, WorkerDeps, tick

LA = "America/Los_Angeles"


def make_subscription(**overrides) -> dict:
    row = {"id": 1, "timezone": LA, "send_time_local": time(8, 0)}
    row.update(overrides)
    return row


def make_deps(
    subscriptions, *, now_utc: datetime, max_attempts: int = 5, stale_pending_seconds: int = 300
) -> WorkerDeps:
    repository = SimpleNamespace(
        list_active=AsyncMock(return_value=subscriptions),
        claim_delivery=AsyncMock(return_value=42),
        reclaim_failed_delivery=AsyncMock(return_value=None),
        reclaim_stale_pending_delivery=AsyncMock(return_value=None),
    )
    delivery_service = SimpleNamespace(send_daily_horoscope=AsyncMock())
    return WorkerDeps(
        repository=repository,
        delivery_service=delivery_service,
        now_utc=lambda: now_utc,
        max_attempts=max_attempts,
        stale_pending_seconds=stale_pending_seconds,
    )


@pytest.mark.asyncio
async def test_tick_skips_subscription_before_local_send_time():
    # 08:00 UTC is 00:00 or 01:00 America/Los_Angeles depending on DST — well before 08:00 local.
    deps = make_deps([make_subscription()], now_utc=datetime(2026, 7, 19, 8, 0, tzinfo=UTC))

    result = await tick(deps)

    assert result == TickResult(due=0, sent=0, skipped=1)
    deps.delivery_service.send_daily_horoscope.assert_not_awaited()
    deps.repository.claim_delivery.assert_not_awaited()


@pytest.mark.asyncio
async def test_tick_claims_and_sends_when_due():
    # 16:00 UTC on 2026-07-19 is 09:00 PDT — past an 08:00 local send time.
    deps = make_deps([make_subscription()], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC))

    result = await tick(deps)

    assert result == TickResult(due=1, sent=1, skipped=0)
    deps.repository.claim_delivery.assert_awaited_once_with(
        1, date(2026, 7, 19), "horoscope:1:2026-07-19"
    )
    deps.delivery_service.send_daily_horoscope.assert_awaited_once_with(
        make_subscription(), 42, date(2026, 7, 19)
    )


@pytest.mark.asyncio
async def test_tick_skips_when_already_claimed_and_not_retryable():
    deps = make_deps([make_subscription()], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC))
    deps.repository.claim_delivery.return_value = None
    deps.repository.reclaim_failed_delivery.return_value = None

    result = await tick(deps)

    assert result == TickResult(due=1, sent=0, skipped=0)
    deps.delivery_service.send_daily_horoscope.assert_not_awaited()


@pytest.mark.asyncio
async def test_tick_retries_via_reclaim_when_previous_attempt_failed():
    deps = make_deps([make_subscription()], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC))
    deps.repository.claim_delivery.return_value = None
    deps.repository.reclaim_failed_delivery.return_value = 99

    result = await tick(deps)

    assert result.sent == 1
    deps.repository.reclaim_failed_delivery.assert_awaited_once_with(1, date(2026, 7, 19), 5)
    deps.delivery_service.send_daily_horoscope.assert_awaited_once_with(
        make_subscription(), 99, date(2026, 7, 19)
    )


@pytest.mark.asyncio
async def test_tick_reclaims_delivery_abandoned_mid_send_after_crash():
    # Simulates a worker killed between claiming a delivery and recording its outcome
    # (e.g. SIGKILL during a deploy): the row already exists (claim_delivery -> None) and
    # isn't 'failed' (reclaim_failed_delivery -> None) — only the stale-pending path
    # should resume it.
    now_utc = datetime(2026, 7, 19, 16, 0, tzinfo=UTC)
    deps = make_deps([make_subscription()], now_utc=now_utc, stale_pending_seconds=300)
    deps.repository.claim_delivery.return_value = None
    deps.repository.reclaim_failed_delivery.return_value = None
    deps.repository.reclaim_stale_pending_delivery.return_value = 77

    result = await tick(deps)

    assert result.sent == 1
    deps.repository.reclaim_stale_pending_delivery.assert_awaited_once_with(
        1, date(2026, 7, 19), 5, now_utc - timedelta(seconds=300)
    )
    deps.delivery_service.send_daily_horoscope.assert_awaited_once_with(
        make_subscription(), 77, date(2026, 7, 19)
    )


@pytest.mark.asyncio
async def test_tick_does_not_reclaim_when_nothing_is_stale():
    # claim_delivery/reclaim_failed_delivery/reclaim_stale_pending_delivery all miss —
    # e.g. another (hypothetical) worker legitimately still has this in flight.
    deps = make_deps([make_subscription()], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC))
    deps.repository.claim_delivery.return_value = None
    deps.repository.reclaim_failed_delivery.return_value = None
    deps.repository.reclaim_stale_pending_delivery.return_value = None

    result = await tick(deps)

    assert result.sent == 0
    deps.delivery_service.send_daily_horoscope.assert_not_awaited()


@pytest.mark.asyncio
async def test_tick_skips_and_logs_unrecognized_timezone():
    deps = make_deps(
        [make_subscription(timezone="Not/AZone")], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC)
    )

    result = await tick(deps)

    assert result == TickResult(due=0, sent=0, skipped=1)
    deps.repository.claim_delivery.assert_not_awaited()


@pytest.mark.asyncio
async def test_tick_aggregates_across_multiple_subscriptions():
    due_now = datetime(2026, 7, 19, 16, 0, tzinfo=UTC)
    subscriptions = [
        make_subscription(id=1, send_time_local=time(8, 0)),  # due
        make_subscription(id=2, send_time_local=time(23, 0)),  # not due yet
    ]
    deps = make_deps(subscriptions, now_utc=due_now)

    result = await tick(deps)

    assert result == TickResult(due=1, sent=1, skipped=1)


@pytest.mark.asyncio
async def test_dst_spring_forward_gap_still_fires_instead_of_being_skipped_forever():
    # 2026-03-08: America/Los_Angeles springs forward 02:00 -> 03:00. 02:30 local never
    # occurs. A subscriber with send_time_local=02:30 must still fire once local time
    # crosses 03:00, not be silently skipped for the whole day.
    subscription = make_subscription(send_time_local=time(2, 30))
    just_after_jump = datetime(2026, 3, 8, 10, 5, tzinfo=UTC)  # 03:05 PDT
    deps = make_deps([subscription], now_utc=just_after_jump)

    result = await tick(deps)

    assert result.sent == 1


@pytest.mark.asyncio
async def test_dst_fall_back_repeated_hour_does_not_double_send():
    # 2026-11-01: America/Los_Angeles falls back, 01:00-02:00 occurs twice. A subscriber
    # with send_time_local=01:30 could pass the due-check on both passes through that
    # hour within the same local_date — the claim step (not the time comparison) must be
    # what prevents a second send.
    subscription = make_subscription(send_time_local=time(1, 30))
    first_pass_pdt = datetime(2026, 11, 1, 8, 35, tzinfo=UTC)  # 01:35 PDT (first 1:30 AM)
    second_pass_pst = datetime(2026, 11, 1, 9, 35, tzinfo=UTC)  # 01:35 PST (repeated 1:30 AM)

    repository = SimpleNamespace(
        list_active=AsyncMock(return_value=[subscription]),
        claim_delivery=AsyncMock(side_effect=[42, None]),
        reclaim_failed_delivery=AsyncMock(return_value=None),
        reclaim_stale_pending_delivery=AsyncMock(return_value=None),
    )
    delivery_service = SimpleNamespace(send_daily_horoscope=AsyncMock())

    deps_first = WorkerDeps(repository, delivery_service, now_utc=lambda: first_pass_pdt)
    deps_second = WorkerDeps(repository, delivery_service, now_utc=lambda: second_pass_pst)

    await tick(deps_first)
    await tick(deps_second)

    assert delivery_service.send_daily_horoscope.await_count == 1
    # Both claim attempts must target the same local_date, despite the UTC offset
    # differing between them (PDT vs PST) — otherwise this whole test would be vacuous.
    first_call_date = repository.claim_delivery.await_args_list[0].args[1]
    second_call_date = repository.claim_delivery.await_args_list[1].args[1]
    assert first_call_date == second_call_date == date(2026, 11, 1)


@pytest.mark.asyncio
async def test_run_tick_safely_swallows_tick_exceptions():
    deps = WorkerDeps(
        repository=SimpleNamespace(list_active=AsyncMock(side_effect=RuntimeError("db down"))),
        delivery_service=SimpleNamespace(),
    )

    await horoscope_email._run_tick_safely(deps)  # must not raise


@pytest.mark.asyncio
async def test_run_tick_safely_logs_only_when_something_was_due():
    deps = make_deps([], now_utc=datetime(2026, 7, 19, 16, 0, tzinfo=UTC))

    await horoscope_email._run_tick_safely(deps)  # nothing due, nothing to assert beyond no-raise


@pytest.mark.asyncio
async def test_run_forever_initializes_ticks_and_shuts_down(monkeypatch):
    init_db_mock = AsyncMock()
    close_db_mock = AsyncMock()
    monkeypatch.setattr(horoscope_email, "init_db", init_db_mock)
    monkeypatch.setattr(horoscope_email, "close_db", close_db_mock)

    fake_repository = SimpleNamespace(list_active=AsyncMock(return_value=[]))
    fake_delivery_service = SimpleNamespace(
        email_sender=SimpleNamespace(close=AsyncMock()),
        horoscope_service=SimpleNamespace(close=AsyncMock()),
    )
    monkeypatch.setattr(
        horoscope_email, "SubscriptionRepository", Mock(return_value=fake_repository)
    )
    monkeypatch.setattr(
        horoscope_email, "DeliveryService", Mock(return_value=fake_delivery_service)
    )
    monkeypatch.setattr(
        horoscope_email.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError)
    )

    with pytest.raises(asyncio.CancelledError):
        await horoscope_email.run_forever()

    init_db_mock.assert_awaited_once()
    fake_repository.list_active.assert_awaited_once()
    fake_delivery_service.email_sender.close.assert_awaited_once()
    fake_delivery_service.horoscope_service.close.assert_awaited_once()
    close_db_mock.assert_awaited_once()
