# OpenStatus — Docker Compose Setup

Monitoring-as-code uptime platform and branded status pages (TypeScript / Next.js). Monitors, status pages, and notification channels are declared in YAML or Terraform and driven from a CLI, a typed API, or an MCP server. Self-hosted deployments run entirely on **private locations** (probes you deploy yourself).

## Concepts in short

| Term | What it is | Why it exists |
|:-----|:-----------|:--------------|
| **Probe** (private location) | A small container that actually runs the checks — it hits your URLs/ports on a schedule, measures the result, and ships it to the ingest server. | Nothing is checked until a probe runs. Self-hosted OpenStatus has no built-in checkers, so **you** run the probe — wherever you want to check from (a VPS, a Raspberry Pi, inside your VPC, or one per region). |
| **Ingest server** (`private-location` service, :8081) | Receives results from probes, writes them to Tinybird, and forwards status changes to workflows. | Single entry point for all probe results; decouples "where checks run" from "where data lives". |
| **Dashboard** (:3002) | Admin UI where you create monitors, status pages, and locations. | This is *configure only* — it does not perform checks itself. |
| **Status page** (:3003) | The public, branded page your users see. | Communicates uptime and incidents to the outside world. |
| **Workflows** (:3000) | Background jobs and scheduled tasks (e.g. marking a probe unhealthy). | Runs the periodic logic; needs an external cron to trigger it (see setup). |
| **Tinybird** (:7181) | Analytics store for every check result. | The dashboard charts read from here — no Tinybird, no data on screen. |

Mental model: **dashboard = configure · probe = check · ingest = collect · Tinybird = store · status page = show.**

> **Naming warning:** the *probe* image is `ghcr.io/openstatushq/private-location` (unprefixed); the *ingest server* inside the stack is `ghcr.io/openstatushq/openstatus-private-location` (prefixed). The probe's `OPENSTATUS_INGEST_URL` points at the ingest server on port `8081`.

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

## Hello-world example: your first monitor

End-to-end, from nothing to a working check against `https://example.com`.

```bash
# 1. Clone + configure the stack
./scripts/setup.sh
cd install/docker-compose/standalone/openstatus-install

# Edit .env.docker and set the required values:
#   AUTH_SECRET=<random>        RESEND_API_KEY=<resend-key>
#   SELF_HOST=true              NEXT_PUBLIC_URL=http://localhost:3002
#   TINYBIRD_URL=http://tinybird-local:7181
#   CRON_SECRET=<random>

# 2. Start all services (prebuilt images = no local build)
export DOCKER_BUILDKIT=1
docker compose -f docker-compose.github-packages.yaml up -d

# 3. Deploy analytics (dashboard is empty until this is "Live")
cd packages/tinybird
tb --local deploy
tb --local deployment promote          # if status shows "Staging"
TOKEN=$(tb --local info | grep '^token:' | awk '{print $2}')
cd ../..
# Put $TOKEN into BOTH vars in .env.docker, then restart:
#   TINY_BIRD_API_KEY="<token>"   TINYBIRD_TOKEN="<token>"
docker compose -f docker-compose.github-packages.yaml up -d
```

Now create the location + monitor in the UI:

```text
4. Open the dashboard    → http://localhost:3002  (sign up, create a workspace)
5. Settings → Private Locations → create one → copy the key
6. Run the probe (this is what actually checks):
```

```bash
docker run -d --name openstatus-probe \
  -e OPENSTATUS_KEY=<your-key> \
  -e OPENSTATUS_INGEST_URL=http://<your-host-ip>:8081 \
  ghcr.io/openstatushq/private-location:latest
```

```text
7. Monitors → Create → URL https://example.com, method GET,
   assign the private location you just made → Save
8. Wait up to ~10 min (the probe refreshes its list every 10 min) or
   restart the probe. Results appear on the dashboard and status page.
```

Confirm the probe is working:

```bash
docker logs openstatus-probe
# Monitor check for 1 (https://example.com) ingested with status "success" (code 200)
```

### Config-as-code variant (CLI)

Prefer managing monitors as reviewable YAML instead of clicking? Use the OpenStatus CLI.

```bash
# Install (macOS); Linux/Windows scripts in the CLI reference
brew install openstatusHQ/cli/openstatus --cask

# Authenticate — create an API key in Dashboard → Settings → General → API Keys
export OPENSTATUS_API_TOKEN=<your-api-token>

# Generate openstatus.yaml from your workspace (after creating one monitor in the UI)
openstatus monitors import          # writes openstatus.yaml + a lock file

# Edit openstatus.yaml, preview, then apply
openstatus monitors apply --dry-run
openstatus monitors apply           # -c custom.yaml to use another file
```

`monitors import` produces the exact, current YAML schema for your version — safer than
hand-writing it. The CLI reads `OPENSTATUS_API_TOKEN`; pass `-t <token>` per command instead
if you prefer. See the [CLI reference](https://www.openstatus.dev/docs/reference/cli-reference).

> **Just want a status page, no checks?** Use the lightweight
> [status-page-only setup](install/docker-compose/status-page-only/) — 4 services,
> no Tinybird, no probe.

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
