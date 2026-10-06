"""Provider-agnostic telemetry for AI-backed business operations."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind, Status, StatusCode


@dataclass(frozen=True)
class AIGenerationRequest:
    """A bounded description of a configured AI provider and business operation."""

    provider: str
    model: str
    operation: str

    def attributes(self, **additional: str) -> dict[str, str]:
        return {
            "ai.provider": self.provider,
            "ai.model": self.model,
            "ai.operation": self.operation,
            **additional,
        }


class AIGenerationTelemetry:
    """Records consistent AI request metrics and spans across provider adapters."""

    def __init__(self) -> None:
        meter = metrics.get_meter("portfolio.ai_generation")
        self._tracer = trace.get_tracer("portfolio.ai_generation")
        self._generations = meter.create_counter(
            "portfolio.ai.generation.total",
            unit="{generation}",
            description="Completed AI-backed business operations by outcome.",
        )
        self._requests = meter.create_counter(
            "portfolio.ai.generation.request.total",
            unit="{request}",
            description="AI provider requests by outcome.",
        )
        self._duration = meter.create_histogram(
            "portfolio.ai.generation.request.duration",
            unit="s",
            description="AI provider request duration.",
        )

    def record_generation(self, request: AIGenerationRequest, outcome: str) -> None:
        self._generations.add(1, request.attributes(outcome=outcome))

    @contextmanager
    def observe_request(self, request: AIGenerationRequest) -> Iterator[None]:
        """Trace and measure a provider request without customer-data attributes."""
        started = perf_counter()
        with self._tracer.start_as_current_span(
            "ai.generate",
            kind=SpanKind.CLIENT,
            attributes={
                "gen_ai.operation.name": "generate_content",
                "gen_ai.provider.name": request.provider,
                "gen_ai.request.model": request.model,
                "portfolio.ai.operation": request.operation,
            },
        ) as span:
            try:
                yield
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                attributes = request.attributes(outcome="error")
                self._requests.add(1, attributes)
                self._duration.record(perf_counter() - started, attributes)
                raise
            else:
                attributes = request.attributes(outcome="success")
                self._requests.add(1, attributes)
                self._duration.record(perf_counter() - started, attributes)


ai_generation_telemetry = AIGenerationTelemetry()
