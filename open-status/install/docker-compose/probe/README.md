# OpenStatus — private-location probe

Self-hosted OpenStatus performs no checks on its own. A **probe** (private location) runs wherever you want to monitor from — a VPS, a Raspberry Pi, inside your VPC — and ships results to the ingest server on port `8081`.

> Naming is confusing on purpose-of-warning: the **probe** is `ghcr.io/openstatushq/private-location` (unprefixed); the **ingest server** inside the stack is `ghcr.io/openstatushq/openstatus-private-location` (prefixed). The probe's `OPENSTATUS_INGEST_URL` points at the ingest server.

## Create a location, then run the probe

1. In the dashboard, go to **Settings → Private Locations** and create one.
2. Copy the generated key.
3. Run the probe:

```bash
docker run -d --name openstatus-probe \
  -e OPENSTATUS_KEY=<your-key> \
  -e OPENSTATUS_INGEST_URL=http://<your-server-ip-or-domain>:8081 \
  ghcr.io/openstatushq/private-location:latest
```

If the probe runs on the same Docker network as the stack, use the internal address instead:

```bash
-e OPENSTATUS_INGEST_URL=http://private-location:8080
```

## Environment variables

| Variable | Required | Purpose |
|:---------|:--------:|:--------|
| `OPENSTATUS_KEY` | yes | Key from **Settings → Private Locations**. The probe exits on startup if unset |
| `OPENSTATUS_INGEST_URL` | yes | URL of your ingest server (port `8081`). Unset → defaults to OpenStatus Cloud, so your self-hosted instance never sees a check |

A healthy probe logs `Monitor check for N (...) ingested with status "success"`.

## Notes

- The probe refreshes its monitor list every ~10 minutes; after creating/editing a monitor, wait up to 10 minutes or restart the probe.
- Deploy multiple probes in different regions/networks for geographic coverage.

Official source: [Create a private location](https://www.openstatus.dev/docs/guides/how-to-create-private-location).
