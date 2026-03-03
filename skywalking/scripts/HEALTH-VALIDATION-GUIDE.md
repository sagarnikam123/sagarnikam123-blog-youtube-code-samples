# SkyWalking Health Validation Guide

## Overview

The `test-health.sh` script provides comprehensive health validation for SkyWalking full cluster mode deployments. It validates all components, checks API responsiveness, verifies cluster coordination, and outputs results in multiple formats.

## Requirements Validated

This script validates the following requirements from the specification:

- **9.1**: OAP Server pods are Running and passing readiness probes
- **9.2**: BanyanDB liaison pods are Running
- **9.3**: BanyanDB data pods are Running
- **9.4**: Satellite pods are Running and accepting connections
- **9.5**: UI pods are Running and accessible
- **9.6**: etcd cluster has quorum and all members are healthy
- **9.7**: All PVCs are bound to volumes
- **9.8**: OAP Server REST API responsiveness
- **9.9**: BanyanDB HTTP API responsiveness
- **9.10**: BanyanDB cluster metadata synchronization
- **9.11**: OAP Server cluster coordination
- **9.12**: Specific component and failure reason reporting
- **9.13**: Structured output format (JSON or YAML)

## Usage

### Basic Usage

```bash
# Check health in default namespace (skywalking)
./test-health.sh

# Check health in custom namespace
./test-health.sh --namespace my-skywalking

# Output in JSON format
./test-health.sh --output json

# Output in YAML format
./test-health.sh --output yaml
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --namespace` | Kubernetes namespace | `skywalking` |
| `-o, --output` | Output format: text, json, yaml | `text` |
| `-h, --help` | Display help message | - |

## Health Checks Performed

### 1. Component Pod Status Checks

#### OAP Server
- Verifies all OAP Server pods are in Running state
- Checks readiness probes are passing
- Reports pod count and status

#### BanyanDB Liaison
- Verifies liaison pods are Running
- Reports pod count
- Warns if no liaison pods found (optional component)

#### BanyanDB Data Nodes
- Verifies all data node pods are Running
- Reports pod count
- Fails if no data nodes found

#### Satellite
- Verifies Satellite pods are Running
- Checks readiness probes (accepting connections)
- Warns if no Satellite pods found (optional component)

#### UI
- Verifies UI pods are Running
- Checks readiness probes (accessible)
- Reports pod count

#### etcd
- Verifies etcd pods are Running
- Checks member health
- Validates cluster quorum
- Warns if no etcd found (optional component)

### 2. Persistent Volume Claims

- Checks all PVCs are in Bound state
- Reports unbound PVCs with failure
- Warns if no PVCs found (may not use persistent storage)

### 3. API Responsiveness

#### OAP Server API
- Tests health endpoint (`/internal/l7check`)
- Tests GraphQL API endpoint
- Measures response latency
- Reports HTTP status codes

#### BanyanDB API
- Tests HTTP management API (`/api/healthz`)
- Measures response latency
- Warns if API not responding as expected

### 4. Cluster Coordination

#### BanyanDB Metadata Consistency
- Verifies etcd contains cluster metadata
- Checks metadata synchronization
- Validates coordination mechanism

#### OAP Server Cluster Coordination
- Verifies service discovery registration
- Checks all replicas are in service endpoints
- Confirms cluster mode is enabled

## Output Formats

### Text Output (Default)

Human-readable format with color-coded status indicators:

```
========================================
SkyWalking Full Cluster Health Validation
========================================

▶ OAP Server Health Checks
─────────────────────────────────────────────────────────────────
✓ PASS: OAP_Server - Pod_Status: All 3 pods running
✓ PASS: OAP_Server - Readiness_Probes: All 3 pods ready

...

========================================
Health Check Summary
========================================
Namespace: skywalking
Timestamp: 2024-01-15T10:30:00Z
Execution time: 45s

Total checks: 25
Passed: 23
Warnings: 2
Failed: 0

✓ All critical health checks PASSED
SkyWalking cluster is HEALTHY
```

### JSON Output

Machine-readable JSON format for automation:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "namespace": "skywalking",
  "summary": {
    "total_checks": 25,
    "passed": 23,
    "failed": 0,
    "warnings": 2,
    "status": "HEALTHY"
  },
  "checks": [
    {
      "component": "OAP_Server",
      "check": "Pod_Status",
      "status": "PASS",
      "message": "All 3 pods running"
    }
  ]
}
```

### YAML Output

YAML format for configuration management:

```yaml
timestamp: 2024-01-15T10:30:00Z
namespace: skywalking
summary:
  total_checks: 25
  passed: 23
  failed: 0
  warnings: 2
  status: HEALTHY
checks:
  - component: OAP_Server
    check: Pod_Status
    status: PASS
    message: "All 3 pods running"
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | All health checks passed |
| 1 | One or more health checks failed |
| 2 | Script error or invalid arguments |

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Validate SkyWalking Health
  run: |
    ./skywalking/scripts/test-health.sh --namespace skywalking --output json > health-report.json

- name: Upload Health Report
  uses: actions/upload-artifact@v3
  with:
    name: health-report
    path: health-report.json
```

### GitLab CI Example

```yaml
health_check:
  script:
    - ./skywalking/scripts/test-health.sh --namespace skywalking
  artifacts:
    reports:
      junit: health-report.xml
```

## Troubleshooting

### Common Issues

#### No Pods Found

**Symptom**: "No OAP Server pods found"

**Solution**:
- Verify deployment completed: `kubectl get pods -n skywalking`
- Check namespace is correct
- Verify Helm release installed: `helm list -n skywalking`

#### Pods Not Ready

**Symptom**: "Pod not ready"

**Solution**:
- Check pod logs: `kubectl logs -n skywalking <pod-name>`
- Describe pod: `kubectl describe pod -n skywalking <pod-name>`
- Verify resource availability
- Check readiness probe configuration

#### API Not Responding

**Symptom**: "Health endpoint not responding"

**Solution**:
- Verify service exists: `kubectl get svc -n skywalking`
- Check service endpoints: `kubectl get endpoints -n skywalking`
- Test connectivity manually: `kubectl port-forward -n skywalking svc/skywalking-oap 12800:12800`
- Check OAP Server logs for errors

#### etcd Quorum Lost

**Symptom**: "Cluster lost quorum"

**Solution**:
- Check etcd pod status: `kubectl get pods -n skywalking -l app.kubernetes.io/name=etcd`
- Review etcd logs: `kubectl logs -n skywalking <etcd-pod>`
- Verify persistent volumes are available
- Consider restoring from backup if data corruption

#### PVC Not Bound

**Symptom**: "PVC not bound"

**Solution**:
- Check PVC status: `kubectl get pvc -n skywalking`
- Verify storage class exists: `kubectl get storageclass`
- Check persistent volume availability: `kubectl get pv`
- Review storage provisioner logs

## Best Practices

### Regular Health Checks

Run health checks:
- After deployment
- After configuration changes
- Before and after upgrades
- As part of monitoring routine (every 5-10 minutes)

### Automated Monitoring

Integrate with monitoring systems:

```bash
# Prometheus exporter pattern
while true; do
  ./test-health.sh --output json > /tmp/health.json
  # Parse and expose metrics
  sleep 300
done
```

### Alert Configuration

Set up alerts for:
- Failed health checks
- Pod not ready for > 5 minutes
- API latency > 1000ms
- etcd quorum loss
- PVC binding failures

## Performance Considerations

### Execution Time

- Typical execution: 30-60 seconds
- Depends on cluster size and responsiveness
- API checks add 5-10 seconds per endpoint

### Resource Usage

- Minimal CPU/memory impact
- Creates temporary pods for API testing
- Temporary pods are automatically cleaned up

## Related Scripts

- `deploy-skywalking-cluster.sh` - Deploy SkyWalking cluster
- `test-connectivity.sh` - Test network connectivity
- `test-data-ingestion.sh` - Test data flow
- `cleanup-skywalking-cluster.sh` - Clean up deployment

## References

- [SkyWalking Documentation](https://skywalking.apache.org/docs/)
- [BanyanDB Documentation](https://skywalking.apache.org/docs/skywalking-banyandb/latest/readme/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [etcd Operations Guide](https://etcd.io/docs/latest/op-guide/)
