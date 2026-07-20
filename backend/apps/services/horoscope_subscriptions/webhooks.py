"""Resend delivery-status webhook.

Verifies the Svix-based signature Resend uses (raw body required — never re-serialize a
parsed body before verifying) via the official `svix` package rather than hand-rolling the
HMAC/timestamp-tolerance logic. Unrecognized event types are ignored, not errored, since
Resend has more event types (opened/clicked/scheduled/...) than we act on and may add more.
"""

import logging
from datetime import UTC, datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, Request, Response
from svix.webhooks import Webhook, WebhookVerificationError

from ...config import get_settings
from .repository import SubscriptionRepository

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")

router = APIRouter()

_STATUS_BY_EVENT = {
    "email.sent": "sent",
    "email.delivered": "delivered",
    "email.bounced": "bounced",
    "email.complained": "complained",
    # Covers the case where Resend accepted the send request (so our own synchronous
    # code already recorded 'sent') but their pipeline later failed to deliver it for a
    # reason we couldn't have seen at call time. update_delivery_status() overwrites
    # 'sent' -> 'failed' unconditionally, and reclaim_failed_delivery() on the next tick
    # picks it up for retry — without incrementing attempt_count, since this wasn't a
    # failed API call on our end.
    "email.failed": "failed",
}

# Bounce/complaint pause the parent subscription, per spec — not just the delivery row.
_PAUSE_SUBSCRIPTION_ON = {"email.bounced", "email.complained"}


@lru_cache
def get_repository() -> SubscriptionRepository:
    return SubscriptionRepository()


@router.post("/resend")
async def handle_resend_webhook(
    request: Request,
    repository: SubscriptionRepository = Depends(get_repository),  # noqa: B008
) -> Response:
    body = await request.body()
    try:
        # svix's underlying verifier raises a raw binascii.Error (a ValueError subclass)
        # for a malformed, non-base64 signature header rather than its own
        # WebhookVerificationError — this endpoint is a security boundary receiving fully
        # untrusted input, so both must map to a clean 401, not an unhandled 500.
        payload = Webhook(settings.resend_webhook_secret).verify(body, dict(request.headers))
    except (WebhookVerificationError, ValueError):
        logger.warning("Rejected Resend webhook with an invalid signature")
        return Response(status_code=401)

    event_type = payload.get("type")
    status = _STATUS_BY_EVENT.get(event_type)
    if status is None:
        logger.debug("Ignoring unrecognized Resend event type: %s", event_type)
        return Response(status_code=200)

    message_id = payload.get("data", {}).get("email_id")
    if not message_id:
        return Response(status_code=200)

    delivery = await repository.get_delivery_by_resend_message_id(message_id)
    if delivery is None:
        return Response(status_code=200)

    delivered_at = datetime.now(UTC) if status == "delivered" else None
    await repository.update_delivery_status(delivery["id"], status, delivered_at=delivered_at)

    if event_type in _PAUSE_SUBSCRIPTION_ON:
        await repository.pause(delivery["subscription_id"])

    return Response(status_code=200)
