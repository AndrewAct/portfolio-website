from unittest.mock import Mock

from apps.monitoring import worker_metrics


def test_configure_worker_metrics_installs_an_otlp_provider(monkeypatch):
    exporter = Mock()
    reader = Mock()
    provider = Mock()
    configured = Mock()

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://metrics.example/otlp")
    monkeypatch.setattr(worker_metrics, "configure_otel_environment", configured)
    monkeypatch.setattr(worker_metrics, "OTLPMetricExporter", Mock(return_value=exporter))
    monkeypatch.setattr(worker_metrics, "PeriodicExportingMetricReader", Mock(return_value=reader))
    monkeypatch.setattr(worker_metrics, "MeterProvider", Mock(return_value=provider))
    monkeypatch.setattr(worker_metrics.metrics, "set_meter_provider", Mock())
    monkeypatch.setattr(worker_metrics.metrics, "get_meter_provider", Mock(return_value=provider))

    assert worker_metrics.configure_worker_metrics() is provider

    configured.assert_called_once_with()
    worker_metrics.OTLPMetricExporter.assert_called_once_with(
        endpoint="https://metrics.example/otlp/v1/metrics"
    )
    worker_metrics.PeriodicExportingMetricReader.assert_called_once_with(exporter)
    worker_metrics.MeterProvider.assert_called_once_with(
        metric_readers=[reader], shutdown_on_exit=False
    )


def test_configure_worker_metrics_leaves_delivery_running_without_an_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", raising=False)
    monkeypatch.setattr(worker_metrics, "configure_otel_environment", Mock())

    assert worker_metrics.configure_worker_metrics() is None


def test_shutdown_worker_metrics_flushes_before_shutdown():
    provider = Mock()

    worker_metrics.shutdown_worker_metrics(provider)

    provider.force_flush.assert_called_once_with()
    provider.shutdown.assert_called_once_with()
