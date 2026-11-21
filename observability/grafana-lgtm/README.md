# Grafana LGTM installation guide

Installation modes for the unified LGTM stack are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Docker all-in-one (`grafana/otel-lgtm`) | Available | [`install/docker/standalone/`](install/docker/standalone/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Helm per-component (K8s) | Available | [`install/helm/components/`](install/helm/components/) |
| Operators per-component (K8s) | Available | [`install/operator/components/`](install/operator/components/) |

The unified Docker Compose setup is the Phase 1 benchmark deployment. The `grafana/otel-lgtm` image is useful for local development. For Kubernetes production, deploy per-component using the official Helm charts.
