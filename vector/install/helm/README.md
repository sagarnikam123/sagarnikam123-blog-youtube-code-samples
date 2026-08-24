# Vector — Helm chart (Kubernetes)

The official Vector Helm chart supports two roles:
- **Agent** (DaemonSet): collects logs/metrics from each node
- **Aggregator** (StatefulSet): receives from agents, processes, and routes to backends

## Install Agent

```bash
helm repo add vector https://helm.vector.dev
helm repo update
helm install vector vector/vector \
  --namespace vector --create-namespace \
  --values values-agent.yaml
```

## Install Aggregator

```bash
helm install vector-aggregator vector/vector \
  --namespace vector --create-namespace \
  --values values-aggregator.yaml
```

## Notes

- Replace `console` sinks with real backends (see [examples](../../examples/)).
- Agent sends to Aggregator via `type: vector` sink/source pair on port 6000.
- Pin chart version for reproducibility.

Official docs: [vector.dev/docs/setup/installation/package-managers/helm](https://vector.dev/docs/setup/installation/package-managers/helm/).
