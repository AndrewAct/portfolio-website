"""Generates and sends one day's horoscope email for an already-claimed delivery row.

Used only by the worker (apps/workers/horoscope_email.py), after it has atomically claimed
a `horoscope_deliveries` row via the repository's INSERT-ON-CONFLICT/UPDATE claim. This
service does not decide *whether* to send — only *how* — so it has no knowledge of due-ness,
polling, or claiming.
"""

import logging
from datetime import date
from typing import Any

import asyncpg

from ...config import get_settings
from ...integrations.resend import ResendEmailSender, ResendSendError
from ..horoscope.service import HoroscopeService
from . import tokens
from .email_templates import build_daily_horoscope_email
from .repository import SubscriptionRepository

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")


class DeliveryService:
    def __init__(
        self,
        repository: SubscriptionRepository | None = None,
        email_sender: ResendEmailSender | None = None,
        horoscope_service: HoroscopeService | None = None,
    ):
        self.repository = repository if repository is not None else SubscriptionRepository()
        self.email_sender = email_sender if email_sender is not None else ResendEmailSender()
        self.horoscope_service = (
            horoscope_service if horoscope_service is not None else HoroscopeService()
        )

    async def send_daily_horoscope(
        self, subscription: asyncpg.Record, delivery_id: int, local_date: date
    ) -> None:
        """Best-effort: any failure is recorded on the delivery row, never raised, so one
        bad subscriber (Gemini hiccup, Resend error) can't halt the rest of a worker tick."""
        try:
            horoscope = await self._generate_horoscope(subscription)
            subject, html_body, text = self._render(subscription, horoscope)
            message_id = await self.email_sender.send(
                to=subscription["email"],
                subject=subject,
                html=html_body,
                text=text,
                idempotency_key=f"horoscope:{subscription['id']}:{local_date.isoformat()}",
            )
        except ResendSendError as exc:
            logger.warning("Delivery %s failed to send: %s", delivery_id, exc)
            await self.repository.mark_delivery_failed(delivery_id, str(exc))
            return
        except Exception as exc:  # external API/generation boundary — isolate per-subscriber
            logger.exception("Delivery %s failed unexpectedly", delivery_id)
            await self.repository.mark_delivery_failed(delivery_id, str(exc))
            return

        await self.repository.mark_delivery_sent(delivery_id, message_id)

    async def _generate_horoscope(self, subscription: asyncpg.Record) -> dict[str, Any]:
        language = subscription["language"]
        english_name, localized_name = self.horoscope_service.get_zodiac_sign(
            subscription["birthdate"], language
        )
        zodiac_sign = english_name if language == "en" else localized_name
        return await self.horoscope_service.get_daily_horoscope(
            zodiac_sign, subscription["gender"], language
        )

    @staticmethod
    def _render(subscription: asyncpg.Record, horoscope: dict[str, Any]) -> tuple[str, str, str]:
        preferences_token = tokens.sign_token(
            subscription_id=subscription["id"],
            purpose="preferences",
            token_version=subscription["token_version"],
        )
        unsubscribe_token = tokens.sign_token(
            subscription_id=subscription["id"],
            purpose="unsubscribe",
            token_version=subscription["token_version"],
        )
        return build_daily_horoscope_email(
            horoscope=horoscope,
            preferences_url=f"{settings.public_base_url}/horoscope/preferences?token={preferences_token}",
            unsubscribe_url=f"{settings.public_base_url}/horoscope/unsubscribe?token={unsubscribe_token}",
        )
