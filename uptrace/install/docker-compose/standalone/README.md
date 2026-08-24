# Uptrace — Docker Compose Setup

Lightweight OTel-native APM built on ClickHouse for benchmarking.

## Architecture

```
OTLP gRPC (:4317) ─┐                    ┌→ ClickHouse (spans/logs/metrics)
                    ├→ OTel Collector → Uptrace ─┤
OTLP HTTP (:4318) ─┘    (with DSN header)       ├→ PostgreSQL (metadata)
                                                  └→ Redis (cache)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| clickhouse | `clickhouse/clickhouse-server:26.3` | Telemetry storage |
| postgres | `postgres:17-alpine` | Metadata (users, projects, alerts) |
| redis | `redis:7-alpine` | Query cache |
| uptrace | `uptrace/uptrace:2.1.0-beta.5` | API + UI |
| otel-collector | `otel/opentelemetry-collector-contrib:0.123.0` | OTLP ingestion |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Uptrace UI | http://localhost:14318 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |
| Login | admin@uptrace.local / admin |

## OTLP DSN

Uptrace uses DSN-based authentication for OTLP:
```
http://project1_secret@localhost:14318?grpc=14317
```

The OTel Collector forwards telemetry with the `uptrace-dsn` header attached.

## Benchmark Notes

- Based on official [uptrace/uptrace](https://github.com/uptrace/uptrace) Docker example
- ClickHouse with ZSTD(1) compression for storage efficiency
- Single project pre-seeded (`Benchmark` project with token `project1_secret`)
- OTel Collector acts as the external OTLP endpoint (adds DSN header)
- No TLS, no email — benchmark isolation
- Multi-arch: ClickHouse + Postgres + Redis all support ARM64 + AMD64
- Uptrace image: check Docker Hub for ARM64 availability
