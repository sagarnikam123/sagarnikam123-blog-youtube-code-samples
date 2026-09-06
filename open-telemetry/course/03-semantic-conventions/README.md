# Module 03 — Semantic Conventions & Analysis Outcomes

> **OTCA Exam Alignment:** Domain 1 — OpenTelemetry Fundamentals (18% Exam Weight)

---

## 1. Why Semantic Conventions Matter

Without semantic conventions, every developer invents their own attribute names:

- Engineer A logs `http_code: 200`
- Engineer B logs `status: "200"`
- Engineer C logs `response_status_code: 200`

This fragmentation breaks cross-service correlation, forces brittle custom queries, and makes automated APM dashboards impossible.

**OpenTelemetry Semantic Conventions** establish a single, universal dictionary of attribute names and values across all languages, cloud providers, and observability backends.

```text
┌─────────────────────────────────────────────────────────────┐
│                   Standardized Telemetry                    │
│   service.name = "auth-service"                             │
│   http.request.method = "POST"                              │
│   http.response.status_code = 401                           │
│   server.address = "auth.internal"                          │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐┌──────────────────────────────┐
│  Automated APM Dashboards    ││ Automated Root-Cause Alerts  │
│  Instant RED metrics (Rate,  ││ Alert triggers on            │
│  Errors, Duration) per route ││ http.response.status_code>=500
└──────────────────────────────┘└──────────────────────────────┘
```

---

## 2. Resource vs. Scope vs. Span Attributes

Telemetry records in OpenTelemetry are structured hierarchically:

| Level | What It Represents | Examples |
| ------- | -------------------- | ---------- |
| **Resource** | The entity producing the telemetry (static per process/container) | `service.name`, `service.version`, `host.name`, `k8s.pod.name`, `cloud.region` |
| **Instrumentation Scope** | The library or package that generated the telemetry | `io.opentelemetry.contrib.fastapi`, version `0.44b0` |
| **Span Attributes** | Specific details of an individual operation/event | `http.request.method`, `url.path`, `db.system`, `db.operation` |

---

## 3. Modern Semantic Conventions (v1.28.0+) vs. Deprecated Keys

OpenTelemetry stabilized its semantic conventions, replacing older fragmented keys. The OTCA exam expects awareness of these modern conventions:

| Category | Modern Stable Attribute (v1.28+) | Deprecated Legacy Attribute | Allowed Values / Example |
| ---------- | ---------------------------------- | ----------------------------- | -------------------------- |
| **HTTP Method** | `http.request.method` | `http.method` | `"GET"`, `"POST"`, `"DELETE"` |
| **HTTP Status** | `http.response.status_code` | `http.status_code` | `200`, `404`, `500` (integer) |
| **Target URL** | `url.full` | `http.url` | `"https://api.example.com/orders?id=12"` |
| **URL Path** | `url.path` | `http.target` | `"/orders"` |
| **Server Host** | `server.address` | `net.peer.name` / `host.name` | `"api.example.com"` |
| **Server Port** | `server.port` | `net.peer.port` | `443`, `8080` (integer) |
| **DB System** | `db.system` | *(unchanged)* | `"postgresql"`, `"mysql"`, `"redis"` |
| **DB Operation** | `db.operation` | *(unchanged)* | `"SELECT"`, `"INSERT"`, `"HGET"` |
| **DB Collection** | `db.collection.name` | `db.sql.table` | `"customers"`, `"orders"` |
| **Messaging** | `messaging.system` | *(unchanged)* | `"kafka"`, `"rabbitmq"` |
| **Msg Destination** | `messaging.destination.name` | *(unchanged)* | `"orders.payment.requested"` |

---

## 4. Analytical Outcomes

Adhering strictly to semantic conventions unlocks powerful automated outcomes:

1. **Automated Service Maps:** Backends detect dependencies by reading `server.address`, `db.system`, and `messaging.system` on Client spans.
2. **Standardized Golden Signals (RED):**
   - **Rate:** Count of spans with `http.request.method`.
   - **Errors:** Spans where `http.response.status_code >= 500` or status is `Error`.
   - **Duration:** Latency percentiles grouped by `http.route`.
3. **Database Performance Insights:** Identifying slow queries grouped by `db.system` and `db.operation` without parsing raw SQL statements.

---

## 5. Official Documentation Links

- [OpenTelemetry Semantic Conventions Specification](https://opentelemetry.io/docs/specs/semconv/)
- [HTTP Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/http/)
- [Database Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/database/)

---

## 6. Module Exercises

| Sub-Lesson | Language | Goal | Run Command |
|------------|----------|------|-------------|
| [`01-semconv-span`](./01-semconv-span/) | Python & Java | Emit HTTP Server and Database Client spans using modern conventions with automated attribute verification | `python test_semconv.py` / `mvn test` |
