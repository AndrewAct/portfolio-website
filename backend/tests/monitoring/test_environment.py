import base64
import os

from apps.monitoring.environment import configure_otel_environment


def test_existing_otel_configuration_takes_precedence(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://configured.example/otlp")
    monkeypatch.setenv("GRAFANA_OTLP_ENDPOINT", "https://legacy.example/otlp")

    configure_otel_environment()

    assert os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://configured.example/otlp"


def test_legacy_grafana_configuration_maps_to_standard_otel_variables(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_HEADERS", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    monkeypatch.delenv("OTEL_RESOURCE_ATTRIBUTES", raising=False)
    monkeypatch.setenv("GRAFANA_OTLP_ENDPOINT", "https://legacy.example/otlp")
    monkeypatch.setenv("GRAFANA_INSTANCE_ID", "12345")
    monkeypatch.setenv("GRAFANA_API_KEY", "secret")
    monkeypatch.setenv("ENVIRONMENT", "production")

    configure_otel_environment()

    expected = base64.b64encode(b"12345:secret").decode()
    environment = os.environ
    assert environment["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://legacy.example/otlp"
    assert environment["OTEL_EXPORTER_OTLP_HEADERS"] == f"Authorization=Basic {expected}"
    assert environment["OTEL_SERVICE_NAME"] == "portfolio-api"
    assert environment["OTEL_RESOURCE_ATTRIBUTES"] == "deployment.environment=production"
