# OTCA Domain 1 Review — OpenTelemetry Fundamentals (18%)

---

## Key Review Notes

### 1. OpenTelemetry Scope & Origin

- Formed in 2019 by merging **OpenTracing** (vendor-neutral tracing API) and **OpenCensus** (Google-backed metrics & tracing SDK).
- Governed under the **Cloud Native Computing Foundation (CNCF)** as an Incubation-level project (top 2 active project alongside Kubernetes).
- **Core Goal:** Standardize the generation, collection, and export of telemetry. It is **NOT** a storage backend or visualization dashboard.

### 2. Signals & Baggage

- **Traces:** Causal progression of distributed transactions composed of directed acyclic graphs of **Spans**.
- **Metrics:** Aggregated numerical measurements (Counters, Gauges, Histograms) over discrete time intervals.
- **Logs:** Structured/unstructured text events with timestamps. Correlated with traces via `trace_id` and `span_id`.
- **Baggage:** Cross-cutting key-value metadata passed along execution threads and network boundaries; not automatically stored as telemetry.

### 3. Reliability Engineering

- **MTTD:** Mean Time to Detect (alert latency).
- **MTTR:** Mean Time to Resolve / Remediate (diagnosis and recovery).
- **MTBF:** Mean Time Between Failures (system stability).
- **SLI:** Service Level Indicator (real-time measurement: e.g. successful requests / total requests).
- **SLO:** Service Level Objective (internal reliability goal: e.g. 99.9% over 30 days).
- **SLA:** Service Level Agreement (contract with customers; financial penalty for breach).
- **Error Budget:** `1.0 - SLO` (allowance for failure used to pace innovation).

### 4. Modern Semantic Conventions

- Attributes are organized into standardized namespaces (`http.*`, `db.*`, `rpc.*`, `messaging.*`).
- Modern standard (v1.28+) uses: `http.request.method` (not `http.method`), `http.response.status_code` (not `http.status_code`), `server.address` (not `net.peer.name`), `url.full` (not `http.url`).

---

## Domain 1 Practice Quiz (10 Questions)

#### Q1: What was the primary motivation behind the creation of OpenTelemetry?

- A) To create a new database backend competing with Prometheus and Elasticsearch.
- B) To merge OpenTracing and OpenCensus into a single, unified, vendor-neutral observability standard.
- C) To build an operating system kernel driver for network packet capture.
- D) To replace all application frameworks with a CNCF runtime.
*Answer:* **B**. OpenTelemetry merged OpenTracing and OpenCensus in 2019 to unify telemetry APIs and SDKs.

#### Q2: Which of the following is explicitly OUT OF SCOPE for the OpenTelemetry project?

- A) Standardizing the wire format for telemetry data.
- B) Providing language-specific SDKs for batching and sampling.
- C) Long-term telemetry storage and dashboard visualization.
- D) Providing an out-of-process Collector proxy.
*Answer:* **C**. OpenTelemetry generates and exports telemetry; it does not provide long-term storage or charting dashboards.

#### Q3: How does W3C Baggage differ from Span Attributes?

- A) Baggage is stored in Prometheus; Span Attributes are stored in Jaeger.
- B) Baggage automatically propagates across downstream network hops; Span Attributes are local to a single span.
- C) Span Attributes are unencrypted; Baggage is cryptographically encrypted.
- D) Baggage can only hold integer values.
*Answer:* **B**. Baggage travels across network hops via HTTP headers, whereas span attributes are scoped only to the specific span where they are attached.

#### Q4: If an application achieves 99.9% availability against a 99.9% SLO, what is the remaining Error Budget?

- A) 100%
- B) 0%
- C) 0.1%
- D) 50%
*Answer:* **B**. The allowed error margin has been fully consumed, leaving 0% error budget.

#### Q5: Under modern OpenTelemetry HTTP semantic conventions (v1.28+), which attribute represents the HTTP verb?

- A) `http.method`
- B) `http.request.method`
- C) `http.verb`
- D) `request.action`
*Answer:* **B**. `http.request.method` replaced the older deprecated `http.method`.

#### Q6: Which reliability metric measures the average time taken from the start of an incident until normal service is restored?

- A) MTTD
- B) MTBF
- C) MTTR
- D) SLO
*Answer:* **C**. MTTR (Mean Time to Resolve/Remediate).

#### Q7: What is an Instrumentation Scope?

- A) The cloud region where the cluster is deployed.
- B) The logical identifier (name and version) of the library or package that emitted the telemetry.
- C) The list of IP addresses allowed through the firewall.
- D) The duration of a distributed trace.
*Answer:* **B**. Instrumentation Scope records which library generated the telemetry (e.g. `io.opentelemetry.spring-webmvc:1.4.0`).

#### Q8: High cardinality in metrics refers to

- A) Having a large number of unique attribute values, such as user IDs or order IDs.
- B) Having high network latency between microservices.
- C) Having more than 10 CPU cores on a host.
- D) Running more than 1,000 pods in a Kubernetes cluster.
*Answer:* **A**. High cardinality denotes a huge volume of distinct values for a given label.

#### Q9: Which signal is best suited for alerting on overall system error rates with minimal storage overhead?

- A) Traces
- B) Metrics
- C) Logs
- D) Baggage
*Answer:* **B**. Metrics aggregate numerical stats over time, making them lightweight and ideal for real-time alerting.

#### Q10: How does OpenTelemetry link logs to distributed traces?

- A) By storing logs and traces in the same binary file on disk.
- B) By embedding the active `trace_id` and `span_id` into the LogRecord data model.
- C) By converting all logs into span events.
- D) By discarding logs that do not match a trace.
*Answer:* **B**. The LogRecord schema includes standardized `trace_id` and `span_id` fields for bidirectional correlation.
