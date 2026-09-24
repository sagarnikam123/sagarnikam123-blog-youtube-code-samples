# OpenStatus installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary | N/A | — | Multi-service TypeScript application; no single binary |
| Docker standalone | N/A | — | Requires the full multi-service stack |
| Docker Compose standalone | Available (official) | [`docker-compose/standalone/`](docker-compose/standalone/) | Full stack: dashboard, status pages, API, workflows, ingest, libSQL, Tinybird |
| Docker Compose (status-page only) | Available (official) | [`docker-compose/status-page-only/`](docker-compose/status-page-only/) | Lightweight 4-service setup — publish incidents only, monitor elsewhere |
| Private-location probe | Available (official) | [`docker-compose/probe/`](docker-compose/probe/) | Runs outside the stack; performs the actual checks |
| Docker Compose cluster | N/A | — | Scale via managed cloud / multiple private locations |
| Kubernetes / Helm | Not published (official) | — | No official chart; community deploy templates only |
| Operator | N/A | — | No official operator |

Self-hosted OpenStatus relies entirely on **private locations** — you deploy probes yourself. The vendor's public multi-region edge fleet is available only on the managed cloud.

Official sources:
- [Self-hosting guide](https://www.openstatus.dev/docs/guides/self-hosting-openstatus)
- [Status-page-only setup](https://www.openstatus.dev/docs/guides/self-host-status-page-only)
- [Create a private location](https://www.openstatus.dev/docs/guides/how-to-create-private-location)
- [docker-compose.yaml (upstream)](https://github.com/openstatusHQ/openstatus/blob/main/docker-compose.yaml)
