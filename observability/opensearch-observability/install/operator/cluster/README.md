# OpenSearch Observability — Kubernetes Operator

The official OpenSearch Kubernetes Operator (`opensearch-k8s-operator`) automates deployment, scaling, upgrades, and management of OpenSearch clusters on Kubernetes using an `OpenSearchCluster` CRD.

## Install the operator

```bash
helm repo add opensearch-operator https://opensearch-project.github.io/opensearch-k8s-operator/
helm repo update
helm install opensearch-operator opensearch-operator/opensearch-operator \
  --namespace opensearch-operator --create-namespace
```

## Deploy an OpenSearch cluster

After the operator is running, apply an `OpenSearchCluster` custom resource:

```bash
kubectl apply -f cluster.yaml
kubectl get opensearchclusters -n opensearch
```

## Example cluster.yaml

```yaml
apiVersion: opensearch.opster.io/v1
kind: OpenSearchCluster
metadata:
  name: observability
  namespace: opensearch
spec:
  general:
    serviceName: observability
    version: 2.19.1
  dashboards:
    enable: true
    version: 2.19.1
    replicas: 1
  nodePools:
    - component: masters
      replicas: 3
      roles:
        - cluster_manager
        - data
      persistence:
        pvc:
          storageClass: ""
          accessModes:
            - ReadWriteOnce
          storage: 50Gi
```

## Notes

- The operator manages rolling upgrades, scaling, and security configuration.
- Add Data Prepper separately (as a Deployment or via its own Helm chart) for OTLP ingestion.
- The Observability Stack umbrella Helm chart is a simpler alternative when you want OpenSearch + Dashboards + Data Prepper + OTel Collector in one release.

Official sources:
- [OpenSearch Kubernetes Operator](https://opensearch-project.github.io/opensearch-k8s-operator/)
- [Operator user guide](https://github.com/opensearch-project/opensearch-k8s-operator/blob/main/docs/userguide/main.md)
- [OpenSearch docs — Operator](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/operator/index/)
