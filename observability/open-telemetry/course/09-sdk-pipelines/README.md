# Module 09 — SDK Pipelines, Composability & Configuration

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. The Head-Based Sampling Hierarchy

Sampling controls what percentage of generated traces are actually stored and exported, preventing network saturation and unbounded storage bills.

**Head-Based Sampling** occurs at the very start of a trace (the "head" or root span) inside the SDK. Once a decision is made to sample or drop, that decision is encoded in the `trace_flags` bitmask (`01` = sampled, `00` = not sampled) and propagated downstream via `traceparent`.

```text
┌─────────────────────────────────────────────────────────────┐
│                   ParentBased Sampler                       │
│                                                             │
│ Does incoming context already have a parent span?           │
│   ├── YES (Remote Parent):                                  │
│   │     ├── If Parent was SAMPLED     ──► SAMPLE child      │
│   │     └── If Parent was NOT SAMPLED ──► DROP child        │
│   │                                                         │
│   └── NO (This is the Root Span):                           │
│         └── Delegate to Root Sampler:                       │
│               e.g. TraceIdRatioBased(0.20) ──► Sample 20%   │
└─────────────────────────────────────────────────────────────┘
```

### Standard Head Samplers

1. `AlwaysOn`: Samples 100% of spans (ideal for dev/staging).
2. `AlwaysOff`: Drops 100% of spans (only collects metrics/logs).
3. `TraceIdRatioBased(ratio)`: Hashes the lower bits of the random 128-bit `TraceId` and compares against the ratio (`0.0` to `1.0`). Ensures consistent sampling distribution across threads.
4. `ParentBased(root_sampler)`: **Production Gold Standard.** Honors downstream parent decisions while applying `root_sampler` to inbound root traces.

> [!IMPORTANT]
> **OTCA Exam Tip: Head vs. Tail Sampling**
>
> - **Head Sampling (SDK):** Cheap and fast, but blind to the outcome. An error or high latency occurring at the *end* of an unsampled trace is lost forever.
> - **Tail Sampling (Collector):** Buffers all spans until the entire trace completes. Can sample 100% of traces containing HTTP errors (`status >= 500`) and 1% of normal `200 OK` traces. Done exclusively in the Collector (Module 13).

---

## 2. Span Processors: Simple vs. Batch

| Parameter | `SimpleSpanProcessor` | `BatchSpanProcessor` |
| ----------- | ------------------------ | ---------------------- |
| **Execution Model** | Synchronous on caller thread | Asynchronous background worker queue |
| **Throughput** | Very Low (blocks application HTTP response until exporter finishes network call) | Very High (non-blocking) |
| **Failure Mode** | Slow backend slows down user requests | Buffer overflow drops oldest spans without impacting user latency |
| **Appropriate For** | Unit tests, CLI tools, serverless shutdown hooks | All production applications |

### Key Batch Tuning Parameters

- `max_queue_size`: Maximum spans buffered before oldest are dropped (default `2048`).
- `scheduled_delay_millis`: Interval between export flushes (default `5000ms`).
- `max_export_batch_size`: Maximum spans transmitted per single OTLP network request (default `512`).
- `export_timeout_millis`: Max network call timeout (default `30000ms`).

---

## 3. The 3 Configuration Methods

OpenTelemetry supports three ways to configure an application SDK:

1. **Programmatic (Code):** Maximum control, ideal for custom logic and unit testing.
2. **Environment Variables:** Zero recompilation; standard for 12-factor apps and Kubernetes (`OTEL_TRACES_SAMPLER=parentbased_traceidratio`, `OTEL_TRACES_SAMPLER_ARG=0.10`).
3. **Declarative Configuration (File):** Standardized YAML configuration file (`otel-config.yaml`) specifying providers, readers, and exporters.

---

## 4. Official Documentation Links

- [SDK Sampler Specification](https://opentelemetry.io/docs/specs/otel/trace/sdk/#sampling)
- [Span Processor Specification](https://opentelemetry.io/docs/specs/otel/trace/sdk/#span-processor)
- [Declarative Configuration Specification](https://opentelemetry.io/docs/specs/otel/configuration/)

---

## 5. Module Exercises & Challenge

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-samplers-and-processors`](./01-samplers-and-processors/) | Python & Java | Configure `TraceIdRatioBased` vs `ParentBased` samplers and observe sampling decisions | `python main.py` / `mvn test` |
| [`challenge`](./challenge/) | Any | **Hands-on Challenge:** Implement dynamic ratio sampling based on environment variables | *(See challenge README)* |
