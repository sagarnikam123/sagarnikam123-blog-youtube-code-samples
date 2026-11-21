# Parseable — Docker Compose standalone

Single-node Parseable with local disk storage for benchmarking.

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Parseable UI | http://localhost:8000 |
| OTLP HTTP logs | http://localhost:8000/v1/logs |
| OTLP HTTP metrics | http://localhost:8000/v1/metrics |
| OTLP HTTP traces | http://localhost:8000/v1/traces |
| Login | admin / admin |

## Notes

- Standalone mode: single binary, local disk Parquet storage.
- All signals stored as open-format Apache Parquet.
- No object storage required for this profile.
- Phase 1 benchmark deployment.

Official source: [Parseable installation](https://www.parseable.com/docs/self-hosted/installation).
