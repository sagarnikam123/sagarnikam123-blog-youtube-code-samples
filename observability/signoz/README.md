# SigNoz installation guide

Installation modes for SigNoz are organized under [`install/`](install/).

## Available modes

| Mode | Status | Guide |
|:-----|:-------|:------|
| Binary/systemd standalone | Available | [`install/binary/standalone/`](install/binary/standalone/) |
| Docker Compose standalone | Available | [`install/docker-compose/standalone/`](install/docker-compose/standalone/) |
| Docker Swarm | Available | [`install/docker-swarm/`](install/docker-swarm/) |
| Helm standalone | Available | [`install/helm/standalone/`](install/helm/standalone/) |
| Helm cluster | Available | [`install/helm/cluster/`](install/helm/cluster/) |
| Kubernetes Kustomize | Available | [`install/k8s/kustomize/`](install/k8s/kustomize/) |

The Docker Compose setup is the Phase 1 benchmark deployment. Run it from its mode directory so its relative configuration and volume paths resolve correctly.
