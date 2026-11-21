# Coroot — Docker Compose + K8s/Helm Setup

eBPF-based zero-instrumentation observability with ClickHouse storage.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Node Agent (eBPF, privileged, Linux only)  │
│    → auto-discovers services & connections  │
└──────────────────────┬──────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│  Coroot Server (:8080)                       │
│    - Built-in OTLP receiver (traces)        │
│    - Service map (auto-generated from eBPF) │
│    - Anomaly detection                       │
├──────────────────────────────────────────────┤
│  Prometheus (:9090) ← node-agent metrics    │
│  ClickHouse (:9000) ← traces, logs, profiles│
└──────────────────────────────────────────────┘
```

## Deployment Options

### Docker Compose (`docker/`)

```bash
cd docker
cp .env.example .env
docker compose up -d          # macOS: server only (no eBPF)
docker compose --profile linux up -d  # Linux: full stack with eBPF node-agent
../scripts/check-health.sh
```

### Kubernetes/Helm (`k8s/`)

```bash
cd k8s
./install.sh
kubectl port-forward -n coroot service/coroot-coroot 8080:8080
```

## Access

| Endpoint | URL |
|:---------|:----|
| Coroot UI | http://localhost:8080 |
| OTLP (built-in) | http://localhost:8080 (Coroot accepts OTLP natively) |

## Services (Docker)

| Service | Image | Role |
|:--------|:------|:-----|
| coroot | `ghcr.io/coroot/coroot` | Server + UI + OTLP receiver |
| node-agent | `ghcr.io/coroot/coroot-node-agent` | eBPF metrics (Linux only) |
| cluster-agent | `ghcr.io/coroot/coroot-cluster-agent` | DB metrics scraper |
| prometheus | `prom/prometheus:v2.53.5` | Metrics storage |
| clickhouse | `clickhouse/clickhouse-server:24.3` | Traces, logs, profiles |

## OTLP Ingestion

Coroot has a built-in OTLP receiver on port 8080. Send traces directly:
- **gRPC:** `localhost:8080`
- **HTTP:** `http://localhost:8080/v1/traces`

No separate OTel Collector needed.

## Benchmark Notes

- **node-agent requires Linux kernel 5.8+** — skipped on macOS via Docker Compose profiles
- eBPF auto-discovers all services and their network connections (zero-instrumentation)
- ClickHouse stores traces, logs, and continuous profiling data
- Prometheus stores time-series metrics from node-agent
- For macOS validation: Coroot server + OTLP tracing works; eBPF metrics won't populate
- K8s variant provides full eBPF support via DaemonSet (needed for Phase 2 benchmarks)
- Multi-arch: Coroot images support both ARM64 + AMD64
