from fastapi import FastAPI
import asyncio
from prometheus_client import REGISTRY
from prometheus_client import generate_latest
from .prometheus import collect_system_metrics, metrics_exporter
from ..core.logger import setup_logging

logger = setup_logging()


class MetricsCollector:
    def __init__(self, app: FastAPI, collection_interval: int = 15):
        self.app = app
        self.collection_interval = collection_interval
        self.is_running = False
        self.task = None

    async def collect_and_export_metrics(self):
        while self.is_running:
            # Collect system metrics
            collect_system_metrics()

            # Generate and forward metrics
            metrics_data = generate_latest(REGISTRY).decode('utf-8')
            metrics_exporter.forward_metrics(metrics_data)

            await asyncio.sleep(self.collection_interval)

    def start(self):
        """Start the background metrics collection"""

        async def start_collection():
            self.is_running = True
            self.task = asyncio.create_task(self.collect_and_export_metrics())

        @self.app.on_event("startup")
        async def startup_event():
            logger.info("Start collecting metrics")
            await start_collection()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            self.is_running = False
            logger.info("Stop collecting metrics")
            if self.task:
                self.task.cancel()