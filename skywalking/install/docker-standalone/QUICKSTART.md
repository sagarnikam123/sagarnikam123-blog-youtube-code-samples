# Quick Start Guide

## Start Everything

```bash
./start-fuzzy-train.sh
```

Or manually:
```bash
docker compose -f docker-compose.fuzzy-train.yml up -d
```

## Access SkyWalking UI

Open http://localhost:8080

Wait 1-2 minutes, then:
1. Select "General Service" layer
2. Find `fuzzy-train-python` or `fuzzy-train-java`
3. Click on service → Go to "Log" tab

## View Logs

```bash
# All services
docker compose -f docker-compose.fuzzy-train.yml logs -f

# Specific service
docker compose -f docker-compose.fuzzy-train.yml logs -f fuzzy-train-python
```

## Check Status

```bash
docker compose -f docker-compose.fuzzy-train.yml ps
```

## Stop Everything

```bash
./stop-fuzzy-train.sh
```

Or manually:
```bash
# Keep data
docker compose -f docker-compose.fuzzy-train.yml down

# Remove data
docker compose -f docker-compose.fuzzy-train.yml down -v
```

## Troubleshooting

### Services not showing in UI?
Wait 2-3 minutes for registration. Check logs:
```bash
docker compose -f docker-compose.fuzzy-train.yml logs oap
```

### OAP not healthy?
```bash
curl http://localhost:12800/healthcheck
```

### BanyanDB issues?
```bash
curl http://localhost:17913/api/healthz
```

### Test Teams webhook?
```bash
curl -X POST \
  'https://default3d08c29d04bc44cca8673238f9d6e4.01.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/eedba587755f4a1ab3bfc24043ecca0d/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=KQe6e02uzatx84L94u-iUDjyg56UQm7pxveo91giPtY' \
  -H 'Content-Type: application/json' \
  -d '[{"scopeId":1,"scope":"SERVICE","name":"test","id0":"test","id1":"","ruleName":"test_rule","alarmMessage":"Test alert","startTime":1234567890000,"tags":[{"key":"level","value":"WARNING"}]}]'
```

## Adjust Log Rate

Edit `docker-compose.fuzzy-train.yml`:
```yaml
command:
  - "--lines-per-second"
  - "5"  # Change from 1 to 5
```

Then:
```bash
docker compose -f docker-compose.fuzzy-train.yml restart fuzzy-train-python
```

## Ports

| Service | Port | URL |
|---------|------|-----|
| UI | 8080 | http://localhost:8080 |
| OAP HTTP | 12800 | http://localhost:12800 |
| OAP gRPC | 11800 | - |
| OAP Metrics | 1234 | http://localhost:1234/metrics |
| BanyanDB | 17912/17913 | http://localhost:17913/api/healthz |

## What's Running?

- **BanyanDB**: Storage backend
- **OAP**: SkyWalking server with alarm rules
- **UI**: Web interface
- **fuzzy-train-python**: Python log generator (1/sec)
- **fuzzy-train-java**: Java log generator (1/sec)

## Alerts

Configured in `config/alarm-settings.yml`:
- Response time > 1s
- SLA < 80%
- Error logs > 10 in 5 min
- Warning logs > 50 in 5 min

Sent to Microsoft Teams webhook automatically.
