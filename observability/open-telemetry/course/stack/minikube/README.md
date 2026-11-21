# Minikube Telemetry Stack

> Kubernetes manifests and Operator guides for running OpenTelemetry Collector and backends on a local Minikube cluster.

## Deployment Steps

```bash
# 1. Start Minikube (if not already running)
minikube start --cpus=4 --memory=6144

# 2. Apply Namespace and Deployments
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/backends.yaml
kubectl apply -f manifests/collector.yaml

# 3. Wait for Pods to be Ready
kubectl wait --namespace observability --for=condition=ready pod --selector=app=otel-collector --timeout=90s
kubectl wait --namespace observability --for=condition=ready pod --selector=app=jaeger --timeout=90s

# 4. Port Forward UIs to Localhost
# Jaeger UI:
kubectl port-forward -n observability svc/jaeger 16686:16686 &

# Prometheus UI:
kubectl port-forward -n observability svc/prometheus 9090:9090 &

# OTel Collector OTLP:
kubectl port-forward -n observability svc/otel-collector 4317:4317 4318:4318 &
```

## Installing the OpenTelemetry Operator (Optional / Module 10)

```bash
# Install cert-manager (required for webhooks)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

# Add and install OpenTelemetry Operator helm chart
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
helm install opentelemetry-operator open-telemetry/opentelemetry-operator \
  --namespace observability \
  --set manager.collectorImage.repository=otel/opentelemetry-collector-contrib \
  --set manager.collectorImage.tag=0.160.0
```
