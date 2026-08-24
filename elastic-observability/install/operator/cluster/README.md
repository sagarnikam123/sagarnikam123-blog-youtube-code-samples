# Elastic Observability — ECK cluster

Elastic Cloud on Kubernetes (ECK) is the official Kubernetes operator for Elasticsearch, Kibana, APM Server, Beats, and Elastic Agent.

## Install the operator

Follow the current versioned manifest from Elastic's documentation, then apply the stack resources:

```bash
# Set ECK_OPERATOR_MANIFEST_URL to the versioned manifest selected from
# Elastic's installation guide, then install it and apply the stack.
kubectl apply -f "$ECK_OPERATOR_MANIFEST_URL"
kubectl apply -f stack.yaml
kubectl get elasticsearch,kibana,apmserver -n elastic-observability
```

`stack.yaml` should define the Elasticsearch and Kibana custom resources plus APM Server or Elastic Agent resources wired to the Elasticsearch cluster. Select one compatible Elastic version for all resources and configure persistent storage and TLS for the target cluster.

Official sources: [Install ECK](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-yaml-manifest-quickstart), [ECK documentation](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install).
