# Gatus — Kubernetes standalone (raw manifests)

Deploy Gatus with plain manifests: a ConfigMap holding `config.yaml`, a single-replica Deployment, and a Service. No operator or Helm required.

## Apply

```bash
kubectl create namespace gatus
kubectl -n gatus apply -f manifests.yaml
```

## Access

```bash
kubectl -n gatus port-forward svc/gatus 8080:80
```

Open <http://localhost:8080>.

## Edit monitors

Monitors live in the `gatus-config` ConfigMap. After editing:

```bash
kubectl -n gatus apply -f manifests.yaml
kubectl -n gatus rollout restart deployment/gatus
```

## Notes

- Single replica: default storage is in-memory. For history and >1 replica, add a `storage:` block (PostgreSQL) and point at an in-cluster database.
- Container listens on `8080`; the Service exposes port `80`.
- For replica management/autoscaling prefer the [Helm chart](../../helm/standalone/).

Official source: [Gatus configuration](https://github.com/TwiN/gatus#configuration).
