# Elastic Observability — Helm standalone (ECK + eck-stack)

Use the ECK operator Helm chart followed by the `eck-stack` chart to deploy a single-node Elasticsearch, Kibana, and APM Server on Kubernetes.

## Install

```bash
# Install ECK operator
helm repo add elastic https://helm.elastic.co
helm repo update
helm install elastic-operator elastic/eck-operator \
  --namespace elastic-system --create-namespace

# Install the stack (single-node dev profile)
helm install elastic-stack elastic/eck-stack \
  --namespace elastic-observability --create-namespace \
  --values values.yaml
kubectl -n elastic-observability get pods
```

Configure `values.yaml` with single-replica Elasticsearch, Kibana, and APM Server settings for a development or validation environment.

Official sources:
- [Install ECK using Helm](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-helm-chart)
- [eck-stack Helm chart](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/managing-deployments-using-helm-chart)
