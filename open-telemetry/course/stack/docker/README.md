# Docker Telemetry Stack

> Unified local observability environment featuring OpenTelemetry Collector Contrib, Jaeger v2, Prometheus 3, Grafana 13, Loki, and Tempo.

## Services & Endpoints

| Service | Port | Description |
| --------- | ------ | ------------- |
| **Grafana UI** | `http://localhost:3000` | Unified UI (Credentials: `admin` / `admin`) |
| **Jaeger v2 UI** | `http://localhost:16686` | Distributed traces visualizer |
| **Prometheus UI** | `http://localhost:9090` | Metrics queries and Prometheus expressions |
| **OTel Collector gRPC** | `localhost:4317` | Standard OTLP gRPC endpoint |
| **OTel Collector HTTP** | `localhost:4318` | Standard OTLP HTTP endpoint (`/v1/traces`, `/v1/metrics`, `/v1/logs`) |
| **Collector Internal Metrics** | `http://localhost:8888/metrics` | Self-monitoring metrics |
| **Collector Prometheus Exporter** | `http://localhost:8889/metrics` | Pipeline telemetry exposed for scraping |
| **Collector Health Check** | `http://localhost:13133` | Health extension endpoint |
| **Collector zPages** | `http://localhost:55679/debug/servicez` | Debug zPages |

## Quick Commands

```bash
# Start all telemetry backends in the background
docker compose up -d

# Check running status
docker compose ps

# View OpenTelemetry Collector debug output (payload batches)
docker compose logs -f collector

# Stop and clean up containers
docker compose down
```
