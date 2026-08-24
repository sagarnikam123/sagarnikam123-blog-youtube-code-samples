# Grafana LGTM — Docker all-in-one (grafana/otel-lgtm)

Grafana publishes `grafana/otel-lgtm`, a single Docker image bundling the OpenTelemetry Collector, Loki, Mimir (via Prometheus), Tempo, Pyroscope, and Grafana. Intended for development, demos, and testing — not production.

## Run

```bash
docker run -d --name lgtm \
  -p 3000:3000 \
  -p 4317:4317 \
  -p 4318:4318 \
  grafana/otel-lgtm:latest
```

## Access

| Endpoint | URL |
|:---------|:----|
| Grafana UI | http://localhost:3000 |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

## Notes

- All components run in one container — not production-suitable.
- No persistent storage by default; mount volumes if needed.
- Pre-provisioned datasources for Loki, Mimir, Tempo, and Pyroscope.
- Pin image tag for reproducibility.

Official sources:
- [grafana/otel-lgtm documentation](https://grafana.com/docs/opentelemetry/docker-lgtm/)
- [Docker Hub](https://hub.docker.com/r/grafana/otel-lgtm)
- [GitHub — docker-otel-lgtm](https://github.com/grafana/docker-otel-lgtm)
