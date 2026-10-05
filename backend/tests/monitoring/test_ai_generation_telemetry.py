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

    attributes = request.attributes(outcome="error")
    telemetry._requests.add.assert_called_once_with(1, attributes)
    telemetry._duration.record.assert_called_once()
    span.record_exception.assert_called_once()
    span.set_status.assert_called_once()
