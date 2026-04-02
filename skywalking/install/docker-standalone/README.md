# SkyWalking Docker Standalone - Complete Setup

Complete SkyWalking deployment with BanyanDB storage, fuzzy-train log generators, Teams webhook alerting, and sample monitoring services.

## Quick Start

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Stop and remove all data
docker compose down -v
```

## What's Included

### Core Services
- **SkyWalking OAP Server** (10.3.0) - APM backend with Teams webhook alerting
- **SkyWalking UI** (10.3.0) - Web interface at http://localhost:8080
- **BanyanDB** (0.9.0) - High-performance storage backend

### Log Generators
- **fuzzy-train-python** - Python log generator (1 log/sec)
- **fuzzy-train-java** - Java log generator (1 log/sec)

### Monitoring Stack
- **OpenTelemetry Collector** - Metrics collection and forwarding
- **Prometheus Exporters** - MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch, Nginx

### Sample Services
- **MySQL 8.0** - Port 3307
- **PostgreSQL 17** - Port 5433
- **Redis 7** - Port 6379
- **MongoDB 8** - Port 27017
- **Elasticsearch 8.17** - Port 9200
- **Nginx 1.27** - Port 8081

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| SkyWalking UI | http://localhost:8080 | Main web interface |
| OAP HTTP API | http://localhost:12800 | REST API |
| OAP gRPC | localhost:11800 | Agent connections |
| OAP Metrics | http://localhost:1234/metrics | Prometheus metrics |
| BanyanDB Health | http://localhost:17913/api/healthz | Storage health check |
| MySQL | localhost:3307 | Sample database |
| PostgreSQL | localhost:5433 | Sample database |
| Redis | localhost:6379 | Sample cache |
| MongoDB | localhost:27017 | Sample NoSQL |
| Elasticsearch | http://localhost:9200 | Sample search engine |
| Nginx | http://localhost:8081 | Sample web server |

## Viewing Fuzzy-Train Logs

1. Open SkyWalking UI: http://localhost:8080
2. Wait 1-2 minutes for services to register
3. Select "General Service" layer from the dropdown
4. Find services: `fuzzy-train-python` or `fuzzy-train-java`
5. Click on the service name
6. Go to the "Log" tab to view generated logs

## Teams Webhook Alerting

Alerts are configured in `config/alarm-settings.yml` and will be sent to the Microsoft Teams webhook for:
- Service response time > 1s
- Service success rate < 80%
- High percentile response times
- Instance/endpoint performance issues
- Database access delays

To update the webhook URL, edit `config/alarm-settings.yml` and restart OAP:
```bash
docker compose restart oap
```

## Helper Scripts

### Start with Health Checks
```bash
./start-fuzzy-train.sh
```
This script:
- Starts all services
- Waits for OAP to be healthy
- Shows access points and tips

### Stop Services
```bash
./stop-fuzzy-train.sh
```

### Check Health
```bash
./check-health.sh
```

## Service Management

### Start all services
```bash
docker compose up -d
```

### Start specific services
```bash
docker compose up -d oap ui fuzzy-train-java
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f oap
docker compose logs -f fuzzy-train-java

# Last 100 lines
docker compose logs --tail 100 oap
```

### Check status
```bash
docker compose ps
```

### Restart a service
```bash
docker compose restart oap
```

### Stop all services
```bash
docker compose down
```

### Stop and remove volumes (clean slate)
```bash
docker compose down -v
```

## Configuration

### Environment Variables

You can customize the setup by setting environment variables before running `docker compose up`:

```bash
# Example: Change ports
export OAP_GRPC_PORT=11800
export OAP_HTTP_PORT=12800
export UI_PORT=8080

# Example: Adjust log generation rate
export FUZZY_TRAIN_PYTHON_LPS=5  # 5 logs per second
export FUZZY_TRAIN_JAVA_LPS=5

# Example: Change data retention
export RECORD_TTL=7  # days
export METRICS_TTL=14  # days

docker compose up -d
```

### Alarm Configuration

Edit `config/alarm-settings.yml` to:
- Add/remove alarm rules
- Change thresholds
- Update Teams webhook URL
- Configure silence periods

After editing, restart OAP:
```bash
docker compose restart oap
```

## Monitoring External Services

The setup includes exporters for the sample services. To monitor your own external services:

1. Update exporter configurations in `docker-compose.yml`
2. Change connection strings to point to your services
3. Restart the exporters:
```bash
docker compose restart mysqld-exporter postgres-exporter redis-exporter
```

## Troubleshooting

### OAP not starting
```bash
# Check logs
docker compose logs oap

# Common issues:
# - BanyanDB not healthy: wait longer or check banyandb logs
# - Port conflicts: change ports in docker-compose.yml
# - Memory issues: increase JAVA_OPTS in docker-compose.yml
```

### Fuzzy-train services not visible in UI
```bash
# 1. Check if services are running
docker compose ps | grep fuzzy-train

# 2. Check logs for connection issues
docker compose logs fuzzy-train-java
docker compose logs fuzzy-train-python

# 3. Wait 1-2 minutes for registration
# 4. Ensure "General Service" layer is selected in UI
```

### No logs appearing
```bash
# Check if log generators are running
docker compose logs fuzzy-train-java
docker compose logs fuzzy-train-python

# Verify OAP is receiving logs
docker compose logs oap | grep -i log
```

### Teams alerts not working
```bash
# 1. Verify alarm-settings.yml has correct webhook URL
cat config/alarm-settings.yml | grep -A 5 webhook

# 2. Check OAP logs for alarm triggers
docker compose logs oap | grep -i alarm

# 3. Test webhook manually with curl
curl -X POST <your-webhook-url> \
  -H "Content-Type: application/json" \
  -d '{"text": "Test alert from SkyWalking"}'
```

### Sample services not starting
```bash
# Check which service is failing
docker compose ps

# View specific service logs
docker compose logs sample-mysql
docker compose logs sample-elasticsearch

# Common issues:
# - Port conflicts: change ports in docker-compose.yml
# - Memory issues: Elasticsearch needs at least 512MB
# - Volume permissions: check Docker volume permissions
```

## Resource Requirements

### Minimum
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB

### Recommended
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB

### Per Service Memory Usage (Approximate)
- OAP: 512MB-1GB
- BanyanDB: 200-500MB
- UI: 100MB
- Elasticsearch: 512MB-1GB
- MySQL: 200-400MB
- PostgreSQL: 100-200MB
- MongoDB: 200-400MB
- Other services: 50-100MB each

## Data Persistence

All data is stored in Docker volumes:
- `banyandb-data` - SkyWalking metrics and traces
- `sample-mysql-data` - MySQL data
- `sample-postgresql-data` - PostgreSQL data
- `sample-redis-data` - Redis data
- `sample-mongodb-data` - MongoDB data
- `sample-elasticsearch-data` - Elasticsearch data

To backup data:
```bash
docker run --rm -v banyandb-data:/data -v $(pwd):/backup alpine tar czf /backup/banyandb-backup.tar.gz /data
```

To restore data:
```bash
docker run --rm -v banyandb-data:/data -v $(pwd):/backup alpine tar xzf /backup/banyandb-backup.tar.gz -C /
```

## Next Steps

- **Configure ERROR log detection**: See `NEXT-STEPS.md` for LAL configuration
- **Add custom services**: Instrument your applications with SkyWalking agents
- **Customize alarms**: Edit `config/alarm-settings.yml` for your needs
- **Scale up**: Move to Kubernetes for production deployments

## Documentation

- [SkyWalking Documentation](https://skywalking.apache.org/docs/)
- [BanyanDB Documentation](https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/)
- [Fuzzy-Train Repository](https://github.com/sagarnikam123/fuzzy-train)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)

## Support

For issues and questions:
- SkyWalking: https://github.com/apache/skywalking/issues
- This setup: Check logs with `docker compose logs -f`
