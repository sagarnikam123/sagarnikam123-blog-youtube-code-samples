# Elastic Observability — Helm cluster (ECK + eck-stack)

Use the ECK operator Helm chart followed by the `eck-stack` chart to deploy a multi-node Elasticsearch cluster, Kibana, and APM Server on Kubernetes.

## Install

```bash
# Install ECK operator
helm repo add elastic https://helm.elastic.co
helm repo update
helm install elastic-operator elastic/eck-operator \
  --namespace elastic-system --create-namespace

# Install the stack (production/cluster profile)
helm install elastic-stack elastic/eck-stack \
  --namespace elastic-observability --create-namespace \
  --values values.yaml
kubectl -n elastic-observability get pods
```

Configure `values.yaml` with multi-replica Elasticsearch (hot/warm/cold tiers), persistent volumes, resource requests, and ingress settings for a production-grade environment.

Official sources:
- [Install ECK using Helm](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-helm-chart)
- [eck-stack Helm chart](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/managing-deployments-using-helm-chart)
- [ECK stack examples](https://github.com/elastic/cloud-on-k8s/tree/main/deploy/eck-stack/examples)
