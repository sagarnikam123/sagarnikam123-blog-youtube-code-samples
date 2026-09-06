# Module 14 — Maintaining & Debugging Pipelines

> **OTCA Exam Alignment:** Domain 4 — Maintaining and Debugging (10% Exam Weight)

---

## 1. Top Failure Modes in OpenTelemetry Pipelines

When telemetry is missing or broken in production, it usually stems from one of four root causes:

### 1. Context Propagation Loss Across Thread Boundaries

- **Symptom:** A trace suddenly breaks into disconnected, orphaned fragments.
- **Cause:** In asynchronous runtimes (Java `CompletableFuture` / `ExecutorService`, Python `asyncio` tasks / threads), background threads do not automatically inherit thread-local context unless explicitly wrapped (`Context.current().wrap(runnable)`).

### 2. Ingress Proxy Header Stripping

- **Symptom:** Distributed traces stop at the API gateway or reverse proxy.
- **Cause:** Cloud load balancers (AWS ALB, NGINX, Cloudflare) may strip unrecognized headers unless configured to allow `traceparent` and `baggage`.

### 3. Collector Buffer Overflows & Silent Drops

- **Symptom:** Telemetry appears intermittent during peak hours.
- **Cause:** The Collector's `batch` or `queued_retry` buffer filled up faster than downstream backends could ingest. The Collector dropped spans to prevent out-of-memory crashes.

### 4. Port & Protocol Mismatch

- **Symptom:** `Connection refused` or `HTTP 415 Unsupported Media Type`.
- **Cause:** Sending HTTP JSON to gRPC port `4317`, or sending gRPC to HTTP port `4318`.

---

## 2. The Collector Debugging Toolkit

| Diagnostic Tool | Port / Endpoint | Purpose |
| ----------------- | ----------------- | --------- |
| **Health Check** | `http://localhost:13133/` | Verifies Collector process is up and receiving traffic. |
| **Self-Monitoring Metrics** | `http://localhost:8888/metrics` | Scrapes internal Collector Prometheus metrics (`otelcol_receiver_accepted_spans`, `otelcol_processor_dropped_spans`). |
| **zPages Debugger** | `http://localhost:55679/debug/servicez` | Real-time web UI displaying active pipelines and component latency. |
| **Debug Exporter** | Console `stdout` | Dumps raw decoded Protobuf data points (`verbosity: detailed`). |

### Key Collector Prometheus Metrics to Monitor

```promql
# Monitor dropped spans due to buffer saturation
rate(otelcol_processor_dropped_spans[5m])

# Monitor export errors (backend down or network timeout)
rate(otelcol_exporter_enqueue_failed_spans[5m])

# Measure memory utilization against memory limiter limit
otelcol_process_memory_rss / otelcol_processor_memory_limiter_limit
```

---

## 3. Schema Management & `schema_url`

As semantic conventions evolve (e.g., migrating `http.status_code` to `http.response.status_code`), OpenTelemetry uses **Schema Files** and `schema_url`:

```yaml
# In telemetry record:
schema_url: "https://opentelemetry.io/schemas/1.28.0"
```

The Collector's `schema` processor can automatically translate telemetry emitted with older schema versions to match newer backends without breaking dashboards!

---

## 4. Official Documentation Links

- [Collector Troubleshooting Guide](https://opentelemetry.io/docs/collector/troubleshooting/)
- [OpenTelemetry Schema Transformation Specification](https://opentelemetry.io/docs/specs/otel/schemas/)

---

## 5. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-broken-pipelines`](./01-broken-pipelines/) | Python & YAML | Diagnose and fix 3 intentionally broken telemetry scenarios | `python diagnose.py` |
