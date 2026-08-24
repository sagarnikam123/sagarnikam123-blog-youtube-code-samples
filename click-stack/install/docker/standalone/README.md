# ClickStack — Docker all-in-one

ClickStack publishes an all-in-one Docker image containing ClickHouse, HyperDX, the OpenTelemetry Collector, and MongoDB.

## Run

```bash
docker run --name clickstack-all-in-one \
  -p 8080:8080 \
  -p 4317:4317 \
  -p 4318:4318 \
  clickhouse/clickstack-all-in-one:latest
```

Open HyperDX at <http://localhost:8080>. The container exposes OTLP/gRPC on `4317` and OTLP/HTTP on `4318`.

For persistent data, mount the paths documented by ClickHouse: `/data/db`, `/var/lib/clickhouse`, and `/var/log/clickhouse-server`. Pin the image tag for repeatable deployments; this mode is intended for demos and local testing, not production scaling.

Official guide: [ClickStack all-in-one](https://clickhouse.com/docs/clickstack/deployment/all-in-one).
