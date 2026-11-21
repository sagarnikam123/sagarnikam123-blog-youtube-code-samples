# ClickStack — Docker all-in-one

ClickStack publishes an all-in-one Docker image containing ClickHouse, HyperDX, the OpenTelemetry Collector, and MongoDB.

## Run

```bash
docker run --detach --name clickstack-all-in-one \
  -p 8080:8080 \
  -p 4317:4317 \
  -p 4318:4318 \
  clickhouse/clickstack-all-in-one:latest
```

Follow the startup logs until ClickHouse is ready, then press `Ctrl+C` to leave the log stream. The detached ClickStack container will continue running.

```bash
docker logs --follow clickstack-all-in-one
```

Use `docker stop clickstack-all-in-one` to stop it and `docker start clickstack-all-in-one` to run it again. Run only one ClickStack deployment at a time because the deployment modes use the same host ports.

## Endpoints

| Purpose | Endpoint |
|:--------|:---------|
| HyperDX UI | <http://localhost:8080> |
| OTLP/gRPC | `http://localhost:4317` |
| OTLP/HTTP base URL | `http://localhost:4318` |
| OTLP/HTTP traces | `http://localhost:4318/v1/traces` |
| OTLP/HTTP metrics | `http://localhost:4318/v1/metrics` |
| OTLP/HTTP logs | `http://localhost:4318/v1/logs` |

For an instrumented application running directly on the host, use one of these environment variables:

```bash
# OTLP/HTTP
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Or OTLP/gRPC
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
```

## Generate sample OpenTelemetry data

Use the official OpenTelemetry `telemetrygen` image to send random data over OTLP/gRPC. On macOS, a generator container reaches the collector exposed on the host through `host.docker.internal`.

```bash
# Traces: 10 per second for 30 seconds
docker run --rm \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint host.docker.internal:4317 --otlp-insecure \
  --duration 30s --rate 10

# Metrics: 10 per second for 30 seconds
docker run --rm \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  metrics --otlp-endpoint host.docker.internal:4317 --otlp-insecure \
  --duration 30s --rate 10

# Logs: 10 per second for 30 seconds
docker run --rm \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  logs --otlp-endpoint host.docker.internal:4317 --otlp-insecure \
  --duration 30s --rate 10
```

Change `--duration` and `--rate` to control the volume. Use `--duration inf` to keep generating data until you press `Ctrl+C`. Then open <http://localhost:8080> and search for the generated telemetry in HyperDX.

For persistent data, mount the paths documented by ClickHouse: `/data/db`, `/var/lib/clickhouse`, and `/var/log/clickhouse-server`. Pin the image tag for repeatable deployments; this mode is intended for demos and local testing, not production scaling.

Official guide: [ClickStack all-in-one](https://clickhouse.com/docs/clickstack/deployment/all-in-one).
