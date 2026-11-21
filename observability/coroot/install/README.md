# Coroot installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary/systemd standalone | Available | [`binary/standalone/`](binary/standalone/) | Linux bare-metal/VM (Ubuntu, Debian, RHEL) |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 2 benchmark; eBPF agent requires Linux |
| Docker Swarm | Available | [`docker-swarm/`](docker-swarm/) | Manual node-agent per host |
| Kubernetes Operator | Available (recommended) | [`operator/cluster/`](operator/cluster/) | CRD-managed deployment with auto-upgrades |
| Docker standalone | Not a separate server mode | — | Use Docker Compose; Coroot needs ClickHouse + Prometheus |
| Helm standalone (no operator) | Not documented separately | — | Operator is the official K8s path |

## Architecture

Coroot consists of:
- **Coroot server** — UI, API, observability analysis engine
- **node-agent** — eBPF-based metrics, logs, traces, profiles collector (Linux kernel 5.8+)
- **cluster-agent** — database metrics (MySQL, Postgres, Redis, etc.)
- **ClickHouse** — traces, logs, profiles storage
- **Prometheus** — metrics storage (or optionally metrics in ClickHouse)

Official sources:
- [Installation overview](https://docs.coroot.com/installation/)
- [Docker](https://docs.coroot.com/installation/docker)
- [Ubuntu/Debian](https://docs.coroot.com/installation/ubuntu/)
- [Kubernetes Operator](https://docs.coroot.com/installation/k8s-operator/)
- [Docker Swarm](https://docs.coroot.com/installation/docker-swarm)
- [Architecture](https://docs.coroot.com/installation/architecture)
