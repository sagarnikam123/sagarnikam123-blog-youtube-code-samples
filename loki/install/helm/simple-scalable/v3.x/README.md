# Loki 3.x Simple Scalable Configurations

Latest Loki 3.x simple scalable configurations with enhanced features.

## Available Configurations

- `loki-3.x.x-read-config.yaml` - Read service (query-frontend, querier)
- `loki-3.x.x-write-config.yaml` - Write service (distributor, ingester)
- `loki-3.x.x-backend-config.yaml` - Backend service (compactor, ruler, index-gateway, query-scheduler)

## New Features

- Enhanced query performance
- Improved scaling mechanisms
- Better resource utilization
- Query-scheduler component
- Advanced caching options

## Usage

```bash
# Start all three services
loki -config.file=loki-3.x.x-read-config.yaml &
loki -config.file=loki-3.x.x-write-config.yaml &
loki -config.file=loki-3.x.x-backend-config.yaml &
```

## Configuration Targets

```yaml
# Read service
target: read

# Write service
target: write

# Backend service
target: backend
```

## Configuration Reference

- [Loki 3.x Configuration Documentation](https://grafana.com/docs/loki/latest/configure/)
- [Simple Scalable Configuration](https://grafana.com/docs/loki/latest/configure/examples/#simple-scalable)
- [Scaling Guidelines](https://grafana.com/docs/loki/latest/operations/scaling/)
- [Migration from 2.x](https://grafana.com/docs/loki/latest/setup/upgrade/)

## Notes

- Query-scheduler included in backend service
- Enhanced performance vs 2.x
- Check compatibility with log shippers
- Review breaking changes from 2.x
