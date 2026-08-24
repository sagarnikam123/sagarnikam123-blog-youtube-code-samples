# SigNoz installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary/systemd standalone | Available | [`binary/standalone/`](binary/standalone/) | Linux bare-metal via Foundry systemd casting |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark via Foundry compose casting |
| Docker Swarm | Available | [`docker-swarm/`](docker-swarm/) | Foundry compose casting with docker-swarm mode |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Official SigNoz Helm chart, single release |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | Official SigNoz Helm chart, production sizing |
| Kubernetes Kustomize | Available | [`k8s/kustomize/`](k8s/kustomize/) | Foundry Kustomize casting generates manifests |
| ArgoCD | Documentation only | — | Uses the Helm chart via ArgoCD Application CRD |
| ECS | Documentation only | — | Uses Foundry ECS Terraform casting |
| Operator | Not published by SigNoz | — | Do not invent one |

All deployments use the Foundry CLI (`foundryctl`) or direct Helm commands.

Official sources:
- [Get started](https://signoz.io/docs/install/)
- [Linux systemd](https://signoz.io/docs/install/linux/)
- [Docker standalone](https://signoz.io/docs/install/docker/)
- [Docker Swarm](https://signoz.io/docs/install/docker-swarm/)
- [Kubernetes / Helm](https://signoz.io/docs/install/kubernetes/others/)
- [Kubernetes / Kustomize](https://signoz.io/docs/install/kubernetes/)
- [ArgoCD](https://signoz.io/docs/install/argocd/)
- [ECS](https://signoz.io/docs/install/ecs/)
