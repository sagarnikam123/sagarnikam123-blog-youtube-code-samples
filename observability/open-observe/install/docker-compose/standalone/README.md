# OpenObserve — Docker Compose Setup

Single-binary observability platform (Rust) for benchmarking. Natively accepts OTLP — no separate collector needed.

## Architecture

```
OTLP gRPC (:5081) ─┐
                    ├→ OpenObserve (single binary) → local disk storage
OTLP HTTP (:5082) ─┘
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| openobserve | `public.ecr.aws/zinclabs/openobserve:v0.92.2` | All-in-one: ingestion + storage + query + UI |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| OpenObserve UI | http://localhost:5080 |
| OTLP gRPC | localhost:5081 |
| OTLP HTTP | localhost:5082 |
| Login | root@example.com / Complexpass#123 |

## OTLP Ingestion Endpoints

OpenObserve natively supports OTLP without a separate collector:

- **gRPC:** `localhost:5081` (standard OTLP gRPC)
- **HTTP Traces:** `http://localhost:5082/v1/traces`
- **HTTP Metrics:** `http://localhost:5082/v1/metrics`
- **HTTP Logs:** `http://localhost:5082/v1/logs`

Note: HTTP endpoints require Basic Auth header (`Authorization: Basic base64(email:password)`).

## Benchmark Notes

- Simplest deployment of all platforms (single container)
- No auth overhead in OTLP gRPC path
- HTTP OTLP requires Basic Auth
- Telemetry reporting disabled (`ZO_TELEMETRY_ENABLED=false`)
- Local disk storage (no S3/object-store)
- Multi-arch: works on both ARM64 (Apple Silicon) and AMD64
