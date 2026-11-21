# Gatus — Docker Compose standalone

Single-node Gatus with an optional PostgreSQL backend for persistent history.

## Architecture

```
Browser (:8080) → gatus (Go binary) ──(in-memory by default)
                                     └──(optional) → postgres  (persistent history)
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| gatus | `twinproduction/gatus:v5.37.0` | Probes + dashboard + API + metrics |
| postgres | `postgres:16-alpine` | Optional persistent history (`--profile postgres`) |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

Edit monitors in [`../../../configs/config.yaml`](../../../configs/config.yaml). Open <http://localhost:8080>.

## Enable persistent history (PostgreSQL)

```bash
# 1. Set the storage block in ../../../configs/config.yaml:
#    storage:
#      type: postgres
#      path: "postgres://gatus:gatus@postgres:5432/gatus?sslmode=disable"
# 2. Start with the postgres profile
docker compose --profile postgres up -d
```

## Access

| Endpoint | URL |
|:---------|:----|
| Gatus dashboard | http://localhost:8080 |
| Health | http://localhost:8080/health |
| Prometheus metrics | http://localhost:8080/metrics |

## Notes

- Default storage is in-memory — history resets on restart. Use the PostgreSQL profile (or SQLite with a mounted volume) to persist.
- Config changes: edit `config.yaml` and `docker compose restart gatus`.
- Pin `GATUS_VERSION` in `.env` for reproducible deployments.
- Multi-arch image: ARM64 and AMD64.

Official source: [Gatus configuration](https://github.com/TwiN/gatus#configuration).
