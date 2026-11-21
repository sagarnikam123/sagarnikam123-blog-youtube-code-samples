# Highlight.io — Docker Compose hobby (self-hosted)

The only officially supported self-hosted deployment method is the Docker Compose hobby deployment from the Highlight.io GitHub repository.

## Prerequisites

- Docker 25.0+ with Docker Compose v2.24+
- Git 2.13+
- At least 8 GB RAM, 4 CPUs, 64 GB disk

## Install

### Option 1: Repository setup script

```bash
cd highlight-io
./scripts/setup.sh
cd highlight-install/docker
docker compose -f compose.hobby.yml up -d
```

### Option 2: Official one-liner

```bash
git clone --recurse-submodules https://github.com/highlight/highlight
cd highlight/docker && ./run-hobby.sh
```

### Option 3: Curl one-liner

```bash
curl -fsS https://raw.githubusercontent.com/highlight/highlight/main/deploy/hobby.sh | bash
```

## Access

After 3-5 minutes for all services to initialize:

| Endpoint | URL |
|:---------|:----|
| Highlight UI | https://localhost (or http://localhost:3000) |
| OTLP gRPC | localhost:4317 |
| OTLP HTTP | localhost:4318 |

Login with the `ADMIN_PASSWORD` from `docker/.env`.

## Health check

```bash
../../scripts/check-health.sh
```

## Upgrade

```bash
cd highlight-install
git pull --recurse-submodules
cd docker && docker compose -f compose.hobby.yml up -d
```

## Capacity

Good for <10k sessions and <50k errors ingested monthly. For larger workloads, contact Highlight for enterprise self-hosted options.

## Notes

- The hobby deployment builds the collector from source (Dockerfile).
- Stack: ClickHouse + Kafka + Zookeeper + PostgreSQL + Redis + backend + frontend + collector.
- Highlight.io was acquired by LaunchDarkly in 2025; the open-source repo remains active.
- No official Helm chart or Kubernetes deployment is published.

Official source: [Self-hosted hobby guide](https://github.com/highlight/highlight/blob/main/README.md#hobby-self-hosted).
