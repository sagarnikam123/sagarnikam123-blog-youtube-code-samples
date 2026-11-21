# Gatus — Helm standalone (official chart)

Gatus ships an official Helm chart from the maintainer.

## Install

```bash
helm repo add twin https://twin.sh/helm-charts
helm repo update
helm install gatus twin/gatus -f values.yaml
```

The [`values.yaml`](values.yaml) here sets the whole Gatus configuration through the chart's `config` value, so no separate ConfigMap is needed.

## Access

```bash
kubectl port-forward svc/gatus 8080:80
```

Open <http://localhost:8080>. The chart Service listens on port `80` and targets container port `8080`.

## Notes

- The chart `image.repository` is `twinproduction/gatus`; leave `image.tag` empty to track the chart `appVersion`, or pin it.
- Runs as non-root (uid/gid 65534) with a read-only root filesystem by default.
- For persistent history, add a `storage:` block under `config` and provision a PVC / external database.

Official source: [Gatus Helm chart](https://github.com/TwiN/helm-charts/tree/master/charts/gatus).
