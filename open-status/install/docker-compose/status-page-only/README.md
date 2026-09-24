# OpenStatus — status-page-only (lightweight)

For teams that already monitor elsewhere and only need to publish incidents, OpenStatus offers a lightweight Docker Compose setup that runs **4 services** instead of the full stack: a database, a one-shot migration runner, the dashboard, and the status page. No Tinybird, no probes, no API/ingest server.

## Setup

This mode uses the same upstream repository. Clone it (via [`scripts/setup.sh`](../../../scripts/setup.sh)) and follow the official status-page-only guide, which selects the reduced service set:

```bash
../../../scripts/setup.sh
cd openstatus-install   # created under ../standalone/openstatus-install by setup.sh
# Follow the guide below to launch only the 4 status-page services.
```

## Services

| Service | Role |
|:--------|:-----|
| db-migrate | One-shot database migrations |
| libsql | Database |
| dashboard | Configure status pages and post incidents |
| status-page | Public status pages |

## When to use

- You run Uptime Kuma / Gatus / Prometheus elsewhere and just want a branded, subscribable status page.
- You manage incidents manually rather than auto-opening them from checks.

## Notes

- No monitoring or analytics in this mode — incidents are posted manually.
- To add monitoring later, switch to the [full standalone stack](../standalone/) and deploy a [probe](../probe/).

Official source: [Self-host the status page only](https://www.openstatus.dev/docs/guides/self-host-status-page-only).
