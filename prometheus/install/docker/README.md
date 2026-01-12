# Docker Installation for Prometheus

This directory contains Docker Compose configurations for deploying Prometheus.

## Quick Start

### Single-Node Prometheus

```bash
# Start Prometheus
docker-compose up -d

# View logs
docker-compose logs -f prometheus

# Stop Prometheus
docker-compose down
```

### Full Monitoring Stack (Prometheus + Grafana + Alertmanager)

```bash
# Start full stack
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose -f docker-compose.full.yml logs -f

# Stop full stack
docker-compose -f docker-compose.full.yml down
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:
- `PROMETHEUS_VERSION`: Prometheus Docker image version
- `PROMETHEUS_PORT`: Host port for Prometheus (default: 9090)
- `PROMETHEUS_RETENTION`: Data retention period (default: 15d)
- `GRAFANA_PORT`: Host port for Grafana (default: 3000)
- `ALERTMANAGER_PORT`: Host port for Alertmanager (default: 9093)

### Prometheus Configuration

Edit `prometheus.yml` to customize scrape configurations.

### Alertmanager Configuration

Edit `alertmanager/alertmanager.yml` to configure alert routing and receivers.

## Custom Image Build

Build a custom Prometheus image with baked-in configuration:

```bash
docker build -t my-prometheus:latest .
docker build --build-arg PROMETHEUS_VERSION=v2.54.1 -t my-prometheus:v2.54.1 .
```

## Access Points

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Prometheus | http://localhost:9090 | N/A |
| Grafana | http://localhost:3000 | admin/admin |
| Alertmanager | http://localhost:9093 | N/A |

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
│   │   └── dashboards/      # Dashboard provisioning config
│   └── dashboards/          # Dashboard JSON files
├── rules/                   # Recording rules
└── alerts/                  # Alerting rules
```

## Persistent Storage

Data is persisted using Docker named volumes:
- `prometheus_data`: Prometheus TSDB data
- `grafana_data`: Grafana configuration and dashboards
- `alertmanager_data`: Alertmanager state

To remove all data:
```bash
docker-compose down -v
```
