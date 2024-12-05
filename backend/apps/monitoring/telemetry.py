import base64
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI
from ..config import get_settings
from ..core.logger import setup_logging

settings = get_settings()
logger = setup_logging()


def setup_telemetry(app: FastAPI):
    """
    Setup OpenTelemetry with Grafana Cloud integration
    """
    # Check if env variables are loaded
    # print(f"OTLP Endpoint: {settings.grafana_otlp_endpoint}")
    # print(f"API Key: {settings.grafana_api_key}...")

    # Create Base64 encoded credentials
    credentials = f"{settings.grafana_instance_id}:{settings.grafana_api_key}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Create resource with service information
    resource = Resource.create({
        "service.name": "fastapi-monitor",
        "service.version": "0.0.1",
        "deployment.environment": settings.environment  # TBD: do we really need it?
    })

    # Initialize tracer with resource
    logger.info("Setting up the OTLP provider for traces")
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{settings.grafana_otlp_endpoint}/v1/traces",  # Traces will end with /v1/traces
        headers={
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-protobuf"
        }
    )

    # Add BatchSpanProcessor to the trace provider
    logger.info("Add BatchSpanProcessor to the trace provider")
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    # Initialize FastAPI instrumentation with custom configuration
    logger.info("Initialize instrumentation for OTLP")
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="health,metrics",  # Healthcheck is excluded (not necessary), and the metrics itself is excluded
        server_request_hook=lambda span, scope: span.set_attribute(
            "service.name", "fastapi-monitor"
        ),
    )

    # Initialize requests instrumentation
    RequestsInstrumentor().instrument(tracer_provider=provider)

    return provider  # Return provider so we can modify all clean manually in case we need
