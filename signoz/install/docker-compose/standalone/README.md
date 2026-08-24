# SigNoz — Docker Compose Setup

Self-contained SigNoz deployment for observability benchmarking.

## Architecture

```
OTLP gRPC/HTTP → OTel Collector → ClickHouse (traces/metrics/logs)
                                     ↑
                  SigNoz Server ──────┘ (queries + UI)
                       ↕
                  PostgreSQL (metadata)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| clickhouse-keeper | `clickhouse/clickhouse-keeper:25.5.6` | Coordination |
| clickhouse | `clickhouse/clickhouse-server:25.5.6` | Telemetry storage |
| postgres | `postgres:16` | Metadata store |
| schema-migrator | `signoz/signoz:v0.130.0` | One-shot DB schema setup |
| otel-collector | `signoz/signoz-otel-collector:v0.111.10` | OTLP ingestion |
| signoz | `signoz/signoz:v0.130.0` | API + UI |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| SigNoz UI | http://localhost:3301 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Benchmark Notes

- All telemetry flows via OTLP → OTel Collector → ClickHouse
- No auth enabled (benchmark isolation rules)
- Memory limits configurable via `.env` (default: 4GB ClickHouse, 2GB SigNoz)
- Boot order enforced: keeper → clickhouse → migrator → collector + server
