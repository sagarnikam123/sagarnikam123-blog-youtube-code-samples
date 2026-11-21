# ClickHouse — Homebrew (macOS)

Installs the single self-contained ClickHouse binary as a Homebrew **cask** (the same binary the `curl https://clickhouse.com/ | sh` quick-install fetches, just managed by brew).

## Install

```bash
brew install --cask clickhouse
```

Puts the `clickhouse` binary on PATH (server, client, keeper, and local are all in the one binary).

## Run

```bash
# Start the server (foreground; add & to background it)
clickhouse server

# In another terminal, open the client
clickhouse client
```

There is **no `brew services` entry** for this cask — it's a plain binary, so you start `clickhouse server` yourself (or wrap it in a launchd/`nohup` script). For a managed service, use the Linux DEB/RPM packages instead.

## Verify

```sql
SELECT version();
SELECT 1;
```

## Ports

| Port | Purpose |
|:-----|:--------|
| 8123 | HTTP interface (queries, health) |
| 9000 | Native client protocol |

## Notes

- Data/config default to the working directory. Use `clickhouse server -- --path=/your/data` for a custom location.
- macOS via brew is great for local dev/testing; for production use the Linux packages with systemd (see [`../deb/`](../deb/) / [`../rpm/`](../rpm/)).
- Update with `brew upgrade --cask clickhouse`.

Official sources:
- [Homebrew cask: clickhouse](https://formulae.brew.sh/cask/clickhouse)
- [Quick install](https://clickhouse.com/docs/get-started/setup/self-managed/quick-install)
