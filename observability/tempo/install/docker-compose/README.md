# Tempo — Docker Compose (with Grafana)

Tempo monolithic mode + Grafana with pre-provisioned Tempo datasource for trace visualization.

## Start

```bash
docker compose up -d
```

## Access

| Service | URL |
|:--------|:----|
| Grafana | http://localhost:3000 (anonymous admin) |
| Tempo API | http://localhost:3200 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |
| Jaeger HTTP | localhost:14268 |
| Zipkin | localhost:9411 |

## Send test traces

```bash
# Using telemetrygen
telemetrygen traces --otlp-insecure --duration 5s
```

Then open Grafana → Explore → select Tempo datasource → search by TraceQL.

Official guide: [Deploy Tempo](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/).
