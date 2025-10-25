# Kubernetes Standard Labels

This document describes the labeling standards implemented across all components in the Loki distributed microservices stack.

## 🎯 **Labeling Strategy**

All components follow [Kubernetes recommended labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/) for consistency, service discovery, and operational excellence.

## 🏷️ **Standard Label Schema**

### **Core Labels (Required)**
```yaml
app.kubernetes.io/name: <application-name>        # The name of the application
app.kubernetes.io/component: <component-name>     # The component within the application
app.kubernetes.io/instance: loki-dev              # A unique name identifying the instance
app.kubernetes.io/part-of: logging-stack          # The name of a higher level application
```

### **Optional Labels**
```yaml
app.kubernetes.io/version: <version>              # The current version of the application
app.kubernetes.io/managed-by: kubectl             # The tool being used to manage the operation
environment: development                           # The environment (development, staging, production)
```

## 📋 **Component Label Mapping**

### **All Components Share Common Labels**
```yaml
# Common to all components
app.kubernetes.io/instance: loki-dev
app.kubernetes.io/part-of: logging-stack
app.kubernetes.io/managed-by: kubectl
environment: development
```

### **Component-Specific Labels**
| Component | name | component | version |
|-----------|------|-----------|----------|
| **Loki** | `loki` | `distributor`, `ingester`, `querier`, etc. | `3.5.5` |
| **MinIO** | `minio` | `storage` | `2025-09-07` |
| **Grafana** | `grafana` | `visualization` | `12.1.0` |
| **Prometheus** | `prometheus` | `monitoring` | `v3.5.0` |
| **Fluent Bit** | `fluent-bit` | `log-collector` | `4.0.10` |

## 🔍 **Operational Benefits**

### **Common Operations**
```bash
# Find all logging stack components
kubectl get all -n loki -l app.kubernetes.io/part-of=logging-stack

# Find specific components
kubectl get pods -n loki -l app.kubernetes.io/name=loki              # All Loki services
kubectl get pods -n loki -l app.kubernetes.io/component=storage      # MinIO
kubectl get pods -n loki -l app.kubernetes.io/component=distributor  # Loki distributor

# Scale components
kubectl scale deployment -n loki -l app.kubernetes.io/component=querier --replicas=3

# Check logs
kubectl logs -n loki -l app.kubernetes.io/component=ingester --tail=10
```

## 🎯 **Best Practices**

1. **Consistency**: All resources (Deployments, Services, ConfigMaps) use the same labels
2. **Hierarchy**: Use `app.kubernetes.io/part-of` to group related components
3. **Specificity**: Use `app.kubernetes.io/component` to identify specific roles
4. **Versioning**: Include version labels for tracking deployments
5. **Environment**: Tag resources with environment for multi-env deployments

## 🔧 **Validation**
```bash
# Verify all components are labeled
kubectl get all -n loki -l app.kubernetes.io/part-of=logging-stack --show-labels

# Check for unlabeled resources
kubectl get all -n loki --show-labels | grep -v "app.kubernetes.io/part-of=logging-stack"
```

This labeling strategy ensures operational excellence, easy troubleshooting, and follows Kubernetes best practices for production-ready deployments.
