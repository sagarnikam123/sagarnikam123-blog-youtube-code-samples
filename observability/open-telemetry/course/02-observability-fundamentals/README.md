# Module 02 — Observability Fundamentals

> **OTCA Exam Alignment:** Domain 1 — OpenTelemetry Fundamentals (18% Exam Weight)

---

## 1. Monitoring vs. Observability

| Dimension | Traditional Monitoring | Modern Observability |
| ----------- | ------------------------ | ---------------------- |
| **Core Paradigm** | Tells you *when* a system is broken | Explains *why* a system is broken |
| **Questions Answered** | Known-Knowns & Known-Unknowns (e.g., "Is CPU > 85%?") | Unknown-Unknowns (e.g., "Why did requests from region `eu-west-1` for cart IDs starting with `9` time out during database failover?") |
| **Data Granularity** | Pre-aggregated static metrics | High-cardinality, high-dimensionality event streams, distributed traces, structured logs |
| **System Architecture** | Monolithic, predictable call graphs | Distributed microservices, serverless, ephemeral containers, async event queues |

---

## 2. The Core Signals of OpenTelemetry

While traditional observability references the "Three Pillars", OpenTelemetry treats telemetry as interconnected signals sharing a unified **Resource** context:

```text
                  ┌──────────────────────────────┐
                  │      Resource Context        │
                  │ (service.name, host.id, etc) │
                  └──────────────┬───────────────┘
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│     Traces       │    │     Metrics      │    │      Logs        │
│ Causal lifecycle │    │ Aggregated stats │    │ Discrete events  │
│ Request graphs   │    │ Counters, Gauges │    │ Contextual text  │
│ Latency analysis │    │ Histograms       │    │ Trace-correlated │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │        Baggage         │
                    │ Cross-cutting metadata │
                    │ (accountId, tenantId)  │
                    └────────────────────────┘
```

1. **Traces (Distributed Tracing):**
   - Tracks the path of an end-to-end transaction as it traverses distributed network boundaries.
   - Built from **Spans** (directed acyclic graph) linked by parent-child relationships.
2. **Metrics:**
   - Numerical measurements aggregated over fixed intervals of time (Counters, UpDownCounters, Gauges, Histograms).
   - Excellent for alerting, capacity planning, and detecting trends with low storage overhead.
3. **Logs:**
   - Discrete, timestamped event records containing structured or unstructured text.
   - In OpenTelemetry, logs carry `trace_id` and `span_id` for instant bidirectional correlation with traces.
4. **Baggage (Auxiliary Context Signal):**
   - Key-value metadata passed along execution threads and network boundaries (e.g., `tenant.id = enterprise-42`).
   - Propagates context between services without storing it directly as telemetry unless explicitly attached.

---

## 3. Reliability Engineering Metrics: MTTD, MTTR, MTBF

| Metric | Full Name | Definition | Observability Impact |
| -------- | ----------- | ------------ | ---------------------- |
| **MTTD** | Mean Time to Detect | Average time from problem occurrence to alert trigger | Driven by metric anomaly detection and SLI threshold alerts. |
| **MTTR** | Mean Time to Resolve / Remediate | Average time to diagnose, fix, and restore normal service | Distributed traces and correlated logs dramatically reduce MTTR by pinpointing failing spans. |
| **MTBF** | Mean Time Between Failures | Average operating time between unexpected outages | Improved by post-mortem analysis and fixing systemic bottlenecks uncovered via traces. |

---

## 4. Service Level Engineering: SLI, SLO, SLA & Error Budgets

```text
100% Availability ──────────────────────────────────────────────────
                  ▲
                  │  SLO: 99.9% Target (Target reliability)
99.9% SLO ────────┼─────────────────────────────────────────────────
                  │  Error Budget: 0.1% allowed failure margin
                  ▼
                  SLI: Current observed availability (e.g., 99.94%)
0% Availability  ──────────────────────────────────────────────────
```

- **SLI (Service Level Indicator):** A quantifiable metric of performance in real time (e.g., `successful_requests / total_requests`).
- **SLO (Service Level Objective):** Target reliability goal agreed upon by the engineering team (e.g., `99.9% of requests succeed with latency < 200ms over 30 days`).
- **SLA (Service Level Agreement):** Legal/contractual commitment to customers with financial penalties for breach.
- **Error Budget:** `1.0 - SLO`. The tolerable allowance for unreliability (e.g., `0.1% = 43 minutes of downtime per month`). Used to govern feature release velocity vs. reliability investments.

> [!IMPORTANT]
> **OTCA Exam Tip: High Cardinality & High Dimensionality**
>
> - **Cardinality:** The number of unique values for a specific attribute (e.g., `user_id` has high cardinality; `http.request.method` has low cardinality).
> - **Dimensionality:** The total number of attributes attached to a single telemetry record.
> Modern observability must handle high-cardinality attributes without crashing metrics engines (hence histograms and exemplars).

---

## 5. Official Documentation Links

- [OpenTelemetry Signals Overview](https://opentelemetry.io/docs/concepts/signals/)
- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Distributed Tracing Concepts](https://opentelemetry.io/docs/concepts/signals/traces/)

---

## 6. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-signals-comparison`](./01-signals-comparison/) | Python & Java | Correlate a single user request across a trace, a metric, and a structured log line | `python main.py` / `mvn compile exec:java` |
