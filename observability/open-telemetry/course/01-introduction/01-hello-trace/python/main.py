import os
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_tracer():
    # 1. Define standard resource attributes identifying this service
    resource = Resource.create({
        "service.name": "hello-service-py",
        "service.version": "1.0.0",
        "deployment.environment": "development"
    })

    # 2. Initialize TracerProvider with the resource
    provider = TracerProvider(resource=resource)

    # 3. Add Console exporter for instant local feedback
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(console_exporter))

    # 4. Add OTLP gRPC exporter (sends to local Collector/Jaeger on localhost:4317 if reachable)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    except Exception as e:
        print(f"Notice: OTLP exporter setup warning (non-fatal): {e}")

    # 5. Register global tracer provider
    trace.set_tracer_provider(provider)
    return provider

def main():
    provider = setup_tracer()
    tracer = trace.get_tracer("hello-tracer", "1.0.0")

    print("\n--- Emitting First OpenTelemetry Span ---")
    with tracer.start_as_current_span("hello-operation") as span:
        # Set modern semantic attributes
        span.set_attribute("http.request.method", "GET")
        span.set_attribute("course.module", "01-introduction")
        span.set_attribute("lesson.title", "hello-trace")

        # Simulate brief workload
        time.sleep(0.05)

        # Add an in-span event (point-in-time timestamped annotation)
        span.add_event("work_completed", {"items_processed": 42})
        print(f"Span executed: Trace ID = {trace.format_trace_id(span.get_span_context().trace_id)}")

    # Flush and shutdown provider to guarantee export before process exit
    provider.shutdown()
    print("--- Span successfully exported to console and OTLP! ---\n")

if __name__ == "__main__":
    main()
