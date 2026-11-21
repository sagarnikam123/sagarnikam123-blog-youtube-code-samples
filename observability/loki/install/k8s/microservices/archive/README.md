# Archive - Unused Files

This directory contains files that are not essential for the core Loki distributed deployment but may be useful for advanced configurations or alternative deployment methods.

## Archived Files

### Docker Compose Alternative
- `docker/` - Docker Compose setup (alternative to Kubernetes)

### Advanced Kubernetes Features
- `affinity-rules.yaml` - Pod affinity and anti-affinity rules
- `kustomization.yaml` - Kustomize configuration
- `local-test/` - Kustomize overlay for local testing
- `memberlist-service.yaml` - Dedicated memberlist service
- `monitoring.yaml` - ServiceMonitor for Prometheus
- `pod-disruption-budgets.yaml` - PDB for high availability

### Configuration Templates
- `loki-common.yaml` - Shared configuration template
- `overrides.yaml` - Per-tenant overrides
- `local-test-values.yaml` - Local testing parameters
- `production-values.yaml` - Production-ready settings

### Experimental Scripts
- `deploy-and-test.sh` - Combined deployment and testing
- `docker-run.sh` - Docker-based deployment
- `test-latest-config.sh` - Latest configuration testing
- `test-local-production.sh` - Local production testing
- `validate-k8s-configs.sh` - Kubernetes config validation
- `validate-production-features.sh` - Production feature validation
- `verify-secrets.sh` - Secret verification

## Usage

These files can be restored to the main project if needed:

```bash
# Restore Docker Compose
cp -r archive/unused-files/docker/ ./

# Restore monitoring
cp archive/unused-files/monitoring.yaml k8s/

# Restore advanced scripts
cp archive/unused-files/deploy-and-test.sh scripts/
```

## Why Archived?

- **Simplicity**: Core deployment focuses on essential files only
- **Maintenance**: Reduces complexity for basic use cases
- **Clarity**: Makes the main structure easier to understand
- **Preservation**: Keeps advanced features available when needed
