# Grafana LGTM Stack — Unified Docker Compose Setup

Composable best-of-breed stack: **L**oki (logs) + **G**rafana (UI) + **T**empo (traces) + **M**imir (metrics).

## Architecture

```
                    ┌→ Mimir (metrics, :9009)  ─┐
OTLP gRPC (:4317) ─┤                            ├→ Grafana (:3000)
OTLP HTTP (:4318) ─┤→ Loki  (logs,    :3100)  ─┤
   (OTel Collector) └→ Tempo (traces,  :3200)  ─┘
                              │
                              └→ Mimir (metrics_generator remote_write)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| mimir | `grafana/mimir:2.16.0` | Metrics storage (monolithic mode) |
| loki | `grafana/loki:3.5.0` | Log storage (monolithic mode) |
| tempo | `grafana/tempo:2.7.2` | Trace storage (monolithic mode) |
| otel-collector | `otel/opentelemetry-collector-contrib:0.115.0` | OTLP fan-out to backends |
| grafana | `grafana/grafana:12.1.1` | Visualization + pre-provisioned datasources |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Grafana UI | http://localhost:3000 (anonymous admin, no login required) |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Pre-provisioned Datasources

Grafana starts with all three datasources connected and cross-linked:

- **Mimir** — default Prometheus-compatible datasource, exemplar links to Tempo
- **Loki** — derived fields extract traceId → link to Tempo
- **Tempo** — trace-to-logs (Loki), trace-to-metrics (Mimir), service map, node graph

## Benchmark Notes

- All backends run in monolithic mode (single-node, filesystem storage)
- Tempo metrics_generator produces span-metrics and service-graphs → pushes to Mimir
- OTel Collector uses `otlphttp` exporters to send OTLP natively to all backends
- No auth (anonymous admin in Grafana, no tenant in backends)
- Memory limits configurable via `.env` (2GB per backend default)
- Multi-arch: all Grafana images support ARM64 + AMD64
