# VictoriaLogs — Kubernetes Operator

The VictoriaMetrics Operator manages VictoriaLogs instances via the `VLogs` custom resource. For each `VLogs` resource, the operator deploys a properly configured Deployment with persistent storage.

## Prerequisites

Install the VictoriaMetrics Operator first:

```bash
helm repo add vm https://victoriametrics.github.io/helm-charts
helm repo update
helm install vm-operator vm/victoria-metrics-operator \
  --namespace vm-operator --create-namespace
```

## Deploy VictoriaLogs

Apply a `VLogs` custom resource:

```bash
kubectl apply -f vlogs.yaml
kubectl get vlogs -n victoria-logs
```

## Example vlogs.yaml

```yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VLogs
metadata:
  name: victoria-logs
  namespace: victoria-logs
spec:
  retentionPeriod: "30d"
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: "2"
      memory: 4Gi
```

## Notes

- Only one replica is allowed per `VLogs` resource (single-node mode via operator).
- The operator handles upgrades and configuration changes automatically.
- For clustered VictoriaLogs, use the [Helm cluster chart](../helm-cluster/) directly.
- Update strategy is set to `Recreate`.

Official sources:
- [VLogs operator resource](https://docs.victoriametrics.com/operator/resources/vlogs/)
- [VM Operator setup](https://docs.victoriametrics.com/operator/setup/)
