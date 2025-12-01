# Loki Monolithic Docker Deployment

Run Loki monolithic using Docker with the same configuration files as the native deployment.

## Quick Start

```bash
# Start Loki with default config
./start-docker.sh

# Start with specific config
./start-docker.sh -c loki-3.5.x-minimal-working.yaml

# Start with MinIO for S3 storage
./start-docker.sh -m

# Stop deployment
./stop-docker.sh

# Stop and remove all data
./stop-docker.sh -v
```

## Features

- **Same Config Files**: Uses identical configs from `../configs/` directory
- **Volume Persistence**: Data persists between container restarts
- **Health Checks**: Built-in container health monitoring
- **Optional MinIO**: S3-compatible storage for testing
- **Easy Management**: Simple start/stop scripts

## Configuration Options

### Available Configs
- `loki-3.5.x-ui-filesystem-inmemory.yaml` (default)
- `loki-3.5.x-dev-local-storage.yaml`
- `loki-3.5.x-minimal-working.yaml`
- `loki-3.5.x-simple-working.yaml`

### Storage Options
- **Filesystem** (default): Local container storage with volume persistence
- **MinIO**: S3-compatible storage using MinIO container

## Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| Loki Web UI | http://localhost:3100/ui/ | Main interface |
| Ring Status | http://localhost:3100/ring | Ring health |
| Configuration | http://localhost:3100/config | Current config |
| Metrics | http://localhost:3100/metrics | Prometheus metrics |
| MinIO Console | http://localhost:9001 | Storage management |

## Docker Commands

### Basic Operations
```bash
# View logs
docker-compose logs -f loki

# Restart Loki
docker-compose restart loki

# Execute commands in container
docker-compose exec loki sh

# Check container status
docker-compose ps
```

### Advanced Operations
```bash
# Start with specific profile
docker-compose --profile s3-storage up -d

# Scale services (not applicable for monolithic)
docker-compose up -d --scale loki=1

# Update image
docker-compose pull loki
docker-compose up -d loki
```

## Volume Management

### Data Locations
- **Loki Data**: `/tmp/loki` (mapped to `loki-data` volume)
- **MinIO Data**: `/data` (mapped to `minio-data` volume)

### Backup Data
```bash
# Backup Loki data
docker run --rm -v loki-monolithic_loki-data:/data -v $(pwd):/backup alpine tar czf /backup/loki-backup.tar.gz -C /data .

# Restore Loki data
docker run --rm -v loki-monolithic_loki-data:/data -v $(pwd):/backup alpine tar xzf /backup/loki-backup.tar.gz -C /data
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs loki

# Verify config file exists
ls -la ../configs/v3.x/v3.5.x/

# Check port conflicts
netstat -tulpn | grep :3100
```

#### Health Check Failing
```bash
# Manual health check
curl http://localhost:3100/ready

# Check container health
docker inspect loki-monolithic | grep Health -A 10
```

#### Permission Issues
```bash
# Fix volume permissions
docker-compose exec loki chown -R loki:loki /tmp/loki
```

### Configuration Issues

#### Wrong Config File
```bash
# Check current config in container
docker-compose exec loki cat /etc/loki/configs/v3.x/v3.5.x/loki-3.5.x-ui-filesystem-inmemory.yaml

# Update config and restart
./start-docker.sh -c new-config.yaml
```

#### Environment Variables
```bash
# Check environment
docker-compose exec loki env | grep HOSTNAME

# Override environment
HOSTNAME=custom-name docker-compose up -d
```

## Monitoring

### Health Checks
- Container health check every 30s
- Ready endpoint: `/ready`
- Startup grace period: 40s

### Metrics Collection
```bash
# Scrape metrics
curl http://localhost:3100/metrics

# Monitor with Prometheus (add to prometheus.yml)
- job_name: 'loki-docker'
  static_configs:
    - targets: ['localhost:3100']
```

## Development

### Custom Images
```bash
# Build custom image
docker build -t custom-loki:latest .

# Update docker-compose.yml
image: custom-loki:latest
```

### Configuration Testing
```bash
# Test config syntax
docker run --rm -v $(pwd)/../configs:/configs grafana/loki:3.5.0 \
  -config.file=/configs/v3.x/v3.5.x/loki-3.5.x-ui-filesystem-inmemory.yaml \
  -verify-config
```

## Comparison: Docker vs Native

| Aspect | Docker | Native |
|--------|--------|--------|
| **Setup** | `./start-docker.sh` | `./scripts/stack/start-loki.sh` |
| **Config** | Same files | Same files |
| **Isolation** | Container isolated | Host process |
| **Resources** | Container limits | Host resources |
| **Networking** | Container network | Host network |
| **Data** | Volume persistence | Host filesystem |
| **Updates** | Image updates | Binary updates |

## Best Practices

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** for production
3. **Regular backups** of data volumes
4. **Monitor container health** and logs
5. **Use secrets** for sensitive configuration
6. **Network security** with proper firewall rules