from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from apps.config import get_settings
from apps.services.horoscope import ai_provider


class ResponseSchema(BaseModel):
    value: str


def _settings(**overrides):
    return get_settings().model_copy(update=overrides)


def test_build_providers_follows_configured_order():
    providers = ai_provider.build_providers(
        _settings(ai_provider_order=" deepseek, google ,openai", deepseek_api_key="k")
    )

    assert [p.provider_name for p in providers] == ["deepseek", "google", "openai"]
    assert providers[0].is_configured is True


@pytest.mark.parametrize("order", ["", " , "])
def test_build_providers_rejects_empty_order(order):
    with pytest.raises(ValueError, match="at least one"):
        ai_provider.build_providers(_settings(ai_provider_order=order))


def test_build_providers_rejects_unknown_provider():
    with pytest.raises(ValueError, match="mistral"):
        ai_provider.build_providers(_settings(ai_provider_order="google,mistral"))


def _fake_openai_client(monkeypatch, *, content, parsed=None):
    message = SimpleNamespace(content=content, parsed=parsed)
    completion = SimpleNamespace(choices=[SimpleNamespace(message=message)])
    completions = SimpleNamespace(
        parse=AsyncMock(return_value=completion), create=AsyncMock(return_value=completion)
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions), close=AsyncMock())
    factory = Mock(return_value=client)
    monkeypatch.setattr(ai_provider, "AsyncOpenAI", factory)
    return factory, client


@pytest.mark.asyncio
async def test_openai_provider_uses_strict_structured_outputs(monkeypatch):
    parsed = ResponseSchema(value="ok")
    factory, client = _fake_openai_client(monkeypatch, content='{"value":"ok"}', parsed=parsed)
    provider = ai_provider.OpenAICompatibleProvider(
        provider_name="openai",
        api_key="k",
        model_name="gpt-test",
        timeout_seconds=7,
        reasoning_effort="low",
    )

    result = await provider.generate_structured(prompt="hi", response_schema=ResponseSchema)
    await provider.close()

    assert result == ai_provider.StructuredResponse(text='{"value":"ok"}', parsed=parsed)
    request = client.chat.completions.parse.call_args.kwargs
    assert request["model"] == "gpt-test"
    assert request["response_format"] is ResponseSchema
    assert request["reasoning_effort"] == "low"
    assert factory.call_args.kwargs["timeout"] == 7
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_json_mode_provider_appends_schema_and_omits_blank_effort(monkeypatch):
    factory, client = _fake_openai_client(monkeypatch, content='{"value":"ok"}')
    provider = ai_provider.OpenAICompatibleProvider(
        provider_name="deepseek",
        api_key="k",
        model_name="deepseek-test",
        timeout_seconds=7,
        base_url="https://example.invalid",
        strict_schema=False,
    )

    result = await provider.generate_structured(prompt="hi", response_schema=ResponseSchema)

    assert result == ai_provider.StructuredResponse(text='{"value": "ok"}')
    request = client.chat.completions.create.call_args.kwargs
    assert request["response_format"] == {"type": "json_object"}
    assert '"value"' in request["messages"][0]["content"]
    assert "reasoning_effort" not in request
    assert factory.call_args.kwargs["base_url"] == "https://example.invalid"


@pytest.mark.asyncio
async def test_unconfigured_openai_provider_refuses_and_closes_quietly():
    provider = ai_provider.OpenAICompatibleProvider(
        provider_name="openai", api_key="", model_name="m", timeout_seconds=1
    )

    assert provider.is_configured is False
    with pytest.raises(RuntimeError, match="openai provider is not configured"):
        await provider.generate_structured(prompt="x", response_schema=ResponseSchema)
    await provider.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(("level", "expected"), [("", None), ("high", "HIGH")])
async def test_gemini_thinking_level_is_optional_and_sampling_params_are_unset(
    monkeypatch, level, expected
):
    models = SimpleNamespace(generate_content=AsyncMock(return_value=None))
    client = SimpleNamespace(aio=SimpleNamespace(models=models, aclose=AsyncMock()), close=Mock())
    monkeypatch.setattr(ai_provider.genai, "Client", Mock(return_value=client))
    provider = ai_provider.GeminiProvider(
        api_key="k", model_name="gemini-test", timeout_seconds=5, thinking_level=level
    )

    await provider.generate_structured(prompt="x", response_schema=ResponseSchema)

    config = models.generate_content.call_args.kwargs["config"]
    assert config.temperature is None and config.top_p is None
    thinking = config.thinking_config
    assert (thinking.thinking_level.name if thinking else None) == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('{"value": "ok"}\n{"value": "dup"}', '{"value": "ok"}'),
        ('```json\n{"value": "ok"}\n```', '{"value": "ok"}'),
        ("no json here", "no json here"),
        ('{"value": ', '{"value": '),
        (None, None),
    ],
)
def test_json_mode_keeps_first_object_and_passes_garbage_through(content, expected):
    assert ai_provider._first_json_object(content) == expected
