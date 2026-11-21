# Lesson 03-k8s-operator — Automated Kubernetes Agent Injection

This sub-lesson demonstrates how the OpenTelemetry Operator injects auto-instrumentation agents into Kubernetes workloads without building custom Docker images.

---

## Architecture: How Operator Injection Works

1. You create an `Instrumentation` Custom Resource (CRD) defining agent image versions, exporters, and samplers.
2. A developer annotates their pod template with:
   - `instrumentation.opentelemetry.io/inject-java: "true"`
   - or `instrumentation.opentelemetry.io/inject-python: "true"`
3. The Operator's **Mutating Admission Webhook** intercepts pod creation, injects an `initContainer` that mounts the agent files into an ephemeral volume, and sets the required `JAVA_TOOL_OPTIONS` or `PYTHONPATH` environment variables.

---

## Deploying on Minikube

```bash
# 1. Apply the Instrumentation resource
kubectl apply -f instrumentation.yaml

# 2. Deploy your application
kubectl apply -f sample-app.yaml

# 3. Inspect the created pod to see the injected agent volume & initContainer
kubectl describe pod -l app=order-service -n observability
```
