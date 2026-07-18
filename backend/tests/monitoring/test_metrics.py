from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from apps.monitoring import prometheus
from apps.monitoring.metrics_collector import MetricsCollector


def make_exporter():
    exporter = object.__new__(prometheus.MetricsExporter)
    exporter.meters = {}
    exporter.meter = Mock()
    return exporter


@pytest.mark.parametrize(
    ("metric_type", "factory"),
    [
        ("counter", "create_counter"),
        ("gauge", "create_gauge"),
        ("histogram", "create_histogram"),
    ],
)
def test_get_or_create_metric_caches_supported_types(metric_type, factory):
    exporter = make_exporter()
    metric = Mock()
    getattr(exporter.meter, factory).return_value = metric

    first = exporter.get_or_create_metric("requests", metric_type, "description")
    second = exporter.get_or_create_metric("requests", metric_type, "description")

    assert first is metric
    assert second is metric
    getattr(exporter.meter, factory).assert_called_once()


def test_forward_metrics_routes_counter_gauge_and_histogram_samples(monkeypatch):
    exporter = make_exporter()
    counter = Mock()
    gauge = Mock()
    histogram = Mock()
    metrics = {"counter": counter, "gauge": gauge, "histogram": histogram}
    monkeypatch.setattr(
        exporter,
        "get_or_create_metric",
        Mock(side_effect=lambda _name, metric_type, _description: metrics[metric_type]),
    )
    text = """
# HELP jobs_total Completed jobs
# TYPE jobs_total counter
jobs_total 3
# HELP temperature Current temperature
# TYPE temperature gauge
temperature 7
# HELP latency_seconds Request latency
# TYPE latency_seconds histogram
latency_seconds_bucket{le="1"} 2
latency_seconds_sum 2
latency_seconds_count 2
"""

    exporter.forward_metrics(text)

    counter.add.assert_called_once()
    gauge.set.assert_called_once()
    histogram.record.assert_called_once()


def test_forward_metrics_logs_parser_errors(monkeypatch):
    exporter = make_exporter()
    logger = Mock()
    monkeypatch.setattr(prometheus, "logger", logger)
    monkeypatch.setattr(
        prometheus,
        "text_string_to_metric_families",
        Mock(side_effect=ValueError("invalid metrics")),
    )

    exporter.forward_metrics("invalid")

    logger.error.assert_called_once()


def test_collect_system_metrics_updates_all_gauges(monkeypatch):
    cpu_gauge = Mock()
    memory_gauge = Mock()
    disk_gauge = Mock()
    cpu_gauge.labels.return_value = Mock()
    memory_gauge.labels.return_value = Mock()
    disk_gauge.labels.return_value = Mock()
    monkeypatch.setattr(prometheus, "system_cpu_usage", cpu_gauge)
    monkeypatch.setattr(prometheus, "system_memory_usage", memory_gauge)
    monkeypatch.setattr(prometheus, "system_disk_usage", disk_gauge)
    monkeypatch.setattr(
        prometheus.psutil,
        "cpu_times_percent",
        lambda: SimpleNamespace(system=1, user=2, idle=97),
    )
    monkeypatch.setattr(
        prometheus.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=100, available=60, used=40),
    )
    monkeypatch.setattr(
        prometheus.psutil,
        "disk_partitions",
        lambda: [
            SimpleNamespace(device="disk0", mountpoint="/", fstype="apfs"),
            SimpleNamespace(device="empty", mountpoint="/empty", fstype=""),
        ],
    )
    monkeypatch.setattr(
        prometheus.psutil,
        "disk_usage",
        lambda _path: SimpleNamespace(total=200, used=80, free=120),
    )

    prometheus.collect_system_metrics()

    assert cpu_gauge.labels.call_count == 3
    assert memory_gauge.labels.call_count == 3
    assert disk_gauge.labels.call_count == 3


def test_collect_system_metrics_logs_failures(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(prometheus, "logger", logger)
    monkeypatch.setattr(
        prometheus.psutil,
        "cpu_times_percent",
        Mock(side_effect=RuntimeError("unavailable")),
    )

    prometheus.collect_system_metrics()

    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_forward_task_and_metrics_endpoint(monkeypatch):
    exporter = SimpleNamespace(forward_metrics=Mock())
    monkeypatch.setattr(prometheus, "metrics_exporter", exporter)
    monkeypatch.setattr(prometheus, "generate_latest", lambda _registry: b"metrics")
    collect = Mock()
    monkeypatch.setattr(prometheus, "collect_system_metrics", collect)

    await prometheus.forward_metrics_task()
    response = await prometheus.metrics_endpoint()

    exporter.forward_metrics.assert_called_once_with("metrics")
    collect.assert_called_once()
    assert response.body == b"metrics"


def test_track_metrics_increments_counter_and_handles_failure(monkeypatch):
    counter = Mock()
    counter.labels.return_value = Mock()
    monkeypatch.setattr(prometheus, "http_requests_total", counter)

    prometheus.track_metrics("GET", "/health", 200, 0.1)

    counter.labels.assert_called_once_with(method="GET", endpoint="/health")
    counter.labels.return_value.inc.assert_called_once()

    logger = Mock()
    monkeypatch.setattr(prometheus, "logger", logger)
    counter.labels.side_effect = RuntimeError("broken registry")
    prometheus.track_metrics("GET", "/health", 500, 0.1)
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_metrics_collector_collects_once(monkeypatch):
    collector = MetricsCollector(collection_interval=1)
    collector.is_running = True
    collect = Mock()
    forward = Mock()
    monkeypatch.setattr("apps.monitoring.metrics_collector.collect_system_metrics", collect)
    monkeypatch.setattr(
        "apps.monitoring.metrics_collector.generate_latest",
        lambda _registry: b"metrics",
    )
    monkeypatch.setattr(
        "apps.monitoring.metrics_collector.metrics_exporter",
        SimpleNamespace(forward_metrics=forward),
    )

    async def stop_after_first_iteration(_interval):
        collector.is_running = False

    monkeypatch.setattr(
        "apps.monitoring.metrics_collector.asyncio.sleep", stop_after_first_iteration
    )

    await collector.collect_and_export_metrics()

    collect.assert_called_once()
    forward.assert_called_once_with("metrics")


@pytest.mark.asyncio
async def test_metrics_collector_starts_and_stops():
    collector = MetricsCollector()

    collector.start()
    assert collector.is_running is True
    assert collector.task is not None

    await collector.stop()
    assert collector.is_running is False
    assert collector.task is None


@pytest.mark.asyncio
async def test_metrics_collector_stop_is_safe_before_start():
    collector = MetricsCollector()

    await collector.stop()

    assert collector.is_running is False
