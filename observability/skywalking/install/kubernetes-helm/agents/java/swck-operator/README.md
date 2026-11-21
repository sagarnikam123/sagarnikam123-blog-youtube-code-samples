# SkyWalking SWCK Operator - Java Agent Auto-Injection

The SkyWalking Cloud on Kubernetes (SWCK) operator provides automatic Java agent injection via mutating webhook.

## Version

- SWCK Operator: v0.9.0
- Java Agent: 9.3.0-java21

## Important Notes

1. **Pod Label Required**: Both namespace AND pod must have labels for injection:
   - Namespace: `swck-injection=enabled`
   - Pod: `swck-java-agent-injected=true`

2. **All 10 CRDs Required**: The operator needs all CRDs (not just JavaAgent and SwAgent)

3. **Health Probes**: v0.9.0 doesn't expose health endpoints properly - probes are disabled

4. **SwAgent Location**: Create SwAgent CR in the target namespace (e.g., hunt), not in operator namespace

## How It Works

1. Deploy SWCK operator (one-time setup)
2. Label namespace with `swck-injection=enabled`
3. All new Java pods in that namespace automatically get the agent injected

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Application Namespaces                                       │
│  (hunt, shared, response, analytics, etc.)                                          │
│                                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   Java App      │  │   Java App      │  │   Java App      │                      │
│  │   + Agent       │  │   + Agent       │  │   + Agent       │  ← Auto-injected     │
│  │   (auto)        │  │   (auto)        │  │   (auto)        │    by SWCK           │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘                      │
│           │                    │                    │                                │
└───────────┼────────────────────┼────────────────────┼────────────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │ gRPC (11800)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         skywalking namespace                                         │
│                         (Deployed via Helm)                                          │
│                                                                                      │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐              │
│  │    Satellite    │─────▶│      OAP        │─────▶│    BanyanDB     │              │
│  │     (x2)        │      │     (x3)        │      │    Cluster      │              │
│  └─────────────────┘      └─────────────────┘      └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      skywalking-swck-system namespace                                │
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  SWCK Operator                                                                 │  │
│  │  - Watches pod creation in labeled namespaces                                  │  │
│  │  - Injects init container + env vars + volumes                                 │  │
│  │  - Points agents to: skywalking-satellite.skywalking.svc:11800                │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Deploy SkyWalking backend first (if not already deployed)
./environments/scnx-global-dev-aps1-eks/deploy.sh install

# 2. Deploy SWCK operator
./agents/java/swck-operator/deploy.sh install

# 3. Label namespace for injection
kubectl label namespace hunt swck-injection=enabled

# 4. Restart deployments to trigger injection
kubectl rollout restart deployment -n hunt

# 5. Verify injection
kubectl get pods -n hunt -o jsonpath='{.items[*].spec.initContainers[*].name}' | tr ' ' '\n' | grep inject
```

## Configuration

### Namespace-level (all pods in namespace)
```bash
kubectl label namespace <namespace> swck-injection=enabled
```

### Pod-level (selective - via annotation)
```yaml
metadata:
  labels:
    swck-java-agent-injected: "true"
```

### Exclude specific pods
```yaml
metadata:
  labels:
    swck-java-agent-injected: "false"
```

### Customize agent per pod (via annotations)
```yaml
metadata:
  annotations:
    # Service name
    agent.skywalking.apache.org/agent.service_name: "my-custom-service"
    # Backend service
    agent.skywalking.apache.org/collector.backend_service: "skywalking-oap.skywalking.svc:11800"
    # Sampling rate
    agent.skywalking.apache.org/agent.sample_n_per_3_secs: "10"
    # Custom agent image
    sidecar.skywalking.apache.org/initcontainer.Image: "apache/skywalking-java-agent:9.3.0-java21"
```

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | Operator namespace (skywalking-swck-system) |
| `crds.yaml` | JavaAgent and SwAgent CRDs |
| `rbac.yaml` | ServiceAccount, ClusterRole, ClusterRoleBinding |
| `operator.yaml` | Operator deployment |
| `webhook.yaml` | MutatingWebhookConfiguration |
| `certificate.yaml` | Certificate for webhook TLS (requires cert-manager) |
| `java-agent-config.yaml` | Default agent ConfigMap and SwAgent CR |
| `self-signed-cert.sh` | Generate self-signed cert (if no cert-manager) |
| `deploy.sh` | Deployment script |

## Troubleshooting

```bash
# Check operator logs
kubectl logs -n skywalking-swck-system -l control-plane=controller-manager

# Check if webhook is registered
kubectl get mutatingwebhookconfiguration skywalking-swck-mutating-webhook-configuration

# Check injection status on a pod
kubectl get pod <pod-name> -n hunt -o yaml | grep -A 20 initContainers

# Check JavaAgent CRs (created after injection)
kubectl get javaagents -n hunt

# Check SwAgent CRs
kubectl get swagents -A
```

## References

- [SWCK Documentation](https://skywalking.apache.org/docs/skywalking-swck/latest/)
- [Java Agent Injector](https://skywalking.apache.org/docs/skywalking-swck/latest/java-agent-injector)
- [SWCK GitHub](https://github.com/apache/skywalking-swck)
