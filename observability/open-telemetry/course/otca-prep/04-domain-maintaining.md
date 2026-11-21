# OTCA Domain 4 Review — Maintaining and Debugging (10%)

---

## Key Review Notes

### 1. Context Propagation Failure Modes

- **Asynchronous Threads / Coroutines:** Thread-local context does not automatically jump across thread pools (`ExecutorService`, `asyncio.create_task`). You must explicitly capture and attach context: `context.attach(parent_ctx)`.
- **Ingress Header Stripping:** Proxies (Cloudflare, AWS ALB, NGINX) may strip headers containing underscores or unrecognized headers. Ensure `traceparent` and `baggage` are explicitly allowed through.
- **HTTP/2 Lowercase Headers:** All HTTP/2 and gRPC headers are strictly lowercase (`traceparent`). Code that expects case-sensitive headers will fail to extract context.

### 2. Monitoring Collector Health & Data Loss

- **`otelcol_processor_dropped_spans`:** Spans dropped due to `memory_limiter` or queue saturation.
- **`otelcol_exporter_enqueue_failed_spans`:** Spans rejected because the export buffer is full (downstream backend down or slow).
- **`otelcol_receiver_refused_spans`:** Inbound spans rejected due to invalid format or backpressure.

### 3. Schema Evolution & `schema_url`

- Standardizes evolution of semantic conventions across versions without breaking downstream dashboards.
- Telemetry records attach a `schema_url` (e.g. `https://opentelemetry.io/schemas/1.28.0`).
- The Collector's `schema` processor translates attributes between older and newer specifications.

---

## Domain 4 Practice Quiz (10 Questions)

#### Q1: If a trace breaks into disconnected fragments when calling an asynchronous background worker thread, what is the most likely cause?

- A) The network card is failing.
- B) The background thread failed to attach the active OpenTelemetry context from the parent thread.
- C) The Collector is out of disk space.
- D) The tracer version is outdated.
*Answer:* **B**. Thread-local context is not automatically propagated to new threads; it must be manually captured and attached.

#### Q2: Which Prometheus metric emitted by the Collector indicates that spans are being discarded because downstream backends are unreachable?

- A) `otelcol_processor_dropped_spans`
- B) `otelcol_exporter_enqueue_failed_spans`
- C) `otelcol_receiver_accepted_spans`
- D) `collector_cpu_seconds`
*Answer:* **B**. `otelcol_exporter_enqueue_failed_spans` indicates export buffer failure due to downstream backend unavailability.

#### Q3: What is the purpose of the `schema_url` field attached to OpenTelemetry resources and scopes?

- A) It provides the URL to the application's source code repository.
- B) It identifies the version of OpenTelemetry semantic conventions used to produce the telemetry, enabling automated schema translation.
- C) It points to the Collector's health check.
- D) It specifies the TLS certificate authority.
*Answer:* **B**. `schema_url` enables schema transformation across semantic convention versions.

#### Q4: Why might a reverse proxy like NGINX cause distributed tracing context to be lost?

- A) NGINX cannot handle JSON.
- B) NGINX configuration may drop custom HTTP headers like `traceparent` and `baggage` unless explicitly permitted.
- C) NGINX only supports UDP.
- D) NGINX modifies span timestamps.
*Answer:* **B**. Reverse proxies frequently strip unrecognized headers unless configured with `underscores_in_headers` or custom pass-through directives.

#### Q5: If you observe high values for `otelcol_processor_dropped_spans`, what remediation step should you take first?

- A) Remove the Collector and send data direct to backends.
- B) Increase Collector memory limits, scale Gateway instances horizontally, or increase downstream exporter throughput.
- C) Delete all application logs.
- D) Switch from gRPC to HTTP.
*Answer:* **B**. Dropped spans indicate processor saturation or memory limits being reached; scaling collector resources addresses the bottleneck.

#### Q6: In HTTP/2 and gRPC, how are W3C trace context header names formatted?

- A) In ALL_CAPS (`TRACEPARENT`).
- B) Exclusively in lowercase (`traceparent`).
- C) In CamelCase (`TraceParent`).
- D) Prefixed with `X-` (`X-Trace-Parent`).
*Answer:* **B**. The HTTP/2 and gRPC specifications mandate that all header field names be strictly lowercase.

#### Q7: What diagnostic command can validate an OpenTelemetry Collector YAML configuration without starting the server?

- A) `otelcol validate --config=config.yaml`
- B) `otelcol test --all`
- C) `kubectl check otel`
- D) `otelcol dry-run`
*Answer:* **A**. `otelcol validate` checks syntax and component configuration without starting network listeners.

#### Q8: What does the Collector zPages endpoint `/debug/tracez` display?

- A) Historical traces stored over the last 30 days.
- B) In-memory counts of active, latency-bucketed, and errored span samples currently held inside the Collector's running pipelines.
- C) CPU thermal readings.
- D) Linux system logs.
*Answer:* **B**. `/debug/tracez` displays live in-memory trace processing metrics.

#### Q9: When an SDK exporter encounters an intermittent network timeout, what is the expected SDK behavior?

- A) Crash the user's web request with an unhandled exception.
- B) Retry with exponential backoff up to the configured timeout, dropping data gracefully if still unreachable without crashing the app.
- C) Reboot the host machine.
- D) Buffer infinite spans in RAM until memory is exhausted.
*Answer:* **B**. SDKs are designed for resilience, protecting application availability over telemetry capture.

#### Q10: What is the primary tool used to verify that an OpenTelemetry Collector pod in Kubernetes is ready to receive network traffic?

- A) Sending an email alert.
- B) Querying the `health_check` extension endpoint (`http://localhost:13133/`) via a Kubernetes readinessProbe.
- C) Restarting the pod every 5 minutes.
- D) Inspecting docker image labels.
*Answer:* **B**. The `health_check` extension (port 13133) provides the HTTP response required by Kubernetes readiness probes.
