from datetime import date, time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, field_validator


class SubscriptionPreferences(BaseModel):
    """Shared shape for both `POST /subscriptions` and `POST /subscriptions/preferences`."""

    email: EmailStr
    birthdate: date
    gender: str = "neutral"
    language: str = "en"
    timezone: str
    send_time_local: time

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone: {value}") from exc
        return value


class SubscribeResponse(BaseModel):
    status: Literal["confirmation_sent"]


class ConfirmResponse(BaseModel):
    status: Literal["confirmed", "already_confirmed"]


class PreferencesResponse(SubscriptionPreferences):
    pass


class UpdatePreferencesResponse(BaseModel):
    status: Literal["updated", "confirmation_sent"]


class UnsubscribeResponse(BaseModel):
    status: Literal["unsubscribed", "already_unsubscribed"]
