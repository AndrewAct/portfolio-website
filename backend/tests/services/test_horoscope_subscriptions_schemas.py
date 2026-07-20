from datetime import date, time

import pytest
from pydantic import ValidationError

from apps.services.horoscope_subscriptions.schemas import SubscriptionPreferences

VALID = {
    "email": "user@example.com",
    "birthdate": date(1990, 4, 7),
    "gender": "female",
    "language": "en",
    "timezone": "America/Los_Angeles",
    "send_time_local": time(8, 0),
}


def test_accepts_valid_iana_timezone():
    prefs = SubscriptionPreferences(**VALID)
    assert prefs.timezone == "America/Los_Angeles"


def test_rejects_unknown_timezone():
    with pytest.raises(ValidationError, match="Unknown IANA timezone"):
        SubscriptionPreferences(**{**VALID, "timezone": "Mars/Olympus_Mons"})


def test_gender_and_language_default_when_omitted():
    minimal = {k: v for k, v in VALID.items() if k not in {"gender", "language"}}
    prefs = SubscriptionPreferences(**minimal)
    assert prefs.gender == "neutral"
    assert prefs.language == "en"
