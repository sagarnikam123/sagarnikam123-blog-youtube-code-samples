# OpenObserve — Kubernetes operator

OpenObserve publishes an enterprise configuration operator for CRD-managed resources such as configurations, alerts, destinations, pipelines, and functions. The operator manages OpenObserve configuration objects; it does not replace the platform deployment chart.

## Install

Use the upstream release manifests for the operator version selected by the deployment:

```bash
kubectl apply -f <openobserve-operator-release>/manifests/00-namespace.yaml
kubectl apply -f <openobserve-operator-release>/manifests/01-o2configs.crd.yaml
kubectl apply -f <openobserve-operator-release>/manifests/01-o2alerts.crd.yaml
kubectl apply -f <openobserve-operator-release>/manifests/01-o2alerttemplates.crd.yaml
kubectl apply -f <openobserve-operator-release>/manifests/01-o2destinations.crd.yaml
kubectl apply -f <openobserve-operator-release>/manifests/01-o2pipelines.crd.yaml
kubectl apply -f <openobserve-operator-release>/manifests/02-rbac.yaml
```

Apply the operator configuration and CRs from the same upstream release. Deploy OpenObserve itself with the [official Helm chart](../../helm/cluster/README.md).

Official sources: [Operator overview](https://openobserve.ai/docs/administration/configuration/o2-k8s-operator/o2-operator-overview/), [Manual deployment](https://openobserve.ai/docs/administration/configuration/o2-k8s-operator/manual-deployment/).
