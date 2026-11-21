# Uptime Kuma — Docker Compose standalone

Single-node Uptime Kuma with a named volume for SQLite persistence.

## Architecture

```
Browser (:3001) → uptime-kuma (Node.js + Vue) → SQLite in /app/data volume
```

## Services

| Service | Image | Role |
|:--------|:------|:-----|
| uptime-kuma | `louislam/uptime-kuma:2` | All-in-one: probes + UI + status pages + SQLite |

## Quick Start

```bash
cp .env.example .env
docker compose up -d
../../../scripts/check-health.sh
```

Open <http://localhost:3001> and create the admin account on first run.

## Access

| Endpoint | URL |
|:---------|:----|
| Uptime Kuma UI | http://localhost:3001 |

## Notes

- Data persists in the `uptime-kuma` named volume mounted at `/app/data`.
- Requires POSIX file locks — avoid backing the volume with NFS.
- Multi-arch image: works on both ARM64 (Apple Silicon) and AMD64.
- Update with `docker compose pull && docker compose up -d`.

Official source: [compose.yaml example](https://github.com/louislam/uptime-kuma/blob/master/compose.yaml).
