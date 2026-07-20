"""HMAC-signed, purpose-scoped tokens for confirm/preferences/unsubscribe links.

Stateless: the raw token is never persisted, verification is pure recomputation.
Purpose-scoping (baked into the signed payload) stops a leaked link for one action
being replayed as a different one — e.g. an unsubscribe link can't confirm a
subscription. `token_version` is included but compared against the subscription's
current value by the caller (this module has no DB access) — that's what actually
lets a link be revoked (bumped on email change / unsubscribe) despite the token
itself being stateless.
"""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Literal

from ...config import get_settings

settings = get_settings()

Purpose = Literal["confirm", "preferences", "unsubscribe"]


class TokenError(ValueError):
    """Malformed, mis-scoped, or expired token."""


@dataclass(frozen=True)
class TokenPayload:
    subscription_id: int
    purpose: Purpose
    token_version: int


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign_token(
    *,
    subscription_id: int,
    purpose: Purpose,
    token_version: int,
    ttl_seconds: int | None = None,
) -> str:
    payload: dict[str, object] = {
        "sub": subscription_id,
        "purpose": purpose,
        "ver": token_version,
        "iat": int(time.time()),
    }
    if ttl_seconds is not None:
        payload["exp"] = int(time.time()) + ttl_seconds

    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = _sign(payload_bytes)
    return f"{_b64encode(payload_bytes)}.{_b64encode(signature)}"


def verify_token(token: str, *, expected_purpose: Purpose) -> TokenPayload:
    """Verify signature, purpose, and expiry. Raises TokenError on any failure."""
    try:
        payload_part, signature_part = token.split(".", 1)
        payload_bytes = _b64decode(payload_part)
        signature = _b64decode(signature_part)
        payload = json.loads(payload_bytes)
    except (ValueError, TypeError) as exc:
        raise TokenError("Malformed token") from exc

    if not hmac.compare_digest(signature, _sign(payload_bytes)):
        raise TokenError("Invalid token signature")

    if payload.get("purpose") != expected_purpose:
        raise TokenError("Token is not valid for this action")

    subscription_id = payload.get("sub")
    token_version = payload.get("ver")
    if not isinstance(subscription_id, int) or not isinstance(token_version, int):
        raise TokenError("Malformed token payload")

    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise TokenError("Token has expired")

    return TokenPayload(
        subscription_id=subscription_id, purpose=expected_purpose, token_version=token_version
    )


def _sign(payload_bytes: bytes) -> bytes:
    return hmac.new(
        settings.subscription_token_secret.encode("utf-8"), payload_bytes, hashlib.sha256
    ).digest()
