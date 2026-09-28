# Alertmanager

Prometheus Alertmanager — receives alerts from Loki ruler (and Prometheus) and routes them to notification channels.

## Quick Start (Docker)

```bash
cd install/docker
docker compose up -d
```

- **UI**: http://localhost:9093
- **Webhook logs**: `docker compose logs -f webhook-receiver`

## Quick Start (Kubernetes)

```bash
kubectl create namespace alerting --dry-run=client -o yaml | kubectl apply -f -
# EDIT install/k8s/alertmanager.yaml first: set the webhook URL in the ConfigMap
kubectl -n alerting apply -f install/k8s/alertmanager.yaml
kubectl -n alerting rollout status deploy/alertmanager

kubectl -n alerting port-forward svc/alertmanager 9093:9093 &   # http://localhost:9093
```

Point the Loki ruler at it (in-cluster):
```yaml
ruler:
  alertmanager_url: http://alertmanager.alerting.svc.cluster.local:9093
  enable_alertmanager_v2: true
  external_url: http://<grafana-or-loki-host>   # MUST include a scheme, else Alertmanager rejects with 422
```

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

> **Why a standalone Alertmanager (not Grafana's built-in one)?** Grafana's built-in
> Alertmanager can only handle Grafana-managed alerts — it has no ingest endpoint for
> externally-posted alerts. The Loki ruler can only push to an Alertmanager-protocol
> endpoint, so ruler-evaluated alerts (native + data-source-managed) require a real
> standalone Alertmanager like this one. Grafana-managed alerts use Grafana's built-in AM.

## Uninstall

Docker:
```bash
cd install/docker
docker compose down        # keep data volume
docker compose down -v     # also delete alertmanager-data
```

Kubernetes:
```bash
kubectl -n alerting delete -f install/k8s/alertmanager.yaml
kubectl delete namespace alerting
```
