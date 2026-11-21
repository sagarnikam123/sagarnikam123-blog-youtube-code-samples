# Parseable — Docker standalone

Run a single-node Parseable instance with one `docker run` command using local disk storage.

## Run

```bash
docker run -d \
  --name parseable \
  -p 8000:8000 \
  -v $PWD/data:/parseable/data \
  -v $PWD/staging:/parseable/staging \
  -e P_USERNAME=admin \
  -e P_PASSWORD=admin \
  parseable/parseable:latest \
  parseable local-store
```

Open <http://localhost:8000>. Login with `admin` / `admin`.

## OTLP ingestion

Send telemetry via OTLP HTTP to port 8000:
- Logs: `http://localhost:8000/v1/logs`
- Metrics: `http://localhost:8000/v1/metrics`
- Traces: `http://localhost:8000/v1/traces`

## Notes

- Standalone mode — single ingest + query node.
- Pin the image tag for repeatable deployments.
- For S3/MinIO-backed storage, replace `local-store` with `s3-store` and pass bucket env vars.
- For distributed mode, use the [Docker Compose distributed setup](../../docker-compose/distributed/).

Official source: [Docker Hub — parseable/parseable](https://hub.docker.com/r/parseable/parseable).
