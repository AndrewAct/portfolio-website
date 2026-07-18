import asyncio
from contextlib import suppress

from prometheus_client import REGISTRY, generate_latest

from .prometheus import collect_system_metrics, metrics_exporter


class MetricsCollector:
    def __init__(self, collection_interval: int = 15):
        self.collection_interval = collection_interval
        self.is_running = False
        self.task: asyncio.Task | None = None

    async def collect_and_export_metrics(self):
        while self.is_running:
            collect_system_metrics()
            metrics_data = generate_latest(REGISTRY).decode("utf-8")
            metrics_exporter.forward_metrics(metrics_data)
            await asyncio.sleep(self.collection_interval)

    def start(self):
        """Start background metrics collection."""
        self.is_running = True
        self.task = asyncio.create_task(self.collect_and_export_metrics())

    async def stop(self):
        """Stop background metrics collection and wait for cancellation."""
        self.is_running = False
        if self.task is None:
            return

        self.task.cancel()
        with suppress(asyncio.CancelledError):
            await self.task
        self.task = None
