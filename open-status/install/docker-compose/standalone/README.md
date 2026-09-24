# OpenStatus — Docker Compose standalone (full stack)

OpenStatus officially supports a single-server Docker Compose deployment. The repository's [`scripts/setup.sh`](../../../scripts/setup.sh) clones the upstream release into `openstatus-install/` here, because the generated Compose project contains many services and changes independently of this guide.

## 1. Clone and configure

```bash
../../../scripts/setup.sh          # clones openstatusHQ/openstatus into ./openstatus-install
cd openstatus-install
cp .env.docker.example .env.docker
```

Edit `.env.docker`. Four values are **required**:

| Variable | Purpose |
|:---------|:--------|
| `AUTH_SECRET` | Session/auth signing secret (random string) |
| `RESEND_API_KEY` | Magic-link login won't work without it |
| `SELF_HOST` | Marks the instance as self-hosted |
| `NEXT_PUBLIC_URL` | Public URL of the dashboard |

Two more matter immediately:

```bash
# Point apps at the local Tinybird container (else charts 404 against Tinybird Cloud)
TINYBIRD_URL=http://tinybird-local:7181
# Shared secret the ingest server uses to authenticate to the workflows app
CRON_SECRET=some-random-string
```

## 2. Build and start

```bash
export DOCKER_BUILDKIT=1
docker compose up -d
# Prefer prebuilt images (no local build):
# docker compose -f docker-compose.github-packages.yaml up -d
```

Migrations run automatically via the one-shot `db-migrate` container.

## 3. Analytics (Tinybird) — required

The dashboard is empty until Tinybird is deployed and Live:

```bash
cd packages/tinybird
tb --local deploy
tb --local deployment ls        # Status must read "Live"; if "Staging": tb --local deployment promote
tb --local info                 # copy the token
```

Set **both** token variables in `.env.docker` to that value, then restart:

```bash
# Read by dashboard/status/server/workflows (Node)
TINY_BIRD_API_KEY="<token>"
# Read by the private-location ingest server (Go)
TINYBIRD_TOKEN="<token>"
```

```bash
cd ../..
docker compose up -d
```

> Setting only `TINY_BIRD_API_KEY` is the most common mistake — the ingest server never reads it and every check is rejected with `403`.

## 4. Deploy a private-location probe

Self-hosted checks are performed by probes you run. See [`../probe/`](../probe/). In the dashboard (**Settings → Private Locations**) create a location, copy the key, then:

```bash
docker run -d --name openstatus-probe \
  -e OPENSTATUS_KEY=<your-key> \
  -e OPENSTATUS_INGEST_URL=http://<your-server-ip-or-domain>:8081 \
  ghcr.io/openstatushq/private-location:latest
```

## 5. Scheduled tasks (cron) — required

Private-location health only updates if a cron hits the workflows app every 5 minutes:

```cron
*/5 * * * * curl -sS -H "Authorization: YOUR_CRON_SECRET" http://localhost:3000/cron/private-location-health
```

(Or run it as a small cron sidecar container — see the self-hosting guide.)

## Access

| Endpoint | URL |
|:---------|:----|
| Dashboard | http://localhost:3002 |
| Status pages | http://localhost:3003 |
| API server | http://localhost:3001 |
| Workflows | http://localhost:3000 |
| Private-location ingest | http://localhost:8081 |

## Notes

- Self-host relies entirely on private locations; the managed-cloud edge fleet is not available.
- IP restriction on status pages is not secure behind a non-Vercel proxy unless the proxy rewrites `X-Forwarded-For`.
- AGPL-3.0 — review obligations before offering as a service to third parties.

Official source: [Self-hosting OpenStatus](https://www.openstatus.dev/docs/guides/self-hosting-openstatus).
