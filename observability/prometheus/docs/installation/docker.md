# Docker Installation Guide

Run Prometheus in Docker containers for local development, testing, and lightweight deployments.

## Overview

Docker installation is ideal for:
- Local development and testing
- Quick prototyping
- Learning Prometheus
- CI/CD pipelines
- Lightweight deployments

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2+ (for multi-container setups)
- Port 9090 available (configurable)

```bash
# Verify Docker installation
docker --version
docker compose version
```

## Quick Start

### Single Command

```bash
docker run -d --name prometheus -p 9090:9090 prom/prometheus
```

Access Prometheus at http://localhost:9090

### Using Docker Compose

```bash
cd install/docker
docker compose up -d
```

### Full Monitoring Stack

```bash
cd install/docker
docker compose -f docker-compose.full.yml up -d
```

This starts:
- Prometheus (port 9090)
- Grafana (port 3000)
- Alertmanager (port 9093)

## Configuration

### Environment Variables

Copy and customize the environment file:

```bash
cp .env.example .env
```

Available variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_VERSION` | `v2.54.1` | Prometheus image version |
| `PROMETHEUS_PORT` | `9090` | Host port for Prometheus |
| `PROMETHEUS_RETENTION` | `15d` | Data retention period |
| `GRAFANA_VERSION` | `11.4.0` | Grafana image version |
| `GRAFANA_PORT` | `3000` | Host port for Grafana |
| `ALERTMANAGER_VERSION` | `v0.28.0` | Alertmanager image version |
| `ALERTMANAGER_PORT` | `9093` | Host port for Alertmanager |

### Prometheus Configuration

Edit `prometheus.yml` to customize scrape configurations:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Add your targets here
  - job_name: "my-app"
    static_configs:
      - targets: ["host.docker.internal:8080"]
```

### Bind Mount Custom Configuration

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  prom/prometheus
```

## Docker Compose Files

### Single-Node (docker-compose.yml)

```yaml
services:
  prometheus:
    image: prom/prometheus:${PROMETHEUS_VERSION:-v2.54.1}
    container_name: prometheus
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-15d}'
      - '--web.enable-lifecycle'
    restart: unless-stopped

volumes:
  prometheus_data:
```

### Full Stack (docker-compose.full.yml)

Includes Prometheus, Grafana, and Alertmanager with pre-configured integrations.

```bash
# Start full stack
docker compose -f docker-compose.full.yml up -d

# View logs
docker compose -f docker-compose.full.yml logs -f

# Stop
docker compose -f docker-compose.full.yml down
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | N/A |
| Grafana | http://localhost:3000 | admin/admin |
| Alertmanager | http://localhost:9093 | N/A |

## Custom Image Build

Build a custom Prometheus image with baked-in configuration:

### Dockerfile

```dockerfile
FROM prom/prometheus:v2.54.1

# Copy custom configuration
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY rules/ /etc/prometheus/rules/
COPY alerts/ /etc/prometheus/alerts/

# Set default command arguments
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.enable-lifecycle"]
```

### Build and Run

```bash
# Build
docker build -t my-prometheus:latest .

# Build with specific version
docker build --build-arg PROMETHEUS_VERSION=v2.54.1 -t my-prometheus:v2.54.1 .

# Run
docker run -d -p 9090:9090 my-prometheus:latest
```

## Persistent Storage

### Named Volumes (Recommended)

```yaml
volumes:
  prometheus_data:
    driver: local
```

Data persists across container restarts and removals.

### Bind Mounts

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /data/prometheus:/prometheus \
  prom/prometheus
```

### Remove Data

```bash
# Remove containers and volumes
docker compose down -v

# Or remove specific volume
docker volume rm prometheus_data
```

## Networking

### Access Host Services

To scrape services running on the host:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "host-app"
    static_configs:
      - targets: ["host.docker.internal:8080"]
```

### Docker Network Discovery

Create a shared network for service discovery:

```yaml
# docker-compose.yml
networks:
  monitoring:
    driver: bridge

services:
  prometheus:
    networks:
      - monitoring

  my-app:
    networks:
      - monitoring
```

Then scrape by container name:

```yaml
scrape_configs:
  - job_name: "my-app"
    static_configs:
      - targets: ["my-app:8080"]
```

## Common Operations

### View Logs

```bash
# Single container
docker logs prometheus -f

# Docker Compose
docker compose logs -f prometheus
docker compose logs -f  # All services
```

### Reload Configuration

```bash
# Using lifecycle API
curl -X POST http://localhost:9090/-/reload

# Or restart container
docker restart prometheus
```

### Check Status

```bash
# Container status
docker ps | grep prometheus

# Health check
curl http://localhost:9090/-/healthy

# Ready check
curl http://localhost:9090/-/ready
```

### Execute Commands in Container

```bash
# Check Prometheus version
docker exec prometheus prometheus --version

# Validate configuration
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Query metrics
docker exec prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=up'
```

## Resource Limits

Set resource constraints in Docker Compose:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.54.1
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

Or with `docker run`:

```bash
docker run -d \
  --name prometheus \
  --cpus="2" \
  --memory="4g" \
  -p 9090:9090 \
  prom/prometheus
```

## Upgrade

### Docker Compose

```bash
# Update version in .env or docker-compose.yml
# Then:
docker compose pull
docker compose up -d
```

### Single Container

```bash
# Stop and remove old container
docker stop prometheus
docker rm prometheus

# Pull new image
docker pull prom/prometheus:v2.55.0

# Start with new version
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v prometheus_data:/prometheus \
  prom/prometheus:v2.55.0
```

## Cleanup

### Stop Services

```bash
# Docker Compose
docker compose down

# Single container
docker stop prometheus
```

### Remove Everything

```bash
# Containers, networks, and volumes
docker compose down -v

# Remove images
docker rmi prom/prometheus:v2.54.1
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs prometheus

# Common issues:
# - Port already in use
# - Invalid configuration file
# - Permission issues on mounted volumes
```

### Configuration Errors

```bash
# Validate configuration
docker run --rm \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
  prom/prometheus \
  promtool check config /etc/prometheus/prometheus.yml
```

### Permission Denied on Volumes

```bash
# Fix permissions (Linux)
sudo chown -R 65534:65534 /path/to/data

# Or run as root (not recommended for production)
docker run -d --user root -p 9090:9090 prom/prometheus
```

### Cannot Reach Host Services

Ensure you're using `host.docker.internal` (Docker Desktop) or the host's IP address:

```bash
# Get host IP on Linux
ip route | grep docker0 | awk '{print $9}'

# Use in prometheus.yml
# targets: ["172.17.0.1:8080"]
```

### High Memory Usage

```bash
# Check container stats
docker stats prometheus

# Reduce retention
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  prom/prometheus \
  --storage.tsdb.retention.time=7d
```

## Directory Structure

```
docker/
├── docker-compose.yml       # Single-node Prometheus
├── docker-compose.full.yml  # Full monitoring stack
├── Dockerfile               # Custom image build
├── prometheus.yml           # Prometheus configuration
├── .env.example             # Environment variables template
├── alertmanager/
│   └── alertmanager.yml     # Alertmanager configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/     # Auto-provisioned datasources
│   │   └── dashboards/      # Dashboard provisioning
│   └── dashboards/          # Dashboard JSON files
├── rules/                   # Recording rules
└── alerts/                  # Alerting rules
```

## Production Considerations

Docker is great for development but consider these for production:

1. **Use Kubernetes** - Better orchestration, scaling, and reliability
2. **External storage** - Use remote write to Mimir/Thanos for long-term storage
3. **High availability** - Docker alone doesn't provide HA
4. **Monitoring** - Monitor the monitoring (meta-monitoring)
5. **Backups** - Implement regular data backups

## Next Steps

1. [Configure scrape targets](../configuration/README.md)
2. [Set up alerting](../configuration/alerting.md)
3. [Upgrade to Kubernetes](./helm.md) for production
