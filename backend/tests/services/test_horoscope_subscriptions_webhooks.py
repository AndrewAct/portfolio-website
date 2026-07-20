import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from svix.webhooks import Webhook

from apps.config import get_settings
from apps.services.horoscope_subscriptions.webhooks import get_repository
from apps.services.horoscope_subscriptions.webhooks import router as webhooks_router

settings = get_settings()


def sign(body: bytes, msg_id: str = "msg_1") -> dict[str, str]:
    timestamp = datetime.now(UTC)
    signer = Webhook(settings.resend_webhook_secret)
    signature = signer.sign(msg_id=msg_id, timestamp=timestamp, data=body.decode())
    return {
        "svix-id": msg_id,
        "svix-timestamp": str(int(timestamp.timestamp())),
        "svix-signature": signature,
    }


def build_app(fake_repository) -> FastAPI:
    app = FastAPI()
    app.include_router(webhooks_router)
    app.dependency_overrides[get_repository] = lambda: fake_repository
    return app


def make_repository(delivery=None) -> SimpleNamespace:
    return SimpleNamespace(
        get_delivery_by_resend_message_id=AsyncMock(return_value=delivery),
        update_delivery_status=AsyncMock(),
        pause=AsyncMock(),
    )


async def post_webhook(app: FastAPI, payload: dict, headers: dict) -> object:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        body = json.dumps(payload).encode()
        return await client.post("/resend", content=body, headers=headers)


@pytest.mark.asyncio
async def test_delivered_event_updates_status_and_delivered_at():
    repository = make_repository(delivery={"id": 7, "subscription_id": 1})
    app = build_app(repository)
    payload = {"type": "email.delivered", "data": {"email_id": "resend-msg-1"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.update_delivery_status.assert_awaited_once()
    args, kwargs = repository.update_delivery_status.await_args
    assert args == (7, "delivered")
    assert kwargs["delivered_at"] is not None
    repository.pause.assert_not_awaited()


@pytest.mark.asyncio
async def test_bounced_event_pauses_subscription():
    repository = make_repository(delivery={"id": 7, "subscription_id": 1})
    app = build_app(repository)
    payload = {"type": "email.bounced", "data": {"email_id": "resend-msg-1"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.update_delivery_status.assert_awaited_once_with(7, "bounced", delivered_at=None)
    repository.pause.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_complained_event_pauses_subscription():
    repository = make_repository(delivery={"id": 7, "subscription_id": 1})
    app = build_app(repository)
    payload = {"type": "email.complained", "data": {"email_id": "resend-msg-1"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.pause.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_failed_event_updates_status_without_pausing_subscription():
    # Covers Resend accepting the send (so our own code already marked it 'sent') but
    # later failing to deliver for a reason only their pipeline could see.
    repository = make_repository(delivery={"id": 7, "subscription_id": 1})
    app = build_app(repository)
    payload = {"type": "email.failed", "data": {"email_id": "resend-msg-1"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.update_delivery_status.assert_awaited_once_with(7, "failed", delivered_at=None)
    repository.pause.assert_not_awaited()


@pytest.mark.asyncio
async def test_unrecognized_event_type_is_ignored():
    repository = make_repository()
    app = build_app(repository)
    payload = {"type": "email.opened", "data": {"email_id": "resend-msg-1"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.get_delivery_by_resend_message_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_signature_is_rejected():
    repository = make_repository()
    app = build_app(repository)
    payload = {"type": "email.delivered", "data": {"email_id": "resend-msg-1"}}
    bad_headers = {
        "svix-id": "msg_1",
        "svix-timestamp": str(int(datetime.now(UTC).timestamp())),
        "svix-signature": "v1,not-a-real-signature",
    }

    response = await post_webhook(app, payload, bad_headers)

    assert response.status_code == 401
    repository.get_delivery_by_resend_message_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_message_id_is_a_no_op():
    repository = make_repository(delivery=None)
    app = build_app(repository)
    payload = {"type": "email.delivered", "data": {"email_id": "unknown-msg"}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.update_delivery_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_email_id_is_a_no_op():
    repository = make_repository()
    app = build_app(repository)
    payload = {"type": "email.delivered", "data": {}}
    body = json.dumps(payload).encode()

    response = await post_webhook(app, payload, sign(body))

    assert response.status_code == 200
    repository.get_delivery_by_resend_message_id.assert_not_awaited()
