import concurrent.futures
from opentelemetry import trace, context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource

def test_async_thread_context_propagation():
    """
    Diagnoses and fixes Context Loss across Thread boundaries.
    """
    print("=== SCENARIO 1: Diagnosing Async Thread Context Loss ===")
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "async-worker"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("async-tracer")

    def broken_background_task():
        # FAILS: Thread does not inherit context automatically!
        with tracer.start_as_current_span("background_broken") as span:
            return span.get_span_context().trace_id

    def fixed_background_task(parent_ctx):
        # FIXED: Attach parent context to worker thread!
        token = context.attach(parent_ctx)
        try:
            with tracer.start_as_current_span("background_fixed") as span:
                return span.get_span_context().trace_id
        finally:
            context.detach(token)

    with tracer.start_as_current_span("parent_request") as parent_span:
        parent_trace_id = parent_span.get_span_context().trace_id
        current_ctx = context.get_current()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            broken_future = executor.submit(broken_background_task)
            fixed_future = executor.submit(fixed_background_task, current_ctx)

            broken_trace_id = broken_future.result()
            fixed_trace_id = fixed_future.result()

    print(f"Parent Trace ID: {trace.format_trace_id(parent_trace_id)}")
    print(f"Broken Trace ID: {trace.format_trace_id(broken_trace_id)} (Disconnected/Orphaned!)")
    print(f"Fixed Trace ID:  {trace.format_trace_id(fixed_trace_id)}  (Correctly Correlated!)")

    # Assert broken task got a different trace ID
    assert broken_trace_id != parent_trace_id, "Broken thread should have lost context"
    # Assert fixed task retained the parent trace ID
    assert fixed_trace_id == parent_trace_id, "Fixed thread must inherit parent trace ID"

    print(">>> Diagnosis Confirmed: Context detachment fixed via context.attach()!\n")

def test_processor_order_validation():
    """
    Validates that memory_limiter must precede batch processor.
    """
    print("=== SCENARIO 2: Validating Collector Processor Ordering ===")
    valid_pipeline = ["memory_limiter", "transform", "batch"]
    invalid_pipeline = ["batch", "transform", "memory_limiter"]

    def validate_pipeline(processors):
        if "memory_limiter" in processors and processors[0] != "memory_limiter":
            raise ValueError("Configuration Error: 'memory_limiter' must be the FIRST processor in the pipeline to prevent OOM!")
        return True

    try:
        validate_pipeline(invalid_pipeline)
    except ValueError as e:
        print(f"Detected invalid order: {e}")

    assert validate_pipeline(valid_pipeline) is True
    print(">>> Diagnosis Confirmed: Pipeline validated with memory_limiter placed first!\n")

def main():
    test_async_thread_context_propagation()
    test_processor_order_validation()
    print("ALL 14-MAINTAINING DIAGNOSTICS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
