"""Provider boundary for structured AI horoscope generation."""

from __future__ import annotations

from typing import Any, Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel


class AIProvider(Protocol):
    """The stable boundary future OpenAI/Anthropic adapters must implement."""

    provider_name: str
    model_name: str

    @property
    def is_configured(self) -> bool: ...

    async def generate_structured(
        self, *, prompt: str, response_schema: type[BaseModel]
    ) -> Any: ...

    async def close(self) -> None: ...


class GeminiProvider:
    provider_name = "google"

    def __init__(self, *, api_key: str, model_name: str, timeout_seconds: int) -> None:
        self.model_name = model_name
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
        return await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                top_p=0.9,
                max_output_tokens=384,
                response_mime_type="application/json",
                response_schema=response_schema,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        )

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.aio.aclose()
        self._client.close()
