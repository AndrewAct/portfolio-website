"""Raw asyncpg persistence for horoscope email subscriptions and their deliveries.

Each method borrows a connection from the pool for the duration of one statement — no
manual transaction/connection reuse across calls, matching this codebase's existing
"thin driver wrapper" style (see url_shortener/database.py). Callers are responsible for
interpreting `None` returns (row not found / precondition not met) and for catching
asyncpg.UniqueViolationError on email writes.
"""

from datetime import date, datetime, time

import asyncpg

from ...database.neon import get_pool


class SubscriptionRepository:
    def __init__(self, pool: asyncpg.Pool | None = None):
        self._pool = pool

    def _get_pool(self) -> asyncpg.Pool:
        return self._pool if self._pool is not None else get_pool()

    @staticmethod
    def _one(row: asyncpg.Record | None) -> asyncpg.Record:
        """Narrows a fetchrow() result for statements with a `RETURNING *` on a row we
        just read by id — subscriptions are never deleted, so these always match exactly
        one row; a None here would mean that invariant broke, not a normal outcome."""
        assert row is not None, "expected exactly one row"
        return row

    # --- subscriptions ---

    async def get_by_email(self, email: str) -> asyncpg.Record | None:
        async with self._get_pool().acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM horoscope_subscriptions WHERE lower(email) = lower($1)", email
            )

    async def get_by_id(self, subscription_id: int) -> asyncpg.Record | None:
        async with self._get_pool().acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM horoscope_subscriptions WHERE id = $1", subscription_id
            )

    async def insert(
        self,
        *,
        email: str,
        birthdate: date,
        gender: str,
        language: str,
        timezone: str,
        send_time_local: time,
    ) -> asyncpg.Record:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO horoscope_subscriptions
                    (email, birthdate, gender, language, timezone, send_time_local)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                email,
                birthdate,
                gender,
                language,
                timezone,
                send_time_local,
            )
            return self._one(row)

    async def update_preferences(
        self,
        subscription_id: int,
        *,
        birthdate: date,
        gender: str,
        language: str,
        timezone: str,
        send_time_local: time,
    ) -> asyncpg.Record:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE horoscope_subscriptions
                SET birthdate = $2, gender = $3, language = $4, timezone = $5,
                    send_time_local = $6, updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                subscription_id,
                birthdate,
                gender,
                language,
                timezone,
                send_time_local,
            )
            return self._one(row)

    async def update_preferences_and_reset_to_pending(
        self,
        subscription_id: int,
        *,
        birthdate: date,
        gender: str,
        language: str,
        timezone: str,
        send_time_local: time,
    ) -> asyncpg.Record:
        """Used when re-subscribing an email that was never confirmed or had unsubscribed."""
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE horoscope_subscriptions
                SET birthdate = $2, gender = $3, language = $4, timezone = $5,
                    send_time_local = $6, status = 'pending_confirmation', updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                subscription_id,
                birthdate,
                gender,
                language,
                timezone,
                send_time_local,
            )
            return self._one(row)

    async def update_email_and_preferences(
        self,
        subscription_id: int,
        *,
        new_email: str,
        birthdate: date,
        gender: str,
        language: str,
        timezone: str,
        send_time_local: time,
    ) -> asyncpg.Record:
        """Resets to pending_confirmation and bumps token_version so old links for this
        subscription stop working. Raises asyncpg.UniqueViolationError if new_email is
        already used by another subscription. Single atomic statement so an email change
        and its accompanying preference edits never land partially."""
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE horoscope_subscriptions
                SET email = $2, birthdate = $3, gender = $4, language = $5, timezone = $6,
                    send_time_local = $7, status = 'pending_confirmation',
                    token_version = token_version + 1, updated_at = now()
                WHERE id = $1
                RETURNING *
                """,
                subscription_id,
                new_email,
                birthdate,
                gender,
                language,
                timezone,
                send_time_local,
            )
            return self._one(row)

    async def confirm(self, subscription_id: int) -> asyncpg.Record | None:
        """Returns None if the subscription wasn't in pending_confirmation (already
        active, paused, or unsubscribed) — callers decide what that means."""
        async with self._get_pool().acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE horoscope_subscriptions
                SET status = 'active', confirmed_at = now(), updated_at = now()
                WHERE id = $1 AND status = 'pending_confirmation'
                RETURNING *
                """,
                subscription_id,
            )

    async def unsubscribe(self, subscription_id: int) -> asyncpg.Record | None:
        async with self._get_pool().acquire() as conn:
            return await conn.fetchrow(
                """
                UPDATE horoscope_subscriptions
                SET status = 'unsubscribed', unsubscribed_at = now(),
                    token_version = token_version + 1, updated_at = now()
                WHERE id = $1 AND status != 'unsubscribed'
                RETURNING *
                """,
                subscription_id,
            )

    async def pause(self, subscription_id: int) -> None:
        async with self._get_pool().acquire() as conn:
            await conn.execute(
                """
                UPDATE horoscope_subscriptions SET status = 'paused', updated_at = now()
                WHERE id = $1
                """,
                subscription_id,
            )

    async def list_active(self) -> list[asyncpg.Record]:
        async with self._get_pool().acquire() as conn:
            return await conn.fetch("SELECT * FROM horoscope_subscriptions WHERE status = 'active'")

    # --- deliveries ---

    async def get_delivery_status(self, subscription_id: int, local_date: date) -> str | None:
        """Read-only precheck the worker runs before attempting any claim/reclaim write.
        Lets it skip subscriptions already resolved today without burning a bigserial id
        on a doomed INSERT ... ON CONFLICT DO NOTHING. Returns None if no row exists yet."""
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status FROM horoscope_deliveries WHERE subscription_id = $1 AND local_date = $2",
                subscription_id,
                local_date,
            )
            return row["status"] if row else None

    async def claim_delivery(
        self, subscription_id: int, local_date: date, idempotency_key: str
    ) -> int | None:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO horoscope_deliveries
                    (subscription_id, local_date, status, idempotency_key)
                VALUES ($1, $2, 'pending', $3)
                ON CONFLICT (subscription_id, local_date) DO NOTHING
                RETURNING id
                """,
                subscription_id,
                local_date,
                idempotency_key,
            )
            return row["id"] if row else None

    async def reclaim_failed_delivery(
        self, subscription_id: int, local_date: date, max_attempts: int
    ) -> int | None:
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE horoscope_deliveries
                SET status = 'pending', updated_at = now()
                WHERE subscription_id = $1 AND local_date = $2
                  AND status = 'failed' AND attempt_count < $3
                RETURNING id
                """,
                subscription_id,
                local_date,
                max_attempts,
            )
            return row["id"] if row else None

    async def reclaim_stale_pending_delivery(
        self, subscription_id: int, local_date: date, max_attempts: int, stale_before: datetime
    ) -> int | None:
        """Rescues a delivery abandoned mid-send (worker killed between claiming it and
        recording an outcome — e.g. SIGKILL during a deploy) rather than one still
        legitimately in flight. Bumps attempt_count here, not just on completion: a claim
        that never resolved within the staleness window was a real, spent attempt, and
        this is what keeps a delivery that's abandoned on every try from being reclaimed
        forever — it still respects max_attempts."""
        async with self._get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE horoscope_deliveries
                SET attempt_count = attempt_count + 1, updated_at = now()
                WHERE subscription_id = $1 AND local_date = $2
                  AND status = 'pending' AND attempt_count < $3
                  AND updated_at < $4
                RETURNING id
                """,
                subscription_id,
                local_date,
                max_attempts,
                stale_before,
            )
            return row["id"] if row else None

    async def mark_delivery_sent(self, delivery_id: int, resend_message_id: str) -> None:
        async with self._get_pool().acquire() as conn:
            await conn.execute(
                """
                UPDATE horoscope_deliveries
                SET status = 'sent', resend_message_id = $2, sent_at = now(),
                    attempt_count = attempt_count + 1, updated_at = now()
                WHERE id = $1
                """,
                delivery_id,
                resend_message_id,
            )

    async def mark_delivery_failed(self, delivery_id: int, error: str) -> None:
        async with self._get_pool().acquire() as conn:
            await conn.execute(
                """
                UPDATE horoscope_deliveries
                SET status = 'failed', last_error = $2,
                    attempt_count = attempt_count + 1, updated_at = now()
                WHERE id = $1
                """,
                delivery_id,
                error[:2000],
            )

    async def get_delivery_by_resend_message_id(
        self, resend_message_id: str
    ) -> asyncpg.Record | None:
        async with self._get_pool().acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM horoscope_deliveries WHERE resend_message_id = $1",
                resend_message_id,
            )

    async def update_delivery_status(
        self, delivery_id: int, status: str, *, delivered_at: datetime | None = None
    ) -> None:
        async with self._get_pool().acquire() as conn:
            await conn.execute(
                """
                UPDATE horoscope_deliveries
                SET status = $2, delivered_at = COALESCE($3, delivered_at), updated_at = now()
                WHERE id = $1
                """,
                delivery_id,
                status,
                delivered_at,
            )
