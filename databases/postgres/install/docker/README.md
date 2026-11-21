# PostgreSQL — Docker standalone

## Run (single-node)

```bash
docker run -d --name postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=appdb \
  -e POSTGRES_USER=appuser \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:17
```

## Access

```bash
# Client inside the container
docker exec -it postgres psql -U appuser -d appdb

# From the host (needs psql)
psql -h 127.0.0.1 -p 5432 -U appuser -d appdb
```

## Ports

| Port | Purpose |
|:-----|:--------|
| 5432 | PostgreSQL client protocol |

## Notes

- Pin the image tag (`17`, `16`) for reproducibility. Alpine variant: `postgres:17-alpine`.
- Mount `/var/lib/postgresql/data` for persistent data.
- `POSTGRES_PASSWORD` is required; `POSTGRES_DB`/`POSTGRES_USER` are optional bootstrap values (default user is `postgres`).
- Drop SQL/shell files into `/docker-entrypoint-initdb.d/` to run on first init.
- A single-service Compose equivalent is in [`docker-compose.yml`](docker-compose.yml).

Official guide: [Postgres Docker Official Image](https://hub.docker.com/_/postgres).
