from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from apps.integrations.resend import ResendSendError
from apps.services.horoscope_subscriptions import tokens
from apps.services.horoscope_subscriptions.delivery_service import DeliveryService

SUBSCRIPTION = {
    "id": 1,
    "email": "user@example.com",
    "birthdate": date(1990, 4, 7),
    "gender": "female",
    "language": "en",
    "timezone": "America/Los_Angeles",
    "token_version": 3,
}

HOROSCOPE = {
    "zodiac_sign": "Aries",
    "zodiac_sign_chinese": "白羊座",
    "daily_horoscope": "A focused day.",
    "lucky_number": 7,
    "compatibility": "Leo",
    "mood": "Calm",
}


def make_delivery_service() -> DeliveryService:
    repository = SimpleNamespace(mark_delivery_sent=AsyncMock(), mark_delivery_failed=AsyncMock())
    email_sender = SimpleNamespace(send=AsyncMock(return_value="resend-msg-1"))
    horoscope_service = SimpleNamespace(
        get_zodiac_sign=Mock(return_value=("Aries", "白羊座")),
        get_daily_horoscope=AsyncMock(return_value=HOROSCOPE),
    )
    return DeliveryService(
        repository=repository,
        email_sender=email_sender,
        horoscope_service=horoscope_service,  # ty:ignore[invalid-argument-type]
    )


@pytest.mark.asyncio
async def test_send_daily_horoscope_success_marks_sent():
    service = make_delivery_service()

    await service.send_daily_horoscope(SUBSCRIPTION, delivery_id=42, local_date=date(2026, 7, 19))

    service.email_sender.send.assert_awaited_once()
    kwargs = service.email_sender.send.await_args.kwargs
    assert kwargs["to"] == "user@example.com"
    assert kwargs["idempotency_key"] == "horoscope:1:2026-07-19"
    service.repository.mark_delivery_sent.assert_awaited_once_with(42, "resend-msg-1")
    service.repository.mark_delivery_failed.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_daily_horoscope_uses_localized_sign_for_non_english():
    service = make_delivery_service()
    subscription = {**SUBSCRIPTION, "language": "zh"}

    await service.send_daily_horoscope(subscription, delivery_id=1, local_date=date(2026, 7, 19))

    call = service.horoscope_service.get_daily_horoscope.await_args
    assert call.args[0] == "白羊座"
    assert call.args[2] == "zh"


@pytest.mark.asyncio
async def test_send_daily_horoscope_records_resend_failure_without_raising():
    service = make_delivery_service()
    service.email_sender.send = AsyncMock(side_effect=ResendSendError("Resend rejected"))

    await service.send_daily_horoscope(SUBSCRIPTION, delivery_id=42, local_date=date(2026, 7, 19))

    service.repository.mark_delivery_failed.assert_awaited_once()
    args = service.repository.mark_delivery_failed.await_args.args
    assert args[0] == 42
    assert "Resend rejected" in args[1]
    service.repository.mark_delivery_sent.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_daily_horoscope_isolates_unexpected_generation_failure():
    service = make_delivery_service()
    service.horoscope_service.get_daily_horoscope = AsyncMock(side_effect=RuntimeError("boom"))

    await service.send_daily_horoscope(SUBSCRIPTION, delivery_id=42, local_date=date(2026, 7, 19))

    service.repository.mark_delivery_failed.assert_awaited_once()
    service.email_sender.send.assert_not_awaited()


def test_render_embeds_purpose_scoped_tokens_matching_subscription_version():
    subject, html_body, text = DeliveryService._render(SUBSCRIPTION, HOROSCOPE)

    assert "Aries" in subject
    for url_field, expected_purpose in (
        ("preferences", "preferences"),
        ("unsubscribe", "unsubscribe"),
    ):
        marker = f"/horoscope/{url_field}?token="
        start = html_body.index(marker) + len(marker)
        end = html_body.index('"', start)
        token = html_body[start:end]
        payload = tokens.verify_token(token, expected_purpose=expected_purpose)
        assert payload.subscription_id == 1
        assert payload.token_version == 3
    assert "A focused day." in text
