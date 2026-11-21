# Coroot — Kubernetes Operator (recommended)

The `coroot-operator` is the recommended way to deploy Coroot on Kubernetes or OpenShift. It manages all components: Coroot server, node-agent DaemonSet, cluster-agent, ClickHouse, and Prometheus.

## Install

```bash
helm repo add coroot https://coroot.github.io/helm-charts
helm repo update coroot

# Install the operator
helm install coroot-operator coroot/coroot-operator \
  --namespace coroot --create-namespace

# Create a Coroot custom resource (use the example or customize)
kubectl apply -f coroot.yaml
kubectl -n coroot get pods
```

## Example coroot.yaml

```yaml
apiVersion: coroot.com/v1
kind: Coroot
metadata:
  name: coroot
  namespace: coroot
spec:
  clickhouse:
    shards: 1
    replicas: 1
    storage:
      size: 50Gi
  nodeAgent:
    logCollector:
      collectLogEntries: true
    ebpfTracer:
      enabled: true
    ebpfProfiler:
      enabled: true
```

## Notes

- The operator auto-upgrades all components unless image versions are pinned.
- Supports both Community and Enterprise editions.
- Supports multi-cluster observability with `remoteCoroot`.
- eBPF node-agent requires Linux kernel 5.8+ on cluster nodes.
- For ArgoCD integration, see [Coroot ArgoCD guide](https://docs.coroot.com/guides/argocd).

Official guide: [Coroot Kubernetes Operator](https://docs.coroot.com/installation/k8s-operator/).
