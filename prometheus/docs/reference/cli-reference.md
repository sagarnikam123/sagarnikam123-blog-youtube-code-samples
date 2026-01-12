# CLI Reference

This document provides a complete reference for the Prometheus Testing Framework command-line interface.

## Installation

The CLI is part of the test framework and can be invoked using Python:

```bash
python3 -m tests.cli [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output with debug logging |
| `--config PATH` | `-c` | Path to configuration file (YAML) |
| `--version` | | Show version information |
| `--help` | | Show help message |

## Commands

### run

Execute tests against a Prometheus deployment.

```bash
python3 -m tests.cli run [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--platform` | `-p` | Choice | `minikube` | Target platform for testing |
| `--deployment-mode` | `-m` | Choice | `monolithic` | Deployment mode |
| `--type` | `-t` | Multiple | All enabled | Test type(s) to run |
| `--prometheus-url` | | String | From config | Prometheus URL to test |
| `--k6-vus` | | Integer | From config | Number of k6 virtual users |
| `--k6-duration` | | String | From config | Duration for k6 load tests |
| `--parallel/--sequential` | | Flag | `--sequential` | Run tests in parallel or sequential |
| `--timeout` | | Integer | `300` | Default timeout in seconds |
| `--fail-fast` | | Flag | False | Stop on first test failure |
| `--output` | `-o` | Path | `./results` | Output directory for results |

#### Platform Values

- `minikube` - Local Kubernetes via Minikube
- `eks` - Amazon Elastic Kubernetes Service
- `gke` - Google Kubernetes Engine
- `aks` - Azure Kubernetes Service
- `docker` - Docker container (monolithic only)
- `binary` - Binary installation (monolithic only)

#### Deployment Mode Values

- `monolithic` - Single Prometheus instance
- `distributed` - Multi-replica with federation/Thanos/Mimir

#### Test Type Values

- `sanity` - Quick validation tests
- `integration` - Component integration tests
- `load` - Load testing with k6
- `stress` - Breaking point discovery
- `performance` - Performance benchmarks
- `scalability` - Scaling behavior tests
- `endurance` - Long-running stability tests
- `reliability` - Failure handling tests
- `chaos` - Chaos engineering tests
- `regression` - Version comparison tests
- `security` - Security validation tests

#### Examples

```bash
# Run all tests on minikube
python3 -m tests.cli run --platform minikube

# Run sanity tests on docker
python3 -m tests.cli run --type sanity --platform docker

# Run load tests with k6 options
python3 -m tests.cli run --type load --k6-vus 100 --k6-duration 30m

# Run distributed tests on EKS
python3 -m tests.cli run --platform eks --deployment-mode distributed

# Run multiple test types
python3 -m tests.cli run --type sanity --type load --type stress

# Run with custom config and fail fast
python3 -m tests.cli run -c config/custom.yaml --fail-fast

# Run tests in parallel with custom timeout
python3 -m tests.cli run --parallel --timeout 600
```

---

### report

Generate test reports from existing results.

```bash
python3 -m tests.cli report [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--format` | `-f` | Multiple | `json,markdown,html` | Report format(s) to generate |
| `--input` | `-i` | Path | Required | Input JSON report file |
| `--output` | `-o` | Path | `./results` | Output directory for reports |
| `--name` | | String | Auto | Base name for output files |

#### Format Values

- `json` - JSON format for programmatic access
- `markdown` - Markdown format for documentation
- `html` - HTML format for web viewing
- `csv` - CSV format for spreadsheet analysis

#### Examples

```bash
# Generate HTML report from JSON
python3 -m tests.cli report --input results/test_report.json --format html

# Generate multiple formats
python3 -m tests.cli report --input results/test_report.json -f html -f markdown -f csv

# Specify output directory and custom name
python3 -m tests.cli report --input results/test_report.json --output ./reports --name my-report
```

---

### cleanup

Remove test resources created during testing.

```bash
python3 -m tests.cli cleanup [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--platform` | `-p` | Choice | Required | Platform to clean up |
| `--namespace` | | String | `monitoring` | Kubernetes namespace |
| `--force` | | Flag | False | Skip confirmation prompt |
| `--all` | | Flag | False | Clean up all resources including volumes |

#### Examples

```bash
# Clean up minikube deployment
python3 -m tests.cli cleanup --platform minikube

# Clean up docker containers
python3 -m tests.cli cleanup --platform docker

# Force cleanup without confirmation
python3 -m tests.cli cleanup --platform eks --force

# Clean up all resources including volumes
python3 -m tests.cli cleanup --platform minikube --all
```

---

### status

Check Prometheus deployment status and health.

```bash
python3 -m tests.cli status [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--platform` | `-p` | Choice | `minikube` | Target platform |
| `--deployment-mode` | `-m` | Choice | `monolithic` | Deployment mode |
| `--prometheus-url` | | String | `http://localhost:9090` | Prometheus URL to check |

#### Examples

```bash
# Check minikube deployment
python3 -m tests.cli status --platform minikube

# Check specific URL
python3 -m tests.cli status --prometheus-url http://localhost:9090

# Check distributed deployment on EKS
python3 -m tests.cli status --platform eks --deployment-mode distributed
```

#### Output

The status command checks and displays:
- `/-/healthy` endpoint status
- `/-/ready` endpoint status
- Runtime information (version, storage retention)

---

### info

Display framework information and system details.

```bash
python3 -m tests.cli info
```

#### Output

Displays:
- Framework version
- System information (OS, Python version, hostname)
- Tool versions (k6, kubectl)
- Available platforms
- Available test types
- Available report formats

#### Example

```bash
python3 -m tests.cli info
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success - all tests passed or operation completed |
| `1` | Failure - tests failed or operation error |

## Environment Variables

The CLI respects the following environment variables for remote cluster access:

| Variable | Description |
|----------|-------------|
| `KUBECONFIG` | Path to Kubernetes configuration file |
| `AWS_PROFILE` | AWS profile for EKS access |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP credentials file for GKE access |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID for AKS access |

## Configuration File

The CLI can load configuration from a YAML file using the `--config` option. See [Configuration Schema](config-schema.md) for the complete schema reference.

```bash
python3 -m tests.cli run --config config/default.yaml
```

CLI arguments override values from the configuration file.

## See Also

- [Configuration Schema](config-schema.md) - YAML configuration reference
- [Getting Started](../testing/getting-started.md) - Quick start guide
- [Test Types](../testing/test-types.md) - Description of each test type
