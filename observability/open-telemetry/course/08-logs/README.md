# Module 08 — Logs Data Model & Trace Correlation

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. Why OpenTelemetry Doesn't Have a "Logging API"

Unlike Traces and Metrics, developers already have mature, battle-tested logging libraries in every language:

- **Java:** SLF4J, Logback, Log4j2, `java.util.logging`
- **Python:** Standard library `logging`, Loguru, structlog
- **Node.js:** Winston, Pino
- **Go:** Zap, Zerolog, `slog`

Asking the global developer community to rewrite millions of `logger.info()` calls to an `otel.log()` API would fail.

Instead, OpenTelemetry employs the **Log Appender Bridge Pattern**:

```text
┌─────────────────────────────────────────────────────────────┐
│ Application Code: logger.info("Order placed", id=901)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Standard Logging Framework (e.g., Logback / Python logging) │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ OpenTelemetry Log Appender Bridge                           │
│  - Captures the log record                                  │
│  - Extracts current TraceID & SpanID from active context    │
│  - Converts into standard OTel LogRecord structure          │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ OpenTelemetry LoggerProvider / OTLP Log Exporter            │
│  - Batches logs                                             │
│  - Exports via OTLP (4317 gRPC / 4318 HTTP) to Loki/Elastic │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. The OpenTelemetry Log Data Model

A standard OpenTelemetry Log Record contains:

| Field | Type | Description |
| ------- | ------ | ------------- |
| `Timestamp` | uint64 | Time when the event occurred. |
| `ObservedTimestamp` | uint64 | Time when the event was observed/collected by the pipeline. |
| `TraceId` | 16-byte hex | Active Trace ID (if emitted during a span). |
| `SpanId` | 8-byte hex | Active Span ID (if emitted during a span). |
| `TraceFlags` | 1-byte | Indicates if the trace was sampled. |
| `SeverityNumber` | 1 to 24 | Standardized numeric severity (1-4: TRACE, 5-8: DEBUG, 9-12: INFO, 13-16: WARN, 17-20: ERROR, 21-24: FATAL). |
| `SeverityText` | string | String severity from source logger (e.g. `"INFO"`). |
| `Body` | AnyValue | The message payload (string, JSON map, or structured array). |
| `Attributes` | Map | Key-value pairs attached to the specific log line. |
| `Resource` | Resource | Service and host metadata (`service.name`, etc.). |

---

## 3. Bidirectional Trace-Log Correlation in Grafana / Loki

When logs carry `trace_id`:

1. **Logs to Traces:** When viewing an error log in Loki, Grafana extracts the `trace_id` derived field and renders an interactive button that jumps directly into the distributed trace in Tempo/Jaeger.
2. **Traces to Logs:** When viewing a slow or failed span in Tempo, Grafana uses the span's start/end timestamps and `service.name` to auto-query Loki for all logs emitted during that exact span's execution window!

---

## 4. Official Documentation Links

- [OpenTelemetry Logs Data Model Specification](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- [Log Appender Bridge Concepts](https://opentelemetry.io/docs/specs/otel/logs/bridge-api/)

---

## 5. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-log-correlation`](./01-log-correlation/) | Python & Java | Bridge standard loggers into OpenTelemetry and verify trace/span ID correlation | `python main.py` / `mvn test` |
