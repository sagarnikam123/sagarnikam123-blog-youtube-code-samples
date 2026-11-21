import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def main():
    print("--- OTLP / HTTP Exporter (Port 4318) ---")
    res = Resource.create({"service.name": "http-exporter-service", "service.version": "1.0.0"})
    provider = TracerProvider(resource=res)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    http_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces")
    exporter = OTLPSpanExporter(endpoint=http_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("http-tracer")
    with tracer.start_as_current_span("http_protobuf_span") as span:
        span.set_attribute("protocol.name", "http/protobuf")
        span.set_attribute("protocol.port", 4318)
        print(f"Emitted HTTP span: TraceID = {trace.format_trace_id(span.get_span_context().trace_id)}")

    provider.shutdown()
    print("--- HTTP export flushed successfully! ---\n")

if __name__ == "__main__":
    main()
