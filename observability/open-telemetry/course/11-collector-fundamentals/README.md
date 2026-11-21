# Module 11 — OpenTelemetry Collector Fundamentals

> **OTCA Exam Alignment:** Domain 3 — OpenTelemetry Collector (26% Exam Weight)

---

## 1. What is the OpenTelemetry Collector?

The **OpenTelemetry Collector** is a high-performance proxy service written in Go. It receives telemetry from applications, processes it (filtering, batching, masking, aggregating), and exports it to one or more observability backends.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      OPENTELEMETRY COLLECTOR PIPELINE                   │
│                                                                         │
│  RECEIVERS (Push/Pull)    PROCESSORS (Sequential)   EXPORTERS (Fan-Out) │
│  ┌─────────────────┐      ┌─────────────────┐       ┌─────────────────┐ │
│  │   OTLP (4317)   ├───►  │  memory_limiter ├───►   │  otlp / Tempo   │ │
│  └─────────────────┘      └────────┬────────┘       └─────────────────┘ │
│  ┌─────────────────┐               │                ┌─────────────────┐ │
│  │   OTLP (4318)   ├───►  ┌────────▼────────┐   ┌──►│  otlp / Jaeger  │ │
│  └─────────────────┘      │    transform    ├───┤   └─────────────────┘ │
│  ┌─────────────────┐      └────────┬────────┘   │   ┌─────────────────┐ │
│  │Prometheus Scrape├───►           │            └──►│   debug/stdout  │ │
│  └─────────────────┘      ┌────────▼────────┐       └─────────────────┘ │
│                           │      batch      │                           │
│                           └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Anatomy of `config.yaml`

A Collector configuration consists of five root blocks:

### 1. `receivers`: How data enters the Collector

- Push: `otlp` (gRPC `4317`, HTTP `4318`), `jaeger`, `zipkin`
- Pull: `prometheus` (scrapes `/metrics` endpoints)

### 2. `processors`: Sequential data manipulation
>
> [!IMPORTANT]
> **OTCA Exam Rule: Processor Ordering Matters!**
> Processors are executed in the exact order declared in the `pipelines` section:
>
> 1. `memory_limiter` **MUST** be placed first in every pipeline to drop or backpressure data before memory exhaustion occurs.
> 2. Filtering / scrubbing / transformation (`transform`, `filter`) should occur next.
> 3. `batch` should be placed last before exporters to optimize network payloads.

### 3. `exporters`: How data exits the Collector

- `otlp` (sends OTLP to Tempo, Jaeger, etc.)
- `prometheus` (exposes Prometheus scrape endpoint)
- `debug` (prints formatted telemetry batches to Collector stdout)

### 4. `extensions`: Auxiliary capabilities

- `health_check` (exposes port `13133` for Kubernetes liveness/readiness probes)
- `zpages` (exposes port `55679` for in-memory debugging)
- `pprof` (exposes port `1777` for Go runtime profiling)

### 5. `service`: Wiring the pipelines

Activates extensions and combines receivers, processors, and exporters into pipelines for `traces`, `metrics`, and `logs`.

```yaml
service:
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo, debug]
```

---

## 3. Connectors (Bridging Signals)

A **Connector** joins two pipelines, acting as both an exporter in one pipeline and a receiver in another:

- **`spanmetrics` connector:** Ingests `traces` and automatically produces RED `metrics` (Request count, Error rate, Duration histograms) grouped by service and route, without application developers writing custom metric code!

---

## 4. Official Documentation Links

- [OpenTelemetry Collector Configuration](https://opentelemetry.io/docs/collector/configuration/)
- [Collector Components Repository (GitHub)](https://github.com/open-telemetry/opentelemetry-collector-contrib)

---

## 5. Module Exercises & Challenge

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-pipeline-components`](./01-pipeline-components/) | YAML / Docker | Run a standalone Collector validating `memory_limiter`, `batch`, and `debug` output | `docker compose up` |
| [`challenge`](./challenge/) | YAML | **Hands-on Challenge:** Build a multi-pipeline configuration with Prometheus scrape receiver and OTLP gRPC export | *(See challenge README)* |
