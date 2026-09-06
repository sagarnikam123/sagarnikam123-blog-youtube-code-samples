import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

def init_telemetry():
    res = Resource.create({"service.name": "signals-demo", "service.version": "1.0.0"})

    # 1. Traces Setup
    trace_provider = TracerProvider(resource=res)
    trace_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(trace_provider)

    # 2. Metrics Setup
    metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=1000)
    meter_provider = MeterProvider(resource=res, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # 3. Logging Setup (standard python logging formatted with trace correlation placeholder)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s] %(message)s")

    return trace_provider, meter_provider

def handle_checkout(tracer, meter):
    # Create metric instrument
    checkout_counter = meter.create_counter(
        name="checkout_requests_total",
        description="Total checkout operations executed",
        unit="1"
    )

    # Start trace span
    with tracer.start_as_current_span("checkout_transaction") as span:
        ctx = span.get_span_context()
        trace_id_hex = trace.format_trace_id(ctx.trace_id)

        # Set span attributes
        span.set_attribute("customer.tier", "platinum")
        span.set_attribute("cart.value_usd", 149.99)

        # Record structured log line correlated to this active trace ID
        logging.info("Processing checkout payment for user", extra={"trace_id": trace_id_hex})

        # Increment metric with low-cardinality dimension
        checkout_counter.add(1, {"status": "success", "payment_method": "credit_card"})

        print(f"\n[Signals Correlated] TraceID: {trace_id_hex}")

def main():
    tp, mp = init_telemetry()
    tracer = trace.get_tracer("signals-tracer")
    meter = metrics.get_meter("signals-meter")

    handle_checkout(tracer, meter)

    # Flush providers
    mp.shutdown()
    tp.shutdown()

if __name__ == "__main__":
    main()
