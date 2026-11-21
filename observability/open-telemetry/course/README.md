# OpenTelemetry Complete Course — Zero to Production & OTCA Ready

> A hands-on, practical OpenTelemetry course for DevOps, SRE, Platform, and Software Engineers.
> **No cloud bills.** Every example runs locally using standard open-source telemetry tools: OpenTelemetry Collector Contrib, Jaeger v2, Prometheus, Grafana, Loki, and Tempo on Docker Compose and Minikube.

---

### What makes this course different

- **16 modular, progressive modules** taking you from telemetry fundamentals to production-grade distributed architectures.
- **OTCA Exam-Aligned**: Comprehensive, weight-proportional coverage of all 4 Linux Foundation OpenTelemetry Certified Associate domains (Fundamentals 18%, API/SDK 46%, Collector 26%, Maintaining & Debugging 10%).
- **Dual-Language First**: Every instrumentation concept includes parallel **Python** and **Java** code examples.
- **Dual-Runtime Parity**: Run on **Docker Compose** or **Minikube** (Kubernetes manifests + OTel Operator).
- **Latest tool versions**: Pinned to the newest stable releases (OTel Collector `0.160.0`, Jaeger v2 `2.20.0`, Prometheus `3.14.0`, Grafana `13.2.1`).
- **Modern Semantic Conventions (v1.28+)**: Learn modern stable standards (`http.request.method`, `server.address`, etc.) instead of deprecated legacy attributes.
- **Challenges in key modules**: Problem-only challenge directories that test your ability to build from specifications.
- **Dedicated OTCA Prep Suite**: Domain review notes, sample questions, and a full mock exam in [`otca-prep/`](./otca-prep/).
- **[CHEATSHEET.md](./CHEATSHEET.md)**: Single-page field guide covering environment variables, OTLP protocol endpoints, SDK configuration, and Collector pipeline snippets.

---

## Prerequisites

| Tool | Version | Install Guide |
| ------ | --------- | --------------- |
| **Docker Engine / Desktop** | `>= 26.0` | [Docker Install](https://docs.docker.com/get-docker/) |
| **Docker Compose** | `>= 2.24` | Bundled with Docker Desktop |
| **Python** | `>= 3.11` | [python.org](https://www.python.org/downloads/) |
| **Java JDK** | `17` or `21 LTS` | [Eclipse Temurin](https://adoptium.net/) or SDKMAN |
| **Minikube** | `>= 1.38.0` | [Minikube Start Guide](https://minikube.sigs.k8s.io/docs/start/) |
| **kubectl** | `>= 1.35.0` | [kubectl Install](https://kubernetes.io/docs/tasks/tools/) |
| **Helm CLI** | `>= 3.17.0` | [Helm Install](https://helm.sh/docs/intro/install/) |
| **Git** | `>= 2.x` | Pre-installed on most systems |
| **curl / jq** | Any | CLI utilities for testing APIs |

---

## Pinned Component Versions

| Component | Version | Image / Package |
| ----------- | --------- | ----------------- |
| **OpenTelemetry Collector Contrib** | `0.160.0` | `otel/opentelemetry-collector-contrib:0.160.0` |
| **OpenTelemetry Python SDK** | `1.44.0` | `opentelemetry-api==1.44.0`, `opentelemetry-sdk==1.44.0` |
| **OpenTelemetry Java SDK** | `1.65.0` | `io.opentelemetry:opentelemetry-bom:1.65.0` |
| **OpenTelemetry Java Agent** | `2.31.1` | `opentelemetry-javaagent.jar:2.31.1` |
| **OpenTelemetry K8s Operator** | `0.158.0` | `ghcr.io/open-telemetry/opentelemetry-operator:0.158.0` |
| **Jaeger (v2 Collector-Engine)** | `2.20.0` | `jaegertracing/jaeger:2.20.0` |
| **Prometheus** | `3.14.0` | `prom/prometheus:v3.14.0` |
| **Grafana** | `13.2.1` | `grafana/grafana:13.2.1` |
| **Grafana Tempo** | `3.0.3` | `grafana/tempo:3.0.3` |
| **Grafana Loki** | `3.7.7` | `grafana/loki:3.7.7` |

---

## Learning Path & OTCA Alignment

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. FUNDAMENTALS (18% OTCA Weight)                                           │
│    Module 01: Introduction & Setup (Architecture, Components, First Trace)  │
│    Module 02: Observability Fundamentals (Signals, MTTD/MTTR, SLI/SLO)      │
│    Module 03: Telemetry Data, Modern Semantic Conventions & Analysis        │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│ 2. API & SDK DEEP DIVE (46% OTCA Weight)                                    │
│    Module 04: API/SDK Split & Three Instrumentation Approaches              │
│    Module 05: Data Model, Resources & OTLP Wire Formats (gRPC / HTTP)       │
│    Module 06: Traces, Spans & Context Propagation (Baggage) [Challenge]    │
│    Module 07: Metrics, Instruments, Views & Exemplars [Challenge]           │
│    Module 08: Logs Data Model, Log Appender Bridges & Trace Correlation     │
│    Module 09: SDK Pipelines, Composability, Samplers & Processors [Challenge│
│    Module 10: Zero-Code / Auto-Instrumentation & Agents (JVM + Python)      │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│ 3. OPENTELEMETRY COLLECTOR (26% OTCA Weight)                                │
│    Module 11: Collector Fundamentals (Receivers, Processors, Exporters) [Ch]│
│    Module 12: Deployment Patterns (Agent, Gateway, DaemonSet, Sidecar)      │
│    Module 13: Scaling & Transforming Data (OTTL, Tail Sampling, Routing) [Ch│
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│ 4. OPERATIONS, CAPSTONE & CERTIFICATION (10% OTCA Weight + Practical Capstone│
│    Module 14: Maintaining & Debugging Pipelines (Diagnosis, Leak/Loss, Fixes│
│    Module 15: Distributed Capstone App (Multi-Service + Queue + LGTM)       │
│    Module 16: OTCA Exam Prep (Per-Domain Notes, Practice Quizzes, Mock Exam)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Course Modules

| # | Module | Folder | OTCA Domain | What You'll Learn |
| --- | -------- | -------- | ------------- | ------------------- |
| 01 | [Introduction & Setup](./01-introduction/) | `01-introduction/` | Fundamentals (18%) | What is OpenTelemetry, core specification, spinning up the local telemetry stack, your first end-to-end trace. |
| 02 | [Observability Fundamentals](./02-observability-fundamentals/) | `02-observability-fundamentals/` | Fundamentals (18%) | Monitoring vs. Observability, the three core signals + baggage, MTTD/MTTR/MTBF, SLIs, SLOs, and Error Budgets. |
| 03 | [Semantic Conventions & Data Model](./03-semantic-conventions/) | `03-semantic-conventions/` | Fundamentals (18%) | Modern stable semantic conventions (v1.28+), resource attributes, scopes, and analytical outcomes. |
| 04 | [API/SDK Architecture & Approaches](./04-api-sdk-architecture/) | `04-api-sdk-architecture/` | API/SDK (46%) | The API vs. SDK architectural boundary, no-op defaults, code-based (manual), library, and zero-code approaches. |
| 05 | [Data Model & OTLP](./05-data-model-and-otlp/) | `05-data-model-and-otlp/` | API/SDK (46%) | OTLP specification, payload schemas, OTLP/gRPC (4317) vs. OTLP/HTTP (4318) payloads, and wire format analysis. |
| 06 | [Traces & Context Propagation](./06-traces-and-context-propagation/) | `06-traces-and-context-propagation/` | API/SDK (46%) | Spans, span links, status codes, W3C TraceContext, distributed propagation, and Baggage. *(Includes Challenge)* |
| 07 | [Metrics & Instruments](./07-metrics/) | `07-metrics/` | API/SDK (46%) | Synchronous & asynchronous instruments, Counter, UpDownCounter, Histogram, Gauge, Views, and Exemplars. *(Includes Challenge)* |
| 08 | [Logs & Correlation](./08-logs/) | `08-logs/` | API/SDK (46%) | Log data model, bridging standard loggers (Logback/Log4j2, Python logging), and trace-log correlation. |
| 09 | [SDK Pipelines & Composability](./09-sdk-pipelines/) | `09-sdk-pipelines/` | API/SDK (46%) | Tracer/Meter providers, Head samplers (ParentBased, TraceIdRatioBased), SpanProcessors, Exporters, and 3 config methods. *(Includes Challenge)* |
| 10 | [Zero-Code & Auto-Instrumentation](./10-auto-instrumentation/) | `10-auto-instrumentation/` | API/SDK (46%) | OpenTelemetry Java Agent runtime injection, Python auto-instrumentation, and Kubernetes Operator automated injection. |
| 11 | [Collector Fundamentals](./11-collector-fundamentals/) | `11-collector-fundamentals/` | Collector (26%) | Components: Receivers, Processors, Exporters, Connectors, Extensions, and telemetry pipelines. *(Includes Challenge)* |
| 12 | [Collector Deployment Patterns](./12-collector-deployment-patterns/) | `12-collector-deployment-patterns/` | Collector (26%) | Architectural topology: Host Agent, Gateway cluster, Kubernetes DaemonSet, and Pod Sidecar patterns. |
| 13 | [Collector Scaling & OTTL](./13-collector-scaling-and-ottl/) | `13-collector-scaling-and-ottl/` | Collector (26%) | OpenTelemetry Transformation Language (OTTL), batching, memory limiter, tail-based sampling, and load-balancing exporter. *(Includes Challenge)* |
| 14 | [Maintaining & Debugging Pipelines](./14-maintaining-and-debugging/) | `14-maintaining-and-debugging/` | Maintaining (10%) | Troubleshooting broken pipelines, diagnosing context propagation loss, Collector debug logging/zPages, and schema evolution. |
| 15 | [Capstone: Distributed App](./15-capstone-distributed-app/) | `15-capstone-distributed-app/` | Practical (All) | Production-style distributed app: Frontend (Python) + Queue (Redis) + Worker (Java) instrumented for all signals across full LGTM stack. |
| 16 | [OTCA Certification Prep](./16-otca-exam-prep/) | `16-otca-exam-prep/` | All Domains | Domain review summaries (18/46/26/10), topic cheat notes, practice quizzes, and a 60-question mock exam with rationales. |

---

## How to Run the Local Telemetry Stack

### Option A: Docker Compose (Default)

```bash
# Navigate to the course root
cd open-telemetry/course

# Start the full local telemetry stack
cd stack/docker
docker compose up -d

# Verify services are healthy
docker compose ps
```

**Service UIs & Ports:**

- **Grafana (Dashboards & LGTM Unified UI):** [http://localhost:3000](http://localhost:3000) (admin / admin)
- **Jaeger v2 UI:** [http://localhost:16686](http://localhost:16686)
- **Prometheus UI:** [http://localhost:9090](http://localhost:9090)
- **OpenTelemetry Collector OTLP/gRPC Ingestion:** `localhost:4317`
- **OpenTelemetry Collector OTLP/HTTP Ingestion:** `localhost:4318`
- **Collector Health Check:** `http://localhost:13133`
- **Collector zPages:** `http://localhost:55679/debug/servicez`

### Option B: Minikube / Kubernetes

```bash
cd open-telemetry/course/stack/minikube

# Start Minikube cluster if not running
minikube start --cpus=4 --memory=6144

# Apply the local telemetry backend manifests
kubectl apply -f manifests/

# Verify pods are running
kubectl get pods -n observability
```

---

## Automated Testing & Linting

This course includes an automated test runner and markdown linting suite to guarantee that all runnable code, exercises, collector configurations, and documentation remain 100% functional and well-formatted.

### Running the Top-Level Test Runner (`test-all.sh`)

The top-level test runner [`test-all.sh`](./test-all.sh) executes 5 verification stages across the entire course:

1. **Markdown Formatting**: Lints all `.md` files using `npx markdownlint-cli2`.
2. **Collector & Manifest YAML Validation**: Validates syntax across all 20 Docker, Minikube, and Collector configuration files via Python `yaml.safe_load_all`.
3. **Python Syntax Verification**: Compiles all `.py` files across all modules with `python3 -m py_compile`.
4. **Python Executions & Unit Tests**: Runs sample pipelines and test suites (e.g. pytest in Module 03, context propagation in Module 06, instruments in Module 07, logs correlation in Module 08, pipelines in Module 09, and diagnostic scripts in Module 14) via `uv`.
5. **Java Maven Project Compilation**: Compiles all 11 Java projects with `mvn test-compile -q` against the pinned OpenTelemetry SDK BOM `1.65.0`.

To run the complete verification suite:

```bash
# Navigate to course root
cd open-telemetry/course

# Ensure runner has execution permissions
chmod +x test-all.sh

# Run the full test suite
./test-all.sh
```

### Markdown Linting (`.markdownlint-cli2.yaml`)

Documentation quality is enforced using the local Node library `markdownlint-cli2` configured by [`.markdownlint-cli2.yaml`](./.markdownlint-cli2.yaml).

**Check all markdown files:**

```bash
cd open-telemetry/course
npx markdownlint-cli2 "**/*.md"
```

**Automatically fix formatting issues:**

```bash
cd open-telemetry/course
npx markdownlint-cli2 --fix "**/*.md"
```

The [`.markdownlint-cli2.yaml`](./.markdownlint-cli2.yaml) configuration disables rules that conflict with rich technical docs (`MD013` line length, `MD033` inline HTML, `MD024` duplicate headings, `MD036` bold emphasis, `MD060` table column style, and `MD001` heading increments) while strictly enforcing code block languages (`MD040`).

---

## Quick Reference & Useful Links

- **[CHEATSHEET.md](./CHEATSHEET.md)** — All-in-one quick reference for OTel env vars, OTLP endpoints, SDK initialization, and Collector configurations.
- [OpenTelemetry Official Documentation](https://opentelemetry.io/docs/)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Linux Foundation OTCA Exam Details](https://training.linuxfoundation.org/certification/opentelemetry-certified-associate-otca/)

---

**License:** MIT — free for learning, self-study, and classroom teaching.
