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

## Concepts in short

| Term | What it is | Why it matters |
|:-----|:-----------|:---------------|
| **Monitor** | One thing you watch — a URL, host:port, DNS name, or ping target — with a type, interval, and thresholds. | The core unit. Uptime Kuma checks each monitor on its own schedule and records up/down. |
| **Heartbeat** | A single check result (up/down + response time) stored per monitor. | The bar chart on each monitor is its heartbeat history; retention is configurable. |
| **Notification** | A channel (Telegram, Discord, Slack, email, Gotify, webhook…) attached to monitors. | Uptime Kuma's strength — 90+ channels. Fires when a monitor changes state. |
| **Status page** | A public (or password-protected) page grouping selected monitors. | What you share with users/customers to communicate uptime. |
| **Everything is UI + SQLite** | No config files: monitors, notifications, and pages are created in the UI and stored in `/app/data`. | Fast to set up; back up `/app/data` for portability (there is no config-as-code). |

Mental model: **one container does it all — probe + UI + status page + SQLite in `/app/data`.**

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

## Hello-world example: your first monitor

From nothing to a working check against `https://example.com`.

```bash
# 1. Start Uptime Kuma
docker run -d --restart=unless-stopped \
  -p 3001:3001 -v uptime-kuma:/app/data \
  --name uptime-kuma louislam/uptime-kuma:2
```

```text
2. Open http://localhost:3001 and create the admin account (first run only).
3. Click "Add New Monitor":
     Monitor Type : HTTP(s)
     Friendly Name: Hello World
     URL          : https://example.com
     Heartbeat    : 60 seconds
   Save.
4. The monitor turns green within ~60s and its heartbeat bar starts filling.
```

Optional — get notified and publish a status page:

```text
5. Settings → Notifications → add a channel (e.g. Telegram/Discord/webhook),
   then attach it to the monitor.
6. Status Pages → New Status Page → add the "Hello World" monitor → publish.
```

Everything above is stored in `/app/data` (the mounted volume). Back that up to keep your setup.

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
