# Loki Scripts

Scripts for managing, monitoring, and testing Loki deployments.

## Structure

```
scripts/
├── local/                       # Local/terminal (monolithic mode)
│   ├── stack/                   # Start/stop local services
│   │   ├── start-all.sh
│   │   ├── start-loki.sh
│   │   ├── start-grafana.sh
│   │   ├── stop-all.sh
│   │   └── ...
│   ├── monitoring/
│   │   └── loki-monolithic-health.sh
│   └── logs/
│       └── generate-logs.sh
│
├── kubernetes/                  # Kubernetes (all deployment modes)
│   ├── monitoring/
│   │   ├── check-resources.sh       # K8s resource monitoring
│   │   ├── check-loki-logs.sh       # Pod log analysis
│   │   └── loki-distributed-health.sh  # Distributed mode only
│   └── utils/
│       └── cleanup.sh
│
└── common/                      # Works in both environments
    └── loki-health.sh           # Auto-detects deployment mode
```

## Local Scripts

For running Loki as a single binary on your local machine.

### Start/Stop Stack

```bash
# Start entire stack (Loki, Grafana, MinIO, etc.)
./local/stack/start-all.sh

# Start individual services
./local/stack/start-loki.sh
./local/stack/start-grafana.sh
./local/stack/start-minio.sh

# Stop services
./local/stack/stop-all.sh
./local/stack/stop-loki.sh
```

### Monitoring

```bash
# Health check for monolithic Loki
./local/monitoring/loki-monolithic-health.sh
```

### Log Generation

```bash
# Generate test logs for ingestion testing
./local/logs/generate-logs.sh
```

## Kubernetes Scripts

For Loki deployed on Kubernetes (single-binary, simple-scalable, or distributed).

### Monitoring

```bash
# Check pod resource usage and pressure indicators
./kubernetes/monitoring/check-resources.sh
./kubernetes/monitoring/check-resources.sh -c ingester

# Analyze Loki pod logs for errors/warnings
./kubernetes/monitoring/check-loki-logs.sh
./kubernetes/monitoring/check-loki-logs.sh -c ingester -t 10m

# Health check for distributed mode only (validates all components)
./kubernetes/monitoring/loki-distributed-health.sh
```

### Utilities

```bash
# Cleanup Loki resources
./kubernetes/utils/cleanup.sh
```

## Common Scripts

Work in both local and Kubernetes environments.

```bash
# Unified health check - auto-detects deployment mode
# Requires port-forward for K8s: kubectl port-forward svc/loki-gateway -n loki 3100:80
./common/loki-health.sh                  # Standard checks
./common/loki-health.sh --quick          # Fast basic checks
./common/loki-health.sh --deep           # Include debug endpoints
./common/loki-health.sh -m kubernetes    # Force K8s mode
./common/loki-health.sh -v               # Verbose output
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOKI_URL` | `http://127.0.0.1:3100` | Loki endpoint |
| `LOKI_NAMESPACE` | `loki` | Kubernetes namespace |
| `LOKI_HOST` | `127.0.0.1` | Loki host (local) |
| `LOKI_PORT` | `3100` | Loki port (local) |
