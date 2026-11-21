import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor, InMemoryLogRecordExporter
from opentelemetry.sdk.resources import Resource

def main():
    resource = Resource.create({"service.name": "order-service", "service.version": "1.0.0"})

    # 1. Setup Tracing
    span_exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer("order-tracer")

    # 2. Setup Logging Provider & Appender Bridge
    log_exporter = InMemoryLogRecordExporter()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    # Attach OpenTelemetry LoggingHandler to standard Python root logger
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    print("--- Emitting Log within an Active Span ---")
    with tracer.start_as_current_span("process_payment") as span:
        ctx = span.get_span_context()
        active_trace_id = ctx.trace_id
        active_span_id = ctx.span_id

        # Standard logging call (no OTel specific imports needed by developer!)
        root_logger.info("Payment authorization confirmed by gateway", extra={"payment_id": "pay_987"})

    # 3. Assert Correlation
    log_records = log_exporter.get_finished_logs()
    assert len(log_records) == 1, f"Expected 1 log record, got {len(log_records)}"

    rec = log_records[0]
    print(f"Log Message:       {rec.log_record.body}")
    print(f"Log Trace ID:      {trace.format_trace_id(rec.log_record.trace_id)}")
    print(f"Log Span ID:       {trace.format_span_id(rec.log_record.span_id)}")
    print(f"Log Severity:      {rec.log_record.severity_text} ({rec.log_record.severity_number})")

    # Verify log carries exact active trace_id and span_id
    assert rec.log_record.trace_id == active_trace_id, "Log trace_id must match active span trace_id!"
    assert rec.log_record.span_id == active_span_id, "Log span_id must match active span_id!"
    assert rec.log_record.body == "Payment authorization confirmed by gateway"

    print("\nSUCCESS: Standard logger automatically bridged and correlated with active span!")

if __name__ == "__main__":
    main()
