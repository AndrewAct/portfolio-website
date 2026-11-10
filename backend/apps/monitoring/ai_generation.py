"""Provider-agnostic telemetry for AI-backed business operations."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter

from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind, Status, StatusCode

# Seconds, sized to real provider latency (2-8s typical, AI_TIMEOUT_SECONDS=20). The SDK
# default (0, 5, 10, 25, ... 10000) assumes milliseconds, so every request landed in (0, 5]
# and histogram_quantile always reported p50=2.5s / p95=4.75s.
REQUEST_DURATION_BUCKETS_SECONDS = (0.5, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30)


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
            explicit_bucket_boundaries_advisory=REQUEST_DURATION_BUCKETS_SECONDS,
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
                error_type = _error_type(exc)
                span.set_status(Status(StatusCode.ERROR, error_type))
                attributes = request.attributes(outcome="error", **{"error.type": error_type})
                self._requests.add(1, attributes)
                self._duration.record(perf_counter() - started, attributes)
                raise
            else:
                attributes = request.attributes(outcome="success")
                self._requests.add(1, attributes)
                self._duration.record(perf_counter() - started, attributes)


def _error_type(exc: Exception) -> str:
    """Bounded label: the HTTP status when the SDK exposes one (402 billing vs 429 rate
    limit), else the exception class name (timeouts, connection errors)."""
    for attribute in ("status_code", "code"):
        value = getattr(exc, attribute, None)
        if isinstance(value, int):
            return str(value)
    return type(exc).__name__


ai_generation_telemetry = AIGenerationTelemetry()
