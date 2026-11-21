# Chaos Mesh - Kubernetes Chaos Engineering

Chaos engineering platform for testing Mimir resilience and failure recovery.

## Installation

### Install Chaos Mesh
```bash
# Add Chaos Mesh Helm repo
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh
helm install chaos-mesh chaos-mesh/chaos-mesh \
  -n chaos-mesh \
  --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock

# Verify installation
kubectl get pods -n chaos-mesh
```

### Access Dashboard
```bash
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 2333:2333
# Open: http://localhost:2333
```

## Chaos Experiments for Mimir

### 1. Pod Failure (Kill Ingester)

**Test**: Verify HA and data replication when ingester dies

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: kill-ingester
  namespace: mimir-test
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: ingester
  scheduler:
    cron: '@every 5m'
```

### 2. Network Delay (Distributor Latency)

**Test**: Simulate network latency to distributor

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: distributor-delay
  namespace: mimir-test
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: distributor
  delay:
    latency: "500ms"
    correlation: "50"
    jitter: "100ms"
  duration: "5m"
```

### 3. Network Partition (Split Brain)

**Test**: Partition ingester from rest of cluster

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: ingester-partition
  namespace: mimir-test
spec:
  action: partition
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: ingester
  direction: both
  duration: "2m"
```

### 4. CPU Stress (Querier Overload)

**Test**: Stress querier CPU to test query performance degradation

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: querier-cpu-stress
  namespace: mimir-test
spec:
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: querier
  stressors:
    cpu:
      workers: 4
      load: 80
  duration: "5m"
```

### 5. Memory Stress (Ingester OOM)

**Test**: Trigger OOM to test memory limits and recovery

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: ingester-memory-stress
  namespace: mimir-test
spec:
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: ingester
  stressors:
    memory:
      workers: 4
      size: "1GB"
  duration: "3m"
```

### 6. Disk I/O Stress (Compactor)

**Test**: Slow down compactor disk I/O

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: compactor-io-stress
  namespace: mimir-test
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/component: compactor
  volumePath: /data
  path: /data/**/*
  delay: "500ms"
  percent: 50
  duration: "5m"
```

### 7. Pod Failure Cascade

**Test**: Kill multiple components simultaneously

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: multi-component-failure
  namespace: mimir-test
spec:
  action: pod-kill
  mode: fixed
  value: "2"
  selector:
    namespaces:
      - mimir-test
    labelSelectors:
      app.kubernetes.io/name: mimir
  duration: "1m"
```

## Chaos Workflows

### Workflow 1: Progressive Failure
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: Workflow
metadata:
  name: progressive-failure
  namespace: mimir-test
spec:
  entry: entry
  templates:
    - name: entry
      templateType: Serial
      children:
        - kill-one-ingester
        - network-delay
        - kill-distributor

    - name: kill-one-ingester
      templateType: PodChaos
      deadline: 2m
      podChaos:
        action: pod-kill
        mode: one
        selector:
          namespaces: [mimir-test]
          labelSelectors:
            app.kubernetes.io/component: ingester

    - name: network-delay
      templateType: NetworkChaos
      deadline: 3m
      networkChaos:
        action: delay
        mode: all
        selector:
          namespaces: [mimir-test]
        delay:
          latency: "200ms"

    - name: kill-distributor
      templateType: PodChaos
      deadline: 2m
      podChaos:
        action: pod-kill
        mode: one
        selector:
          namespaces: [mimir-test]
          labelSelectors:
            app.kubernetes.io/component: distributor
```

## Running Experiments

```bash
# Apply chaos experiment
kubectl apply -f experiments/kill-ingester.yaml

# Check experiment status
kubectl get podchaos -n mimir-test

# View experiment details
kubectl describe podchaos kill-ingester -n mimir-test

# Pause experiment
kubectl annotate podchaos kill-ingester -n mimir-test \
  experiment.chaos-mesh.org/pause=true

# Resume experiment
kubectl annotate podchaos kill-ingester -n mimir-test \
  experiment.chaos-mesh.org/pause-

# Delete experiment
kubectl delete podchaos kill-ingester -n mimir-test
```

## Monitoring During Chaos

```bash
# Watch pod status
kubectl get pods -n mimir-test -w

# Check Mimir ring status
kubectl exec -n mimir-test -l app.kubernetes.io/component=ingester -- \
  wget -q -O- http://localhost:8080/ingester/ring

# Monitor metrics
kubectl port-forward -n mimir-test svc/mimir-gateway 8080:80
curl http://localhost:8080/metrics | grep -E "(up|ring|ingester)"
```

## Success Criteria

- ✅ No data loss during pod failures
- ✅ Queries continue to work (may be slower)
- ✅ Ring rebalances correctly
- ✅ Failed pods recover automatically
- ✅ No cascading failures
- ✅ Metrics ingestion continues

## Resources

- [Chaos Mesh Documentation](https://chaos-mesh.org/docs/)
- [Chaos Engineering Principles](https://principlesofchaos.org/)
- [Mimir HA Guide](https://grafana.com/docs/mimir/latest/configure/configure-high-availability/)
