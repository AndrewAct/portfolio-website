from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_fastapi_native_telemetry_emits_route_metrics_and_a_request_trace():
    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    app = FastAPI(
        telemetry={
            "tracer_provider": tracer_provider,
            "meter_provider": meter_provider,
            "logs": False,
            "operation_spans": False,
            "auto_configure": False,
        }
    )

    @app.get("/items/{item_id}")
    async def get_item(item_id: str):
        return {"item_id": item_id}

    with TestClient(app) as client:
        response = client.get("/items/one")

    assert response.status_code == 200
    assert [span.name for span in span_exporter.get_finished_spans()] == ["GET /items/{item_id}"]
    metrics_data = metric_reader.get_metrics_data()
    metric_names = {
        metric.name
        for resource_metric in metrics_data.resource_metrics
        for scope_metric in resource_metric.scope_metrics
        for metric in scope_metric.metrics
    }
    assert metric_names == {"http.server.request.duration", "http.server.active_requests"}
