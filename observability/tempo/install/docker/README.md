# Tempo — Docker standalone

Run Tempo in monolithic mode with a single Docker container.

## Run

```bash
docker run -d --name tempo \
  -p 3200:3200 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14268:14268 \
  -p 9411:9411 \
  -v $(pwd)/tempo.yaml:/etc/tempo/tempo.yaml:ro \
  -v tempo-data:/tmp/tempo \
  grafana/tempo:2.7.2 \
  -config.file=/etc/tempo/tempo.yaml
```

## Access

| Port | Protocol | Purpose |
|:-----|:---------|:--------|
| 3200 | HTTP | Tempo API (ready, status, TraceQL) |
| 4317 | gRPC | OTLP traces |
| 4318 | HTTP | OTLP traces |
| 14268 | HTTP | Jaeger |
| 9411 | HTTP | Zipkin |

## Docker Compose

Use the included `docker-compose.yml` for a ready-to-run single-node setup:

```bash
docker compose up -d
curl http://localhost:3200/ready
```

Official guide: [Deploy Tempo](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/).
