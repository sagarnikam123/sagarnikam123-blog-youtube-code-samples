# Elastic Observability — ECK operator standalone

Single-node Elasticsearch, Kibana, and APM Server managed by the ECK operator using raw YAML manifests. Use this mode for a development Kubernetes cluster without Helm.

## Install

```bash
# Install the ECK operator CRDs and controller
kubectl create -f https://download.elastic.co/downloads/eck/2.16.1/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/2.16.1/operator.yaml

# Apply the single-node stack
kubectl apply -f stack.yaml
kubectl -n elastic-observability get elasticsearch,kibana,apmserver
```

The `stack.yaml` in the `cluster/` sibling directory is a multi-node example. For a single-node variant, use a one-replica `nodeSets` entry.

Official source: [Install ECK using YAML manifests](https://www.elastic.co/docs/deploy-manage/deploy/cloud-on-k8s/install-using-yaml-manifest-quickstart).
