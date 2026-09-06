# Module 06 — Traces & Context Propagation

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. Anatomy of a Span

A **Span** represents a single unit of contiguous work within a distributed system.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Span Name: "POST /checkout"                                             │
│ Trace ID:  4bf92f3577b34da6a3ce929d0e0e4736 (16 bytes / 32 hex chars)  │
│ Span ID:   00f067aa0ba902b7                 (8 bytes / 16 hex chars)   │
│ Parent ID: 5fb397be34d23b0f                 (null for root spans)      │
│ Kind:      SERVER / CLIENT / PRODUCER / CONSUMER / INTERNAL             │
│ Start / End Timestamp: [2026-09-06T08:00:00.000Z -> 08:00:00.045Z]     │
├─────────────────────────────────────────────────────────────────────────┤
│ Attributes:                                                             │
│   http.request.method = "POST", http.response.status_code = 200        │
├─────────────────────────────────────────────────────────────────────────┤
│ Events (Timestamped Annotations):                                       │
│   {"time": 08:00:00.015Z, "name": "cache_lookup_miss"}                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Links: References to other related spans (e.g. batch jobs)             │
├─────────────────────────────────────────────────────────────────────────┤
│ Status: UNSET (default), OK, or ERROR (with exception stack trace)      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Span Kinds Explained

- `SERVER`: Receives a synchronous network request (e.g. HTTP server handler).
- `CLIENT`: Initiates a synchronous network request to an external service or database.
- `PRODUCER`: Asynchronously publishes an event/message to an intermediary message queue (e.g., Kafka producer).
- `CONSUMER`: Asynchronously consumes an event/message from an intermediary message broker.
- `INTERNAL`: Default internal application operation (e.g., helper function, compute loop).

---

## 2. Distributed Context Propagation: Inject & Extract

When an HTTP request moves from Service A to Service B, how does Service B know its parent Trace ID?

Through **Context Propagation**:

1. **Injector (Service A - Client):** Serializes active context into outbound network carrier (HTTP headers).
2. **Extractor (Service B - Server):** Deserializes carrier headers and restores the parent Context.

```text
Service A (Frontend)                                  Service B (Payment Worker)
┌──────────────────────────────┐                      ┌──────────────────────────────┐
│ Active Trace Context         │                      │ Extracted Context            │
│ TraceID: 4bf92f3577b...      │                      │ ParentSpanID: 00f067aa0ba... │
│ SpanID:  00f067aa0ba...      │                      │                              │
│                              │                      │ New Child Span Created:      │
│ Propagator.inject(headers) ──┼── HTTP Headers ─────►│ Propagator.extract(headers)  │
│   traceparent: 00-4bf...     │                      │ TraceID: 4bf92f3577b...      │
└──────────────────────────────┘                      └──────────────────────────────┘
```

### Standard W3C `traceparent` Header Format

```text
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             │  │                                │                │
      Version│  Trace ID (32 hex)                │Span ID (16 hex)│Trace Flags
             └───────────────────────────────────┴────────────────┴──────────── (01=Sampled)
```

---

## 3. W3C Baggage vs. Span Attributes

| Property | Span Attributes | W3C Baggage |
| ---------- | ----------------- | ------------- |
| **Scope** | Local to the single span where it was set. | Propagates downstream across network boundaries to all subsequent services. |
| **Telemetry Impact** | Directly stored in the backend (searchable in Jaeger/Tempo). | **NOT automatically stored** as telemetry. Must be explicitly extracted and added to span attributes. |
| **Typical Use Case** | Latency breakdown, query params, errors. | Cross-cutting metadata (`tenant.id`, `customer.tier`, `account.id`). |
| **Security Risk** | Backend access controls apply. | **Exposed on wire**: Transmitted in plaintext HTTP headers across public networks. Never put secrets or PII in baggage! |

---

## 4. Span Links (Batching & Fan-In / Fan-Out)

While parent-child spans model synchronous hierarchical execution, **Span Links** model:

1. **Batching**: A worker processing 100 queue messages concurrently links its processing span to all 100 individual incoming message spans.
2. **Fan-Out**: An event triggered by one workflow asynchronously influences another unrelated workflow.

---

## 5. Official Documentation Links

- [Trace Context W3C Recommendation](https://www.w3.org/TR/trace-context/)
- [W3C Baggage Specification](https://www.w3.org/TR/baggage/)
- [OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)

---

## 6. Module Exercises & Challenge

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-propagation`](./01-propagation/) | Python & Java | Manually inject W3C traceparent and baggage, transmit across HTTP, extract in downstream service | `python client_server_demo.py` / `mvn test` |
| [`challenge`](./challenge/) | Any | **Hands-on Challenge:** Implement multi-hop baggage propagation across 3 services without losing context | *(See challenge README)* |
