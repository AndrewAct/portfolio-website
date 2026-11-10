from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from apps.services.horoscope import ai_provider


class ResponseSchema(BaseModel):
    value: str


def test_gemini_provider_reports_configuration_without_creating_a_client():
    provider = ai_provider.GeminiProvider(api_key="", model_name="gemini-test", timeout_seconds=5)

    assert provider.provider_name == "google"
    assert provider.model_name == "gemini-test"
    assert provider.is_configured is False


@pytest.mark.asyncio
async def test_gemini_provider_owns_sdk_request_shape_and_client_lifecycle(monkeypatch):
    models = SimpleNamespace(generate_content=AsyncMock(return_value={"value": "ok"}))
    client = SimpleNamespace(aio=SimpleNamespace(models=models, aclose=AsyncMock()), close=Mock())
    client_factory = Mock(return_value=client)
    monkeypatch.setattr(ai_provider.genai, "Client", client_factory)
    provider = ai_provider.GeminiProvider(
        api_key="test-key", model_name="gemini-test", timeout_seconds=5
    )

    result = await provider.generate_structured(
        prompt="Generate a horoscope", response_schema=ResponseSchema
    )
    await provider.close()

    assert result == {"value": "ok"}
    assert provider.is_configured is True
    request = models.generate_content.call_args.kwargs
    assert request["model"] == "gemini-test"
    assert request["contents"] == "Generate a horoscope"
    assert request["config"].response_schema is ResponseSchema
    client.aio.aclose.assert_awaited_once()
    client.close.assert_called_once()


@pytest.mark.asyncio
async def test_unconfigured_gemini_provider_refuses_generation():
    provider = ai_provider.GeminiProvider(api_key="", model_name="gemini-test", timeout_seconds=5)

    with pytest.raises(RuntimeError, match="not configured"):
        await provider.generate_structured(prompt="ignored", response_schema=ResponseSchema)
