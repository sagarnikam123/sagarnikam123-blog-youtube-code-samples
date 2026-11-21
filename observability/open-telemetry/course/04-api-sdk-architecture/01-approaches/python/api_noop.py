from opentelemetry import trace

def main():
    print("=== Running with API ONLY (No SDK Registered) ===")
    
    # 1. Obtain a tracer directly from the global API
    # Since no TracerProvider was registered, OTel automatically returns a DefaultTracer (No-Op)
    tracer = trace.get_tracer("library-sample", "1.0.0")

    # 2. Start span
    with tracer.start_as_current_span("library_operation") as span:
        print(f"Span is_recording: {span.is_recording()}")
        
        # Attributes are safely accepted but dropped immediately in-memory
        span.set_attribute("data.processed", 100)
        span.add_event("completed")

        ctx = span.get_span_context()
        print(f"Is valid trace context: {ctx.is_valid}")
        print(f"Trace ID format: {trace.format_trace_id(ctx.trace_id)}")

    print("=== Result: Zero overhead, zero output, zero crashes! ===\n")

if __name__ == "__main__":
    main()
