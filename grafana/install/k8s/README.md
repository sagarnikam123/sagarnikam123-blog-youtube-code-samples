# Grafana — Kubernetes raw manifests

Deploy Grafana on Kubernetes using plain YAML manifests (no Helm or operator).

## Example deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
        - name: grafana
          image: grafana/grafana-oss:13.2.0
          ports:
            - containerPort: 3000
          volumeMounts:
            - name: grafana-storage
              mountPath: /var/lib/grafana
      volumes:
        - name: grafana-storage
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: ClusterIP
  ports:
    - port: 3000
      targetPort: 3000
  selector:
    app: grafana
```

## Access

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

Open <http://localhost:3000>.

## Notes

- For persistent storage, replace `emptyDir` with a `PersistentVolumeClaim`.
- For production, use the [Helm chart](../helm/) or [Operator](../operator/) for configuration management.
- These manifests are for simple dev/test deployments.

Official guide: [Deploy Grafana on Kubernetes](https://grafana.com/docs/grafana/latest/setup-grafana/installation/kubernetes/).
