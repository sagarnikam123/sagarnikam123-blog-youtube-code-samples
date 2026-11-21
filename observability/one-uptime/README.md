# OneUptime — Docker Compose Setup

Broader reliability platform (monitoring, incidents, on-call, status pages) with built-in OTLP observability.

## Architecture

OneUptime is a complex platform with many microservices:
```
OTLP gRPC (:4317) ─┐
                    ├→ Ingest Service → ClickHouse (telemetry)
OTLP HTTP (:4318) ─┘                → PostgreSQL (metadata)
                                     → Redis (cache/queues)
                    Dashboard UI (:80)
```

## Quick Start

OneUptime uses the official Docker Compose bundle for its single-server installation:

```bash
./scripts/setup.sh
cd install/docker-compose/standalone/oneuptime-install
npm start
```

In another shell, after services initialize:

```bash
cd one-uptime
./scripts/check-health.sh
```

For Kubernetes deployments, use the [Helm installation modes](install/helm/).

## Access

| Endpoint | URL |
|:---------|:----|
| OneUptime UI | http://localhost (register on first use) |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Services (from official compose)

Key services include:
- **app** — Main dashboard/API (Node.js)
- **ingest** — OTLP telemetry ingestion
- **probe** — Uptime monitoring probes
- **worker** — Background job processing
- **clickhouse** — Telemetry storage (logs, traces, metrics)
- **postgres** — Metadata (users, projects, incidents, alerts)
- **redis** — Cache and job queues

## Benchmark Notes

- **Heaviest compose of all platforms** — many microservices, 8GB RAM minimum
- Uses official `release` branch from GitHub (daily releases)
- OTLP natively supported via ingest service
- Includes non-observability features (status pages, on-call, incidents)
- First start requires account registration via UI
- Multi-arch: check official images for ARM64 support (most are AMD64 + ARM64)
- For benchmark: only telemetry features (logs/traces/metrics) are exercised

## Installation guide

See the [installation mode index](install/README.md). The repository intentionally uses the upstream Docker Compose bundle rather than recreating OneUptime's large multi-service stack.
