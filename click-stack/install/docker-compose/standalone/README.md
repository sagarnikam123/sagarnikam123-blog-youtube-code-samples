# ClickStack — Docker Compose Setup

ClickHouse-native observability stack (ClickHouse + HyperDX UI + OTel Collector) for benchmarking.

## Architecture

```
OTLP gRPC (:4317) ─┐
                    ├→ ClickStack OTel Collector → ClickHouse (otel_logs, otel_traces, otel_metrics_*)
OTLP HTTP (:4318) ─┘                                  ↑
                                        HyperDX (UI + API) ──→ MongoDB (app state)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| ch-server | `clickhouse/clickhouse-server:26.1-alpine` | Telemetry storage |
| otel-collector | `clickhouse/clickstack-otel-collector:2` | OTLP ingestion → ClickHouse |
| app (HyperDX) | `hyperdx/hyperdx:2` | UI + API + dashboards |
| db (MongoDB) | `mongo:5.0.32-focal` | Application state persistence |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| HyperDX UI | http://localhost:8080 |
| HyperDX API | http://localhost:8000 |
| ClickHouse HTTP | http://localhost:8123 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |
| OTel Collector metrics | http://localhost:8888 |

## Benchmark Notes

- Based on official [ClickHouse/ClickStack](https://github.com/ClickHouse/ClickStack) repo
- Uses Map(LowCardinality(String), String) schema (recommended for observability)
- OTel Collector uses OpAMP protocol for dynamic config from HyperDX
- DEFAULT_SOURCES pre-configures log/trace/metric/session sources in HyperDX
- No authentication enabled (benchmark isolation)
- ClickHouse configured with `access_management=1` for DDL operations
- Multi-arch: ClickHouse alpine image supports ARM64 + AMD64
