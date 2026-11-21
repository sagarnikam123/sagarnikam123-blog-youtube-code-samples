# ClickHouse — Docker standalone

## Run (single-node)

```bash
docker run -d --name clickhouse \
  -p 8123:8123 \
  -p 9000:9000 \
  -v clickhouse-data:/var/lib/clickhouse \
  -v clickhouse-logs:/var/log/clickhouse-server \
  clickhouse/clickhouse-server:25.5
```

## Access

```bash
# HTTP interface
curl http://localhost:8123/ -d "SELECT version()"

# Native client
docker exec -it clickhouse clickhouse-client
```

## Ports

| Port | Protocol | Purpose |
|:-----|:---------|:--------|
| 8123 | HTTP | Queries, health checks, play UI |
| 9000 | Native | High-performance binary protocol |
| 9009 | Inter-server | Replication (cluster only) |

## Notes

- Pin image tag for reproducibility.
- Alpine variant available: `clickhouse/clickhouse-server:25.5-alpine`.
- Mount `/var/lib/clickhouse` for persistent data.

Official guide: [Docker install](https://clickhouse.com/docs/get-started/setup/self-managed/docker).
