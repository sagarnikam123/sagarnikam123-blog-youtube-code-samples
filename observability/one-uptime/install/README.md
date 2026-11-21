# OneUptime installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Official single-server install; Phase 2 benchmark |
| Docker standalone | Not published for the full platform | — | OneUptime is a multi-service application |
| Docker Compose cluster | Not documented as an official platform mode | — | Use Kubernetes Helm for distributed deployments |
| Kubernetes standalone | Available through Helm | [`helm/standalone/`](helm/standalone/) | Development/small deployment |
| Kubernetes cluster | Available through Helm | [`helm/cluster/`](helm/cluster/) | Production-oriented deployment |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Official chart |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | Official chart |
| Binary | Not published for the full platform | — | OneUptime is a multi-service application |
| Operator | Database operators are chart dependencies/options | — | No separate OneUptime platform operator |

The Kubernetes Agent and Docker Agent are telemetry collectors, not alternate installations of the OneUptime platform.

Official sources: [Docker Compose](https://oneuptime.com/docs/installation/docker-compose), [Helm chart](https://github.com/OneUptime/helm-chart), [Kubernetes Agent](https://oneuptime.com/docs/telemetry/kubernetes-agent).
