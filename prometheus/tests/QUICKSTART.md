# Quick Start Guide

## Working Directory

**IMPORTANT**: All test commands must be run from the repository root directory:

```bash
cd /Users/snikam/Documents/git/sagarnikam123-blog-youtube-code-samples/prometheus
```

## Installation

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Verify installation
python3 -m tests.cli info
```

## Running Tests Against Your Minikube Deployment

### 1. Check Prometheus Status
```bash
python3 -m tests.cli status --platform minikube
```

### 2. Run Sanity Tests (Quick Validation)
```bash
python3 -m tests.cli run --type sanity --platform minikube
```

### 3. Run All Tests
```bash
python3 -m tests.cli run --platform minikube
```

### 4. Run Specific Test Types
```bash
# Performance tests
python3 -m tests.cli run --type performance --platform minikube

# Load tests
python3 -m tests.cli run --type load --platform minikube

# Security tests
python3 -m tests.cli run --type security --platform minikube
```

## Test Results

Results are saved to `./results/` directory by default:
- `test_report.json` - Machine-readable results
- `test_report.md` - Human-readable markdown
- `test_report.html` - HTML report with charts

## Common Options

```bash
# Verbose output
python3 -m tests.cli -v run --type sanity --platform minikube

# Custom output directory
python3 -m tests.cli run --type sanity --platform minikube --output ./my-results

# Custom Prometheus URL
python3 -m tests.cli run --type sanity --prometheus-url http://localhost:9090

# Run tests in parallel
python3 -m tests.cli run --platform minikube --parallel

# Stop on first failure
python3 -m tests.cli run --platform minikube --fail-fast
```

## Cleanup

```bash
# Clean up test resources
python3 -m tests.cli cleanup --platform minikube
```

## Available Test Types

- `sanity` - Quick validation (~60s)
- `integration` - Component integration (~5min)
- `load` - Performance under load (~30min)
- `stress` - Breaking point discovery (~20min)
- `performance` - Benchmark measurements (~10min)
- `scalability` - Scaling behavior (~30min)
- `endurance` - Long-running stability (24h+)
- `reliability` - Failure recovery (~15min)
- `chaos` - Unexpected failures (~20min)
- `regression` - Version comparison (~30min)
- `security` - Security validation (~10min)

## Help

```bash
# General help
python3 -m tests.cli --help

# Command-specific help
python3 -m tests.cli run --help
python3 -m tests.cli report --help
python3 -m tests.cli cleanup --help
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the correct directory
pwd  # Should show: .../prometheus

# Reinstall dependencies
pip install -r tests/requirements.txt
```

### Connection Errors
```bash
# Verify Prometheus is accessible
kubectl get pods -n prometheus
kubectl port-forward -n prometheus svc/prometheus-kube-prometheus-prometheus 9090:9090

# Test in browser: http://localhost:9090
```

### Permission Errors
```bash
# Ensure kubectl context is correct
kubectl config current-context

# Verify namespace exists
kubectl get ns prometheus
```

## Next Steps

- Read full documentation: `docs/testing/README.md`
- View test configuration: `tests/config/default.yaml`
- Customize thresholds: `tests/config/thresholds.yaml`
