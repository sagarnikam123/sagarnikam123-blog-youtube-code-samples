# Alertmanager

Prometheus Alertmanager — receives alerts from Loki ruler (and Prometheus) and routes them to notification channels.

## Quick Start (Docker)

```bash
cd install/docker
docker compose up -d
```

- **UI**: http://localhost:9093
- **Webhook logs**: `docker compose logs -f webhook-receiver`

## Configuration

Config file: `configs/alertmanager.yaml`

### Receivers

Currently configured with a webhook receiver (prints alerts to container logs). Replace with:
- Slack: `slack_configs`
- Email: `email_configs`
- PagerDuty: `pagerduty_configs`
- OpsGenie: `opsgenie_configs`

### Testing

Send a test alert manually:
```bash
curl -X POST http://localhost:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {"alertname": "TestAlert", "severity": "warning", "job": "test"},
    "annotations": {"summary": "This is a test alert"},
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

## Integration with Loki Ruler

The Loki config at `loki/configs/v3.x/v3.7.x/loki-3.7.x-ruler-alerting-docker.yaml` points to this Alertmanager via:
```yaml
ruler:
  alertmanager_url: http://alertmanager:9093
```
