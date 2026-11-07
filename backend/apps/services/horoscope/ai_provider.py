"""Provider boundary for structured AI horoscope generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from google import genai
from google.genai import types
from openai import AsyncOpenAI
from pydantic import BaseModel

if TYPE_CHECKING:
    from ...config import Settings


class AIProvider(Protocol):
    """The stable boundary every provider adapter implements."""

    provider_name: str
    model_name: str

    @property
    def is_configured(self) -> bool: ...

    async def generate_structured(
        self, *, prompt: str, response_schema: type[BaseModel]
    ) -> Any: ...

    async def close(self) -> None: ...


@dataclass(frozen=True)
class StructuredResponse:
    """Matches the `.parsed` / `.text` shape the service already reads from Gemini."""

    text: str | None
    parsed: Any = None


class GeminiProvider:
    provider_name = "google"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        thinking_level: str = "",
    ) -> None:
        self.model_name = model_name
        self._thinking_level = thinking_level
        self._client = (
            genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
            )
            if api_key
            else None
        )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def generate_structured(self, *, prompt: str, response_schema: type[BaseModel]) -> Any:
        if self._client is None:
            raise RuntimeError("Gemini provider is not configured")
        # No temperature/top_p: Gemini 3.x ignores them and newer generations reject them.
        # thinking_level is per-model ("minimal" is Flash-Lite only), so blank omits it.
        thinking = (
            types.ThinkingConfig(thinking_level=self._thinking_level)
            if self._thinking_level
            else None
        )
        return await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_schema=response_schema,
                thinking_config=thinking,
            ),
        )

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.aio.aclose()
        self._client.close()


class OpenAICompatibleProvider:
    """OpenAI Chat Completions adapter, also used for OpenAI-compatible APIs (DeepSeek).

    `strict_schema=True` uses OpenAI structured outputs; APIs that only offer JSON mode get
    the schema appended to the prompt and are validated by the service like any other reply.
    """

    def __init__(
        self,
        *,
        provider_name: str,
        api_key: str,
        model_name: str,
        timeout_seconds: int,
        base_url: str | None = None,
        strict_schema: bool = True,
        reasoning_effort: str = "",
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self._strict_schema = strict_schema
        self._reasoning_effort = reasoning_effort
        # No SDK retries: a retried timeout doubles the wait; the provider chain is the failover.
        self._client = (
            AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds, max_retries=0)
            if api_key
            else None
        )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def generate_structured(
        self, *, prompt: str, response_schema: type[BaseModel]
    ) -> StructuredResponse:
        if self._client is None:
            raise RuntimeError(f"{self.provider_name} provider is not configured")
        extra: dict[str, Any] = (
            {"reasoning_effort": self._reasoning_effort} if self._reasoning_effort else {}
        )
        if self._strict_schema:
            completion = await self._client.chat.completions.parse(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format=response_schema,
                **extra,
            )
            message = completion.choices[0].message
            return StructuredResponse(text=message.content, parsed=message.parsed)

        schema = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        completion = await self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nReturn only a JSON object matching this JSON "
                    f"Schema:\n{schema}",
                }
            ],
            response_format={"type": "json_object"},
            **extra,
        )
        return StructuredResponse(text=_first_json_object(completion.choices[0].message.content))

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()


def _first_json_object(content: str | None) -> str | None:
    """JSON mode guarantees valid JSON, not *only* JSON: DeepSeek occasionally appends a
    trailing fragment after the object. Keep the first object; anything unparseable is
    returned as-is so the service's validation still rejects it and fails over."""
    if not content:
        return content
    start = content.find("{")
    if start == -1:
        return content
    try:
        obj, _ = json.JSONDecoder().raw_decode(content, start)
    except json.JSONDecodeError:
        return content
    return json.dumps(obj, ensure_ascii=False)


def build_provider(name: str, settings: Settings) -> AIProvider:
    if name == "google":
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=settings.gemini_timeout_seconds,
            thinking_level=settings.gemini_thinking_level,
        )
    if name == "openai":
        return OpenAICompatibleProvider(
            provider_name="openai",
            api_key=settings.openai_api_key,
            model_name=settings.openai_model,
            timeout_seconds=settings.ai_timeout_seconds,
            reasoning_effort=settings.openai_reasoning_effort,
        )
    if name == "deepseek":
        return OpenAICompatibleProvider(
            provider_name="deepseek",
            api_key=settings.deepseek_api_key,
            model_name=settings.deepseek_model,
            timeout_seconds=settings.ai_timeout_seconds,
            base_url=settings.deepseek_base_url,
            strict_schema=False,
            reasoning_effort=settings.deepseek_reasoning_effort,
        )
    raise ValueError(f"Unknown AI provider {name!r} in AI_PROVIDER_ORDER")


def build_providers(settings: Settings) -> list[AIProvider]:
    """Ordered failover chain; an unknown name fails at startup, a missing key is skipped
    at request time (so a chain can be configured before every key exists)."""
    names = [name.strip() for name in settings.ai_provider_order.split(",") if name.strip()]
    if not names:
        raise ValueError("AI_PROVIDER_ORDER must name at least one provider")
    return [build_provider(name, settings) for name in names]
