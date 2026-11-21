# ClickHouse — quick install (single binary)

The fastest way to get ClickHouse running. Downloads a self-contained binary for your OS.

## Install

```bash
curl https://clickhouse.com/ | sh
```

## Run

```bash
# Start server
./clickhouse server

# In another terminal, use client
./clickhouse client
```

## Verify

```sql
SELECT version();
SELECT 1;
```

## Notes

- Single binary includes server, client, keeper, local, and all tools.
- No systemd, no packages — runs from current directory.
- Data stored in `./` by default. Use `--path` for custom data dir.
- For production, use DEB/RPM packages with proper systemd management.

Official guide: [Quick install](https://clickhouse.com/docs/get-started/setup/self-managed/quick-install).
