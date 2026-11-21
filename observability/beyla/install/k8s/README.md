# Beyla — Kubernetes DaemonSet (raw manifests)

Deploy Beyla as a DaemonSet using plain YAML manifests, without Helm.

## Apply

```bash
kubectl create namespace beyla
kubectl apply -f daemonset.yaml
kubectl apply -f configmap.yaml
kubectl -n beyla get pods
```

## Generate traffic and check metrics

```bash
kubectl port-forward -n beyla daemonset/beyla 9400:9400
curl http://localhost:9400/metrics
```

## Notes

- The DaemonSet runs privileged pods for eBPF access.
- ConfigMap holds the Beyla configuration YAML.
- Adjust `discovery.instrument` to target specific namespaces or ports.
- For Helm-based deployment, see [`../helm/`](../helm/).

Official guide: [Deploy Beyla in Kubernetes](https://grafana.com/docs/beyla/latest/setup/kubernetes/).
