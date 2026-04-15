# Fluent Operator

Fluent Operator provides a Kubernetes-native way to manage Fluent Bit (and Fluentd) using CRDs instead of raw ConfigMaps. You define log pipelines as Kubernetes objects.

## Why Operator vs Raw Manifests / Helm?

| | Raw k8s / Helm | Operator |
|---|---|---|
| Config management | ConfigMap (manual) | CRDs (declarative, versioned) |
| Multi-pipeline | Hard | Easy via multiple CRs |
| Hot reload | Manual restart | Automatic on CR change |
| Validation | None | CRD schema validation |
| Best for | Simple setups | Complex / multi-tenant clusters |

## Versions

| Operator | Helm Chart | Status |
|----------|------------|--------|
| v3.x | fluent-operator-3.5.0 | Latest / Active |
| v2.x | fluent-operator-2.x | Older stable |

## Structure

```
operator/
├── v2.x/
│   ├── README.md       # Install + upgrade guide
│   ├── values.yaml     # Helm values
│   └── fluent-bit-cr.yaml  # Example CRD resources
└── v3.x/
    ├── README.md
    ├── values.yaml
    └── fluent-bit-cr.yaml
```

## Key CRDs (v3.x)

| CRD | Purpose |
|-----|---------|
| `FluentBit` | Deploys and configures the Fluent Bit DaemonSet |
| `ClusterInput` | Cluster-wide log input (e.g. tail, systemd) |
| `ClusterFilter` | Cluster-wide filter (e.g. kubernetes metadata) |
| `ClusterOutput` | Cluster-wide output (e.g. Loki, Elasticsearch) |
| `ClusterParser` | Cluster-wide parser definitions |
| `Input` | Namespace-scoped input |
| `Filter` | Namespace-scoped filter |
| `Output` | Namespace-scoped output |

## Links

- GitHub: https://github.com/fluent/fluent-operator
- Releases: https://github.com/fluent/fluent-operator/releases
- Docs: https://fluent-operator.netlify.app/
- Helm Charts: https://github.com/fluent/helm-charts
