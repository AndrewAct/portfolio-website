"""Low-cardinality container resource metrics exported through OpenTelemetry."""

from __future__ import annotations

import os
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import psutil
from opentelemetry.metrics import CallbackOptions, Meter, Observation, get_meter


@dataclass(frozen=True)
class SystemSnapshot:
    cpu_utilization: float
    memory_usage: int
    memory_limit: int | None
    filesystem_usage: int
    filesystem_limit: int


class SystemMetrics:
    """Expose only the API container's CPU, memory, and root filesystem usage.

    cgroup v2 is preferred, then cgroup v1. The psutil fallback preserves useful
    host-level metrics for non-container local development without multiplying
    metric series by CPU, process, or mountpoint.
    """

    def __init__(self, meter: Meter | None = None) -> None:
        self._meter = meter or get_meter("portfolio.system")
        self._last_cpu_usage: int | None = None
        self._last_cpu_time: float | None = None
        self._installed = False

    def install(self) -> None:
        if self._installed:
            return
        self._meter.create_observable_gauge(
            "system.cpu.utilization",
            callbacks=[self._observe_cpu],
            unit="1",
            description="CPU utilization for this application container.",
        )
        self._meter.create_observable_gauge(
            "system.memory.usage",
            callbacks=[self._observe_memory_usage],
            unit="By",
            description="Memory in use by this application container.",
        )
        self._meter.create_observable_gauge(
            "system.memory.limit",
            callbacks=[self._observe_memory_limit],
            unit="By",
            description="Memory limit available to this application container.",
        )
        self._meter.create_observable_gauge(
            "system.memory.utilization",
            callbacks=[self._observe_memory_utilization],
            unit="1",
            description="Memory utilization for this application container.",
        )
        self._meter.create_observable_gauge(
            "system.filesystem.usage",
            callbacks=[self._observe_filesystem_usage],
            unit="By",
            description="Used bytes on the container root filesystem.",
        )
        self._meter.create_observable_gauge(
            "system.filesystem.limit",
            callbacks=[self._observe_filesystem_limit],
            unit="By",
            description="Total bytes on the container root filesystem.",
        )
        self._meter.create_observable_gauge(
            "system.filesystem.utilization",
            callbacks=[self._observe_filesystem_utilization],
            unit="1",
            description="Utilization of the container root filesystem.",
        )
        self._installed = True

    def _snapshot(self) -> SystemSnapshot:
        memory_usage, memory_limit = _memory_usage_and_limit()
        filesystem = psutil.disk_usage("/")
        return SystemSnapshot(
            cpu_utilization=self._cpu_utilization(),
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            filesystem_usage=filesystem.used,
            filesystem_limit=filesystem.total,
        )

    def _cpu_utilization(self) -> float:
        usage = _cgroup_cpu_usage()
        now = time.monotonic()
        if usage is None:
            return max(0.0, min(psutil.cpu_percent(interval=None) / 100, 1.0))

        previous_usage, previous_time = self._last_cpu_usage, self._last_cpu_time
        self._last_cpu_usage, self._last_cpu_time = usage, now
        if previous_usage is None or previous_time is None or now <= previous_time:
            return 0.0

        available_cpus = _cgroup_cpu_limit() or (os.cpu_count() or 1)
        elapsed_cpu_seconds = (usage - previous_usage) / 1_000_000
        elapsed_wall_seconds = now - previous_time
        utilization = elapsed_cpu_seconds / elapsed_wall_seconds / available_cpus
        return max(0.0, min(utilization, 1.0))

    def _observe_cpu(self, _options: CallbackOptions) -> Iterable[Observation]:
        return [Observation(self._snapshot().cpu_utilization)]

    def _observe_memory_usage(self, _options: CallbackOptions) -> Iterable[Observation]:
        return [Observation(self._snapshot().memory_usage)]

    def _observe_memory_limit(self, _options: CallbackOptions) -> Iterable[Observation]:
        limit = self._snapshot().memory_limit
        return [] if limit is None else [Observation(limit)]

    def _observe_memory_utilization(self, _options: CallbackOptions) -> Iterable[Observation]:
        snapshot = self._snapshot()
        if not snapshot.memory_limit:
            return []
        return [Observation(snapshot.memory_usage / snapshot.memory_limit)]

    def _observe_filesystem_usage(self, _options: CallbackOptions) -> Iterable[Observation]:
        return [Observation(self._snapshot().filesystem_usage)]

    def _observe_filesystem_limit(self, _options: CallbackOptions) -> Iterable[Observation]:
        return [Observation(self._snapshot().filesystem_limit)]

    def _observe_filesystem_utilization(self, _options: CallbackOptions) -> Iterable[Observation]:
        snapshot = self._snapshot()
        return [Observation(snapshot.filesystem_usage / snapshot.filesystem_limit)]


def _read_int(path: Path) -> int | None:
    try:
        value = path.read_text().strip()
    except OSError:
        return None
    if not value or value == "max":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _memory_usage_and_limit() -> tuple[int, int | None]:
    usage = _read_int(Path("/sys/fs/cgroup/memory.current"))
    limit = _read_int(Path("/sys/fs/cgroup/memory.max"))
    if usage is None:
        usage = _read_int(Path("/sys/fs/cgroup/memory/memory.usage_in_bytes"))
        limit = _read_int(Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"))

    # cgroup v1 uses an enormous sentinel for an unlimited memory cgroup.
    if limit is not None and limit >= 2**60:
        limit = None
    if usage is not None:
        return usage, limit

    memory = psutil.virtual_memory()
    return memory.used, memory.total


def _cgroup_cpu_usage() -> int | None:
    v2_stat = Path("/sys/fs/cgroup/cpu.stat")
    try:
        for line in v2_stat.read_text().splitlines():
            key, value = line.split(maxsplit=1)
            if key == "usage_usec":
                return int(value)
    except (OSError, ValueError):
        pass
    nanoseconds = _read_int(Path("/sys/fs/cgroup/cpuacct/cpuacct.usage"))
    return None if nanoseconds is None else nanoseconds // 1_000


def _cgroup_cpu_limit() -> float | None:
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            return max(float(quota) / float(period), 1.0)
    except (OSError, ValueError):
        pass

    quota = _read_int(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us"))
    period = _read_int(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us"))
    if quota is not None and period and quota > 0:
        return max(quota / period, 1.0)
    return None
