# Vector — Kubernetes DaemonSet (raw manifests)

## Apply

```bash
kubectl create namespace vector
kubectl apply -f configmap.yaml
kubectl apply -f daemonset.yaml
kubectl -n vector get pods
```

## Verify

```bash
kubectl -n vector logs daemonset/vector | head -20
```

## Notes

- DaemonSet mounts `/var/log` and `/var/lib/docker` to access pod logs.
- ConfigMap holds the Vector pipeline config.
- Replace `console` sink with a real backend from [examples](../../examples/).
- For Helm-based deployment, see [`../helm/`](../helm/).

Official docs: [vector.dev/docs/setup/installation/platforms/kubernetes](https://vector.dev/docs/setup/installation/platforms/kubernetes/).
