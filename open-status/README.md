# OpenStatus — Docker Compose Setup

Monitoring-as-code uptime platform and branded status pages (TypeScript / Next.js). Monitors, status pages, and notification channels are declared in YAML or Terraform and driven from a CLI, a typed API, or an MCP server. Self-hosted deployments run entirely on **private locations** (probes you deploy yourself).

## Architecture

OpenStatus is a multi-service application. Self-hosting uses the official Docker Compose bundle:

```
Probe (private location, runs anywhere) ──▶ private-location ingest (:8081)
                                                     │
                                                     ├──▶ Tinybird (:7181)  check analytics
                                                     └──▶ workflows (:3000)  status changes
libSQL (:8080 HTTP / :5001 gRPC)  ◀── server (:3001 API) ── dashboard (:3002)
                                                          └─ status-page (:3003)
```

## Quick Start

OpenStatus ships a large, frequently-changing Compose project, so `scripts/setup.sh` clones the upstream repo into this directory rather than recreating the stack here.

```bash
./scripts/setup.sh
cd install/docker-compose/standalone/openstatus-install
# edit .env.docker: set AUTH_SECRET, RESEND_API_KEY, SELF_HOST, NEXT_PUBLIC_URL,
#                    TINYBIRD_URL=http://tinybird-local:7181, CRON_SECRET
export DOCKER_BUILDKIT=1
docker compose up -d          # or: docker compose -f docker-compose.github-packages.yaml up -d
```

Then complete the **Tinybird analytics** step (`cd packages/tinybird && tb --local deploy`) — the dashboard shows no data until it is Live. See [`install/docker-compose/standalone/README.md`](install/docker-compose/standalone/README.md) for the full walk-through, including the private-location probe and the required cron job.

In another shell:

```bash
cd open-status
./scripts/check-health.sh
```

## Access

| Endpoint | URL |
|:---------|:----|
| Dashboard | http://localhost:3002 |
| Status pages | http://localhost:3003 |
| API server | http://localhost:3001 |
| Workflows | http://localhost:3000 |
| Private-location ingest | http://localhost:8081 |

## Services (from official compose)

| Service | Port | Role |
|:--------|:-----|:-----|
| db-migrate | — | One-shot migrations; exits after applying |
| workflows | 3000 | Background jobs and scheduled tasks |
| server | 3001 | API backend (ConnectRPC + REST v1) |
| dashboard | 3002 | Admin/configuration UI |
| status-page | 3003 | Public status pages |
| private-location | 8081 | Ingest server — receives results from probes |
| libsql | 8080 / 5001 | Database (HTTP / gRPC) |
| tinybird-local | 7181 | Check analytics and metrics |

The **probe** runs outside the stack (`ghcr.io/openstatushq/private-location:latest`) wherever you want to check from.

## Notes

- **License:** AGPL-3.0. Internal self-hosting is fine; offering it as a service to third parties triggers AGPL obligations — consult counsel.
- **Self-host = private locations only.** The vendor's global edge probe fleet is managed-cloud only.
- **Status-page-only** lightweight setup (4 services, no Tinybird/probes) is documented separately for teams that monitor elsewhere.
- Prefer prebuilt images? Use `docker-compose.github-packages.yaml` (pulls from `ghcr.io/openstatushq/*`).

## Installation guide

See the [installation mode index](install/README.md). This repository intentionally uses the upstream Docker Compose bundle rather than recreating OpenStatus's multi-service stack.

Official sources:
- [OpenStatus site](https://openstatus.dev)
- [Self-hosting guide](https://www.openstatus.dev/docs/guides/self-hosting-openstatus)
- [GitHub repository](https://github.com/openstatusHQ/openstatus)
