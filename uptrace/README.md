# Uptrace installation guide

Installation modes for Uptrace are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Kubernetes / Helm | Catalogued for follow-up | [`install/README.md`](install/README.md) |

The Docker Compose setup is the Phase 1 benchmark deployment. Run it from its mode directory so its ClickHouse, PostgreSQL, Redis, and collector paths resolve correctly.
