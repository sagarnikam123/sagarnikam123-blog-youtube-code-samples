# Fluent Bit

Install guides and configurations for Fluent Bit across multiple deployment modes and versions.

## Versions

| Series | Latest | Status |
|--------|--------|--------|
| v5.x | v5.0.1 | Latest |
| v4.x | v4.2.3.1 | Stable / Active |
| v3.x | v3.0.4 | Older stable |

## Structure

```
fluent-bit/
└── install/
    ├── binary/          # Install as a system binary / service
    │   ├── v3.x/
    │   ├── v4.x/
    │   └── v5.x/
    ├── docker/          # Docker & Docker Compose
    │   ├── v3.x/        # fluent-bit.conf + docker-compose.yaml
    │   ├── v4.x/        # fluent-bit.yaml + docker-compose.yaml
    │   └── v5.x/        # fluent-bit.yaml + docker-compose.yaml
    ├── helm/            # Helm chart install on Kubernetes
    │   ├── v3.x/        # values.yaml + README
    │   ├── v4.x/        # values.yaml + README
    │   └── v5.x/        # values.yaml + README
    ├── k8s/             # Raw Kubernetes manifests (no Helm)
    │   ├── v3.x/        # rbac + configmap (.conf) + daemonset
    │   ├── v4.x/        # rbac + configmap (.yaml) + daemonset
    │   └── v5.x/        # rbac + configmap (.yaml) + daemonset
    └── operator/        # Fluent Operator (CRD-based, Kubernetes-native)
        ├── README.md    # Operator overview + CRD reference
        ├── v2.x/        # values.yaml + fluent-bit-cr.yaml
        └── v3.x/        # values.yaml + fluent-bit-cr.yaml
```

## Config Format by Version

| Version | Recommended Format | Notes |
|---------|--------------------|-------|
| v3.x | `.conf` (classic INI) | YAML not yet default |
| v4.x | `.yaml` | YAML recommended, `.conf` still works |
| v5.x | `.yaml` | YAML only recommended |

## Install Method Comparison

| Method | Best For |
|--------|----------|
| binary | VMs, bare metal, non-container environments |
| docker | Local dev, single-host log collection |
| helm | Kubernetes, simple config via values.yaml |
| k8s | Kubernetes, full control over raw manifests |
| operator | Kubernetes, CRD-based declarative pipelines, multi-tenant |

## Links

- GitHub: https://github.com/fluent/fluent-bit
- Releases: https://github.com/fluent/fluent-bit/releases
- Docs: https://docs.fluentbit.io/manual
- Helm Charts: https://github.com/fluent/helm-charts
- Docker Hub: https://hub.docker.com/r/fluent/fluent-bit
