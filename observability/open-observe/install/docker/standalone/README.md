# OpenObserve — Docker standalone

Run a single-node OpenObserve instance with one `docker run` command. No external databases required in local mode.

## Run

```bash
docker run -d \
  --name openobserve \
  -v $PWD/data:/data \
  -p 5080:5080 \
  -e ZO_DATA_DIR="/data" \
  -e ZO_ROOT_USER_EMAIL="root@example.com" \
  -e ZO_ROOT_USER_PASSWORD="Complexpass#123" \
  openobserve/openobserve:latest
```

Open <http://localhost:5080> and log in.

## OTLP ingestion

OpenObserve natively accepts OTLP on port 5080:
- gRPC: `localhost:5081`
- HTTP: `localhost:5082`

(Ports depend on the configuration; default single-node exposes the API on 5080 with OTLP on 5081/5082.)

## Notes

- Data is persisted to the `./data` volume mount.
- Pin the image tag for repeatable deployments.
- For SIMD-optimized performance, use `public.ecr.aws/zinclabs/openobserve:latest-simd`.
- For HA mode, switch to the Helm chart with object storage.

Official source: [Docker Hub — openobserve/openobserve](https://hub.docker.com/r/openobserve/openobserve).
