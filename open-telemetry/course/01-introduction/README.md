# Module 01 — Introduction & Setup

> **OTCA Exam Alignment:** Domain 1 — OpenTelemetry Fundamentals (18% Exam Weight)

---

## 1. What is OpenTelemetry?

**OpenTelemetry (OTel)** is an open-source, vendor-neutral observability framework under the Cloud Native Computing Foundation (CNCF). It provides a standardized collection of APIs, SDKs, tooling, and protocols designed to generate, process, and transmit telemetry data (metrics, logs, and traces).

### What OpenTelemetry IS

- A standardized **specification** for telemetry across languages.
- An **API** layer defining telemetry data constructs without vendor bias.
- An **SDK** implementation handling configuration, batching, and export pipelines.
- A wire protocol (**OTLP** - OpenTelemetry Protocol) over gRPC and HTTP.
- An out-of-process proxy/collector (**OpenTelemetry Collector**) to ingest, process, transform, and route data.

### What OpenTelemetry IS NOT

- **Not an observability backend:** OTel does not store data long-term or provide visual charting dashboards. It sends telemetry to backends like Jaeger, Prometheus, Tempo, Loki, Elasticsearch, or commercial tools.
- **Not a proprietary agent:** OTel eliminates vendor lock-in by providing a unified instrumentation layer.

```text
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                        │
│   ┌───────────────────────────┐ ┌───────────────────────┐   │
│   │     OpenTelemetry API     │ │   Auto-Instrumentation│   │
│   └─────────────┬─────────────┘ └───────────┬───────────┘   │
│                 │                           │               │
│   ┌─────────────▼───────────────────────────▼───────────┐   │
│   │                 OpenTelemetry SDK                   │   │
│   │     (TracerProvider / MeterProvider / Logger)       │   │
│   │     (BatchSpanProcessor / Exporters)                │   │
│   └─────────────────────────────┬───────────────────────┘   │
└─────────────────────────────────┼───────────────────────────┘
                                  │ OTLP (gRPC: 4317 / HTTP: 4318)
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 OpenTelemetry Collector                     │
│    Receivers ──► Processors (Batch, Filter) ──► Exporters   │
└───────┬─────────────────────────┬───────────────────┬───────┘
        │                         │                   │
        ▼                         ▼                   ▼
┌───────────────┐         ┌───────────────┐   ┌───────────────┐
│ Jaeger / Tempo│         │  Prometheus   │   │  Loki / Logs  │
│   (Traces)    │         │   (Metrics)   │   │    (Logs)     │
└───────────────┘         └───────────────┘   └───────────────┘
```

---

## 2. Specification Structure & Components

| Component | Purpose | Stability / Rule |
| ----------- | --------- | ------------------ |
| **Specification** | Defines requirements and data models across all languages | Versioned; breaking changes only in major spec releases |
| **API** | Defines interfaces and data types used to instrument application code | Must have zero operational dependencies; safe to publish in libraries |
| **SDK** | Implements the API with pipeline logic, memory management, batching, and exporters | Configured at application startup; swappable without changing API code |
| **Semantic Conventions** | Standardized naming conventions for span names, resource attributes, and metrics | Versioned schema (v1.28+); avoids conflicting field names |
| **OTLP Protocol** | Protobuf-based binary and JSON wire format | Transports Traces, Metrics, and Logs over gRPC (`4317`) and HTTP (`4318`) |
| **OTel Collector** | Proxy service for aggregation, filtering, scrubbing, and multi-backend export | Written in Go; runs as an Agent, Gateway, or Sidecar |

> [!IMPORTANT]
> **OTCA Exam Tip: The API / SDK Split**
> The OpenTelemetry API is decoupled from the SDK. If an application is instrumented using only the API and no SDK is registered at runtime, OpenTelemetry defaults to a **no-op (no-operation) implementation**. The application continues to run normally with zero telemetry overhead and zero crashes.

---

## 3. Official Documentation Links

- [OpenTelemetry Overview](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenTelemetry Specification Architecture](https://opentelemetry.io/docs/specs/otel/overview/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [OpenTelemetry Collector Overview](https://opentelemetry.io/docs/collector/)

---

## 4. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-hello-trace`](./01-hello-trace/) | Python & Java | Emit your first span to Console and Jaeger via OTLP | `python main.py` / `mvn compile exec:java` |
