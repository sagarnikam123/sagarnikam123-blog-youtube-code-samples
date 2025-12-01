# Loki 2.x Simple Scalable Configurations

Stable Loki 2.x simple scalable configurations for medium-scale deployments.

## Available Configurations

- `loki-2.x.x-read-config.yaml` - Read service (query-frontend, querier)
- `loki-2.x.x-write-config.yaml` - Write service (distributor, ingester)
- `loki-2.x.x-backend-config.yaml` - Backend service (compactor, ruler, index-gateway)

## Features

- Proven stability
- 3-service architecture
- Horizontal scaling capability
- Production battle-tested

## Usage

```bash
# Start all three services
loki -config.file=loki-2.x.x-read-config.yaml &
loki -config.file=loki-2.x.x-write-config.yaml &
loki -config.file=loki-2.x.x-backend-config.yaml &
```

## Scaling

```bash
# Scale read for query performance
# Run multiple read instances

# Scale write for ingestion throughput
# Run multiple write instances
```

## Configuration Reference

- [Loki 2.9.x Configuration Documentation](https://grafana.com/docs/loki/v2.9.x/configure/)
- [Simple Scalable Configuration](https://grafana.com/docs/loki/v2.9.x/configure/examples/#simple-scalable)
- [Scaling Guidelines](https://grafana.com/docs/loki/v2.9.x/operations/scaling/)