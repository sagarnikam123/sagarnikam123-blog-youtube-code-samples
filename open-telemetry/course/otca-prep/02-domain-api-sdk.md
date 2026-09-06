# OTCA Domain 2 Review — OpenTelemetry API and SDK (46%)

---

## Key Review Notes

### 1. The API / SDK Boundary

- **API:** Interfaces and data models. Dependencies for library authors. Defaults to a **No-Op implementation** if no SDK is configured. Never throws exceptions, has zero third-party operational dependencies.
- **SDK:** Implementation of the API. Manages memory, batch queues, samplers, and exporters. Added and configured only by the application entry point.

### 2. Spans, Status & Kinds

- **Trace ID:** 16-byte (32-hex-character) unique identifier.
- **Span ID:** 8-byte (16-hex-character) unique identifier.
- **Span Kinds:** `SERVER` (inbound request), `CLIENT` (outbound call), `PRODUCER` (async enqueue), `CONSUMER` (async dequeue), `INTERNAL` (internal logic).
- **Span Status:** `UNSET` (default), `OK` (explicit success), `ERROR` (operation failed).
- **Events:** Point-in-time timestamped annotations inside a span.
- **Links:** References to other causal spans (e.g. batch job linking multiple upstream requests).

### 3. Context Propagation

- **Carrier:** The transport medium carrying context (e.g. HTTP header map, Kafka record headers).
- **Propagator:** Encodes (`inject`) and decodes (`extract`) context to/from the carrier.
- **W3C `traceparent`:** `00-{trace_id}-{parent_id}-{trace_flags}` (e.g. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`).

### 4. Metrics Instruments & Views

- **Synchronous:** `Counter` (monotonic +), `UpDownCounter` (+/-), `Histogram` (distribution).
- **Asynchronous (Callback):** `ObservableCounter`, `ObservableUpDownCounter`, `ObservableGauge` (instantaneous snapshot).
- **Temporality:** Cumulative (running total, default for Prometheus) vs Delta (change since last export).
- **Views:** Customize histogram buckets, drop high-cardinality attributes, or rename metrics without changing source code.
- **Exemplars:** Trace ID references embedded in metric data points connecting metrics to traces.

### 5. Logging: Appender Bridge

- OTel does not provide an application logging API.
- Developers use standard loggers (Logback, Python `logging`, Zap).
- OTel provides **Log Appender Bridges** that intercept logs, attach active `trace_id` and `span_id`, and forward to an OTLP `LoggerProvider`.

### 6. Samplers & Processors

- **Samplers (Head):** `AlwaysOn`, `AlwaysOff`, `TraceIdRatioBased`, `ParentBased`.
- **Span Processors:** `SimpleSpanProcessor` (sync, dev/testing) vs `BatchSpanProcessor` (async queue, production).

---

## Domain 2 Practice Quiz (25 Questions)

#### Q1: If an application is instrumented with the OpenTelemetry API but no SDK is registered at runtime, what happens?

- A) The application throws a `ProviderNotFoundException` and crashes.
- B) The API uses a No-Op implementation, returning non-recording dummy spans with zero crashes.
- C) Telemetry is automatically written to `/tmp/otel.log`.
- D) The API defaults to exporting OTLP over port 4317.
*Answer:* **B**. The API defaults to a No-Op implementation, guaranteeing safety for library authors.

#### Q2: What is the length in bytes and hex characters of an OpenTelemetry Trace ID?

- A) 8 bytes, 16 hex characters.
- B) 16 bytes, 32 hex characters.
- C) 32 bytes, 64 hex characters.
- D) 4 bytes, 8 hex characters.
*Answer:* **B**. Trace IDs are 16 bytes (128 bits) represented as 32 hexadecimal characters.

#### Q3: What is the length in bytes and hex characters of an OpenTelemetry Span ID?

- A) 8 bytes, 16 hex characters.
- B) 16 bytes, 32 hex characters.
- C) 4 bytes, 8 hex characters.
- D) 64 bytes, 128 hex characters.
*Answer:* **A**. Span IDs are 8 bytes (64 bits) represented as 16 hexadecimal characters.

#### Q4: Which SpanKind should be used by an HTTP web framework when receiving an incoming request?

- A) `CLIENT`
- B) `INTERNAL`
- C) `SERVER`
- D) `CONSUMER`
*Answer:* **C**. `SERVER` represents synchronous inbound network request handling.

#### Q5: Which SpanKind should be used when publishing a message to a Kafka topic?

- A) `CLIENT`
- B) `PRODUCER`
- C) `SERVER`
- D) `INTERNAL`
*Answer:* **B**. `PRODUCER` represents the asynchronous enqueuing of messages into a broker.

#### Q6: In the W3C traceparent header `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`, what does the trailing `01` signify?

- A) The HTTP protocol version.
- B) The Trace Flags bitmask indicating that the trace was sampled.
- C) The priority of the request.
- D) The number of retries remaining.
*Answer:* **B**. `01` is the bitmask flag indicating the span was sampled.

#### Q7: What is the standard default port for OTLP over gRPC?

- A) 4318
- B) 4317
- C) 16686
- D) 9090
*Answer:* **B**. Port 4317 is standard for OTLP/gRPC. (4318 is OTLP/HTTP).

#### Q8: What is the standard default port for OTLP over HTTP?

- A) 4317
- B) 4318
- C) 8080
- D) 3000
*Answer:* **B**. Port 4318 is standard for OTLP/HTTP.

#### Q9: What happens if `span.end()` is never called on an active span?

- A) The span is automatically ended after 60 seconds.
- B) The span's end timestamp is never recorded and the span is leaked in memory without being exported.
- C) The runtime throws a fatal segmentation fault.
- D) The Collector estimates the end time.
*Answer:* **B**. Failing to end a span leaks memory and prevents export. Always end spans in a `finally` block or context manager.

#### Q10: Which metric instrument is best suited to measure current available memory on a server?

- A) Counter
- B) UpDownCounter
- C) ObservableGauge
- D) Histogram
*Answer:* **C**. ObservableGauge polls non-monotonic instantaneous values periodically via callback.

#### Q11: Which metric instrument is strictly monotonic and can only increase?

- A) Gauge
- B) UpDownCounter
- C) Counter
- D) Histogram
*Answer:* **C**. Counter values are strictly non-negative and non-decreasing.

#### Q12: Why should application libraries (like a database client driver) only depend on the OpenTelemetry API and NOT the SDK?

- A) The SDK is written only in C++.
- B) The SDK brings heavy transitive dependencies (gRPC, batch queues, network exporters) that would create version conflicts for library users.
- C) The SDK is deprecated.
- D) The API has faster networking code.
*Answer:* **B**. Library authors must avoid imposing operational dependencies on application developers.

#### Q13: In an SDK pipeline, what is the role of an `Exemplar`?

- A) It provides an example configuration file.
- B) It attaches a specific sampled Trace ID to an aggregated metric data point.
- C) It drops spans that exceed 10KB.
- D) It formats logs as JSON.
*Answer:* **B**. Exemplars connect metric aggregates (e.g. latency spikes) directly to individual traces.

#### Q14: Which head-based sampler honors the sampling decision of upstream callers while applying a ratio to unparented root traces?

- A) `AlwaysOn`
- B) `TraceIdRatioBased`
- C) `ParentBased`
- D) `AlwaysOff`
*Answer:* **C**. `ParentBased` delegates root spans to a root sampler while maintaining consistent downstream trace continuity.

#### Q15: What is the default temporality preferred by Prometheus for metric counters?

- A) Delta
- B) Gauge
- C) Cumulative
- D) Monotonic
*Answer:* **C**. Prometheus expects Cumulative metrics (running totals from process start).

#### Q16: What is the primary purpose of an OpenTelemetry Metric View?

- A) To render graphical charts in a web browser.
- B) To customize bucket boundaries, drop unwanted attributes, or alter instrument aggregation without changing code.
- C) To route traces to multiple collectors.
- D) To translate gRPC into HTTP.
*Answer:* **B**. Views provide declarative customization of metric aggregations and cardinality filtering.

#### Q17: How does an application developer typically send logs to OpenTelemetry?

- A) By calling `otel.log("message")`.
- B) By using existing logging frameworks (Logback, Python logging) connected to an OpenTelemetry Log Appender Bridge.
- C) By writing logs directly to `/dev/null`.
- D) By attaching text strings to Baggage.
*Answer:* **B**. OpenTelemetry bridges existing standard logging frameworks into the OTLP log pipeline.

#### Q18: What is the purpose of Span Links?

- A) To create hyperlinks to the Jaeger documentation.
- B) To associate a span with one or more causally related spans, such as in batch processing or fan-in pipelines.
- C) To connect Prometheus to Grafana.
- D) To bind a span to a network socket.
*Answer:* **B**. Span links model non-hierarchical causal relationships, such as batch message processing.

#### Q19: Which SpanProcessor should be used in production applications?

- A) `SimpleSpanProcessor`
- B) `ConsoleSpanProcessor`
- C) `BatchSpanProcessor`
- D) `NoOpSpanProcessor`
*Answer:* **C**. `BatchSpanProcessor` buffers spans asynchronously, preventing user-facing request latency.

#### Q20: When using `OTEL_EXPORTER_OTLP_ENDPOINT="http://collector:4318"` for HTTP, what path does the SDK append for traces?

- A) `/traces`
- B) `/v1/traces`
- C) `/api/v1/spans`
- D) `/otlp/traces`
*Answer:* **B**. The specification dictates appending `/v1/traces` when a signal-agnostic base HTTP endpoint is provided.

#### Q21: What is the main security risk of W3C Baggage?

- A) It can cause buffer overflows in the JVM.
- B) Baggage is transmitted in plaintext HTTP headers across public networks; putting PII or secrets in baggage risks exposure.
- C) It invalidates TLS certificates.
- D) It prevents traces from being sampled.
*Answer:* **B**. Baggage is sent unencrypted in HTTP headers across network hops.

#### Q22: What are the three valid Span Status codes in OpenTelemetry?

- A) `SUCCESS`, `FAILURE`, `PENDING`
- B) `UNSET`, `OK`, `ERROR`
- C) `200`, `400`, `500`
- D) `RECORDING`, `NOT_RECORDING`, `DROPPED`
*Answer:* **B**. The three official Span Status codes are `UNSET`, `OK`, and `ERROR`.

#### Q23: How are exceptions properly recorded on a span?

- A) By calling `span.setStatus(StatusCode.ERROR)` and `span.recordException(throwable)`.
- B) By printing the stack trace to `System.err`.
- C) By creating a new child span named `Exception`.
- D) By stopping the tracer.
*Answer:* **A**. `recordException` attaches a standardized span event containing exception details and stack traces.

#### Q24: What mechanism does the OpenTelemetry Java Agent use to instrument code without modifying source code?

- A) Python monkey patching.
- B) Java bytecode manipulation via `java.lang.instrument` and ByteBuddy during class loading.
- C) eBPF kernel probes.
- D) Compiling code with a custom compiler.
*Answer:* **B**. Bytecode manipulation dynamically inserts telemetry bytecode into loaded classes.

#### Q25: Which environment variable can disable a specific auto-instrumentation component in the Java Agent?

- A) `OTEL_STOP_COMPONENT=name`
- B) `OTEL_INSTRUMENTATION_<NAME>_ENABLED=false`
- C) `DISABLE_OTEL=true`
- D) `OTEL_EXCLUDE_PACKAGE=name`
*Answer:* **B**. `OTEL_INSTRUMENTATION_<NAME>_ENABLED=false` silences specific integrations.
