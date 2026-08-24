# OpenObserve — binary standalone

OpenObserve ships as a single self-contained binary for Linux (amd64/arm64), macOS (amd64/arm64), and Windows. In single-node/local mode it uses SQLite for metadata and local disk for Parquet storage with no external dependencies.

## Install (Linux amd64)

```bash
VERSION=0.14.5
curl -L -o openobserve \
  "https://github.com/openobserve/openobserve/releases/download/v${VERSION}/openobserve-v${VERSION}-linux-amd64-musl"
chmod +x openobserve
```

## Run

```bash
ZO_ROOT_USER_EMAIL="root@example.com" \
ZO_ROOT_USER_PASSWORD="Complexpass#123" \
./openobserve
```

OpenObserve listens on port 5080 by default. Open <http://localhost:5080> and log in.

## Notes

- Single-node mode: `ZO_LOCAL_MODE=true` (default). Uses SQLite + local disk.
- Can ingest and search over 2 TB/day on a single machine.
- For HA/cluster mode, set `ZO_LOCAL_MODE=false` and configure PostgreSQL + object storage.
- Pin the binary version for reproducible deployments.

Official sources:
- [GitHub releases](https://github.com/openobserve/openobserve/releases)
- [Architecture](https://openobserve.ai/docs/architecture/)
- [Environment variables](https://openobserve.ai/docs/administration/configuration/environment-variables/)
