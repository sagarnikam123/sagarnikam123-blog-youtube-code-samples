# Mimirtool - Mimir CLI Tool

Official CLI for Grafana Mimir operations, testing, and management.

## Installation

```bash
# Download latest release
wget https://github.com/grafana/mimir/releases/latest/download/mimirtool-linux-amd64
chmod +x mimirtool-linux-amd64
mv mimirtool-linux-amd64 /usr/local/bin/mimirtool

# Verify
mimirtool version

# Docker
docker run grafana/mimirtool:latest version
```

## Configuration

```bash
# Set environment variables
export MIMIR_ADDRESS=http://localhost:8080
export MIMIR_TENANT_ID=demo
export MIMIR_API_KEY=<optional>
```

## Use Cases

### 1. Alertmanager Management

```bash
# Get alertmanager config
mimirtool alertmanager get

# Load alertmanager config
mimirtool alertmanager load alertmanager.yaml

# Delete alertmanager config
mimirtool alertmanager delete
```

### 2. Rules Management

```bash
# List rule groups
mimirtool rules list

# Get specific rule group
mimirtool rules get --namespace=default --group=alerts

# Load rules from file
mimirtool rules load rules.yaml

# Delete rule group
mimirtool rules delete --namespace=default --group=alerts

# Sync rules from directory
mimirtool rules sync --rule-dirs=./rules/

# Lint rules
mimirtool rules lint rules.yaml
```

### 3. Load Testing

```bash
# Generate load test
mimirtool analyze grafana \
  --address=http://localhost:8080 \
  --tenant-id=demo

# Analyze dashboard queries
mimirtool analyze dashboard dashboard.json

# Analyze ruler
mimirtool analyze ruler \
  --address=http://localhost:8080 \
  --tenant-id=demo
```

### 4. Bucket Operations

```bash
# List blocks in bucket
mimirtool bucket list \
  --backend=s3 \
  --s3.endpoint=localhost:9000 \
  --s3.bucket-name=mimir

# Validate blocks
mimirtool bucket validate \
  --backend=s3 \
  --s3.endpoint=localhost:9000 \
  --s3.bucket-name=mimir
```

### 5. Remote Read

```bash
# Query remote read
mimirtool remote-read query \
  --address=http://localhost:8080 \
  --tenant-id=demo \
  'up{job="mimir"}'

# Export metrics
mimirtool remote-read export \
  --address=http://localhost:8080 \
  --tenant-id=demo \
  --match='up' \
  --output=metrics.json
```

### 6. ACL Management (Multi-tenancy)

```bash
# Get ACL
mimirtool acl get

# Set ACL
mimirtool acl set acl.yaml
```

## Example Configurations

### rules.yaml
```yaml
namespace: default
groups:
  - name: example
    interval: 30s
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)

      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected
```

### alertmanager.yaml
```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXX'
        channel: '#alerts'
```

## Load Testing Workflow

```bash
# 1. Analyze existing Grafana dashboards
mimirtool analyze grafana \
  --address=http://localhost:8080 \
  --tenant-id=demo \
  --grafana-url=http://grafana:3000

# 2. Generate load based on analysis
mimirtool analyze dashboard dashboard.json \
  --output=load-test.yaml

# 3. Review generated queries and adjust
cat load-test.yaml
```

## Useful Scripts

**sync-rules.sh**:
```bash
#!/bin/bash
RULES_DIR="./rules"
MIMIR_URL="http://localhost:8080"
TENANT="demo"

mimirtool rules sync \
  --address="$MIMIR_URL" \
  --id="$TENANT" \
  --rule-dirs="$RULES_DIR"
```

**backup-config.sh**:
```bash
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup rules
mimirtool rules list > "$BACKUP_DIR/rules.yaml"

# Backup alertmanager config
mimirtool alertmanager get > "$BACKUP_DIR/alertmanager.yaml"

echo "Backup completed: $BACKUP_DIR"
```

## Resources

- [Mimirtool Documentation](https://grafana.com/docs/mimir/latest/manage/tools/mimirtool/)
- [GitHub Repository](https://github.com/grafana/mimir/tree/main/cmd/mimirtool)
