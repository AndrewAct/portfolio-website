import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.services.horoscope.router import get_horoscope_service, router
from apps.services.horoscope.service import GeneratedHoroscope, HoroscopeService


class FakeModels:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response

    def list(self):
        if self.error:
            raise self.error
        return [SimpleNamespace(name="models/flash")]


def service_with_response(text: str | None = None, parsed=None) -> HoroscopeService:
    service = HoroscopeService()
    service.api_key = "test-key"
    models = FakeModels(SimpleNamespace(text=text, parsed=parsed))
    service.client = SimpleNamespace(models=models, aio=SimpleNamespace(models=models))
    return service


@pytest.mark.parametrize(
    ("birthdate", "expected"),
    [
        (date(2000, 3, 21), "Aries"),
        (date(2000, 4, 20), "Taurus"),
        (date(2000, 5, 21), "Gemini"),
        (date(2000, 6, 21), "Cancer"),
        (date(2000, 7, 23), "Leo"),
        (date(2000, 8, 23), "Virgo"),
        (date(2000, 9, 23), "Libra"),
        (date(2000, 10, 23), "Scorpio"),
        (date(2000, 11, 22), "Sagittarius"),
        (date(2000, 12, 22), "Capricorn"),
        (date(2000, 1, 20), "Aquarius"),
        (date(2000, 2, 19), "Pisces"),
    ],
)
def test_zodiac_boundaries(birthdate, expected):
    english, localized = HoroscopeService().get_zodiac_sign(birthdate)

    assert english == expected
    assert localized == expected


def test_zodiac_localization_and_unknown_language():
    service = HoroscopeService()

    assert service.get_zodiac_sign(date(2000, 4, 7), "zh") == ("Aries", "白羊座")
    assert service.get_zodiac_sign(date(2000, 4, 7), "fr") == ("Aries", "Aries")


def test_prompts_and_templates_are_localized():
    assert "Aries" in HoroscopeService._prompt_generator("en", "Aries", "female")
    assert "白羊座" in HoroscopeService._prompt_generator("zh", "白羊座", "女性")
    assert "Aries" in HoroscopeService._get_horoscope_templates("en")
    assert "白羊座" in HoroscopeService._get_horoscope_templates("zh")


@pytest.mark.asyncio
async def test_close_releases_sync_and_async_clients():
    service = HoroscopeService()
    service.client = None
    await service.close()

    async_client = SimpleNamespace(aclose=AsyncMock())
    service.client = SimpleNamespace(aio=async_client, close=Mock())
    await service.close()

    async_client.aclose.assert_awaited_once()
    service.client.close.assert_called_once()


@pytest.mark.asyncio
async def test_daily_horoscope_falls_back_without_api_key(monkeypatch):
    service = HoroscopeService()
    fallback = {"source": "fallback"}
    monkeypatch.setattr(service, "_generate_fallback_horoscope", Mock(return_value=fallback))

    assert await service.get_daily_horoscope("Aries", "neutral") == fallback


@pytest.mark.asyncio
async def test_daily_horoscope_uses_fast_lite_structured_output():
    response = json.dumps(
        {
            "daily_horoscope": "A focused day.",
            "lucky_number": 17,
            "compatibility": "Taurus",
            "mood": "Calm",
        }
    )
    service = service_with_response(response)

    result = await service.get_daily_horoscope("Aries", "neutral")

    assert result == {
        "daily_horoscope": "A focused day.",
        "zodiac_sign": "Aries",
        "zodiac_sign_chinese": "白羊座",
        "lucky_number": 17,
        "compatibility": "Taurus",
        "mood": "Calm",
    }
    call = service.client.aio.models.calls[0]
    assert call["model"] == "gemini-3.1-flash-lite"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is GeneratedHoroscope
    assert call["config"].thinking_config.thinking_level.value == "MINIMAL"


@pytest.mark.asyncio
async def test_daily_horoscope_accepts_sdk_parsed_model():
    parsed = GeneratedHoroscope(
        daily_horoscope="Keep the important conversation simple.",
        lucky_number=8,
        compatibility="Leo",
        mood="Grounded",
    )
    service = service_with_response(parsed=parsed)

    result = await service.get_daily_horoscope("Gemini", "female")

    assert result["daily_horoscope"] == parsed.daily_horoscope
    assert result["zodiac_sign_chinese"] == "双子座"


@pytest.mark.asyncio
async def test_daily_horoscope_maps_chinese_sign_to_english():
    payload = {
        "daily_horoscope": "稳步前进。",
        "lucky_number": 8,
        "compatibility": "金牛座",
        "mood": "平静",
    }
    service = service_with_response(json.dumps(payload))

    result = await service.get_daily_horoscope("白羊座", "女性", "zh")

    assert result["zodiac_sign"] == "Aries"
    assert result["zodiac_sign_chinese"] == "白羊座"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["invalid-json", None])
async def test_daily_horoscope_falls_back_for_invalid_response(failure, monkeypatch):
    service = service_with_response(failure)
    fallback = {"source": "fallback"}
    monkeypatch.setattr(service, "_generate_fallback_horoscope", Mock(return_value=fallback))

    assert await service.get_daily_horoscope("Aries", "neutral") == fallback


@pytest.mark.asyncio
async def test_daily_horoscope_falls_back_when_api_raises(monkeypatch):
    service = HoroscopeService()
    service.api_key = "key"
    models = FakeModels(error=RuntimeError("offline"))
    service.client = SimpleNamespace(models=models, aio=SimpleNamespace(models=models))
    fallback = {"source": "fallback"}
    monkeypatch.setattr(service, "_generate_fallback_horoscope", Mock(return_value=fallback))

    assert await service.get_daily_horoscope("Aries", "neutral") == fallback


@pytest.mark.asyncio
async def test_daily_horoscope_falls_back_when_prompt_generation_raises(monkeypatch):
    service = HoroscopeService()
    fallback = {"source": "fallback"}
    monkeypatch.setattr(service, "_prompt_generator", Mock(side_effect=ValueError("bad prompt")))
    monkeypatch.setattr(service, "_generate_fallback_horoscope", Mock(return_value=fallback))

    assert await service.get_daily_horoscope("Aries", "neutral") == fallback


@pytest.mark.parametrize(
    ("sign", "language", "english", "localized"),
    [
        ("Aries", "en", "Aries", "Aries"),
        ("白羊座", "zh", "Aries", "白羊座"),
        ("unknown", "en", "Aries", "Aries"),
        ("unknown", "zh", "Aries", "白羊座"),
    ],
)
def test_fallback_horoscope_normalizes_signs(sign, language, english, localized, monkeypatch):
    service = HoroscopeService()
    monkeypatch.setattr("apps.services.horoscope.service.random.randint", lambda *_args: 7)
    monkeypatch.setattr("apps.services.horoscope.service.random.choice", lambda values: values[0])

    result = service._generate_fallback_horoscope(sign, language)

    assert result["zodiac_sign"] == english
    assert result["zodiac_sign_chinese"] == localized
    assert result["lucky_number"] == 7
    assert result["compatibility"] != english
    assert result["daily_horoscope"]


@pytest.mark.asyncio
async def test_horoscope_http_contract_for_sign_and_birthdate():
    class FakeService:
        def get_zodiac_sign(self, _birthdate, language):
            return "Aries", "白羊座" if language == "zh" else "Aries"

        async def get_daily_horoscope(self, zodiac_sign, _gender, _language="en"):
            return {
                "zodiac_sign": "Aries",
                "zodiac_sign_chinese": "白羊座",
                "daily_horoscope": f"Forecast for {zodiac_sign}",
                "lucky_number": 3,
                "compatibility": "Leo",
                "mood": "Calm",
            }

    app = FastAPI()
    app.include_router(router, prefix="/horoscope")
    app.dependency_overrides[get_horoscope_service] = FakeService
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        by_sign = await client.get("/horoscope/Aries", params={"gender": "neutral"})
        by_date = await client.post(
            "/horoscope",
            json={"birthdate": "2000-04-07", "gender": "neutral", "language": "zh"},
        )
        by_date_with_slash = await client.post(
            "/horoscope/",
            json={"birthdate": "2000-04-07", "gender": "neutral", "language": "en"},
        )

    assert by_sign.status_code == 200
    assert by_date.json()["daily_horoscope"] == "Forecast for 白羊座"
    assert by_date_with_slash.status_code == 200
