"""Compatibility bridge from the former Grafana-specific settings to OTEL_* env vars."""

from __future__ import annotations

import base64
import os


def configure_otel_environment() -> None:
    """Prefer standard OTEL_* configuration, with a safe one-release legacy bridge."""
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return

    endpoint = os.getenv("GRAFANA_OTLP_ENDPOINT")
    instance_id = os.getenv("GRAFANA_INSTANCE_ID")
    api_key = os.getenv("GRAFANA_API_KEY")
    if not endpoint or not instance_id or not api_key:
        return

    token = base64.b64encode(f"{instance_id}:{api_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {token}"
    os.environ.setdefault("OTEL_SERVICE_NAME", "portfolio-api")
    os.environ.setdefault(
        "OTEL_RESOURCE_ATTRIBUTES",
        f"deployment.environment={os.getenv('ENVIRONMENT', 'development')}",
    )
