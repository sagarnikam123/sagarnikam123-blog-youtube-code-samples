# Module 15 — Distributed Capstone Application End-to-End

> **OTCA Exam Alignment:** Practical Synthesis — All Domains (Fundamentals, API/SDK, Collector, Maintaining)

---

## 1. System Architecture

The capstone represents a real-world, polyglot microservice architecture instrumented for all three telemetry signals (Traces, Metrics, Logs) and Baggage across network and runtime boundaries.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT / BROWSER                              │
│                                   │                                     │
│                     HTTP POST /checkout (with baggage)                  │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│ 1. FRONTEND SERVICE (Python)                                            │
│    - HTTP Server receiving inbound request                              │
│    - Emits ROOT SERVER SPAN with modern semantic conventions            │
│    - Injects W3C Baggage: tenant.id=enterprise-99                       │
│    - Increments Counter: checkout_requests_total                        │
│    - Emits structured Log with trace_id                                 │
│    - Forwards request to Worker via HTTP/OTLP Context Carrier           │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                               HTTP POST /process-payment
                               Header: traceparent + baggage
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│ 2. PAYMENT WORKER SERVICE (Java)                                        │
│    - Extracts parent trace context and baggage                          │
│    - Emits CHILD SERVER SPAN                                            │
│    - Promotes baggage tenant.id to Span Attribute                       │
│    - Records latency in Histogram: payment_duration_seconds             │
│    - Emits correlated Log with matching trace_id                        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. OPENTELEMETRY COLLECTOR CONTRIB (Port 4317 / 4318)                   │
│    - Batching, memory protection, attribute normalization               │
└───────────────┬───────────────────┬─────────────────────┬───────────────┘
                │                   │                     │
                ▼                   ▼                     ▼
        ┌───────────────┐   ┌───────────────┐     ┌───────────────┐
        │  Tempo/Jaeger │   │  Prometheus   │     │  Loki (Logs)  │
        │   (Traces)    │   │   (Metrics)   │     │               │
        └───────┬───────┘   └───────┬───────┘     └───────┬───────┘
                │                   │                     │
                └───────────────────┼─────────────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │   GRAFANA 13 (Unified UI)   │
                     │ Click from Log ──► Trace    │
                     │ Click from Metric ──► Trace │
                     └─────────────────────────────┘
```

---

## 2. Telemetry Contracts Verified

1. **Distributed Trace Graph:**
   - Single continuous Trace ID linking Python Frontend and Java Worker.
   - Child span `parent_id` matches Frontend span's `span_id`.
2. **Baggage Propagation:**
   - `tenant.id=enterprise-99` originates in Python and is promoted to a searchable attribute in the Java worker.
3. **Cross-Signal Correlation:**
   - Loki logs contain `trace_id` allowing instant jumping to Tempo/Jaeger waterfalls.
   - Prometheus metric data points carry Exemplar trace IDs for slow transactions.

---

## 3. Running the Capstone

### Option A: Docker Compose

```bash
# 1. Start the core local stack (if not already running)
cd open-telemetry/course/stack/docker
docker compose up -d

# 2. Start the distributed capstone services
cd ../../15-capstone-distributed-app/docker
docker compose up -d

# 3. Generate sample traffic
curl -X POST http://localhost:8000/checkout -H "X-Tenant-Id: enterprise-99"
```

### Option B: Minikube / Kubernetes

```bash
cd open-telemetry/course/15-capstone-distributed-app/minikube
kubectl apply -f app-manifests.yaml
```

---

## 4. Visualizing in Grafana & Jaeger

- **Jaeger Web UI:** [http://localhost:16686](http://localhost:16686)
  - Search for service `frontend-service-py` or `worker-service-java`. View the cross-language span waterfall.
- **Grafana Explore:** [http://localhost:3000](http://localhost:3000)
  - Navigate to **Explore** -> select **Loki** -> query `{app="capstone"}`. Click the blue **TraceID** button to open the trace in Tempo!
