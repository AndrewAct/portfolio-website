from unittest.mock import Mock

from apps.monitoring.system_metrics import SystemMetrics, SystemSnapshot


def test_system_metrics_registers_a_bounded_set_of_observable_gauges():
    meter = Mock()
    metrics = SystemMetrics(meter=meter)

    metrics.install()
    metrics.install()

    names = [call.args[0] for call in meter.create_observable_gauge.call_args_list]
    assert names == [
        "system.cpu.utilization",
        "system.memory.usage",
        "system.memory.limit",
        "system.memory.utilization",
        "system.filesystem.usage",
        "system.filesystem.limit",
        "system.filesystem.utilization",
    ]


def test_system_metric_callbacks_emit_container_resource_values(monkeypatch):
    metrics = SystemMetrics(meter=Mock())
    snapshot = SystemSnapshot(
        cpu_utilization=0.25,
        memory_usage=200,
        memory_limit=800,
        filesystem_usage=300,
        filesystem_limit=600,
    )
    monkeypatch.setattr(metrics, "_snapshot", lambda: snapshot)

    assert [item.value for item in metrics._observe_cpu(None)] == [0.25]
    assert [item.value for item in metrics._observe_memory_usage(None)] == [200]
    assert [item.value for item in metrics._observe_memory_limit(None)] == [800]
    assert [item.value for item in metrics._observe_memory_utilization(None)] == [0.25]
    assert [item.value for item in metrics._observe_filesystem_usage(None)] == [300]
    assert [item.value for item in metrics._observe_filesystem_limit(None)] == [600]
    assert [item.value for item in metrics._observe_filesystem_utilization(None)] == [0.5]


def test_memory_utilization_skips_an_unlimited_cgroup(monkeypatch):
    metrics = SystemMetrics(meter=Mock())
    monkeypatch.setattr(
        metrics,
        "_snapshot",
        lambda: SystemSnapshot(0.1, 200, None, 300, 600),
    )

    assert list(metrics._observe_memory_limit(None)) == []
    assert list(metrics._observe_memory_utilization(None)) == []
