# ClickStack — browser local mode

ClickStack provides a local-mode distribution that bundles ClickHouse, HyperDX, the OpenTelemetry Collector, and MongoDB. HyperDX authentication is disabled in this mode.

## Run

```bash
docker run --detach --name clickstack-local \
  -p 8080:8080 \
  -p 4317:4317 \
  -p 4318:4318 \
  clickhouse/clickstack-local:latest
```

The official UI-only command maps port `8080`. Ports `4317` and `4318` are also mapped above so applications and telemetry generators running on the host can send OpenTelemetry data to the bundled collector.

Follow the startup logs until ClickHouse is ready, then press `Ctrl+C` to leave the log stream. The detached ClickStack container will continue running.

```bash
docker logs --follow clickstack-local
```

Use `docker stop clickstack-local` to stop it and `docker start clickstack-local` to run it again. Run only one ClickStack deployment at a time because the deployment modes use the same host ports.

## Endpoints

| Purpose | Endpoint |
|:--------|:---------|
| HyperDX UI | <http://localhost:8080> |
| OTLP/gRPC | `http://localhost:4317` |
| OTLP/HTTP base URL | `http://localhost:4318` |
| OTLP/HTTP traces | `http://localhost:4318/v1/traces` |
| OTLP/HTTP metrics | `http://localhost:4318/v1/metrics` |
| OTLP/HTTP logs | `http://localhost:4318/v1/logs` |

For an instrumented application running directly on the host, use one of these configurations:

```bash
# OTLP/HTTP
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

# Or OTLP/gRPC
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
```

## Generate sample OpenTelemetry data

On macOS, run the official OpenTelemetry `telemetrygen` image and send data to the collector through `host.docker.internal`:

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

Change `--duration` and `--rate` to control the volume. Use `--duration inf` to generate data until you press `Ctrl+C`, then open <http://localhost:8080> to inspect it.

Use this mode for demos, debugging, and development only. Follow the official [local mode deployment guide](https://clickhouse.com/docs/clickstack/deployment/local-mode-only).
