# Loki Multi-Node Cluster - Docker Compose

3-node Loki cluster with memberlist for local testing and learning.

## Architecture

```
                    ┌─────────────┐
                    │   Gateway   │ :3100
                    │   (nginx)   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ Loki-1  │◄─────►│ Loki-2  │◄─────►│ Loki-3  │
    │  :3101  │       │  :3102  │       │  :3103  │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼──────┐
                    │    MinIO    │ :9000/:9001
                    │  (S3 store) │
                    └─────────────┘
```

## Quick Start

```bash
cd install/docker/simple-scalable

# Start cluster
docker-compose up -d

# Watch logs
docker-compose logs -f

# Check ring membership
curl http://localhost:3100/ring

# Check memberlist
curl http://localhost:3100/memberlist

# Stop cluster
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Loki Gateway | http://localhost:3100 | - |
| Loki UI | http://localhost:3100/ui | - |
| Loki Node 1 | http://localhost:3101 | - |
| Loki Node 2 | http://localhost:3102 | - |
| Loki Node 3 | http://localhost:3103 | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| Grafana | http://localhost:3000 | admin/admin |

## Files

| File | Description |
|------|-------------|
| `docker-compose.yaml` | Main compose file with all services |
| `nginx.conf` | Gateway load balancer config |
| `grafana-datasources.yaml` | Grafana Loki datasource |

## Testing Cluster Behavior

### Send logs via gateway (load balanced)
```bash
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"app":"test"},"values":[["'$(date +%s)000000000'","hello cluster"]]}]}'
```

### Query logs
```bash
curl -G http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={app="test"}' \
  --data-urlencode 'limit=10'
```

### Check ring membership
```bash
# All nodes should appear in the ring
curl -s http://localhost:3100/ring | grep -E "loki-[123]"
```

### Simulate node failure
```bash
# Stop one node
docker-compose stop loki-2

# Check ring (should show loki-2 as unhealthy)
curl http://localhost:3100/ring

# Logs should still work (2 nodes remaining)
curl -G http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={app="test"}'

# Restart node
docker-compose start loki-2
```

## Components

- **Loki x3**: Monolithic mode with memberlist clustering
- **MinIO**: Shared S3-compatible storage
- **Nginx Gateway**: Load balancer for read/write paths
- **Grafana**: Visualization (pre-configured with Loki datasource)

## When to Use

| ✅ Good For | ❌ Not For |
|-------------|-----------|
| Learning memberlist clustering | Production workloads |
| Testing HA behavior | Single-node needs |
| Preparing for K8s deployment | Resource-constrained machines |

## Resource Requirements

- ~2GB RAM minimum
- ~4 CPU cores recommended
- ~5GB disk for volumes
