"""Compatibility bridge from the former Grafana-specific settings to OTEL_* env vars."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def configure_otel_environment() -> None:
    """Prefer standard OTEL_* configuration, with a safe one-release legacy bridge.

    Docker Compose injects ``.env`` into the container, but local ``uv run``
    does not. Loading this project's file keeps both execution modes identical
    without overriding explicitly exported shell variables.
    """
    load_dotenv(_ENV_FILE, override=False)
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return

    endpoint = os.getenv("GRAFANA_OTLP_ENDPOINT")
    instance_id = os.getenv("GRAFANA_INSTANCE_ID")
    api_key = os.getenv("GRAFANA_API_KEY")
    if not endpoint or not instance_id or not api_key:
        return

    token = base64.b64encode(f"{instance_id}:{api_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    # OTEL_EXPORTER_OTLP_HEADERS is a comma-delimited environment format, not
    # a raw HTTP header. Encode the Basic-auth value so its required space (and
    # any base64 punctuation) survives the OpenTelemetry environment parser.
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization={quote(f'Basic {token}', safe='')}"
    os.environ.setdefault("OTEL_SERVICE_NAME", "portfolio-api")
    os.environ.setdefault(
        "OTEL_RESOURCE_ATTRIBUTES",
        f"deployment.environment={os.getenv('ENVIRONMENT', 'development')}",
    )
