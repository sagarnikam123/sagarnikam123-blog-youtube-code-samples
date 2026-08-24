# Observability Benchmark — Platform Installations

This directory contains Docker Compose setups for 12 observability platforms, ready for the [benchmark methodology](https://sagarnikam123.github.io/posts/open-source-observability-benchmark/).

## Platform Overview

### Phase 1 (Docker Compose on bare VM)

| Platform | Folder | UI Port | OTLP gRPC | OTLP HTTP |
|:---------|:-------|:--------|:-----------|:-----------|
| SigNoz | `signoz/` | 3301 | 4317 | 4318 |
| OpenObserve | `open-observe/` | 5080 | 5081 | 5082 |
| ClickStack | `click-stack/` | 8080 | 4317 | 4318 |
| Grafana LGTM | `grafana-lgtm/` | 3000 | 4317 | 4318 |
| VictoriaMetrics | `victoria-metrics/` | 3000 | 4317 | 4318 |
| Uptrace | `uptrace/` | 14318 | 4317 | 4318 |

### Phase 2 (includes K8s where needed)

| Platform | Folder | UI Port | OTLP gRPC | OTLP HTTP |
|:---------|:-------|:--------|:-----------|:-----------|
| Apache SkyWalking | `skywalking/install/docker-standalone/` | 8080 | 4317 | 4318 |
| Coroot | `coroot/docker/` | 8080 | 8080 | 8080 |
| OneUptime | `one-uptime/` | 80 | 4317 | 4318 |
| Highlight.io | `highlight-io/` | 3000 | 4317 | 4318 |
| Elastic Observability | `elastic-observability/` | 5601 | 4317 | 4318 |
| OpenSearch Observability | `opensearch-observability/` | 5601 | 4317 | 4318 |

## Quick Start (Phase 1 Compose platforms)

```bash
cd <platform-folder>
cp install/docker-compose/standalone/.env.example install/docker-compose/standalone/.env
docker compose -f install/docker-compose/standalone/docker-compose.yml up -d
./scripts/check-health.sh
```

For Phase 2 platforms or upstream-managed Compose bundles, follow the platform README and keep the health check invocation under `<platform-folder>/scripts/`.

## Validate OTLP Endpoint

```bash
# Install telemetrygen (one-time)
go install github.com/open-telemetry/opentelemetry-collector-contrib/cmd/telemetrygen@latest

# Validate any platform's OTLP endpoint
./benchmark/validate-otlp.sh localhost:4317           # gRPC
./benchmark/validate-otlp.sh --http localhost:4318    # HTTP
```

## Benchmark Isolation Rules

From the methodology:
1. Never run platforms simultaneously
2. Clean VM per run (clone base → deploy → benchmark → destroy)
3. Generator on separate machine
4. Never measure a product with itself

## Per-Platform Deliverables

Each platform keeps operational scripts at its root:
- `<platform>/scripts/check-health.sh` — verify services and OTLP endpoints
- mode-specific `docker-compose.yml` and `.env.example` files remain under that platform's `install/` directory
- `README.md` — architecture, access URLs, and mode-specific instructions

## Machine-Readable Config

`platforms.json` contains structured metadata for all platforms (ports, paths, phases) for automation scripts.
