# Module 07 — Metrics, Instruments & Views

> **OTCA Exam Alignment:** Domain 2 — OpenTelemetry API & SDK (46% Exam Weight)

---

## 1. The 6 OpenTelemetry Metric Instruments

OpenTelemetry classifies metric instruments across two dimensions:

1. **Synchronous vs. Asynchronous (Observable):** Synchronous instruments are invoked directly in request loops (`counter.add(1)`). Asynchronous instruments register a callback function invoked periodically by the SDK reader.
2. **Monotonicity:** Whether the value can only increase, or can move up and down.

| Instrument | Sync / Async | Monotonic? | Typical Real-World Use Case |
| ------------ | -------------- | ------------ | ----------------------------- |
| **Counter** | Synchronous | Yes (strictly non-negative) | Number of HTTP requests served, bytes sent, error counts. |
| **UpDownCounter** | Synchronous | No (can add +1 or -1) | Active websocket connections, items in a shopping cart, threads in pool. |
| **Histogram** | Synchronous | N/A (value distribution) | HTTP request latency (ms), database query duration, payload sizes. |
| **Observable Counter** | Asynchronous | Yes (strictly non-negative) | CPU user time (seconds), total pages swapped in by OS. |
| **Observable UpDownCounter** | Asynchronous | No | Number of active database connections reported by pool manager. |
| **Observable Gauge** | Asynchronous | No (instantaneous snapshot) | Current memory usage (MB), CPU temperature, room temperature. |

---

## 2. Aggregation Temporality: Cumulative vs. Delta

```text
Time T1: Value = 10
Time T2: Added 5

Delta Aggregation:      T1: 10,   T2: 5     (Reports difference since last export)
Cumulative Aggregation: T1: 10,   T2: 15    (Reports running total since process start)
```

- **Cumulative (Default for Prometheus):** Counters and Histograms report cumulative values from the start of the process. If an export cycle is dropped, the subsequent cycle self-heals without losing data.
- **Delta:** Reports only the delta (change) observed during the last export window. Preferred by push backends like Datadog or AWS CloudWatch.

---

## 3. Metric Views

**Views** allow application owners to customize how raw instruments are aggregated and exported without touching the application source code:

1. **Drop unwanted dimensions:** Scrub high-cardinality labels before they hit the metrics store.
2. **Customize Histogram Buckets:** Replace default exponential or wide buckets with tight, domain-specific thresholds (e.g., `[5ms, 10ms, 25ms, 50ms, 100ms, 250ms]`).
3. **Change Aggregation:** Convert a Histogram to Drop, or change Sum to LastValue.

---

## 4. Exemplars (Connecting Metrics to Traces)

An **Exemplar** is a reference to a specific Trace ID stored alongside an aggregated metric data point (such as a high-latency histogram bucket).

- **The Problem:** A histogram tells you 99% of requests completed under 50ms, but 1% took 4,500ms. Which trace was the slow one?
- **The Exemplar Solution:** The metrics engine samples a Trace ID for that outlier bucket, allowing an operator in Grafana to click directly from the latency graph into the offending distributed trace.

---

## 5. Official Documentation Links

- [OpenTelemetry Metrics Data Model Specification](https://opentelemetry.io/docs/specs/otel/metrics/data-model/)
- [Metric Instruments Guide](https://opentelemetry.io/docs/concepts/signals/metrics/)
- [Exemplars Specification](https://opentelemetry.io/docs/specs/otel/metrics/sdk/#exemplar-defaults)

---

## 6. Module Exercises & Challenge

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-instruments`](./01-instruments/) | Python & Java | Create and emit Counter, UpDownCounter, Histogram, and Gauge | `python main.py` / `mvn test` |
| [`challenge`](./challenge/) | Any | **Hands-on Challenge:** Implement an SDK Metric View to configure custom histogram latency buckets | *(See challenge README)* |
