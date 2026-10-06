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
    counter_names = [call.args[0] for call in meter.create_observable_counter.call_args_list]
    assert counter_names == [
        "process.runtime.python.gc.collections",
        "process.runtime.python.gc.collected_objects",
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


def test_gc_callbacks_emit_cumulative_values_by_generation(monkeypatch):
    metrics = SystemMetrics(meter=Mock())
    monkeypatch.setattr(
        "apps.monitoring.system_metrics.gc.get_stats",
        lambda: [
            {"collections": 10, "collected": 20, "uncollectable": 0},
            {"collections": 30, "collected": 40, "uncollectable": 0},
            {"collections": 50, "collected": 60, "uncollectable": 0},
        ],
    )

    collections = list(metrics._observe_gc_collections(None))
    collected_objects = list(metrics._observe_gc_collected_objects(None))

    assert [item.value for item in collections] == [10, 30, 50]
    assert [item.value for item in collected_objects] == [20, 40, 60]
    assert [item.attributes for item in collections] == [
        {"gc.generation": "0"},
        {"gc.generation": "1"},
        {"gc.generation": "2"},
    ]
