# Security Hardening Guide

## Current Security Status ⚠️

**Development Setup - NOT Production Ready**

### Known Security Issues:
1. **Hardcoded MinIO credentials** (admin/password123)
2. **No TLS encryption** between components
3. **No authentication** enabled (`auth_enabled: false`)
4. **Insecure MinIO connection** (`insecure: true`)

## Production Security Checklist

### 1. Enable Authentication
```yaml
# In all component configs
auth_enabled: true
```

### 2. Secure MinIO Credentials
```bash
# Generate secure credentials
kubectl create secret generic minio-creds \
  --from-literal=accesskey=$(openssl rand -base64 20) \
  --from-literal=secretkey=$(openssl rand -base64 32) \
  -n loki
```

### 3. Enable TLS
```yaml
# Add to server config in all components
server:
  http_tls_config:
    cert_file: /etc/loki/tls/tls.crt
    key_file: /etc/loki/tls/tls.key
  grpc_tls_config:
    cert_file: /etc/loki/tls/tls.crt
    key_file: /etc/loki/tls/tls.key
```

### 4. Network Policies
```yaml
# Restrict pod-to-pod communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: loki-network-policy
  namespace: loki
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 5. RBAC Hardening
- Use dedicated service accounts
- Minimal required permissions
- Regular permission audits

### 6. Resource Limits
```yaml
resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi
```

## Security Monitoring

### Log Security Events
- Failed authentication attempts
- Unauthorized access attempts
- Configuration changes

### Regular Security Tasks
- [ ] Rotate MinIO credentials monthly
- [ ] Update Loki version quarterly
- [ ] Review RBAC permissions
- [ ] Audit network policies
- [ ] Monitor resource usage

## Quick Security Improvements

1. **Change default credentials** immediately
2. **Enable resource limits** in all deployments
3. **Add network policies** to restrict traffic
4. **Enable audit logging** in Kubernetes
5. **Use secrets management** (Vault, AWS Secrets Manager)