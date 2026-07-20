from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from apps.services.horoscope_subscriptions.router import get_subscription_service
from apps.services.horoscope_subscriptions.router import router as subscriptions_router
from apps.services.horoscope_subscriptions.schemas import (
    ConfirmResponse,
    PreferencesResponse,
    SubscribeResponse,
    UnsubscribeResponse,
    UpdatePreferencesResponse,
)

VALID_BODY = {
    "email": "user@example.com",
    "birthdate": "1990-04-07",
    "gender": "female",
    "language": "en",
    "timezone": "America/Los_Angeles",
    "send_time_local": "08:00:00",
}


def build_app(fake_service) -> FastAPI:
    app = FastAPI()
    app.include_router(subscriptions_router, prefix="/subscriptions")
    app.dependency_overrides[get_subscription_service] = lambda: fake_service
    return app


@pytest.mark.asyncio
async def test_subscribe_without_and_with_trailing_slash():
    fake_service = SimpleNamespace(
        subscribe=AsyncMock(return_value=SubscribeResponse(status="confirmation_sent"))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        no_slash = await client.post("/subscriptions", json=VALID_BODY)
        with_slash = await client.post("/subscriptions/", json=VALID_BODY)

    assert no_slash.status_code == 200
    assert no_slash.json() == {"status": "confirmation_sent"}
    assert with_slash.status_code == 200
    assert fake_service.subscribe.await_count == 2


@pytest.mark.asyncio
async def test_subscribe_rejects_invalid_timezone():
    fake_service = SimpleNamespace(subscribe=AsyncMock())
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/subscriptions", json={**VALID_BODY, "timezone": "Not/AZone"})

    assert response.status_code == 422
    fake_service.subscribe.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirm_passes_token_through():
    fake_service = SimpleNamespace(
        confirm=AsyncMock(return_value=ConfirmResponse(status="confirmed"))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/subscriptions/confirm", params={"token": "abc.def"})

    assert response.status_code == 200
    assert response.json() == {"status": "confirmed"}
    fake_service.confirm.assert_awaited_once_with("abc.def")


@pytest.mark.asyncio
async def test_confirm_surfaces_service_http_exception():
    fake_service = SimpleNamespace(
        confirm=AsyncMock(side_effect=HTTPException(status_code=400, detail="bad token"))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/subscriptions/confirm", params={"token": "bad"})

    assert response.status_code == 400
    assert response.json()["detail"] == "bad token"


@pytest.mark.asyncio
async def test_get_preferences_returns_current_values():
    fake_service = SimpleNamespace(
        get_preferences=AsyncMock(return_value=PreferencesResponse(**VALID_BODY))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/subscriptions/preferences", params={"token": "tok"})

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_update_preferences_posts_body_and_token():
    fake_service = SimpleNamespace(
        update_preferences=AsyncMock(return_value=UpdatePreferencesResponse(status="updated"))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/subscriptions/preferences", params={"token": "tok"}, json=VALID_BODY
        )

    assert response.status_code == 200
    assert response.json() == {"status": "updated"}
    token, request = fake_service.update_preferences.await_args.args
    assert token == "tok"
    assert request.email == "user@example.com"


@pytest.mark.asyncio
async def test_unsubscribe_passes_token_through():
    fake_service = SimpleNamespace(
        unsubscribe=AsyncMock(return_value=UnsubscribeResponse(status="unsubscribed"))
    )
    app = build_app(fake_service)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/subscriptions/unsubscribe", params={"token": "tok"})

    assert response.status_code == 200
    fake_service.unsubscribe.assert_awaited_once_with("tok")
