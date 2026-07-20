from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import asyncpg
import pytest
from fastapi import HTTPException

from apps.services.horoscope_subscriptions import tokens
from apps.services.horoscope_subscriptions.schemas import SubscriptionPreferences
from apps.services.horoscope_subscriptions.subscription_service import SubscriptionService


def make_subscription(**overrides) -> dict:
    row = {
        "id": 1,
        "email": "user@example.com",
        "status": "pending_confirmation",
        "birthdate": date(1990, 4, 7),
        "gender": "female",
        "language": "en",
        "timezone": "America/Los_Angeles",
        "send_time_local": time(8, 0),
        "token_version": 1,
        "updated_at": datetime(2026, 7, 19, 8, 0, 0),
    }
    row.update(overrides)
    return row


def make_repository(**method_return_values) -> SimpleNamespace:
    repo = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        insert=AsyncMock(),
        update_preferences_and_reset_to_pending=AsyncMock(),
        update_preferences=AsyncMock(),
        update_email_and_preferences=AsyncMock(),
        get_by_id=AsyncMock(return_value=None),
        confirm=AsyncMock(),
        unsubscribe=AsyncMock(),
    )
    for name, value in method_return_values.items():
        getattr(repo, name).return_value = value
    return repo


def make_service(repository, email_sender=None) -> SubscriptionService:
    email_sender = email_sender or SimpleNamespace(send=AsyncMock(), close=AsyncMock())
    return SubscriptionService(repository=repository, email_sender=email_sender)


PREFS = SubscriptionPreferences(
    email="user@example.com",
    birthdate=date(1990, 4, 7),
    gender="female",
    language="en",
    timezone="America/Los_Angeles",
    send_time_local=time(8, 0),
)


@pytest.mark.asyncio
async def test_subscribe_inserts_new_row_and_sends_confirmation():
    repository = make_repository(insert=make_subscription())
    service = make_service(repository)

    result = await service.subscribe(PREFS)

    assert result.status == "confirmation_sent"
    repository.insert.assert_awaited_once()
    repository.update_preferences_and_reset_to_pending.assert_not_awaited()
    service.email_sender.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_resets_existing_row_to_pending_regardless_of_status():
    existing = make_subscription(status="active")
    repository = make_repository(
        get_by_email=existing, update_preferences_and_reset_to_pending=make_subscription()
    )
    service = make_service(repository)

    result = await service.subscribe(PREFS)

    assert result.status == "confirmation_sent"
    repository.update_preferences_and_reset_to_pending.assert_awaited_once()
    repository.insert.assert_not_awaited()
    service.email_sender.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_activates_pending_subscription():
    subscription = make_subscription(status="pending_confirmation")
    repository = make_repository(get_by_id=subscription, confirm=make_subscription(status="active"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)

    result = await service.confirm(token)

    assert result.status == "confirmed"
    repository.confirm.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_confirm_is_idempotent_when_already_active():
    repository = make_repository(get_by_id=make_subscription(status="active"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)

    result = await service.confirm(token)

    assert result.status == "already_confirmed"
    repository.confirm.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirm_rejects_unsubscribed_subscription():
    repository = make_repository(get_by_id=make_subscription(status="unsubscribed"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.confirm(token)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_handles_concurrent_confirm_race():
    repository = make_repository(
        get_by_id=make_subscription(status="pending_confirmation"), confirm=None
    )
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)

    result = await service.confirm(token)

    assert result.status == "already_confirmed"


@pytest.mark.asyncio
async def test_confirm_rejects_stale_token_version():
    repository = make_repository(get_by_id=make_subscription(token_version=2))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="confirm", token_version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.confirm(token)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_rejects_unknown_subscription():
    repository = make_repository(get_by_id=None)
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=999, purpose="confirm", token_version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.confirm(token)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_confirm_rejects_malformed_token():
    service = make_service(make_repository())

    with pytest.raises(HTTPException) as exc_info:
        await service.confirm("not-a-real-token")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_rejects_wrong_purpose_token():
    repository = make_repository(get_by_id=make_subscription())
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.confirm(token)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_preferences_returns_current_fields():
    repository = make_repository(get_by_id=make_subscription(status="active"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="preferences", token_version=1)

    result = await service.get_preferences(token)

    assert result.email == "user@example.com"
    assert result.timezone == "America/Los_Angeles"


@pytest.mark.asyncio
async def test_update_preferences_without_email_change_updates_in_place():
    repository = make_repository(get_by_id=make_subscription(status="active"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="preferences", token_version=1)

    result = await service.update_preferences(token, PREFS)

    assert result.status == "updated"
    repository.update_preferences.assert_awaited_once()
    repository.update_email_and_preferences.assert_not_awaited()
    service.email_sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_preferences_with_email_change_requires_reconfirmation():
    repository = make_repository(
        get_by_id=make_subscription(status="active", email="old@example.com"),
        update_email_and_preferences=make_subscription(email="new@example.com"),
    )
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="preferences", token_version=1)
    new_prefs = PREFS.model_copy(update={"email": "new@example.com"})

    result = await service.update_preferences(token, new_prefs)

    assert result.status == "confirmation_sent"
    repository.update_email_and_preferences.assert_awaited_once()
    repository.update_preferences.assert_not_awaited()
    service.email_sender.send.assert_awaited_once()
    assert service.email_sender.send.await_args.kwargs["to"] == "new@example.com"


@pytest.mark.asyncio
async def test_update_preferences_email_collision_returns_409():
    repository = make_repository(get_by_id=make_subscription(status="active"))
    repository.update_email_and_preferences.side_effect = asyncpg.UniqueViolationError(
        "duplicate key"
    )
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="preferences", token_version=1)
    new_prefs = PREFS.model_copy(update={"email": "taken@example.com"})

    with pytest.raises(HTTPException) as exc_info:
        await service.update_preferences(token, new_prefs)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_unsubscribe_transitions_active_subscription():
    repository = make_repository(
        get_by_id=make_subscription(status="active"),
        unsubscribe=make_subscription(status="unsubscribed"),
    )
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=1)

    result = await service.unsubscribe(token)

    assert result.status == "unsubscribed"
    repository.unsubscribe.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_unsubscribe_is_idempotent_when_already_unsubscribed():
    repository = make_repository(get_by_id=make_subscription(status="unsubscribed"))
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=1)

    result = await service.unsubscribe(token)

    assert result.status == "already_unsubscribed"
    repository.unsubscribe.assert_not_awaited()


@pytest.mark.asyncio
async def test_unsubscribe_handles_concurrent_unsubscribe_race():
    repository = make_repository(get_by_id=make_subscription(status="active"), unsubscribe=None)
    service = make_service(repository)
    token = tokens.sign_token(subscription_id=1, purpose="unsubscribe", token_version=1)

    result = await service.unsubscribe(token)

    assert result.status == "already_unsubscribed"


@pytest.mark.asyncio
async def test_confirmation_idempotency_key_anchored_to_updated_at():
    subscription = make_subscription()
    repository = make_repository(insert=subscription)
    service = make_service(repository)

    await service.subscribe(PREFS)

    key = service.email_sender.send.await_args.kwargs["idempotency_key"]
    assert key == f"confirm:1:{subscription['updated_at'].timestamp()}"


@pytest.mark.asyncio
async def test_close_closes_email_sender():
    service = make_service(make_repository())

    await service.close()

    service.email_sender.close.assert_awaited_once()
