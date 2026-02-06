# SkyWalking Docker Standalone with Monitoring Features

Single-node Docker deployment with BanyanDB storage and optional monitoring for databases, message queues, gateways, and infrastructure.

## Quick Start

```bash
# Start core SkyWalking only
docker compose up -d

# Start with sample services (MySQL, Redis, Nginx, PostgreSQL, MongoDB, Elasticsearch) for testing
docker compose --profile examples up -d

# Access UI
open http://localhost:8080
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Network                                     │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │  BanyanDB   │  │  OAP Server │  │     UI      │                          │
│  │  Port:17912 │◄─┤  gRPC:11800 │◄─┤  Port:8080  │                          │
│  │  Metrics:   │  │  HTTP:12800 │  │             │                          │
│  │    2121     │  │             │  │             │                          │
│  └─────────────┘  └──────▲──────┘  └─────────────┘                          │
│                          │                                                   │
│                          │ OTLP                                              │
│                          │                                                   │
│                   ┌──────┴──────┐                                            │
│                   │    OTel     │◄─── Prometheus Scrape                      │
│                   │  Collector  │                                            │
│                   └──────▲──────┘                                            │
│                          │                                                   │
│    ┌─────────────────────┼─────────────────────┐                             │
│    │         │           │           │         │                             │
│ ┌──┴──┐  ┌───┴───┐  ┌────┴────┐  ┌───┴───┐  ┌──┴──┐                         │
│ │MySQL│  │ Redis │  │PostgreSQL│ │MongoDB│  │Nginx│  ... (Exporters)        │
│ └─────┘  └───────┘  └─────────┘  └───────┘  └─────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Available Profiles

| Profile | Description | What it starts |
|---------|-------------|----------------|
| `examples` | Sample services + exporters for testing | MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch, Nginx + their exporters |
| `monitoring` | ALL exporters (no sample services) | All exporters |
| **Databases** | | |
| `mysql` | MySQL monitoring | MySQL exporter |
| `postgresql` | PostgreSQL monitoring | PostgreSQL exporter |
| `redis` | Redis monitoring | Redis exporter |
| `mongodb` | MongoDB monitoring | MongoDB exporter |
| `elasticsearch` | Elasticsearch monitoring | Elasticsearch exporter |
| **Message Queues** | | |
| `kafka` | Kafka monitoring | Kafka exporter |
| `rabbitmq` | RabbitMQ monitoring | RabbitMQ exporter |
| `pulsar` | Apache Pulsar monitoring | Scrapes built-in metrics |
| `rocketmq` | Apache RocketMQ monitoring | RocketMQ exporter |
| `activemq` | Apache ActiveMQ monitoring | JMX exporter |
| **Gateways** | | |
| `nginx` | Nginx monitoring | Nginx exporter |
| `apisix` | Apache APISIX monitoring | Scrapes built-in Prometheus plugin |
| `kong` | Kong Gateway monitoring | Scrapes built-in Prometheus plugin |
| **Stream Processing** | | |
| `flink` | Apache Flink monitoring | Scrapes built-in Prometheus reporter |
| **Infrastructure** | | |
| `infrastructure` | Linux VM monitoring | Node exporter |
| `banyandb` | BanyanDB self-monitoring | Scrapes BanyanDB metrics |

## Usage Examples

### Testing with Sample Services

```bash
# Start everything including sample databases
docker compose --profile examples up -d

# This starts:
# - Core: BanyanDB, OAP, UI
# - Sample services: MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch, Nginx
# - Exporters: All database and nginx exporters
# - OTel Collector
```

### Monitoring Your Own Services

```bash
# 1. Copy and edit environment file
cp .env.example .env

# 2. Configure your service endpoints in .env
# MYSQL_HOST=your-mysql-host
# REDIS_HOST=your-redis-host
# KAFKA_BROKERS=your-kafka:9092

# 3. Start with specific profiles
docker compose --profile mysql --profile redis --profile kafka up -d
```

### Enable All Monitoring

```bash
docker compose --profile monitoring up -d
```

### Monitor BanyanDB Storage

```bash
# BanyanDB metrics are always available at port 2121
# Enable scraping with banyandb profile
docker compose --profile banyandb up -d
```

## Viewing Dashboards

After starting with `--profile examples`:

1. Open http://localhost:8080
2. Wait 1-2 minutes for metrics to be collected
3. Navigate to:
   - **Marketplace → Self Observability** - OAP server metrics
   - **MySQL** menu - MySQL database metrics
   - **PostgreSQL** menu - PostgreSQL database metrics
   - **Redis** menu - Redis cache metrics
   - **MongoDB** menu - MongoDB database metrics
   - **Elasticsearch** menu - Elasticsearch cluster metrics
   - **Nginx** menu - Nginx web server metrics

## Core Services Ports

| Service | Port | Description |
|---------|------|-------------|
| UI | 8080 | Web interface |
| OAP gRPC | 11800 | Agent communication |
| OAP HTTP | 12800 | REST API |
| BanyanDB gRPC | 17912 | Storage backend |
| BanyanDB HTTP | 17913 | Health check |
| BanyanDB Metrics | 2121 | Prometheus metrics |
| OTel Collector | 4317/4318 | OTLP receiver |

### Sample Services Ports (with `--profile examples`)

| Service | Port | Description |
|---------|------|-------------|
| Sample MySQL | 3307 | Test MySQL instance |
| Sample PostgreSQL | 5433 | Test PostgreSQL instance |
| Sample Redis | 6379 | Test Redis instance |
| Sample MongoDB | 27017 | Test MongoDB instance |
| Sample Elasticsearch | 9200 | Test Elasticsearch instance |
| Sample Nginx | 8081 | Test Nginx instance |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# SkyWalking versions
SKYWALKING_VERSION=10.3.0
BANYANDB_VERSION=0.9.0

# MySQL monitoring target
MYSQL_HOST=sample-mysql
MYSQL_PORT=3306
MYSQL_USER=exporter
MYSQL_EXPORTER_PASSWORD=exporterpassword

# PostgreSQL monitoring target
POSTGRES_HOST=sample-postgresql
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis monitoring target
REDIS_HOST=sample-redis
REDIS_PORT=6379

# MongoDB monitoring target
MONGODB_HOST=sample-mongodb
MONGODB_PORT=27017

# Elasticsearch monitoring target
ES_HOST=sample-elasticsearch
ES_PORT=9200

# Kafka monitoring target
KAFKA_BROKERS=kafka:9092

# RabbitMQ monitoring target
RABBITMQ_HOST=rabbitmq
RABBITMQ_MANAGEMENT_PORT=15672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

### OTel Collector Configuration

The OTel Collector config is in `otel-collector/config.yaml`. Key points:

- **job_name must match SkyWalking's OTel rules**:
  - `mysql-monitoring` for MySQL
  - `postgresql-monitoring` for PostgreSQL
  - `redis-monitoring` for Redis
  - `mongodb-monitoring` for MongoDB
  - `elasticsearch-monitoring` for Elasticsearch
  - `kafka-monitoring` for Kafka
  - `rabbitmq-monitoring` for RabbitMQ
  - `pulsar-monitoring` for Pulsar
  - `rocketmq-monitoring` for RocketMQ
  - `activemq-monitoring` for ActiveMQ
  - `nginx-monitoring` for Nginx
  - `apisix-monitoring` for APISIX
  - `kong-monitoring` for Kong
  - `flink-monitoring` for Flink
  - `banyandb-monitoring` for BanyanDB
  - `skywalking-so11y` for OAP self-observability
  - `vm-monitoring` for Linux VMs

- **Required labels**:
  - `host_name` - Service hostname
  - `service_instance_id` - Instance identifier

## Troubleshooting

### Check service status

```bash
docker compose ps
```

### Check OTel Collector logs

```bash
docker compose logs otel-collector
```

### Verify metrics are being scraped

```bash
# Check collector metrics
curl http://localhost:8888/metrics

# Check OAP health
curl http://localhost:12800/healthcheck

# Check BanyanDB metrics
curl http://localhost:2121/metrics
```

### Query services via GraphQL

```bash
# List MySQL services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"MYSQL\") { name } }"}'

# List PostgreSQL services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"POSTGRESQL\") { name } }"}'

# List Redis services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"REDIS\") { name } }"}'

# List MongoDB services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"MONGODB\") { name } }"}'

# List Elasticsearch services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"ELASTICSEARCH\") { name } }"}'

# List OAP self-observability
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"SO11Y_OAP\") { name } }"}'

# List BanyanDB services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"BANYANDB\") { name } }"}'
```

### Common Issues

1. **Dashboard not appearing**: Wait 1-2 minutes for metrics to be collected.

2. **"Failed to scrape" in OTel logs**: Target service not reachable. Check network connectivity.

3. **Services show but no metrics**: Verify `job_name` in OTel config matches SkyWalking's OTel rules.

4. **BanyanDB not starting**: Ensure you're using v0.9.0+ with correct flags (`--metadata-root-path`, etc.)

## Commands Reference

```bash
# Start core only
docker compose up -d

# Start with sample services
docker compose --profile examples up -d

# Start with specific monitoring
docker compose --profile mysql --profile postgresql up -d

# Start with all monitoring (no samples)
docker compose --profile monitoring up -d

# Stop everything
docker compose --profile examples down

# Remove all data
docker compose --profile examples down -v

# View logs
docker compose logs -f oap
docker compose logs -f otel-collector

# Restart OTel collector after config change
docker compose restart otel-collector
```

## File Structure

```
docker-standalone/
├── docker-compose.yml          # Main compose file with profiles
├── .env.example                # Environment template
├── README.md                   # This file
├── otel-collector/
│   └── config.yaml             # OpenTelemetry Collector configuration
└── examples/
    ├── mysql/
    │   ├── docker-compose.yml  # Standalone MySQL (alternative)
    │   └── init.sql            # MySQL initialization
    ├── redis/
    │   └── docker-compose.yml  # Standalone Redis (alternative)
    └── nginx/
        ├── docker-compose.yml  # Standalone Nginx (alternative)
        └── nginx.conf          # Nginx configuration with stub_status
```
