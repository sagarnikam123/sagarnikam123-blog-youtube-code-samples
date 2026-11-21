# VictoriaMetrics Full Stack — Docker Compose Setup

Specialized signal-specific databases: VictoriaMetrics (metrics) + VictoriaLogs (logs) + VictoriaTraces (traces) + Grafana (UI).

## Architecture

```
                    ┌→ VictoriaMetrics (:8428) ─ Prometheus remote write
OTLP gRPC (:4317) ─┤
OTLP HTTP (:4318) ─┤→ VictoriaLogs    (:9428) ─ OTLP/HTTP logs
   (OTel Collector) └→ VictoriaTraces  (:16686) ─ OTLP/gRPC traces
                              ↓
                        Grafana (:3000) ─ queries all three
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| victoriametrics | `victoriametrics/victoria-metrics:v1.149.0` | Metrics TSDB |
| victorialogs | `victoriametrics/victoria-logs:v1.52.0-victorialogs` | Log storage |
| victoriatraces | `victoriametrics/victoria-traces:v0.11.0-victorialogs` | Trace storage |
| otel-collector | `otel/opentelemetry-collector-contrib:0.115.0` | OTLP fan-out |
| grafana | `grafana/grafana:12.1.1` | Visualization |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Grafana UI | http://localhost:3000 (anonymous admin) |
| VictoriaMetrics UI | http://localhost:8428/vmui |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Signal Routing

| Signal | OTel Collector Exporter | Backend Endpoint |
|:-------|:------------------------|:-----------------|
| Metrics | `prometheusremotewrite` | `http://victoriametrics:8428/api/v1/write` |
| Logs | `otlphttp` | `http://victorialogs:9428/insert/opentelemetry` |
| Traces | `otlp` (gRPC) | `victoriatraces:4317` |

## Benchmark Notes

- Each signal has its own dedicated database (no shared backend)
- VictoriaMetrics: 30d retention, single-node mode
- VictoriaLogs: 50GB disk space limit
- VictoriaTraces: Jaeger-compatible query API at :16686
- Grafana installs `victoriametrics-logs-datasource` plugin on startup
- No auth enabled (benchmark isolation)
- Multi-arch: all VM images support ARM64 + AMD64
