# Module 05 — Data Model & OTLP (Wire Protocol)

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. The OpenTelemetry Data Model

Every telemetry record transmitted in OpenTelemetry conforms to a three-tier hierarchy:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. RESOURCE (Entity emitting the telemetry)                            │
│    Attributes: service.name="cart-service", k8s.pod.name="cart-9x1z"    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 2. INSTRUMENTATION SCOPE (Library that instrumented the code)           │
│    Name: "io.opentelemetry.spring-webmvc", Version: "1.32.0"            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 3. TELEMETRY SIGNALS                                                    │
│    ├── Traces: Spans, SpanEvents, Links, TraceContext                   │
│    ├── Metrics: MetricDescriptor, AggregationTemporality, DataPoints    │
│    └── Logs: Body, SeverityText, SeverityNumber, ObservedTimestamp      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. OTLP (OpenTelemetry Protocol)

**OTLP** is the purpose-built, vendor-agnostic specification defining the encoding and delivery of telemetry data between SDKs, the OpenTelemetry Collector, and downstream backends.

### Transport Options

| Dimension | OTLP / gRPC | OTLP / HTTP (Protobuf) | OTLP / HTTP (JSON) |
| ----------- | ------------- | ------------------------ | --------------------- |
| **Default Port** | `4317` | `4318` | `4318` |
| **Path Prefix** | `opentelemetry.proto.collector.*` | `/v1/traces`, `/v1/metrics`, `/v1/logs` | `/v1/traces`, `/v1/metrics`, `/v1/logs` |
| **Content-Type** | `application/grpc` | `application/x-protobuf` | `application/json` |
| **Streaming** | Full duplex HTTP/2 streaming | Request/response HTTP/1.1 or HTTP/2 | Request/response HTTP/1.1 or HTTP/2 |
| **Ideal For** | High-throughput backend services | Restricted firewalls, serverless (Lambda), browser clients | Debugging with `curl`, edge proxies |

---

## 3. OTLP Environment Variables

```bash
# Target the Collector via gRPC (port 4317)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# Target the Collector via HTTP Protobuf (port 4318)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"

# Custom HTTP endpoints per signal (note: endpoints include full path for HTTP)
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:4318/v1/traces"
export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT="http://localhost:4318/v1/metrics"
export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT="http://localhost:4318/v1/logs"

# Header authentication
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer my-secret-token,X-Tenant=corp"
```

> [!IMPORTANT]
> **OTCA Exam Tip: HTTP Endpoint Path Construction**
> When configuring `OTEL_EXPORTER_OTLP_ENDPOINT` for HTTP (e.g., `http://collector:4318`), the SDK automatically appends `/v1/traces`, `/v1/metrics`, or `/v1/logs`.
> HOWEVER, if you set the signal-specific variable `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, the SDK uses the exact URL provided **without** appending `/v1/traces`.

---

## 4. Official Documentation Links

- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [OTLP Protocol Buffers Schema (GitHub)](https://github.com/open-telemetry/opentelemetry-proto)
- [SDK Environment Variable Specification](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/)

---

## 5. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-otlp-protocols`](./01-otlp-protocols/) | Python & Java | Compare OTLP/gRPC (4317) vs. OTLP/HTTP (4318) export pipelines | `python export_grpc.py` & `python export_http.py` |
