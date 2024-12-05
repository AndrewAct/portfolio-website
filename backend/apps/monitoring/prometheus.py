from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from fastapi import APIRouter, Response
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from prometheus_client.parser import text_string_to_metric_families
import base64
import psutil
import time
from ..config import get_settings
from ..core.logger import setup_logging
import asyncio
from typing import Dict
from fastapi.background import BackgroundTasks

settings = get_settings()
logger = setup_logging()

# Create desired metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

# http_request_duration_seconds = Histogram(
#     'http_request_duration_seconds',
#     'HTTP request duration in seconds',
#     ['method', 'endpoint']
# )

system_cpu_usage = Gauge(
    'system_cpu_usage',
    'System CPU Usage Percentage',
    ['cpu_type']
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System Memory Usage in Bytes',
    ['type']
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'Disk Usage in Bytes',
    ['device', 'mountpoint', 'type']
)


class MetricsExporter:
    def __init__(self):
        self.setup_otlp_exporter()
        self.meters: Dict[str, any] = {}

    def setup_otlp_exporter(self):
        """Set up OTLP exporter"""
        auth_token = f"{settings.grafana_instance_id}:{settings.grafana_api_key}"
        basic_auth = base64.b64encode(auth_token.encode()).decode('utf-8')

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "X-Scope-OrgID": str(settings.grafana_instance_id)
        }

        exporter = OTLPMetricExporter(
            endpoint=f"{settings.grafana_otlp_endpoint}/v1/metrics",
            headers=headers,
            timeout=30
        )

        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=30_000  # Export data on 2 minute basis - will increase if the data load is too heavy
        )

        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter("app_metrics")

    def get_or_create_metric(self, name, metric_type, description):
        """Obtain or create OTLP metrics"""
        if name not in self.meters:
            if metric_type == "counter":
                self.meters[name] = self.meter.create_counter(
                    name,
                    description=description,
                    unit="1"
                )
            elif metric_type == "gauge":
                self.meters[name] = self.meter.create_gauge(
                    name,
                    description=description,
                    unit="1"
                )
            elif metric_type == "histogram":
                self.meters[name] = self.meter.create_histogram(
                    name,
                    description=description,
                    unit="1"
                )
        return self.meters[name]

    def forward_metrics(self, metrics_text: str):
        """Forward metrics to OTLP"""
        logger.info("We are preparing to send metrics...")
        try:
            for family in text_string_to_metric_families(metrics_text):
                metric_type = family.type
                if metric_type in ["counter", "gauge", "histogram"]:
                    metric = self.get_or_create_metric(
                        family.name,
                        metric_type,
                        family.documentation
                    )

                    for sample in family.samples:
                        if metric_type == "counter":
                            metric.add(sample.value, sample.labels)
                        elif metric_type == "gauge":
                            metric.set(sample.value, sample.labels)
                        elif metric_type == "histogram":
                            if not sample.name.endswith("_sum") and not sample.name.endswith("_count"):
                                metric.record(sample.value, sample.labels)

            # logger.info(metric)
            logger.info("Metrics forwarded successfully")

        except Exception as e:
            logger.error(f"Error forwarding metrics: {e}")


# Create new exporter instance
metrics_exporter = MetricsExporter()


def collect_system_metrics():
    """Collect System Metrics"""
    try:
        # CPU metrics
        cpu_times_percent = psutil.cpu_times_percent()
        system_cpu_usage.labels('system').set(cpu_times_percent.system)
        system_cpu_usage.labels('user').set(cpu_times_percent.user)
        system_cpu_usage.labels('idle').set(cpu_times_percent.idle)

        # Memory metrics
        memory = psutil.virtual_memory()
        system_memory_usage.labels('total').set(memory.total)
        system_memory_usage.labels('available').set(memory.available)
        system_memory_usage.labels('used').set(memory.used)

        # Disk metrics
        for partition in psutil.disk_partitions():
            if partition.fstype:
                disk_usage = psutil.disk_usage(partition.mountpoint)
                system_disk_usage.labels(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    type='total'
                ).set(disk_usage.total)
                system_disk_usage.labels(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    type='used'
                ).set(disk_usage.used)
                system_disk_usage.labels(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    type='free'
                ).set(disk_usage.free)

    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")


async def forward_metrics_task():
    """Forward metrics in daemon"""
    metrics_data = generate_latest(REGISTRY).decode('utf-8')
    metrics_exporter.forward_metrics(metrics_data)


router = APIRouter()

# Prev version: send metrics with background task (while did not in my case)
# @router.get('/metrics')
# async def metrics(background_tasks: BackgroundTasks):
#     """Expose metrics and forward to OTLP"""
#     collect_system_metrics()
#
#     # Send metrics in background (daemon)
#     background_tasks.add_task(forward_metrics_task)
#
#     return Response(
#         generate_latest(REGISTRY),
#         media_type=CONTENT_TYPE_LATEST
#     )


@router.get('/metrics')
async def metrics():
    """Expose metrics in Prometheus format"""
    # Collect latest system metrics before generating response
    collect_system_metrics()

    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


def track_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track metrics from middleware"""
    try:
        # Update prometheus metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()

        # http_request_duration_seconds.labels(
        #     method=method,
        #     endpoint=endpoint
        # ).observe(duration)

    except Exception as e:
        logger.error(f"Error tracking metrics: {e}")