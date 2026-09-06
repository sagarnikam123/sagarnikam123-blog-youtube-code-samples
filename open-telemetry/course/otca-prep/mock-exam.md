# OpenTelemetry Certified Associate (OTCA) Full Mock Exam

> **Exam Simulation:** 60 Questions | 90 Minutes | Passing Score: 70% (42/60)
> **Weighting:** Fundamentals 18% (11 Qs) | API & SDK 46% (28 Qs) | Collector 26% (15 Qs) | Maintaining 10% (6 Qs)

---

## Instructions

1. Set a timer for 90 minutes.
2. Select one answer per question unless multi-select is specified.
3. Check your answers against the **Answer Key & Explanations** section at the bottom.

---

## Questions

### [Domain 1: Fundamentals — 18%]

#### 1. OpenTelemetry is governed under which foundation?

- A) Apache Software Foundation (ASF)
- B) Cloud Native Computing Foundation (CNCF)
- C) Linux Foundation Networking (LFN)
- D) Eclipse Foundation

#### 2. Which two open-source telemetry projects merged in 2019 to create OpenTelemetry?

- A) Prometheus and Grafana
- B) OpenTracing and OpenCensus
- C) Zipkin and Jaeger
- D) StatsD and Fluentd

#### 3. What is the fundamental difference between traditional monitoring and modern observability?

- A) Monitoring is for hardware; observability is for software.
- B) Monitoring alerts on known failure modes; observability allows interrogating unknown-unknown failure states using high-cardinality telemetry.
- C) Observability replaces metrics with text logs.
- D) Monitoring runs in the cloud; observability runs on-premises.

#### 4. Which OpenTelemetry signal provides a causal, directed acyclic graph of a request across distributed services?

- A) Metrics
- B) Traces
- C) Logs
- D) Baggage

#### 5. What is the role of Baggage in OpenTelemetry?

- A) To compress log files before archiving.
- B) To store binary images in span attributes.
- C) To propagate cross-cutting key-value metadata across execution contexts and network boundaries.
- D) To automatically encrypt network packets.

#### 6. If your team defines an SLO of 99.9% availability over 30 days, what is your Error Budget?

- A) 1.0%
- B) 0.1%
- C) 0.01%
- D) 99.9%

#### 7. Under modern OpenTelemetry Semantic Conventions (v1.28+), which attribute represents an HTTP response status code?

- A) `http.status_code`
- B) `http.response.status_code`
- C) `response.status`
- D) `http.code`

#### 8. Which reliability metric measures the average operating time between unexpected system failures?

- A) MTTR
- B) MTBF
- C) MTTD
- D) SLI

#### 9. Why is high cardinality challenging for traditional metrics systems?

- A) It consumes too much CPU for math operations.
- B) Each unique combination of label values generates a distinct time series, causing memory explosion in time-series databases.
- C) High cardinality prevents network routing.
- D) It violates the OpenTelemetry specification.

#### 10. Does OpenTelemetry provide its own visualization dashboards and storage backend?

- A) Yes, OpenTelemetry includes a native dashboard UI and long-term time-series database.
- B) No, OpenTelemetry focuses exclusively on generating and transmitting telemetry to third-party or open-source backends.
- C) Only for traces, not for metrics or logs.
- D) Only when running on Kubernetes.

#### 11. What information is stored in an OpenTelemetry `Resource`?

- A) The username and password of the database.
- B) Static attributes describing the entity producing the telemetry, such as `service.name`, `host.name`, or `k8s.pod.name`.
- C) The exact duration of an individual HTTP request.
- D) The current CPU utilization percentage.

---

### [Domain 2: API and SDK — 46%]

#### 12. If a library is instrumented with the OpenTelemetry API, but the consuming application registers no SDK, what happens at runtime?

- A) An unhandled `NullPointerException` crashes the application.
- B) The API falls back to a No-Op implementation, imposing virtually zero overhead and zero errors.
- C) The library attempts to connect to `localhost:4317` over gRPC.
- D) Spans are logged to the operating system syslog.

#### 13. What is the exact size of an OpenTelemetry Trace ID?

- A) 8 bytes (16 hex characters)
- B) 16 bytes (32 hex characters)
- C) 32 bytes (64 hex characters)
- D) 64 bytes (128 hex characters)

#### 14. What is the exact size of an OpenTelemetry Span ID?

- A) 8 bytes (16 hex characters)
- B) 16 bytes (32 hex characters)
- C) 4 bytes (8 hex characters)
- D) 32 bytes (64 hex characters)

#### 15. In the W3C Trace Context header `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`, what does `00f067aa0ba902b7` represent?

- A) The Trace ID
- B) The Parent / Span ID
- C) The Trace Flags
- D) The Version

#### 16. Which SpanKind represents an inbound synchronous RPC or HTTP request?

- A) `CLIENT`
- B) `SERVER`
- C) `INTERNAL`
- D) `CONSUMER`

#### 17. Which SpanKind represents an asynchronous message dequeue operation from a message broker?

- A) `PRODUCER`
- B) `CONSUMER`
- C) `SERVER`
- D) `CLIENT`

#### 18. What are the three valid Span Status values in the OpenTelemetry specification?

- A) `SUCCESS`, `WARN`, `FAILED`
- B) `UNSET`, `OK`, `ERROR`
- C) `ACTIVE`, `SUSPENDED`, `TERMINATED`
- D) `RECORDING`, `NOT_RECORDING`, `EXPORTED`

#### 19. What is the default port for OTLP communication over gRPC?

- A) 4318
- B) 4317
- C) 9090
- D) 16686

#### 20. What is the default port for OTLP communication over HTTP?

- A) 4317
- B) 4318
- C) 8080
- D) 3000

#### 21. Which metric instrument is non-monotonic and can increment and decrement synchronously?

- A) Counter
- B) UpDownCounter
- C) ObservableCounter
- D) Histogram

#### 22. Which metric instrument is best suited to measure request latency distribution?

- A) Counter
- B) UpDownCounter
- C) Histogram
- D) Gauge

#### 23. What is an Asynchronous (Observable) metric instrument?

- A) An instrument that sends UDP packets asynchronously.
- B) An instrument that calculates values only when polled by an SDK reader via a registered callback function.
- C) An instrument running on an async thread pool.
- D) An instrument that only records when an error occurs.

#### 24. What is the difference between Cumulative and Delta metric temporality?

- A) Cumulative measures CPU; Delta measures memory.
- B) Cumulative reports running totals since process start; Delta reports only the change since the last export cycle.
- C) Cumulative is for logs; Delta is for traces.
- D) Cumulative is synchronous; Delta is asynchronous.

#### 25. What is the role of an OpenTelemetry Metric View?

- A) To display charts in Grafana.
- B) To programmatically customize metric aggregation, define histogram buckets, or filter attributes without modifying source code.
- C) To translate PromQL queries into SQL.
- D) To compress metrics with Brotli.

#### 26. What is an Exemplar in OpenTelemetry metrics?

- A) A sample configuration provided in the documentation.
- B) A reference to a specific Trace ID attached to an aggregated metric data point.
- C) A mock tracer used in unit tests.
- D) A standard dashboard template.

#### 27. Why does OpenTelemetry not provide a direct application logging API like `logger.info()`?

- A) Logging is considered an obsolete observability signal.
- B) Mature logging frameworks already exist in all languages; OTel provides Log Appender Bridges to intercept and correlate existing logs.
- C) Logs are too large for network transmission.
- D) The CNCF voted against logging.

#### 28. What is the primary function of a Log Appender Bridge?

- A) To convert logs into PDF format.
- B) To hook into standard logging libraries (Logback, Python logging), capture log events, and enrich them with the active `trace_id` and `span_id`.
- C) To encrypt log records on disk.
- D) To stream logs directly to AWS S3.

#### 29. Which head-based sampler automatically samples child spans if their remote parent span was sampled?

- A) `AlwaysOff`
- B) `TraceIdRatioBased`
- C) `ParentBased`
- D) `NeverSample`

#### 30. What happens if a developer creates a span with `tracer.start_span()` but forgets to call `span.end()`?

- A) The span ends automatically when the function returns.
- B) The span end time is never recorded, and the span leaks in memory without being exported.
- C) The JVM throws an `IllegalStateException`.
- D) The Collector estimates the end time.

#### 31. Which SpanProcessor should be used in production web applications?

- A) `SimpleSpanProcessor`
- B) `BatchSpanProcessor`
- C) `ConsoleSpanProcessor`
- D) `SynchronousSpanProcessor`

#### 32. In W3C Baggage, are key-value pairs automatically recorded as span attributes?

- A) Yes, all baggage entries automatically become span attributes.
- B) No, baggage travels across the network but must be explicitly extracted and added as span attributes if desired.
- C) Only integer baggage items are converted.
- D) Only if the baggage begins with `otel.`.

#### 33. Which environment variable sets the global service name for OpenTelemetry SDKs?

- A) `SERVICE_NAME`
- B) `OTEL_SERVICE_NAME`
- C) `APP_NAME`
- D) `OTEL_RESOURCE_SERVICE`

#### 34. What is the purpose of Span Links?

- A) To connect a span to a URL.
- B) To link one span to another causally related span without requiring a direct parent-child relationship (e.g. batch jobs).
- C) To connect two OpenTelemetry Collectors together.
- D) To create hyperlinks in Grafana dashboards.

#### 35. What is the effect of setting `OTEL_TRACES_SAMPLER="always_off"`?

- A) The application stops running.
- B) Traces are completely dropped by the SDK, while metrics and logs can still be processed.
- C) Traces are exported only to local disk.
- D) The Collector disables its receivers.

#### 36. How does the OpenTelemetry Java Agent achieve zero-code instrumentation?

- A) It recompiles the Java code into C++.
- B) It uses the Java Instrumentation API and ByteBuddy to manipulate bytecode during JVM class loading.
- C) It intercepts Linux system calls using eBPF.
- D) It monitors network packets with tcpdump.

#### 37. Which environment variable specifies the OTLP transport protocol?

- A) `OTEL_TRANSPORT`
- B) `OTEL_EXPORTER_OTLP_PROTOCOL`
- C) `OTEL_PROTOCOL_TYPE`
- D) `OTEL_WIRE_FORMAT`

#### 38. When should manual instrumentation be favored over zero-code auto-instrumentation?

- A) When measuring HTTP request latency in standard web frameworks.
- B) When instrumenting internal domain business logic, custom state machines, or adding proprietary business attributes.
- C) When you want to avoid writing code.
- D) When deploying on Kubernetes.

#### 39. Which method call on an active span registers an exception and records a standardized exception event?

- A) `span.fail(e)`
- B) `span.record_exception(e)` (or `span.recordException(e)`)
- C) `span.attach_error(e)`
- D) `span.log(e)`

---

### [Domain 3: OpenTelemetry Collector — 26%]

#### 40. In what language is the OpenTelemetry Collector developed?

- A) Java
- B) Rust
- C) Go
- D) C++

#### 41. In an OpenTelemetry Collector pipeline, what is the mandatory position of the `memory_limiter` processor?

- A) As the final processor before the exporter.
- B) Between the batch processor and exporter.
- C) As the very first processor in the pipeline.
- D) In the extensions block.

#### 42. What is the role of a Connector in the OpenTelemetry Collector?

- A) It connects the Collector to a power source.
- B) It connects two pipelines, acting as an exporter in one and a receiver in another (e.g., `spanmetrics`).
- C) It connects the Collector to the Kubernetes API.
- D) It handles TLS termination.

#### 43. What does the `spanmetrics` connector generate from incoming traces?

- A) It generates PDF audit reports.
- B) It derives RED metrics (Request rate, Error rate, Duration histograms) directly from trace spans.
- C) It converts spans into logs.
- D) It terminates slow database queries.

#### 44. What is the main advantage of the Host Agent (DaemonSet) deployment pattern?

- A) It eliminates the need for applications to use an SDK.
- B) Applications send telemetry to local loopback (`localhost`), minimizing network latency and offloading batching/compression.
- C) It stores all traces in local files.
- D) It is cheaper than running a single Gateway.

#### 45. Why is tail-based sampling performed in the Collector rather than the application SDK?

- A) SDKs do not support math operations.
- B) Tail sampling requires buffering all spans of an entire distributed trace until completion to evaluate error status or latency.
- C) Go is faster than Java.
- D) SDKs cannot parse JSON.

#### 46. How does the `loadbalancing` exporter facilitate tail sampling in a multi-gateway cluster?

- A) It sends duplicate copies of every span to all gateways.
- B) It hashes the `trace_id` so that all spans of a given trace are routed to the exact same Gateway instance.
- C) It uses round-robin load balancing.
- D) It balances network traffic by packet size.

#### 47. What does OTTL stand for?

- A) OpenTelemetry Translation Layer
- B) OpenTelemetry Transformation Language
- C) Operational Telemetry Transmission Link
- D) Open Trace Tracking Language

#### 48. Which OTTL statement drops a span attribute named `user.ssn`?

- A) `drop(attributes["user.ssn"])`
- B) `delete_key(attributes, "user.ssn")`
- C) `remove("user.ssn")`
- D) `erase(attributes.user.ssn)`

#### 49. What endpoint and port does the Collector's `health_check` extension expose by default?

- A) `http://localhost:8888/health`
- B) `http://localhost:13133/`
- C) `http://localhost:4317/health`
- D) `http://localhost:9090/-/healthy`

#### 50. What is the primary purpose of the `batch` processor in the Collector?

- A) To sort spans alphabetically by name.
- B) To group telemetry into larger batches before export, maximizing network compression and reducing HTTP/gRPC overhead.
- C) To execute database migrations.
- D) To enforce rate limits on incoming requests.

#### 51. In the Collector, which component is responsible for scraping Prometheus `/metrics` endpoints?

- A) `otlp` receiver
- B) `prometheus` receiver
- C) `scrape` processor
- D) `pull` connector

#### 52. What is the function of the Collector's `zpages` extension on port `55679`?

- A) It generates static documentation websites.
- B) It provides in-process diagnostic web pages showing live pipeline components, receiver traffic, and trace queues.
- C) It encrypts network traffic with SSL.
- D) It stores telemetry on disk.

#### 53. If a Collector configuration specifies multiple exporters in a single pipeline, what does the Collector do?

- A) It throws a configuration validation error.
- B) It sends data only to the first exporter in the list.
- C) It fans out and transmits the telemetry to all listed exporters in parallel.
- D) It picks an exporter at random.

#### 54. Which deployment topology is generally considered an enterprise anti-pattern for production microservices?

- A) Host Agent (DaemonSet)
- B) Centralized Gateway
- C) Sending telemetry directly from all applications to external SaaS backends without an intermediate Collector
- D) Hybrid Agent + Gateway

---

### [Domain 4: Maintaining and Debugging — 10%]

#### 55. If an application's distributed trace breaks into disconnected fragments after delegating work to an asynchronous thread pool, what is the root cause?

- A) The network cable was disconnected.
- B) Thread-local OpenTelemetry context was not explicitly attached to the worker thread.
- C) The Collector rejected the spans.
- D) The database driver is incompatible.

#### 56. Which Collector metric indicates that incoming spans were dropped because internal processor queues were full?

- A) `otelcol_processor_dropped_spans`
- B) `otelcol_receiver_accepted_spans`
- C) `otelcol_exporter_sent_spans`
- D) `process_cpu_seconds`

#### 57. What can cause distributed trace context to be stripped when passing through an HTTP reverse proxy?

- A) The proxy is running HTTP/2.
- B) The proxy configuration strips non-standard headers or headers with underscores unless explicitly permitted.
- C) Traces are too large for HTTP.
- D) The proxy modifies the IP address.

#### 58. What is the purpose of the `schema_url` field in OpenTelemetry data models?

- A) To provide a link to the application's documentation.
- B) To identify the exact version of OpenTelemetry semantic conventions used, enabling automatic schema translation across versions.
- C) To validate JSON schemas against OpenAPI specs.
- D) To configure database connections.

#### 59. Which command can validate an OpenTelemetry Collector configuration file without running the daemon?

- A) `otelcol validate --config=config.yaml`
- B) `otelcol dry-run`
- C) `otelcol --check-syntax`
- D) `kubectl check otel`

#### 60. When diagnosing an OpenTelemetry Collector that is consuming excessive memory, what should you verify first?

- A) Whether the `memory_limiter` processor is present and placed first in all pipelines.
- B) Whether Python is installed.
- C) Whether the Docker container has root privileges.
- D) Whether the Prometheus port is 9090.

---

## Answer Key & Explanations

| # | Domain | Correct Answer | Technical Rationale |
| --- | -------- | ---------------- | --------------------- |
| 1 | Fundamentals | **B** | OpenTelemetry is a flagship project under the Cloud Native Computing Foundation (CNCF). |
| 2 | Fundamentals | **B** | Merged OpenTracing (APIs) and OpenCensus (SDKs & wire format) in 2019. |
| 3 | Fundamentals | **B** | Observability solves unknown-unknowns using exploratory, high-cardinality telemetry. |
| 4 | Fundamentals | **B** | Traces construct causal call graphs across distributed service boundaries. |
| 5 | Fundamentals | **C** | Baggage propagates user metadata across execution and network hops. |
| 6 | Fundamentals | **B** | Error Budget = `100% - SLO` = `100% - 99.9% = 0.1%`. At 99.9% availability, 0% budget remains. |
| 7 | Fundamentals | **B** | Modern semantic convention (v1.28+) is `http.response.status_code`. |
| 8 | Fundamentals | **B** | MTBF = Mean Time Between Failures. |
| 9 | Fundamentals | **B** | Every unique label set creates a new metric time series, causing memory explosion in TSDBs. |
| 10 | Fundamentals | **B** | OTel standardizes generation and transmission; it intentionally excludes storage/dashboards. |
| 11 | Fundamentals | **B** | Resources describe the static entity emitting telemetry (`service.name`, `host.name`). |
| 12 | API/SDK | **B** | The API uses No-Op defaults when no SDK is registered, avoiding crashes. |
| 13 | API/SDK | **B** | Trace IDs are 16 bytes (128 bits), encoded as 32 hexadecimal characters. |
| 14 | API/SDK | **A** | Span IDs are 8 bytes (64 bits), encoded as 16 hexadecimal characters. |
| 15 | API/SDK | **B** | In `00-{trace_id}-{span_id}-{flags}`, the middle 16-hex field is the Parent/Span ID. |
| 16 | API/SDK | **B** | Inbound network requests are handled as `SpanKind.SERVER`. |
| 17 | API/SDK | **B** | Asynchronous message consumers use `SpanKind.CONSUMER`. |
| 18 | API/SDK | **B** | The three official span status codes are `UNSET`, `OK`, and `ERROR`. |
| 19 | API/SDK | **B** | OTLP/gRPC uses standard port 4317. |
| 20 | API/SDK | **B** | OTLP/HTTP uses standard port 4318. |
| 21 | API/SDK | **B** | `UpDownCounter` is non-monotonic and can increment or decrement. |
| 22 | API/SDK | **C** | `Histogram` records statistical distribution of continuous numerical values. |
| 23 | API/SDK | **B** | Observable instruments calculate values via registered callbacks when polled. |
| 24 | API/SDK | **B** | Cumulative reports running total; Delta reports difference since last export. |
| 25 | API/SDK | **B** | Views customize bucket boundaries, drop attributes, or alter aggregations. |
| 26 | API/SDK | **B** | Exemplars link specific Trace IDs directly to aggregated metric data points. |
| 27 | API/SDK | **B** | OTel bridges existing logging frameworks instead of creating a new logging API. |
| 28 | API/SDK | **B** | Log Appender Bridges intercept logs and attach active `trace_id` and `span_id`. |
| 29 | API/SDK | **C** | `ParentBased` sampler honors downstream parent sampling decisions. |
| 30 | API/SDK | **B** | Failing to call `span.end()` leaves end time unrecorded and leaks memory. |
| 31 | API/SDK | **B** | `BatchSpanProcessor` batches spans asynchronously to avoid blocking threads. |
| 32 | API/SDK | **B** | Baggage propagates over the network but is NOT automatically an attribute. |
| 33 | API/SDK | **B** | `OTEL_SERVICE_NAME` is the universal environment variable for service name. |
| 34 | API/SDK | **B** | Span links connect related spans across independent asynchronous workflows. |
| 35 | API/SDK | **B** | `always_off` drops 100% of traces at the head. |
| 36 | API/SDK | **B** | Java Agent modifies bytecode dynamically during JVM class loading. |
| 37 | API/SDK | **B** | `OTEL_EXPORTER_OTLP_PROTOCOL` specifies `grpc`, `http/protobuf`, or `http/json`. |
| 38 | API/SDK | **B** | Manual instrumentation is required for domain-specific business logic. |
| 39 | API/SDK | **B** | `record_exception` / `recordException` records standardized exception events. |
| 40 | Collector | **C** | The OpenTelemetry Collector is implemented in Go. |
| 41 | Collector | **C** | `memory_limiter` MUST be the first processor in every pipeline to avoid OOM. |
| 42 | Collector | **B** | Connectors bridge two pipelines (e.g. `spanmetrics` connects traces to metrics). |
| 43 | Collector | **B** | `spanmetrics` derives RED metrics directly from trace spans. |
| 44 | Collector | **B** | Host agents receive on localhost, minimizing latency and offloading compression. |
| 45 | Collector | **B** | Tail sampling requires buffering all spans of an entire trace before sampling. |
| 46 | Collector | **B** | Hashing `trace_id` sends all spans of a trace to the same Gateway instance. |
| 47 | Collector | **B** | OTTL = OpenTelemetry Transformation Language. |
| 48 | Collector | **B** | `delete_key(attributes, "user.ssn")` removes target key from attributes. |
| 49 | Collector | **B** | `health_check` serves HTTP port 13133. |
| 50 | Collector | **B** | The `batch` processor aggregates records to optimize network payload size. |
| 51 | Collector | **B** | The `prometheus` receiver scrapes standard Prometheus endpoints. |
| 52 | Collector | **B** | zPages (port 55679) display internal in-process debugging pages. |
| 53 | Collector | **C** | The Collector fans out telemetry to all listed exporters in parallel. |
| 54 | Collector | **C** | Direct app-to-backend lacks centralized secret management and filtering. |
| 55 | Maintaining | **B** | Thread-local context is not automatically passed across asynchronous threads. |
| 56 | Maintaining | **A** | `otelcol_processor_dropped_spans` counts spans dropped due to saturation/memory limits. |
| 57 | Maintaining | **B** | Proxies often strip unrecognized custom headers like `traceparent`. |
| 58 | Maintaining | **B** | `schema_url` tracks semantic convention versions for automated translation. |
| 59 | Maintaining | **A** | `otelcol validate --config=...` validates syntax without launching listeners. |
| 60 | Maintaining | **A** | Verify that `memory_limiter` is placed first in all pipelines. |

---

### Scoring Guide

- **54 - 60 (90%+):** Exceptional. Fully prepared for the OTCA certification exam.
- **42 - 53 (70% - 89%):** Passing score. Review missed domain notes in [`otca-prep/`](./).
- **Below 42 (< 70%):** Revisit Modules 04–09 (API/SDK) and Modules 11–13 (Collector).
