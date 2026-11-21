# Getting Started with Prometheus Testing

This guide walks you through setting up and running your first tests against a Prometheus deployment.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10+ | Test framework runtime |
| kubectl | Latest | Kubernetes cluster access |
| k6 | Latest | Load testing |

### Installing Prerequisites

**Python 3.10+**
```bash
# macOS
brew install python@3.10

# Ubuntu/Debian
sudo apt install python3.10 python3.10-venv

# Windows
# Download from https://www.python.org/downloads/
```

**kubectl**
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

**k6**
```bash
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
```


## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd prometheus
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python3 -m tests.cli info
```

Expected output:
```
Prometheus Test Framework
Version: 0.1.0

System Information
┌──────────────────┬─────────────────────┐
│ Property         │ Value               │
├──────────────────┼─────────────────────┤
│ OS               │ macOS 14.0          │
│ Python Version   │ 3.10.12             │
│ k6 Version       │ v0.47.0             │
│ kubectl Version  │ v1.28.0             │
└──────────────────┴─────────────────────┘
```

## Running Your First Test

### Option 1: Test Local Docker Deployment

Start Prometheus in Docker:
```bash
cd install/docker
docker-compose up -d
```

Run sanity tests:
```bash
python3 -m tests.cli run --type sanity --platform docker
```

### Option 2: Test Minikube Deployment

Start Minikube and deploy Prometheus:
```bash
minikube start
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

Port-forward Prometheus:
```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
```

Run sanity tests:
```bash
python3 -m tests.cli run --type sanity --platform minikube
```

### Option 3: Test Existing Prometheus

If you have Prometheus running elsewhere:
```bash
python3 -m tests.cli run --type sanity --prometheus-url http://your-prometheus:9090
```


## Understanding Test Output

After running tests, you'll see a summary:

```
Prometheus Test Framework
Platform: docker
Deployment Mode: monolithic

Running: sanity tests

Test Results Summary
┌──────────────┬────────┐
│ Metric       │ Value  │
├──────────────┼────────┤
│ Status       │ PASSED │
│ Total Tests  │ 5      │
│ Passed       │ 5      │
│ Failed       │ 0      │
│ Skipped      │ 0      │
│ Success Rate │ 100.0% │
│ Duration     │ 12.34s │
└──────────────┴────────┘

Reports saved to:
  • ./results/test_report.json
  • ./results/test_report.md
  • ./results/test_report.html
```

## Common Commands

```bash
# Check Prometheus status
python3 -m tests.cli status --platform docker

# Run specific test types
python3 -m tests.cli run --type sanity --platform docker
python3 -m tests.cli run --type load --platform minikube

# Run multiple test types
python3 -m tests.cli run --type sanity --type integration --platform docker

# Run with custom configuration
python3 -m tests.cli run --config tests/config/custom.yaml --platform eks

# Run load tests with k6 options
python3 -m tests.cli run --type load --k6-vus 50 --k6-duration 10m

# Generate reports from existing results
python3 -m tests.cli report --input results/test_report.json --format html

# Clean up test resources
python3 -m tests.cli cleanup --platform minikube
```

## Configuration

Tests can be configured via YAML files. The default configuration is at `tests/config/default.yaml`.

Create a custom configuration:
```yaml
# tests/config/my-config.yaml
test:
  name: "my-test-suite"
  platform: "eks"
  deployment_mode: "distributed"
  prometheus:
    url: "http://prometheus.monitoring.svc:9090"

sanity:
  enabled: true
  timeout: 120s

load:
  enabled: true
  duration: 15m
  k6:
    vus: 50
```

Run with custom config:
```bash
python3 -m tests.cli run --config tests/config/my-config.yaml
```

See [Configuration Reference](./configuration.md) for all options.

## Next Steps

- [Test Types](./test-types.md) - Learn about each test type
- [Configuration](./configuration.md) - Full configuration reference
- [CI/CD Integration](./ci-cd-integration.md) - Automate testing in pipelines
- [Interpreting Results](./interpreting-results.md) - Analyze test reports

## Troubleshooting

### Prometheus Unreachable

```
Error: PROM_UNREACHABLE - Cannot connect to Prometheus at http://localhost:9090
```

**Solutions:**
1. Verify Prometheus is running: `curl http://localhost:9090/-/healthy`
2. Check port-forwarding is active (for Kubernetes)
3. Verify firewall rules allow connections

### k6 Not Found

```
Error: k6 not found at /usr/local/bin/k6
```

**Solutions:**
1. Install k6: `brew install k6` (macOS) or see k6 installation docs
2. Update k6 path in config: `runner.k6_path: "/path/to/k6"`

### kubectl Not Configured

```
Error: kubectl not configured for cluster access
```

**Solutions:**
1. Set KUBECONFIG: `export KUBECONFIG=~/.kube/config`
2. Verify cluster access: `kubectl cluster-info`
