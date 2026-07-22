"""Horoscope email delivery worker: polls Postgres for due subscriptions and sends.

State lives entirely in Postgres (claimed deliveries, attempt counts), not in-process —
that's the whole restart story. After a crash, the next tick just re-evaluates "due" the
same way; a delivery never attempted today becomes due immediately, and the database's
UNIQUE(subscription_id, local_date) constraint is what makes concurrent/duplicate claims
safe (see repository.claim_delivery / reclaim_failed_delivery). This covers a delivery
never started or one that finished attempting and failed — but not one abandoned *mid*-
attempt (worker killed between claiming it and recording an outcome, e.g. SIGKILL during
a deploy with no signal handler installed). repository.reclaim_stale_pending_delivery
covers that case: a delivery stuck at status='pending' past a staleness threshold gets
reclaimed the same way a failed one does.

Run as: python -m apps.workers.horoscope_email
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg

from ..config import get_settings
from ..database.neon import close_db, init_db
from ..services.horoscope_subscriptions.delivery_service import DeliveryService
from ..services.horoscope_subscriptions.repository import SubscriptionRepository

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")


@dataclass
class TickResult:
    due: int = 0
    sent: int = 0
    skipped: int = 0


@dataclass
class WorkerDeps:
    repository: SubscriptionRepository
    delivery_service: DeliveryService
    now_utc: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    max_attempts: int = settings.worker_max_delivery_attempts
    stale_pending_seconds: int = settings.worker_stale_pending_seconds


async def tick(deps: WorkerDeps) -> TickResult:
    """One polling pass: claim and send every subscription whose local send time has
    passed today and hasn't been delivered/attempted-out yet."""
    result = TickResult()
    now_utc = deps.now_utc()

    for subscription in await deps.repository.list_active():
        if not _is_due(subscription, now_utc, result):
            continue
        await _claim_and_send(deps, subscription, now_utc, result)

    return result


def _is_due(subscription: asyncpg.Record, now_utc: datetime, result: TickResult) -> bool:
    try:
        zone = ZoneInfo(subscription["timezone"])
    except ZoneInfoNotFoundError:
        logger.error(
            "Subscription %s has an unrecognized timezone %r; skipping",
            subscription["id"],
            subscription["timezone"],
        )
        result.skipped += 1
        return False

    if now_utc.astimezone(zone).time() < subscription["send_time_local"]:
        result.skipped += 1
        return False

    result.due += 1
    return True


async def _claim_and_send(
    deps: WorkerDeps, subscription: asyncpg.Record, now_utc: datetime, result: TickResult
) -> None:
    # Computed once and threaded through both claim calls below — never re-derived, so a
    # midnight-boundary race within one tick can't produce two different local dates.
    local_date = now_utc.astimezone(ZoneInfo(subscription["timezone"])).date()
    idempotency_key = f"horoscope:{subscription['id']}:{local_date.isoformat()}"

    # Cheap read first, so a subscription already resolved today (sent/delivered) never
    # reaches an INSERT — every prior tick for the rest of the day used to attempt one
    # anyway and lose it to ON CONFLICT DO NOTHING, burning a bigserial id each time.
    status = await deps.repository.get_delivery_status(subscription["id"], local_date)
    sub_id = subscription["id"]

    if status is None:
        delivery_id = await deps.repository.claim_delivery(sub_id, local_date, idempotency_key)
        if delivery_id is None:
            # Precheck saw no row, yet the INSERT still lost to ON CONFLICT DO NOTHING —
            # a bigserial id just got burned for nothing. Shouldn't happen with one
            # worker; repeated hits mean two worker processes are live at once.
            logger.warning(
                "sub=%s date=%s claim lost a race after a clean precheck", sub_id, local_date
            )
        else:
            logger.info("sub=%s date=%s claimed delivery_id=%s", sub_id, local_date, delivery_id)
    elif status == "failed":
        delivery_id = await deps.repository.reclaim_failed_delivery(
            sub_id, local_date, deps.max_attempts
        )
        if delivery_id is not None:
            logger.info(
                "sub=%s date=%s retried failed delivery_id=%s", sub_id, local_date, delivery_id
            )
        else:
            logger.warning(
                "sub=%s date=%s gave up after max_attempts=%s",
                sub_id,
                local_date,
                deps.max_attempts,
            )
    elif status == "pending":
        # Covers a worker killed between claiming a delivery and recording its outcome
        # (e.g. SIGKILL during a deployment). Bounded by max_attempts like the failed path.
        stale_before = now_utc - timedelta(seconds=deps.stale_pending_seconds)
        delivery_id = await deps.repository.reclaim_stale_pending_delivery(
            sub_id, local_date, deps.max_attempts, stale_before
        )
        if delivery_id is not None:
            logger.info(
                "sub=%s date=%s reclaimed stale delivery_id=%s", sub_id, local_date, delivery_id
            )
    else:
        # 'sent', 'delivered', or any other terminal status — already resolved today.
        delivery_id = None
        logger.debug("sub=%s date=%s already resolved (status=%s)", sub_id, local_date, status)

    if delivery_id is None:
        # Retries exhausted, nothing stale yet, or claimed by another worker between our
        # read and write — all fine, nothing to do.
        return

    await deps.delivery_service.send_daily_horoscope(subscription, delivery_id, local_date)
    result.sent += 1


async def run_forever() -> None:
    await init_db()
    deps = WorkerDeps(repository=SubscriptionRepository(), delivery_service=DeliveryService())
    logger.info(
        "Horoscope email worker started, polling every %ss", settings.worker_poll_interval_seconds
    )
    try:
        while True:
            await _run_tick_safely(deps)
            await asyncio.sleep(settings.worker_poll_interval_seconds)
    finally:
        await _shutdown(deps)


async def _run_tick_safely(deps: WorkerDeps) -> None:
    """Never lets a single bad tick (transient DB blip, etc.) kill the worker loop."""
    try:
        result = await tick(deps)
    except Exception:
        logger.exception("Worker tick failed; will retry next interval")
        return
    if result.due:
        logger.info(
            "Tick complete: due=%s sent=%s skipped=%s", result.due, result.sent, result.skipped
        )


async def _shutdown(deps: WorkerDeps) -> None:
    await deps.delivery_service.email_sender.close()
    await deps.delivery_service.horoscope_service.close()
    await close_db()


if __name__ == "__main__":
    asyncio.run(run_forever())
