# SkyWalking Scripts

This directory contains operational and testing scripts for SkyWalking cluster deployments.

## Deployment Scripts

### deploy-skywalking-cluster.sh
Automated deployment script for SkyWalking full cluster mode.

**Usage:**
```bash
./deploy-skywalking-cluster.sh <environment>
```

**Environments:** minikube, eks-dev, eks-prod

**Features:**
- Prerequisite validation
- Environment-specific configuration
- Automated Helm installation
- Pod readiness waiting
- Deployment status reporting
- Dry-run mode support

### cleanup-skywalking-cluster.sh
Automated cleanup script for removing SkyWalking deployments.

**Usage:**
```bash
./cleanup-skywalking-cluster.sh <environment> [OPTIONS]
```

**Options:**
- `--delete-pvcs` - Delete persistent volume claims
- `--delete-namespace` - Delete namespace
- `--force` - Skip confirmation prompts

## Testing Scripts

### test-health.sh
Comprehensive health validation for all SkyWalking components.

**Usage:**
```bash
./test-health.sh [OPTIONS]
```

**Options:**
- `-n, --namespace` - Kubernetes namespace (default: skywalking)
- `-o, --output` - Output format: text, json, yaml (default: text)

**Validates:**
- Component pod status and readiness
- Persistent volume claims
- API responsiveness (OAP, BanyanDB)
- Cluster coordination (etcd, OAP, BanyanDB)
- Structured error reporting

**Documentation:** See [HEALTH-VALIDATION-GUIDE.md](./HEALTH-VALIDATION-GUIDE.md)

### test-connectivity.sh
Network connectivity testing between SkyWalking components.

**Usage:**
```bash
./test-connectivity.sh [OPTIONS]
```

**Tests:**
- Agent → Satellite (GRPC 11800)
- Satellite → OAP Server (GRPC 11800)
- OAP Server → BanyanDB (GRPC 17912)
- BanyanDB HTTP API (17913)
- etcd cluster communication (2379, 2380)
- UI → OAP Server (REST 12800)

### test-data-ingestion.sh
End-to-end data flow validation through the complete pipeline.

**Usage:**
```bash
./test-data-ingestion.sh [OPTIONS]
```

**Tests:**
- Test application deployment with agent injection
- Data flow: Agent → Satellite → OAP → BanyanDB
- Data persistence across pod restarts
- Component failure localization

### test-self-observability.sh
Validation of SkyWalking self-observability features.

**Usage:**
```bash
./test-self-observability.sh [OPTIONS]
```

**Tests:**
- OAP Server self-observability metrics
- BanyanDB metrics collection
- Satellite metrics collection
- Java Agent metrics from test applications
- Component JVM metrics, storage metrics, throughput metrics

### test-general-services.sh
Validation of general services monitoring marketplace features.

**Usage:**
```bash
./test-general-services.sh [OPTIONS]
```

**Environment Variables:**
- `NAMESPACE` - SkyWalking namespace (default: skywalking)
- `TEST_NAMESPACE` - Test services namespace (default: skywalking-test-services)
- `TIMEOUT` - Maximum execution time in seconds (default: 600)
- `CLEANUP` - Cleanup test resources after execution (default: true)

**Tests:**
- MySQL deployment with mysql-exporter
- Redis deployment with redis-exporter
- RabbitMQ deployment with built-in metrics
- OTel Collector configuration and deployment
- Metrics scraping and forwarding
- Metrics visibility in SkyWalking UI (Visual Database, Visual Cache, Visual MQ)

**Documentation:** See [TEST-GENERAL-SERVICES-GUIDE.md](./TEST-GENERAL-SERVICES-GUIDE.md)

### test-kubernetes-monitoring.sh
Validation of Kubernetes monitoring marketplace features.

**Usage:**
```bash
./test-kubernetes-monitoring.sh [OPTIONS]
```

**Tests:**
- kube-state-metrics deployment
- node-exporter deployment
- OTel Collector configuration for Kubernetes
- Kubernetes cluster metrics visibility
- Pod and node metrics in SkyWalking UI

**Documentation:** See [TEST-KUBERNETES-MONITORING-GUIDE.md](./TEST-KUBERNETES-MONITORING-GUIDE.md)

### test-mq-monitoring.sh
Validation of message queue monitoring marketplace features.

**Usage:**
```bash
./test-mq-monitoring.sh [OPTIONS]
```

**Tests:**
- ActiveMQ deployment with exporter
- RabbitMQ deployment with exporter
- OTel Collector configuration for MQ
- Message queue metrics visibility in SkyWalking UI

**Documentation:** See [TEST-MQ-MONITORING-GUIDE.md](./TEST-MQ-MONITORING-GUIDE.md)

### test-visualization.sh
Validation of data visualization in SkyWalking UI.

**Usage:**
```bash
./test-visualization.sh [OPTIONS]
```

**Options:**
- `-n, --namespace` - Kubernetes namespace (default: skywalking)
- `-t, --timeout` - Timeout in seconds (default: 300)

**Tests:**
- Service topology graph visualization
- Trace view with complete spans and timing
- Metrics dashboards with time-series data
- Log view with filtering capabilities
- Database dashboard (query performance)
- Cache dashboard (hit/miss ratios)
- Message queue dashboard (throughput, lag)
- Kubernetes dashboard (cluster and pod metrics)
- Self-observability dashboards (component metrics)
- Custom query execution via GraphQL API

**Documentation:** See [TEST-VISUALIZATION-GUIDE.md](./TEST-VISUALIZATION-GUIDE.md)

## Operational Scripts

### start-all.sh
Start all SkyWalking components (standalone/docker deployments).

### stop-all.sh
Stop all SkyWalking components (standalone/docker deployments).

### status.sh
Check status of SkyWalking components.

### health-check.sh
Basic health check using GraphQL API (legacy, use test-health.sh for cluster mode).

## Network Policy Scripts

### apply-network-policies.sh
Apply network policies for component isolation.

### remove-network-policies.sh
Remove network policies.

## Agent Scripts

### install-java-agent.sh
Install and configure SkyWalking Java agent.

## Script Execution Order

### Initial Deployment
1. `deploy-skywalking-cluster.sh` - Deploy cluster
2. `test-health.sh` - Validate deployment
3. `test-connectivity.sh` - Verify network connectivity
4. `test-data-ingestion.sh` - Test data flow
5. `test-visualization.sh` - Validate UI data visualization
6. `test-self-observability.sh` - Validate self-observability
7. `test-general-services.sh` - Validate marketplace features (optional)
8. `test-kubernetes-monitoring.sh` - Validate K8s monitoring (optional)
9. `test-mq-monitoring.sh` - Validate MQ monitoring (optional)

### Regular Operations
1. `test-health.sh` - Regular health monitoring
2. `status.sh` - Quick status check

### Cleanup
1. `cleanup-skywalking-cluster.sh` - Remove deployment

## Exit Codes

All scripts follow consistent exit code conventions:

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Test/validation failure |
| 2 | Script error or invalid arguments |

## Common Options

Most scripts support these common options:

- `-n, --namespace` - Kubernetes namespace
- `-h, --help` - Display help message
- `-v, --verbose` - Verbose output

## Prerequisites

### Required Tools
- `kubectl` - Kubernetes CLI
- `helm` - Helm package manager
- `curl` - HTTP client
- `jq` - JSON processor (for JSON output)
- `yq` - YAML processor (for YAML output)

### Optional Tools
- `nc` or `telnet` - Network connectivity testing

## Environment Variables

Scripts respect these environment variables:

- `KUBECONFIG` - Kubernetes configuration file
- `HELM_NAMESPACE` - Default Helm namespace

## Troubleshooting

### Script Fails with "Command not found"

**Solution:** Install missing prerequisites

```bash
# macOS
brew install kubectl helm jq yq

# Linux
apt-get install kubectl helm jq
```

### Cannot Connect to Cluster

**Solution:** Verify kubectl configuration

```bash
kubectl cluster-info
kubectl get nodes
```

### Permission Denied

**Solution:** Make scripts executable

```bash
chmod +x *.sh
```

## Best Practices

1. **Always run health checks after deployment**
   ```bash
   ./deploy-skywalking-cluster.sh minikube
   ./test-health.sh --namespace skywalking
   ```

2. **Use dry-run mode for testing**
   ```bash
   ./deploy-skywalking-cluster.sh minikube --dry-run
   ```

3. **Save health check results**
   ```bash
   ./test-health.sh --output json > health-$(date +%Y%m%d-%H%M%S).json
   ```

4. **Run connectivity tests before data ingestion tests**
   ```bash
   ./test-connectivity.sh && ./test-data-ingestion.sh
   ```

5. **Use structured output for automation**
   ```bash
   ./test-health.sh --output json | jq '.summary.status'
   ```

## Integration Examples

### CI/CD Pipeline

```bash
#!/bin/bash
set -e

# Deploy
./deploy-skywalking-cluster.sh minikube

# Validate
./test-health.sh --output json > health.json
./test-connectivity.sh
./test-data-ingestion.sh

# Check results
if [ $? -eq 0 ]; then
  echo "All tests passed"
else
  echo "Tests failed"
  exit 1
fi
```

### Monitoring Script

```bash
#!/bin/bash

while true; do
  ./test-health.sh --output json > /tmp/skywalking-health.json

  # Parse and send to monitoring system
  status=$(jq -r '.summary.status' /tmp/skywalking-health.json)

  if [ "$status" != "HEALTHY" ]; then
    # Send alert
    echo "SkyWalking cluster unhealthy!"
  fi

  sleep 300  # Check every 5 minutes
done
```

## Related Documentation

- [Deployment Guide](../helm-values/README.md)
- [Configuration Guide](../helm-values/CONFIGURATION-VALIDATION.md)
- [Health Validation Guide](./HEALTH-VALIDATION-GUIDE.md)
- [Testing Guide](../tests/README.md)

## Support

For issues or questions:
1. Check script help: `./script-name.sh --help`
2. Review logs: `kubectl logs -n skywalking <pod-name>`
3. Check documentation in this directory
4. Refer to [SkyWalking Documentation](https://skywalking.apache.org/docs/)
