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

## High Availability (clustered) setup

Alertmanager has built-in HA via a gossip cluster (Hashicorp memberlist) — no external
coordinator needed. Run multiple identical replicas; they replicate **silences** and the
**notification log** to each other so notifications are de-duplicated across the cluster.
Refs: [Prometheus HA docs](https://prometheus.io/docs/alerting/latest/high_availability/),
[PromLabs overview](https://promlabs.com/blog/2023/08/31/high-availability-for-prometheus-and-alertmanager-an-overview/).

How it behaves:
- **Fail-open, at-least-once**: on a network partition each side keeps sending, so you may
  get duplicate notifications rather than a missed alert. This is by design.
- **Staggered sends by peer position**: replicas order themselves and wait `position ×
  peer-timeout` (0s, 15s, 30s, …) before sending. If replica 0 is down, replica 1 sends
  after 15s. This is why a survivor still notifies.
- **No quorum/voting**: any N replicas tolerate N-1 failures; odd vs even count doesn't
  matter. 2-3 replicas is typical.

Run it:

```bash
# Docker (3-node cluster; UIs on 9093 / 9193 / 9293)
cd install/docker
docker compose -f docker-compose-ha.yaml up -d

# Kubernetes (3-replica StatefulSet; edit the webhook URL in the ConfigMap first)
kubectl create namespace alerting --dry-run=client -o yaml | kubectl apply -f -
kubectl -n alerting apply -f install/k8s/alertmanager-ha.yaml
kubectl -n alerting rollout status statefulset/alertmanager

# verify the cluster formed (expect status "ready" and 3 peers)
kubectl -n alerting exec alertmanager-0 -- wget -qO- http://localhost:9093/api/v2/status \
  | grep -o '"status":"[a-z]*"'
```

**Critical rules for HA (from the Prometheus docs):**
- **Senders must target ALL replicas, never a load balancer.** A LB is a single point of
  failure and breaks each replica's independent processing. Point the Loki ruler at the
  comma-separated list of all replicas:
  ```yaml
  ruler:
    alertmanager_url: >-
      http://alertmanager-0.alertmanager-headless.alerting.svc.cluster.local:9093,
      http://alertmanager-1.alertmanager-headless.alerting.svc.cluster.local:9093,
      http://alertmanager-2.alertmanager-headless.alerting.svc.cluster.local:9093
  ```
- **`--cluster.advertise-address` must be a routable IP, not a hostname.** In k8s it's set
  to the pod IP via the downward API (`status.podIP`); a hostname silently breaks gossip.
- **Open cluster port 9094 (TCP + UDP) between all replicas.**
- **Keep gossip/timeout flags identical across replicas**, and run NTP (clock skew causes
  spurious duplicates).
- Each replica persists silences + notification log (Docker volumes / k8s per-pod PVC) so
  state survives restarts.

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

HA teardown:
```bash
# Docker
cd install/docker && docker compose -f docker-compose-ha.yaml down -v
# Kubernetes (StatefulSet PVCs are not auto-deleted)
kubectl -n alerting delete -f install/k8s/alertmanager-ha.yaml
kubectl -n alerting delete pvc -l app=alertmanager
kubectl delete namespace alerting
```
