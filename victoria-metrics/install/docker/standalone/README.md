# VictoriaMetrics — Docker single-node

Run VictoriaMetrics single-node with one `docker run` command.

## Run

```bash
docker run -d --name victoriametrics \
  -v $(pwd)/victoria-metrics-data:/victoria-metrics-data \
  -p 8428:8428 \
  victoriametrics/victoria-metrics:v1.150.0 \
  --selfScrapeInterval=10s \
  -storageDataPath=/victoria-metrics-data
```

Access vmui at <http://localhost:8428/vmui>.

## Notes

- Single container, no external dependencies.
- Pin image tag for reproducible deployments.
- For the full observability stack (VictoriaLogs + VictoriaTraces + Grafana), use the [Docker Compose benchmark](../../docker-compose/standalone/).

Official guide: [VictoriaMetrics Quick Start — Docker](https://docs.victoriametrics.com/victoriametrics/quick-start/#starting-victoriametrics-single-node-via-docker).
