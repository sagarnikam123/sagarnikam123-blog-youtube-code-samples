# Coroot — Docker Compose standalone

Deploy all Coroot components (server, ClickHouse, Prometheus, node-agent, cluster-agent) using Docker Compose. The existing benchmark deployment lives at [`../../../docker/`](../../../docker/).

## Quick Start

Use the official upstream Compose directly:

```bash
curl -fsS https://raw.githubusercontent.com/coroot/coroot/main/deploy/docker-compose.yaml | \
  docker compose -f - up -d
```

Or use the benchmark Compose with health check:

```bash
cd ../../docker
cp .env.example .env
docker compose up -d
# On Linux with eBPF:
docker compose --profile linux up -d
../../scripts/check-health.sh
```

## Notes

- node-agent requires Linux kernel 5.8+ (eBPF). On macOS, only the server + OTLP traces work.
- ClickHouse system logs should be disabled for disk savings (see the upstream docs).
- Phase 2 benchmark path.

Official guide: [Coroot Docker installation](https://docs.coroot.com/installation/docker).
