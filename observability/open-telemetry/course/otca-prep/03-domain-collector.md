# OTCA Domain 3 Review — OpenTelemetry Collector (26%)

---

## Key Review Notes

### 1. Collector Architecture & Pipeline Structure

A Collector `config.yaml` has five core sections:

1. `receivers`: Push (OTLP gRPC 4317, HTTP 4318) or Pull (Prometheus scraper).
2. `processors`: Sequential data manipulation. **`memory_limiter` MUST BE FIRST**; `batch` should be last before export.
3. `exporters`: Send data to backends (OTLP, Prometheus, Tempo, Loki, debug).
4. `extensions`: Health check (`13133`), zPages (`55679`), pprof (`1777`), auth.
5. `service`: Activates extensions and declares pipelines for `traces`, `metrics`, and `logs`.

### 2. Connectors

- Connect two distinct pipelines.
- **`spanmetrics` connector:** Ingests traces and automatically outputs RED metrics (Rate, Errors, Duration) to a metrics pipeline.

### 3. Deployment Topologies

- **Host Agent (DaemonSet):** Runs on every node/VM. Captures host telemetry, local loopback delivery from apps.
- **Centralized Gateway:** Scalable deployment behind an NLB. Centralizes secret management, heavy OTTL transformations, and tail-based sampling.
- **Sidecar:** High memory overhead; used when complete container isolation is required.
- **Hybrid (Agent + Gateway):** Recommended enterprise pattern.

### 4. OpenTelemetry Transformation Language (OTTL)

- Runs inside the `transform` processor.
- Contexts: `resource`, `span`, `metric`, `datapoint`, `log`.
- Functions: `set()`, `replace_pattern()`, `delete_key()`, `truncate_all()`.

### 5. Tail-Based Sampling & Load Balancing

- Tail sampling buffers traces until complete; keeps 100% of errors and high latency, while dropping normal traffic.
- **`loadbalancing` exporter:** Hashing by `trace_id` ensures all spans of a distributed trace route to the same Gateway instance so tail sampling functions correctly.

---

## Domain 3 Practice Quiz (15 Questions)

#### Q1: In an OpenTelemetry Collector pipeline, where MUST the `memory_limiter` processor be placed?

- A) At the very end of the pipeline immediately before the exporter.
- B) Between the batch processor and the exporter.
- C) As the very first processor in the pipeline.
- D) In the extensions block only.
*Answer:* **C**. The memory limiter must be first to evaluate incoming batches and apply backpressure or drops before other processors consume memory.

#### Q2: What is the primary purpose of the OpenTelemetry Collector's `health_check` extension?

- A) To check if the application code contains syntax errors.
- B) To provide an HTTP endpoint (default port 13133) for Kubernetes liveness and readiness probes.
- C) To run weekly antivirus scans on the host.
- D) To test database query latency.
*Answer:* **B**. `health_check` exposes port 13133 so container orchestrators can monitor collector health.

#### Q3: Which component bridges two pipelines by acting as an exporter in one and a receiver in another?

- A) Adapter
- B) Connector
- C) Propagator
- D) Sampler
*Answer:* **B**. Connectors (e.g. `spanmetrics`) bridge different telemetry signal pipelines.

#### Q4: What problem does the `loadbalancing` exporter solve in a multi-instance Gateway architecture?

- A) It compresses data using gzip.
- B) It ensures all spans with the same `trace_id` are routed to the same Gateway instance for tail-based sampling.
- C) It balances CPU across hyperthreads.
- D) It distributes database queries to read replicas.
*Answer:* **B**. Tail sampling requires the entire trace in one memory space; the `loadbalancing` exporter hashes `trace_id` to route spans consistently.

#### Q5: What is the main drawback of deploying the OpenTelemetry Collector as a Pod Sidecar across an entire cluster?

- A) Sidecars cannot receive gRPC traffic.
- B) Multiplied resource footprint; running hundreds of individual collector instances wastes substantial cluster memory and CPU.
- C) Sidecars cannot write to disk.
- D) Sidecars require root access.
*Answer:* **B**. Running a sidecar per pod consumes significant cumulative memory across a large cluster.

#### Q6: Which OTTL context should you specify to redact a span attribute named `user.credit_card`?

- A) `context: metric`
- B) `context: span`
- C) `context: host`
- D) `context: environment`
*Answer:* **B**. Span attributes are manipulated within the `span` context.

#### Q7: Which OTTL statement correctly masks password query parameters in `url.full`?

- A) `set(attributes["url.full"], "hidden")`
- B) `replace_pattern(attributes["url.full"], "password=[^&]+", "password=REDACTED")`
- C) `drop_all(attributes)`
- D) `mask_string(url.full)`
*Answer:* **B**. `replace_pattern` performs regex substitution on target attributes.

#### Q8: What is the default port for the Collector's internal self-monitoring Prometheus metrics?

- A) 4317
- B) 8888
- C) 9090
- D) 13133
*Answer:* **B**. Port 8888 serves the Collector's internal `/metrics` endpoint.

#### Q9: What is the purpose of the Collector's `zpages` extension (port 55679)?

- A) It serves zip archives of logs.
- B) It provides in-process diagnostic web pages showing live pipelines, receivers, and trace buffer state.
- C) It is an encrypted tunnel for telemetry.
- D) It compresses JSON payloads into gzip.
*Answer:* **B**. zPages provide live internal debugging views for Collector maintainers.

#### Q10: If you need to drop all spans where `http.target == "/healthz"`, which processor should you use?

- A) `memory_limiter`
- B) `filter` or `transform` (OTTL)
- C) `batch`
- D) `probabilistic_sampler`
*Answer:* **B**. The `filter` processor or `transform` processor with OTTL conditions is designed for dropping unwanted telemetry.

#### Q11: What is the benefit of a Centralized Gateway Collector cluster compared to sending telemetry directly from applications to backends?

- A) It eliminates the need for applications to store vendor API keys and shields backends from sudden traffic spikes.
- B) It replaces the need for an application SDK.
- C) It makes all spans run faster.
- D) It compiles application code to machine binaries.
*Answer:* **A**. Gateways centralize credentials, enforce retention/sampling policies, and decouple apps from backends.

#### Q12: Which receiver would you configure in the Collector to ingest metrics from existing Prometheus scrape targets?

- A) `otlp`
- B) `prometheus`
- C) `kafka`
- D) `zipkin`
*Answer:* **B**. The `prometheus` receiver can scrape standard Prometheus metrics endpoints.

#### Q13: What does the `batch` processor do in the OpenTelemetry Collector?

- A) It executes SQL batch scripts on a database.
- B) It aggregates telemetry records over time/size thresholds before sending to exporters, reducing network call overhead.
- C) It compiles Go code into binaries.
- D) It encrypts network traffic with AES-256.
*Answer:* **B**. The `batch` processor groups data points to improve network compression and throughput.

#### Q14: Which exporter should be used during local testing to view the complete, human-readable Protobuf payload structure in terminal stdout?

- A) `file`
- B) `debug` (with `verbosity: detailed`)
- C) `prometheus`
- D) `otlp`
*Answer:* **B**. The `debug` exporter (formerly logging exporter) dumps decoded telemetry batches to stdout.

#### Q15: In an OpenTelemetry Collector pipeline, can multiple exporters be specified for a single pipeline?

- A) No, a pipeline can only have exactly one exporter.
- B) Yes, the Collector automatically fans out telemetry to all listed exporters in parallel.
- C) Only if all exporters use the same port.
- D) Only in Kubernetes environments.
*Answer:* **B**. The Collector supports fan-out, sending data to multiple backends simultaneously.
