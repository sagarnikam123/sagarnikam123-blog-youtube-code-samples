# Module 04 — OTel Architecture: API vs. SDK Split & Three Approaches

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. The API vs. SDK Split

One of the most fundamental architectural patterns in OpenTelemetry is the strict separation between the **API** and the **SDK**.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION CODE                               │
│                                                                         │
│   Calls: tracer.spanBuilder("doWork").startSpan()                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     OpenTelemetry API                           │   │
│   │  - Pure interface package (interfaces, abstract classes)        │   │
│   │  - NO third-party operational dependencies (no gRPC, HTTP, etc) │   │
│   │  - Library authors ONLY depend on the API                       │   │
│   └────────────────────────────────┬────────────────────────────────┘   │
└────────────────────────────────────┼────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │ Is SDK registered at runtime?         │
                 └───────┬───────────────────────┬───────┘
                         │ NO                    │ YES
                         ▼                       ▼
      ┌─────────────────────────────┐ ┌───────────────────────────────────┐
      │     No-Op Implementation    │ │         OpenTelemetry SDK         │
      │  - Returns dummy span       │ │  - Manages memory & batching      │
      │  - Zero network overhead    │ │  - Samplers, processors, exporters│
      │  - Zero runtime crashes     │ │  - Application owners configure it│
      └─────────────────────────────┘ └───────────────────────────────────┘
```

### Why This Split Matters

1. **Dependency Hell Prevention:** If libraries (like Spring, FastAPI, or gRPC) depended on an SDK, they would force their chosen version of gRPC, HTTP clients, and batch exporters onto application owners.
2. **Safe Library Instrumentation:** Open-source library authors can safely instrument their code using the lightweight OTel API. If the end user doesn't care about observability, the API simply does nothing (no-op).

---

## 2. The Three Instrumentation Approaches

| Approach | How It Works | Best Used For | Trade-offs |
| ---------- | -------------- | --------------- | ------------ |
| **1. Zero-Code / Agent** | Bytecode manipulation (Java `-javaagent`) or runtime monkey-patching (`opentelemetry-instrument` in Python). | Quick wins, legacy systems, standard frameworks (Spring, Django, Express). | Limited domain context; captures generic framework spans only. |
| **2. Code-Based (Manual)** | Explicitly calling OTel API (`tracer.start_as_current_span()`, setting custom business attributes). | Core domain logic, custom background workers, complex state machines. | Requires source code changes and maintenance. |
| **3. Library Instrumentation** | Third-party libraries (e.g., database drivers, HTTP clients) emit OTel spans natively using the API. | Frameworks and infrastructure libraries. | Depends on library maintainers supporting OTel. |

---

## 3. The Lifecycle of an Instrument

```text
1. Get Global Instance       tracer_provider = trace.get_tracer_provider()
2. Acquire Named Tracer      tracer = tracer_provider.get_tracer("payment-service", "1.0.0")
3. Start Span Context        span = tracer.start_span("process_payment")
4. Perform Work & Annotate   span.set_attribute("tenant.id", "t-901")
5. End Span                  span.end()
```

> [!IMPORTANT]
> **OTCA Exam Focus: What happens if an exception occurs?**
> Spans must be ended inside a `finally` block (or language equivalent like Python `with` context manager) to ensure `span.end()` is invoked. If `span.end()` is never called, the span's end timestamp is never recorded and the span is leaked in memory.

---

## 4. Official Documentation Links

- [OpenTelemetry API vs SDK Specification](https://opentelemetry.io/docs/specs/otel/overview/#api-and-sdk)
- [Instrumentation Approaches](https://opentelemetry.io/docs/concepts/instrumentation/)

---

## 5. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-approaches`](./01-approaches/) | Python & Java | Compare identical code running with API No-Op vs. Registered SDK | `python api_noop.py` vs `python manual_sdk.py` |
