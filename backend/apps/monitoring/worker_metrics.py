"""OTLP metric setup for non-ASGI worker processes."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from .environment import configure_otel_environment

logger = logging.getLogger(__name__)


def configure_worker_metrics() -> MeterProvider | None:
    """Install the metrics exporter required by a standalone worker.

    FastAPI creates the API process's provider during its lifespan. A worker does
    not enter that lifecycle, so it must install its own provider before code
    records custom metrics. Telemetry remains optional: a bad or absent endpoint
    must not prevent scheduled email delivery.
    """
    configure_otel_environment()
    endpoint = _metrics_endpoint()
    if endpoint is None:
        logger.warning("Worker metrics disabled: no valid OTLP metrics endpoint configured")
        return None

    try:
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))
        provider = MeterProvider(metric_readers=[reader], shutdown_on_exit=False)
        metrics.set_meter_provider(provider)
    except Exception:
        logger.exception("Worker metrics setup failed; continuing without telemetry")
        return None

    if metrics.get_meter_provider() is not provider:
        # The OpenTelemetry API permits setting the global provider only once.
        # This should not happen in a fresh worker process, but do not leak an
        # unused exporter if an embedding environment configured one first.
        provider.shutdown()
        logger.warning(
            "Worker metrics provider was already configured; using the existing provider"
        )
        return None
    return provider


def shutdown_worker_metrics(provider: MeterProvider | None) -> None:
    """Flush completed counters before a worker exits."""
    if provider is None:
        return
    try:
        provider.force_flush()
        provider.shutdown()
    except Exception:
        logger.exception("Worker metrics shutdown failed")


def _metrics_endpoint() -> str | None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT")
    if endpoint is None:
        base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        endpoint = (
            f"{base_endpoint.removesuffix('/')}/v1/metrics" if base_endpoint is not None else None
        )
    if not endpoint or os.getenv("OTEL_METRICS_EXPORTER", "otlp").lower() == "none":
        return None

    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return endpoint
