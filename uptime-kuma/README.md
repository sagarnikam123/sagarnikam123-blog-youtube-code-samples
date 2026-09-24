# Uptime Kuma installation guide

UI-first, self-hosted uptime monitoring tool (Node.js + Vue). HTTP(S), TCP, DNS, ping, and certificate checks with 90+ notification channels and built-in status pages. Config lives in SQLite (or MariaDB), not in files.

Installation modes are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Binary (non-Docker, Node.js + PM2) | Available | [`install/binary/standalone/`](install/binary/standalone/) |
| Docker standalone | Available | [`install/docker/standalone/`](install/docker/standalone/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Helm (community) | Available | [`install/helm/standalone/`](install/helm/standalone/) |

See the [installation mode index](install/README.md) for the full matrix.

## Quick Start

```bash
docker run -d --restart=unless-stopped \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  --name uptime-kuma \
  louislam/uptime-kuma:2
./scripts/check-health.sh
```

Open <http://localhost:3001> and create the admin account on first run.

## Access

| Endpoint | URL |
|:---------|:----|
| Uptime Kuma UI | http://localhost:3001 |

## Notes

- **Storage:** SQLite in the `/app/data` volume by default. Requires POSIX file locks — avoid NFS to prevent DB corruption. Back up `/app/data`.
- **Config-as-code:** none. Monitors are created through the UI and stored in the DB; use export/backup for portability.
- **HA:** single-writer SQLite; not multi-node by design. Multi-region means running separate instances.
- Pin the image tag (`:2` tracks the v2 major line) for reproducible deployments.

Official sources:
- [Uptime Kuma site](https://uptime.kuma.pet)
- [How to Install (wiki)](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install)
- [GitHub repository](https://github.com/louislam/uptime-kuma)
