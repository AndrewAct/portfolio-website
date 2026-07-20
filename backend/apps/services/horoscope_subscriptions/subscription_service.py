"""Subscribe/confirm/preferences/unsubscribe orchestration.

Security boundary worth spelling out: `subscribe()` is reachable anonymously (only
knowledge of an email address is required), so it never edits an already-active
subscription in place — any submission through it resets to `pending_confirmation` and
requires a fresh confirm click. In-place preference edits without reconfirmation are only
available through `update_preferences()`, which requires a previously-issued, purpose-
scoped token proving control of the mailbox. This closes what would otherwise be a way for
anyone who knows a subscriber's email to silently rewrite their live preferences.
"""

import logging

import asyncpg
from fastapi import HTTPException

from ...config import get_settings
from ...integrations.resend import ResendEmailSender
from . import tokens
from .email_templates import build_confirmation_email
from .repository import SubscriptionRepository
from .schemas import (
    ConfirmResponse,
    PreferencesResponse,
    SubscribeResponse,
    SubscriptionPreferences,
    UnsubscribeResponse,
    UpdatePreferencesResponse,
)

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")


class SubscriptionService:
    def __init__(
        self,
        repository: SubscriptionRepository | None = None,
        email_sender: ResendEmailSender | None = None,
    ):
        self.repository = repository if repository is not None else SubscriptionRepository()
        self.email_sender = email_sender if email_sender is not None else ResendEmailSender()

    async def close(self) -> None:
        await self.email_sender.close()

    async def subscribe(self, request: SubscriptionPreferences) -> SubscribeResponse:
        existing = await self.repository.get_by_email(request.email)
        if existing is None:
            subscription = await self.repository.insert(
                email=request.email,
                birthdate=request.birthdate,
                gender=request.gender,
                language=request.language,
                timezone=request.timezone,
                send_time_local=request.send_time_local,
            )
        else:
            subscription = await self.repository.update_preferences_and_reset_to_pending(
                existing["id"],
                birthdate=request.birthdate,
                gender=request.gender,
                language=request.language,
                timezone=request.timezone,
                send_time_local=request.send_time_local,
            )

        await self._send_confirmation(subscription)
        return SubscribeResponse(status="confirmation_sent")

    async def confirm(self, token: str) -> ConfirmResponse:
        payload = self._verify(token, purpose="confirm")
        subscription = await self._load_matching_subscription(payload)

        if subscription["status"] == "active":
            return ConfirmResponse(status="already_confirmed")
        if subscription["status"] != "pending_confirmation":
            raise HTTPException(
                status_code=400,
                detail="This subscription is no longer active; please subscribe again",
            )

        confirmed = await self.repository.confirm(subscription["id"])
        if confirmed is None:
            # Status changed between our read and the UPDATE (e.g. concurrent confirm click).
            return ConfirmResponse(status="already_confirmed")
        return ConfirmResponse(status="confirmed")

    async def get_preferences(self, token: str) -> PreferencesResponse:
        payload = self._verify(token, purpose="preferences")
        subscription = await self._load_matching_subscription(payload)

        return PreferencesResponse(
            email=subscription["email"],
            birthdate=subscription["birthdate"],
            gender=subscription["gender"],
            language=subscription["language"],
            timezone=subscription["timezone"],
            send_time_local=subscription["send_time_local"],
        )

    async def update_preferences(
        self, token: str, request: SubscriptionPreferences
    ) -> UpdatePreferencesResponse:
        payload = self._verify(token, purpose="preferences")
        subscription = await self._load_matching_subscription(payload)

        email_changed = request.email.lower() != subscription["email"].lower()
        if not email_changed:
            await self.repository.update_preferences(
                subscription["id"],
                birthdate=request.birthdate,
                gender=request.gender,
                language=request.language,
                timezone=request.timezone,
                send_time_local=request.send_time_local,
            )
            return UpdatePreferencesResponse(status="updated")

        try:
            updated = await self.repository.update_email_and_preferences(
                subscription["id"],
                new_email=request.email,
                birthdate=request.birthdate,
                gender=request.gender,
                language=request.language,
                timezone=request.timezone,
                send_time_local=request.send_time_local,
            )
        except asyncpg.UniqueViolationError as exc:
            raise HTTPException(
                status_code=409,
                detail="This email is already associated with another subscription",
            ) from exc

        await self._send_confirmation(updated)
        return UpdatePreferencesResponse(status="confirmation_sent")

    async def unsubscribe(self, token: str) -> UnsubscribeResponse:
        payload = self._verify(token, purpose="unsubscribe")
        subscription = await self._load_matching_subscription(payload)

        if subscription["status"] == "unsubscribed":
            return UnsubscribeResponse(status="already_unsubscribed")

        updated = await self.repository.unsubscribe(subscription["id"])
        if updated is None:
            return UnsubscribeResponse(status="already_unsubscribed")
        return UnsubscribeResponse(status="unsubscribed")

    async def _send_confirmation(self, subscription: asyncpg.Record) -> None:
        token = tokens.sign_token(
            subscription_id=subscription["id"],
            purpose="confirm",
            token_version=subscription["token_version"],
            ttl_seconds=settings.confirm_token_ttl_days * 86400,
        )
        confirm_url = f"{settings.public_base_url}/horoscope/confirm?token={token}"
        subject, html_body, text = build_confirmation_email(confirm_url=confirm_url)
        await self.email_sender.send(
            to=subscription["email"],
            subject=subject,
            html=html_body,
            text=text,
            # Anchored to this row's updated_at (set once per logical subscribe/email-change
            # action) so a network-level retry of the same action doesn't double-send, while
            # a genuinely separate resubmit — which produces a new updated_at — still does.
            idempotency_key=f"confirm:{subscription['id']}:{subscription['updated_at'].timestamp()}",
        )

    @staticmethod
    def _verify(token: str, *, purpose: tokens.Purpose) -> tokens.TokenPayload:
        try:
            return tokens.verify_token(token, expected_purpose=purpose)
        except tokens.TokenError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def _load_matching_subscription(self, payload: tokens.TokenPayload) -> asyncpg.Record:
        subscription = await self.repository.get_by_id(payload.subscription_id)
        if subscription is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if subscription["token_version"] != payload.token_version:
            raise HTTPException(status_code=400, detail="This link is no longer valid")
        return subscription
