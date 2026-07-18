import base64
from unittest.mock import Mock

from fastapi import FastAPI

from apps.monitoring import telemetry


def test_setup_telemetry_wires_exporter_processor_and_instrumentation(monkeypatch):
    resource = object()
    provider = Mock()
    exporter = object()
    processor = object()
    requests_instrumentor = Mock()

    resource_create = Mock(return_value=resource)
    provider_factory = Mock(return_value=provider)
    exporter_factory = Mock(return_value=exporter)
    processor_factory = Mock(return_value=processor)
    set_provider = Mock()
    instrument_app = Mock()
    requests_factory = Mock(return_value=requests_instrumentor)

    monkeypatch.setattr(telemetry.Resource, "create", resource_create)
    monkeypatch.setattr(telemetry, "TracerProvider", provider_factory)
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", exporter_factory)
    monkeypatch.setattr(telemetry, "BatchSpanProcessor", processor_factory)
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", set_provider)
    monkeypatch.setattr(telemetry.FastAPIInstrumentor, "instrument_app", instrument_app)
    monkeypatch.setattr(telemetry, "RequestsInstrumentor", requests_factory)

    app = FastAPI()
    result = telemetry.setup_telemetry(app)

    assert result is provider
    provider_factory.assert_called_once_with(resource=resource)
    set_provider.assert_called_once_with(provider)
    provider.add_span_processor.assert_called_once_with(processor)
    requests_instrumentor.instrument.assert_called_once_with(tracer_provider=provider)

    exporter_kwargs = exporter_factory.call_args.kwargs
    expected_token = base64.b64encode(b"test-instance:test-key").decode()
    assert exporter_kwargs["endpoint"] == "https://example.invalid/v1/traces"
    assert exporter_kwargs["headers"]["Authorization"] == f"Basic {expected_token}"

    hook = instrument_app.call_args.kwargs["server_request_hook"]
    span = Mock()
    hook(span, {})
    span.set_attribute.assert_called_once_with("service.name", "fastapi-monitor")
