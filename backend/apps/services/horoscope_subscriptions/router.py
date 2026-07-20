from functools import lru_cache

from fastapi import APIRouter, Depends, Query

from .schemas import (
    ConfirmResponse,
    PreferencesResponse,
    SubscribeResponse,
    SubscriptionPreferences,
    UnsubscribeResponse,
    UpdatePreferencesResponse,
)
from .subscription_service import SubscriptionService

router = APIRouter()


@lru_cache
def get_subscription_service() -> SubscriptionService:
    return SubscriptionService()


@router.post("", response_model=SubscribeResponse)
@router.post("/", response_model=SubscribeResponse, include_in_schema=False)
async def subscribe(
    request: SubscriptionPreferences,
    service: SubscriptionService = Depends(get_subscription_service),  # noqa: B008
):
    """Subscribe or re-subscribe an email. Always (re)sends a confirmation, even for an
    already-active subscriber — this endpoint takes no token, so it never edits a live
    subscription in place (see subscription_service module docstring)."""
    return await service.subscribe(request)


@router.get("/confirm", response_model=ConfirmResponse)
async def confirm(
    token: str = Query(...),
    service: SubscriptionService = Depends(get_subscription_service),  # noqa: B008
):
    return await service.confirm(token)


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    token: str = Query(...),
    service: SubscriptionService = Depends(get_subscription_service),  # noqa: B008
):
    return await service.get_preferences(token)


@router.post("/preferences", response_model=UpdatePreferencesResponse)
async def update_preferences(
    request: SubscriptionPreferences,
    token: str = Query(...),
    service: SubscriptionService = Depends(get_subscription_service),  # noqa: B008
):
    return await service.update_preferences(token, request)


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe(
    token: str = Query(...),
    service: SubscriptionService = Depends(get_subscription_service),  # noqa: B008
):
    return await service.unsubscribe(token)
