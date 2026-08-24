# Highlight.io — Docker Compose Setup

Developer-first observability platform (session replay, error tracking, logs, traces) for benchmarking.

## Architecture

```
OTLP gRPC (:4317) ─┐
                    ├→ Highlight Collector → ClickHouse (telemetry)
OTLP HTTP (:4318) ─┘         ↓                → Kafka (queuing)
                         Backend Service       → PostgreSQL (metadata)
                              ↓                → Redis (cache)
                         Frontend UI (:3000)
```

## Quick Start

Highlight.io requires cloning the official repo (it builds the collector from source):

```bash
./scripts/setup.sh
cd highlight-install/docker
docker compose -f compose.hobby.yml up -d
# Wait 3-5 minutes for all services
../../scripts/check-health.sh
```

Or use the official one-liner:
```bash
curl -fsS https://raw.githubusercontent.com/highlight/highlight/main/deploy/hobby.sh | bash
```

## Access

| Endpoint | URL |
|:---------|:----|
| Highlight UI | http://localhost:3000 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Services

| Service | Role |
|:--------|:-----|
| collector | Custom OTel-based collector (OTLP ingestion) |
| clickhouse | Telemetry storage (logs, traces, sessions) |
| kafka + zookeeper | Event queuing |
| postgres | Metadata (users, projects) |
| redis | Cache |
| backend | API + data processing |
| frontend | UI |

## Benchmark Notes

- **Note:** Highlight.io was acquired by LaunchDarkly in 2025 — open-source repo remains active
- Developer-first: strong on session replay + frontend error tracking
- Backend observability (logs/traces) is the focus for this benchmark
- Requires building collector from source (Dockerfile) — no pre-built OTLP image
- Heavy stack: Kafka + Zookeeper + ClickHouse + PostgreSQL + Redis
- 8GB RAM minimum, 16 CPUs recommended
- Session replay features won't be exercised in benchmarks (backend observability only)
- Multi-arch: verify ARM64 support for hobby deployment

## Installation guide

See the [installation mode index](install/README.md). The repository intentionally uses Highlight's upstream self-hosting assets rather than duplicating the multi-service deployment.
