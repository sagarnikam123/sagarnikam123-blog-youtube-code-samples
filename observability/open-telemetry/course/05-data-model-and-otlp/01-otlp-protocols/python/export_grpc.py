import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def main():
    print("--- OTLP / gRPC Exporter (Port 4317) ---")
    res = Resource.create({"service.name": "grpc-exporter-service", "service.version": "1.0.0"})
    provider = TracerProvider(resource=res)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    grpc_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=grpc_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("grpc-tracer")
    with tracer.start_as_current_span("grpc_span") as span:
        span.set_attribute("protocol.name", "grpc")
        span.set_attribute("protocol.port", 4317)
        print(f"Emitted gRPC span: TraceID = {trace.format_trace_id(span.get_span_context().trace_id)}")

    provider.shutdown()
    print("--- gRPC export flushed successfully! ---\n")

if __name__ == "__main__":
    main()
