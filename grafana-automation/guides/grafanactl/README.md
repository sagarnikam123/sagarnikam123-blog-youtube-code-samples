# Grafana CLI (grafanactl) Guide

Complete guide for managing Grafana resources using the official Grafana CLI tool.

> **Note**: As of date, the project is in "public preview" and still under active development.

## Installation

```bash
# Homebrew (macOS/Linux)
brew install grafana/tap/grafanactl

# Download binary
wget https://github.com/grafana/grafanactl/releases/latest/download/grafanactl-linux-amd64
chmod +x grafanactl-linux-amd64
sudo mv grafanactl-linux-amd64 /usr/local/bin/grafanactl

# Go install (go >= v1.24 installed)
go install github.com/grafana/grafanactl@latest

# Docker
docker run --rm grafana/grafanactl:latest --help
```

## Check Installation & Help

```shell
# Help page
grafanactl  # get available commands to run
grafanactl --help

# Version
grafanactl --version

# Location where installation is
which grafanactl
```

## Configuration

Two ways: using environment variables or through a configuration file.
- By default, Grafana CLI uses the default context
- Default config (on Mac): `"/Users/<user>/Library/Application Support/grafanactl/config.yaml"`

```shell
# View entire configuration
grafanactl config view

# Get the existing contexts
grafanactl config list-contexts

# Check the configuration for any issue
grafanactl config check
# Note: this command will give you following errors if not configured:
# "✘ Configuration: Invalid configuration: server is required"
#   solution - set GRAFANA_SERVER
# "✘ Configuration: Invalid configuration: missing contexts.default.org-id or contexts.default.stack-id"
#   solution - set GRAFANA_ORG_ID
```

### Method 1: Environment Variables
Deals only with a single context, good for starting with Local instance or CI environments.

```bash
# Required to interact with Grafana instance
export GRAFANA_SERVER='http://localhost:3000'
export GRAFANA_ORG_ID='1'
export GRAFANA_STACK_ID='<stack-id>' # when using Grafana Cloud

# For executing operations
# If using a Grafana service account (recommended)
export GRAFANA_TOKEN='<grafana-token>'

# If using basic authentication
export GRAFANA_USER='<grafana-user>'
export GRAFANA_PASSWORD='<grafana-password>'
```

### Method 2: Configuration File
Store multiple contexts, providing a convenient way to switch between Grafana instances.

```bash
# Create config directory
mkdir -p ~/.config/grafanactl

# Create configuration file
cat > ~/.config/grafanactl/config.yaml << EOF
contexts:
  local:
    grafana:
      server: http://localhost:3000
      token: <grafana-service-account-token>
  production:
    grafana:
      url: https://production.grafana.example
      token: <glsa_prod_token_here>
current-context: local
EOF
```

### Method 3: Command Line Configuration

#### Configure the default context
```shell
grafanactl config set contexts.default.grafana.server http://localhost:3000
grafanactl config set contexts.default.grafana.org-id 1

# Authenticate with a service account token
grafanactl config set contexts.default.grafana.token <grafana-service-account-token>

# Or alternatively, use basic authentication
grafanactl config set contexts.default.grafana.user <grafana-user>
grafanactl config set contexts.default.grafana.password <grafana-password>
```

#### Configure new context
```shell
grafanactl config set contexts.production.grafana.server https://production.grafana.example
grafanactl config set contexts.production.grafana.org-id 1
```

### Switch Contexts
```bash
# List available contexts
grafanactl config get-contexts

# Switch to different context
grafanactl config use-context production

# View current configuration
grafanactl config current-context
```

## Dashboard Management

```bash
# List dashboards
grafanactl get dashboards
grafanactl get dashboards --folder monitoring

# Get dashboard details
grafanactl get dashboard my-dashboard-uid
grafanactl get dashboard my-dashboard-uid -o yaml
grafanactl get dashboard my-dashboard-uid -o json

# Export dashboard
grafanactl get dashboard my-dashboard-uid -o json > dashboard.json

# Create/Update dashboard
grafanactl apply -f dashboard.json
grafanactl apply -f dashboard.yaml

# Delete dashboard
grafanactl delete dashboard my-dashboard-uid

# Search dashboards
grafanactl get dashboards --search "system"
```

## Folder Management

```bash
# List folders
grafanactl get folders

# Create folder
grafanactl create folder --title "Monitoring" --uid monitoring

# Get folder
grafanactl get folder monitoring

# Delete folder
grafanactl delete folder monitoring
```

## Datasource Management

```bash
# List datasources
grafanactl get datasources

# Get datasource
grafanactl get datasource prometheus

# Create datasource
grafanactl apply -f datasource.yaml

# Delete datasource
grafanactl delete datasource prometheus

# Test datasource
grafanactl test datasource prometheus
```

## Alert Management

```bash
# List alert rules
grafanactl get alert-rules

# Get alert rule
grafanactl get alert-rule my-alert-uid

# Create/Update alert rule
grafanactl apply -f alert-rule.yaml

# Delete alert rule
grafanactl delete alert-rule my-alert-uid

# List notification policies
grafanactl get notification-policies
```

## Dashboards as Code

```bash
# Initialize dashboard project
mkdir my-dashboards && cd my-dashboards
grafanactl dashboard init

# Generate dashboard from template
grafanactl dashboard generate --template prometheus

# Validate dashboards
grafanactl dashboard validate .

# Deploy dashboards
grafanactl dashboard deploy .

# Watch for changes
grafanactl dashboard watch .
```

## Resource Exploration

```bash
# Describe resource
grafanactl describe dashboard my-dashboard-uid
grafanactl describe datasource prometheus

# Get resource in different formats
grafanactl get dashboard my-dashboard-uid -o wide
grafanactl get dashboard my-dashboard-uid -o yaml
grafanactl get dashboard my-dashboard-uid -o json

# Filter resources
grafanactl get dashboards --selector "tag=monitoring"
grafanactl get dashboards --field-selector "folder=monitoring"
```

## Bulk Operations

```bash
# Export all dashboards
grafanactl get dashboards -o yaml > all-dashboards.yaml

# Export specific folder
grafanactl get dashboards --folder monitoring -o yaml > monitoring-dashboards.yaml

# Apply multiple resources
grafanactl apply -f dashboards/
grafanactl apply -R -f .

# Delete multiple resources
grafanactl delete -f dashboards/
```

## Configuration File Examples

### Complete Config File
```yaml
# ~/.config/grafanactl/config.yaml
apiVersion: v1
kind: Config
contexts:
- name: local
  context:
    server: http://localhost:3000
    token: xxxxxxxxxxxxxxxxxxxxxxxxx
- name: production
  context:
    server: https://grafana.company.com
    token: xxxxxxxxxxxxxxxxxxxxxxxxx
current-context: local
```

### Datasource YAML Example
```yaml
# datasource.yaml
apiVersion: v1
kind: Datasource
metadata:
  name: prometheus
spec:
  name: Prometheus
  type: prometheus
  access: proxy
  url: http://prometheus:9090
  isDefault: true
  jsonData:
    httpMethod: POST
    manageAlerts: true
    prometheusType: Prometheus
    cacheLevel: High
```

### Dashboard YAML Example
```yaml
# dashboard.yaml
apiVersion: v1
kind: Dashboard
metadata:
  name: system-metrics
spec:
  title: "System Metrics"
  tags: ["system", "monitoring"]
  panels:
    - id: 1
      title: "CPU Usage"
      type: "stat"
      targets:
        - expr: "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          refId: "A"
      gridPos:
        h: 8
        w: 12
        x: 0
        y: 0
  time:
    from: "now-1h"
    to: "now"
  refresh: "5s"
```

## Environment Variables

```bash
# Authentication
GRAFANA_URL="http://localhost:3000"
GRAFANA_TOKEN="your-api-token"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Configuration
GRAFANA_CONFIG_HOME="~/.config/grafanactl"
GRAFANA_CONTEXT="local"

# Output
GRAFANA_OUTPUT="json"  # json, yaml, table, wide
GRAFANA_NO_HEADERS="false"

# Debugging
GRAFANA_DEBUG="true"
GRAFANA_LOG_LEVEL="debug"
```

## Advanced Operations

### Multi-Environment Workflow
```bash
# Development
grafanactl config use-context dev
grafanactl apply -f dashboards/

# Staging
grafanactl config use-context staging
grafanactl apply -f dashboards/

# Production
grafanactl config use-context prod
grafanactl apply -f dashboards/
```

### CI/CD Integration
```yaml
# .github/workflows/grafana-deploy.yml
name: Deploy Grafana Resources
on:
  push:
    branches: [main]
    paths: ['grafana/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup grafanactl
        run: |
          wget https://github.com/grafana/grafanactl/releases/latest/download/grafanactl-linux-amd64
          chmod +x grafanactl-linux-amd64
          sudo mv grafanactl-linux-amd64 /usr/local/bin/grafanactl

      - name: Deploy to Grafana
        env:
          GRAFANA_SERVER: ${{ secrets.GRAFANA_URL }}
          GRAFANA_TOKEN: ${{ secrets.GRAFANA_TOKEN }}
          GRAFANA_ORG_ID: "1"
        run: |
          grafanactl apply -f grafana/datasources/
          grafanactl apply -f grafana/dashboards/
          grafanactl apply -f grafana/alerts/
```

### Backup and Restore
```bash
# Backup all resources
mkdir grafana-backup
grafanactl get dashboards -o yaml > grafana-backup/dashboards.yaml
grafanactl get datasources -o yaml > grafana-backup/datasources.yaml
grafanactl get folders -o yaml > grafana-backup/folders.yaml

# Restore from backup
grafanactl apply -f grafana-backup/
```

## Best Practices

1. **Use contexts** for different environments
2. **Version control** your YAML configurations
3. **Test with dry-run** before applying changes
4. **Use service account tokens** instead of user credentials
5. **Organize resources** in separate directories
6. **Validate configurations** before deployment

## Troubleshooting

### Common Issues

1. **Configuration Invalid**
   ```bash
   # Check configuration
   grafanactl config check

   # Set required variables
   export GRAFANA_SERVER="http://localhost:3000"
   export GRAFANA_ORG_ID="1"
   ```

2. **Authentication Failed**
   ```bash
   # Verify token
   curl -H "Authorization: Bearer $GRAFANA_TOKEN" $GRAFANA_SERVER/api/user
   ```

3. **Resource Not Found**
   ```bash
   # List available resources
   grafanactl get dashboards
   grafanactl get datasources
   ```

### Debug Mode
```bash
# Enable debug logging
export GRAFANA_DEBUG=true
export GRAFANA_LOG_LEVEL=debug

# Run command with verbose output
grafanactl get dashboards -v
```

## References

- [Grafanactl Documentation](https://grafana.github.io/grafanactl/)
- [Environment Variables Reference](https://grafana.github.io/grafanactl/reference/environment-variables/)
- [Configuration Reference](https://grafana.github.io/grafanactl/reference/configuration/)
- [GitHub Repository](https://github.com/grafana/grafanactl)
