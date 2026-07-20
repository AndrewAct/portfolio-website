"""Async Resend email client.

Hand-rolled against Resend's REST API with a shared httpx.AsyncClient (connection reuse)
rather than the official `resend` SDK, which is synchronous/requests-based.

Open/click tracking is a Resend domain-level dashboard setting, not a per-request API
field — it must be turned off for the sending domain in the Resend dashboard, not here.
"""

import logging
from typing import Any

import httpx

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger("horoscope_subscriptions")

RESEND_BASE_URL = "https://api.resend.com"


class ResendSendError(RuntimeError):
    """Raised when Resend rejects or fails to accept an email."""


class ResendEmailSender:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self.from_email = settings.resend_from_email
        self.reply_to = settings.resend_reply_to_email
        self._client = client or httpx.AsyncClient(
            base_url=RESEND_BASE_URL,
            timeout=settings.resend_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def send(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str,
        idempotency_key: str,
    ) -> str:
        """Send an email via Resend. Returns the Resend message id."""
        payload: dict[str, Any] = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        }
        if self.reply_to:
            payload["reply_to"] = self.reply_to
        try:
            response = await self._client.post(
                "/emails",
                json=payload,
                headers={"Idempotency-Key": idempotency_key},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Resend send failed for idempotency key %s", idempotency_key)
            raise ResendSendError(str(exc)) from exc

        message_id = response.json().get("id")
        if not message_id:
            raise ResendSendError("Resend response did not contain a message id")
        return message_id
