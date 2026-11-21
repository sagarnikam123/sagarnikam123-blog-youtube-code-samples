from opentelemetry import trace
from opentelemetry.trace import SpanContext, TraceFlags
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased, ALWAYS_ON, ALWAYS_OFF
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource

def main():
    exporter = InMemorySpanExporter()

    # 1. ParentBased Sampler with AlwaysOff as root fallback
    # This guarantees that root spans are NEVER sampled, BUT spans with sampled parents ARE sampled!
    sampler = ParentBased(root=ALWAYS_OFF, remote_parent_sampled=ALWAYS_ON)
    provider = TracerProvider(sampler=sampler, resource=Resource.create({"service.name": "sampling-demo"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("sampler-tracer")

    print("--- 1. Testing Unparented Root Span (Root = ALWAYS_OFF) ---")
    with tracer.start_as_current_span("unparented_root") as root_span:
        print(f"Root span is_recording: {root_span.is_recording()}")
        print(f"Root span sampled:      {root_span.get_span_context().trace_flags.sampled}")
        assert not root_span.get_span_context().trace_flags.sampled, "Root span must NOT be sampled!"

    print("\n--- 2. Testing Downstream Child with Remote Sampled Parent ---")
    # Simulate incoming HTTP request with traceparent ending in 01 (sampled)
    remote_context = SpanContext(
        trace_id=0x4bf92f3577b34da6a3ce929d0e0e4736,
        span_id=0x00f067aa0ba902b7,
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED)
    )

    parent_ctx = trace.set_span_in_context(trace.NonRecordingSpan(remote_context))
    with tracer.start_as_current_span("child_operation", context=parent_ctx) as child_span:
        print(f"Child span is_recording: {child_span.is_recording()}")
        print(f"Child span sampled:      {child_span.get_span_context().trace_flags.sampled}")
        assert child_span.get_span_context().trace_flags.sampled, "Child must be sampled because remote parent was sampled!"

    finished = exporter.get_finished_spans()
    assert len(finished) == 1, f"Expected exactly 1 finished span (only the sampled child), got {len(finished)}"
    assert finished[0].name == "child_operation"

    print("\nSUCCESS: ParentBased sampling logic verified successfully!")
    provider.shutdown()

if __name__ == "__main__":
    main()
