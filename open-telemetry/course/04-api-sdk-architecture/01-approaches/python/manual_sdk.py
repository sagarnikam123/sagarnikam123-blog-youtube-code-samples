from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource

def main():
    print("=== Running with FULL SDK Registered ===")

    # 1. Application configures SDK
    res = Resource.create({"service.name": "order-service"})
    provider = TracerProvider(resource=res)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

    # 2. Same library code as before
    tracer = trace.get_tracer("library-sample", "1.0.0")

    with tracer.start_as_current_span("library_operation") as span:
        print(f"Span is_recording: {span.is_recording()}")
        span.set_attribute("data.processed", 100)
        span.add_event("completed")

        ctx = span.get_span_context()
        print(f"Is valid trace context: {ctx.is_valid}")
        print(f"Trace ID: {trace.format_trace_id(ctx.trace_id)}")

    provider.shutdown()
    print("=== Result: Telemetry actively processed and exported! ===\n")

if __name__ == "__main__":
    main()
