from opentelemetry import trace, baggage, propagate
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource

def setup_telemetry():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource.create({"service.name": "propagation-demo"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Register Composite Propagator supporting both W3C TraceContext and Baggage
    composite = CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()])
    propagate.set_global_textmap(composite)

    return provider, exporter

def client_service(tracer):
    carrier = {}

    # 1. Client starts root span
    with tracer.start_as_current_span("client_request", kind=SpanKind.CLIENT) as client_span:
        # Set baggage on current context
        ctx = baggage.set_baggage("user.tier", "vip")
        ctx = baggage.set_baggage("tenant.id", "t-800", context=ctx)

        # 2. Inject active context (TraceContext + Baggage) into HTTP headers carrier
        propagate.inject(carrier, context=ctx)

        print(f"[Client] Injected carrier headers:\n  {carrier}")
        print(f"[Client] Root Span ID: {trace.format_span_id(client_span.get_span_context().span_id)}")
        print(f"[Client] Trace ID:     {trace.format_trace_id(client_span.get_span_context().trace_id)}\n")

    return carrier

def server_service(tracer, carrier):
    # 3. Server receives HTTP carrier and extracts parent context
    extracted_context = propagate.extract(carrier)

    # 4. Server starts child span linked to extracted context
    with tracer.start_as_current_span("server_handle", context=extracted_context, kind=SpanKind.SERVER) as server_span:
        # Retrieve baggage values from extracted context
        user_tier = baggage.get_baggage("user.tier", context=extracted_context)
        tenant_id = baggage.get_baggage("tenant.id", context=extracted_context)

        # Explicitly attach baggage to span attributes so it is indexed in observability backend
        server_span.set_attribute("customer.tier", user_tier)
        server_span.set_attribute("tenant.id", tenant_id)

        print(f"[Server] Extracted Baggage: user.tier={user_tier}, tenant.id={tenant_id}")
        print(f"[Server] Child Span ID:  {trace.format_span_id(server_span.get_span_context().span_id)}")
        print(f"[Server] Child Trace ID: {trace.format_trace_id(server_span.get_span_context().trace_id)}\n")

def main():
    provider, exporter = setup_telemetry()
    tracer = trace.get_tracer("propagation-tracer")

    # Simulate Client calling Server over network
    headers = client_service(tracer)
    server_service(tracer, headers)

    spans = exporter.get_finished_spans()
    assert len(spans) == 2, f"Expected 2 spans, got {len(spans)}"

    client_span = [s for s in spans if s.kind == SpanKind.CLIENT][0]
    server_span = [s for s in spans if s.kind == SpanKind.SERVER][0]

    # Verify Distributed Trace Continuity
    assert client_span.context.trace_id == server_span.context.trace_id, "TraceIDs must match!"
    assert server_span.parent.span_id == client_span.context.span_id, "Server parent must equal Client span_id!"
    assert server_span.attributes["tenant.id"] == "t-800", "Baggage tenant.id must be promoted to attribute!"

    print("VERIFICATION SUCCESS: Distributed context and baggage propagated across services perfectly!")

if __name__ == "__main__":
    main()
