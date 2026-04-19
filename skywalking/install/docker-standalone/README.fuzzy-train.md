# SkyWalking with Fuzzy-Train Log Generators + Teams Alerting

Complete Docker setup with:
- SkyWalking OAP + UI
- BanyanDB standalone storage
- Fuzzy-train fake log generators (Python + Java)
- Microsoft Teams webhook alerting

## Quick Start

```bash
# Navigate to directory
cd sagarnikam123-blog-youtube-code-samples/skywalking/install/docker-standalone

# Start all services
docker compose -f docker-compose.fuzzy-train.yml up -d

# Check status
docker compose -f docker-compose.fuzzy-train.yml ps

# View logs
docker compose -f docker-compose.fuzzy-train.yml logs -f
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| SkyWalking UI | http://localhost:8080 | Web interface |
| OAP gRPC | localhost:11800 | Agent communication |
| OAP HTTP | localhost:12800 | REST API |
| OAP Metrics | http://localhost:1234/metrics | Prometheus metrics |
| BanyanDB gRPC | localhost:17912 | Storage backend |
| BanyanDB HTTP | http://localhost:17913 | Health check |
| BanyanDB Metrics | http://localhost:2121/metrics | Prometheus metrics |

## View Logs in SkyWalking UI

1. Open http://localhost:8080
2. Wait 1-2 minutes for services to register
3. Select "General Service" layer from dropdown
4. Find services:
   - `fuzzy-train-python`
   - `fuzzy-train-java`
5. Click on a service
6. Go to "Log" tab to see generated logs

## Services Running

### Core Services
- **banyandb**: Storage backend (standalone mode)
- **oap**: SkyWalking OAP server with alarm rules
- **ui**: SkyWalking web interface

### Log Generators
- **fuzzy-train-python**: Python-based fake log generator (1 log/sec)
- **fuzzy-train-java**: Java-based fake log generator (1 log/sec)

## Alerting Configuration

Alerts are configured in `config/alarm-settings.yml` and sent to Microsoft Teams webhook.

### Alarm Rules

| Rule | Condition | Severity |
|------|-----------|----------|
| Service Response Time | > 1s for 3 minutes | WARNING |
| Service SLA | < 80% for 2 minutes | CRITICAL |
| Service Percentile | > 1s (p50/75/90/95/99) | WARNING |
| Instance Response Time | > 1s for 2 minutes | WARNING |
| Endpoint Response Time | > 1s for 2 minutes | WARNING |
| Database Response Time | > 1s for 2 minutes | WARNING |
| Error Logs | > 10 ERROR logs in 5 min | CRITICAL |
| Warning Logs | > 50 WARN logs in 5 min | WARNING |

### Teams Webhook

The webhook URL is configured in `config/alarm-settings.yml`:
```yaml
hooks:
  webhook:
    teams-alerts:
      is-default: true
      urls:
        - <YOUR_POWER_AUTOMATE_WEBHOOK_URL>
```

## Adjust Log Generation Rate

Edit `docker-compose.fuzzy-train.yml` and change `--lines-per-second`:

```yaml
fuzzy-train-python:
  command:
    - "--lines-per-second"
    - "5"  # Change from 1 to 5 logs per second
```

Then restart:
```bash
docker compose -f docker-compose.fuzzy-train.yml restart fuzzy-train-python
```

## Troubleshooting

### Check service health

```bash
# All services
docker compose -f docker-compose.fuzzy-train.yml ps

# OAP health
curl http://localhost:12800/healthcheck

# BanyanDB health
curl http://localhost:17913/api/healthz
```

### View logs

```bash
# All services
docker compose -f docker-compose.fuzzy-train.yml logs -f

# Specific service
docker compose -f docker-compose.fuzzy-train.yml logs -f oap
docker compose -f docker-compose.fuzzy-train.yml logs -f fuzzy-train-python
docker compose -f docker-compose.fuzzy-train.yml logs -f fuzzy-train-java
```

### Verify log generators are working

```bash
# Python generator
docker compose -f docker-compose.fuzzy-train.yml logs fuzzy-train-python --tail=20

# Java generator
docker compose -f docker-compose.fuzzy-train.yml logs fuzzy-train-java --tail=20
```

### Query services via GraphQL

```bash
# List all services
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"GENERAL\") { name } }"}'

# Check if fuzzy-train services are registered
curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"GENERAL\") { name } }"}' | grep fuzzy-train
```

### Test Teams webhook manually

```bash
curl -X POST \
  '<YOUR_POWER_AUTOMATE_WEBHOOK_URL>' \
  -H 'Content-Type: application/json' \
  -d '[{
    "scopeId": 1,
    "scope": "SERVICE",
    "name": "test-service",
    "id0": "test-id",
    "id1": "",
    "ruleName": "test_rule",
    "alarmMessage": "Test alarm from Docker setup",
    "startTime": 1234567890000,
    "tags": [{"key": "level", "value": "WARNING"}]
  }]'
```

## Stop and Cleanup

```bash
# Stop all services
docker compose -f docker-compose.fuzzy-train.yml down

# Stop and remove volumes (deletes all data)
docker compose -f docker-compose.fuzzy-train.yml down -v
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   BanyanDB   │  │  OAP Server  │  │      UI      │          │
│  │  Port:17912  │◄─┤  gRPC:11800  │◄─┤  Port:8080   │          │
│  │  HTTP:17913  │  │  HTTP:12800  │  │              │          │
│  │  Metrics:    │  │  Metrics:    │  │              │          │
│  │    2121      │  │    1234      │  │              │          │
│  └──────────────┘  └──────▲───────┘  └──────────────┘          │
│                            │                                     │
│                            │ gRPC (11800)                        │
│                            │                                     │
│              ┌─────────────┴─────────────┐                       │
│              │                           │                       │
│       ┌──────┴──────┐           ┌───────┴──────┐                │
│       │ fuzzy-train │           │ fuzzy-train  │                │
│       │   Python    │           │     Java     │                │
│       │ (1 log/sec) │           │ (1 log/sec)  │                │
│       └─────────────┘           └──────────────┘                │
│                                                                  │
│                            │                                     │
│                            │ Webhook (HTTPS)                     │
│                            ▼                                     │
│                   ┌────────────────┐                             │
│                   │ Microsoft Teams│                             │
│                   │    Webhook     │                             │
│                   └────────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Files

- `docker-compose.fuzzy-train.yml` - Main compose file
- `config/alarm-settings.yml` - Alarm rules and Teams webhook
- `ui-init-templates/menu.yaml` - UI menu customization (optional)

## Data Persistence

Data is stored in Docker volumes:
- `banyandb-data` - All SkyWalking data (traces, logs, metrics)

To backup:
```bash
docker run --rm -v skywalking_banyandb-data:/data -v $(pwd):/backup alpine tar czf /backup/banyandb-backup.tar.gz /data
```

To restore:
```bash
docker run --rm -v skywalking_banyandb-data:/data -v $(pwd):/backup alpine tar xzf /backup/banyandb-backup.tar.gz -C /
```

## Source Information

- Fuzzy-train repository: https://github.com/sagarnikam123/fuzzy-train
- SkyWalking documentation: https://skywalking.apache.org/
- BanyanDB documentation: https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/
