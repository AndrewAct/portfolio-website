from unittest.mock import MagicMock, Mock

import pytest

from apps.monitoring.ai_generation import AIGenerationRequest, AIGenerationTelemetry, SpanKind


def test_generation_request_uses_bounded_provider_model_operation_attributes():
    request = AIGenerationRequest("openai", "gpt-example", "horoscope_generation")

    assert request.attributes(outcome="success") == {
        "ai.provider": "openai",
        "ai.model": "gpt-example",
        "ai.operation": "horoscope_generation",
        "outcome": "success",
    }


def test_telemetry_records_success_for_any_provider():
    tracer = MagicMock()
    telemetry = AIGenerationTelemetry()
    telemetry._generations = Mock()
    telemetry._requests = Mock()
    telemetry._duration = Mock()
    telemetry._tracer = tracer
    request = AIGenerationRequest("anthropic", "claude-example", "horoscope_generation")
    tracer.start_as_current_span.return_value.__enter__.return_value = Mock()

    with telemetry.observe_request(request):
        pass
    telemetry.record_generation(request, "success")

    attributes = request.attributes(outcome="success")
    telemetry._requests.add.assert_called_once_with(1, attributes)
    telemetry._duration.record.assert_called_once()
    telemetry._generations.add.assert_called_once_with(1, attributes)
    tracer.start_as_current_span.assert_called_once_with(
        "ai.generate",
        kind=SpanKind.CLIENT,
        attributes={
            "gen_ai.operation.name": "generate_content",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": "claude-example",
            "portfolio.ai.operation": "horoscope_generation",
        },
    )


def test_telemetry_marks_provider_errors_before_reraising():
    telemetry = AIGenerationTelemetry()
    telemetry._requests = Mock()
    telemetry._duration = Mock()
    telemetry._tracer = MagicMock()
    span = Mock()
    telemetry._tracer.start_as_current_span.return_value.__enter__.return_value = span
    request = AIGenerationRequest("google", "gemini-example", "horoscope_generation")

    with pytest.raises(RuntimeError, match="provider unavailable"):
        with telemetry.observe_request(request):
            raise RuntimeError("provider unavailable")

    attributes = request.attributes(outcome="error", **{"error.type": "RuntimeError"})
    telemetry._requests.add.assert_called_once_with(1, attributes)
    telemetry._duration.record.assert_called_once()
    span.record_exception.assert_called_once()
    span.set_status.assert_called_once()


class _StatusError(Exception):
    status_code = 402


class _CodeError(Exception):
    code = 429


@pytest.mark.parametrize(
    ("error", "expected"),
    [(_StatusError(), "402"), (_CodeError(), "429"), (TimeoutError(), "TimeoutError")],
)
def test_error_type_prefers_http_status_over_class_name(error, expected):
    from apps.monitoring.ai_generation import _error_type

    assert _error_type(error) == expected


def test_request_duration_uses_second_scale_buckets(monkeypatch):
    # Regression: SDK default buckets are millisecond-scale, so 3-5s requests all fell
    # into (0, 5] and the dashboard showed a flat p50=2.5s / p95=4.75s.
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    from apps.monitoring import ai_generation

    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    monkeypatch.setattr(ai_generation.metrics, "get_meter", provider.get_meter)
    monkeypatch.setattr(ai_generation, "perf_counter", Mock(side_effect=[0.0, 3.5]))
    telemetry = AIGenerationTelemetry()
    telemetry._tracer = MagicMock()

    with telemetry.observe_request(AIGenerationRequest("openai", "m", "horoscope_generation")):
        pass

    (point,) = [
        point
        for resource_metric in reader.get_metrics_data().resource_metrics
        for scope_metric in resource_metric.scope_metrics
        for metric in scope_metric.metrics
        if metric.name == "portfolio.ai.generation.request.duration"
        for point in metric.data.data_points
    ]
    assert tuple(point.explicit_bounds) == ai_generation.REQUEST_DURATION_BUCKETS_SECONDS
    # 3.5s lands in (3, 4], not a 0-5s catch-all.
    assert point.bucket_counts[point.explicit_bounds.index(4)] == 1
