# PostgreSQL — Docker Compose standalone

Single-node PostgreSQL with two companions:

- **Adminer** — lightweight web DB client (browse/query without a local psql).
- **postgres-exporter** — Prometheus metrics exporter, so the DB can be scraped and visualized in Grafana.

## Start

```bash
docker compose up -d
```

## Access

```bash
# psql client
docker exec -it postgres psql -U appuser -d appdb     # password: apppass

# Adminer UI
open http://localhost:8080     # system: PostgreSQL, server: postgres, user: appuser, db: appdb

# Exporter metrics
curl -s http://localhost:9187/metrics | head
```

## Ports

| Service | Port | Purpose |
|:--------|:-----|:--------|
| postgres | 5432 | Client protocol |
| adminer | 8080 | Web DB UI |
| postgres-exporter | 9187 | Prometheus metrics |

## Notes

- The exporter connects via `DATA_SOURCE_NAME`; here it uses the `exporter` role created by the init script.
- Point Prometheus at `postgres-exporter:9187`, then use Grafana's Prometheus datasource — or connect Grafana's PostgreSQL datasource straight to `postgres:5432` for SQL-based panels.
- Enable richer stats by loading `pg_stat_statements` (add `shared_preload_libraries` in a mounted config).

Official sources:
- [Postgres Docker](https://hub.docker.com/_/postgres)
- [postgres_exporter](https://github.com/prometheus-community/postgres_exporter)
