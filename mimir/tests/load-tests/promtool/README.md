# Promtool - Official Prometheus Testing Tool

Official Prometheus CLI for testing queries, rules, and TSDB performance.

## Installation

```bash
# macOS
brew install prometheus

# Linux
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*/
./promtool --version

# Docker
docker run --rm prom/prometheus:latest promtool --version
```

## Use Cases

### 1. Query Testing

```bash
# Test query against Mimir
promtool query instant http://localhost:8080 'up' \
  --header "X-Scope-OrgID: demo"

# Range query
promtool query range http://localhost:8080 \
  'rate(http_requests_total[5m])' \
  --start=2024-01-01T00:00:00Z \
  --end=2024-01-01T01:00:00Z \
  --step=1m \
  --header "X-Scope-OrgID: demo"

# Query series
promtool query series http://localhost:8080 \
  --match='up' \
  --header "X-Scope-OrgID: demo"
```

### 2. Rule Testing

```bash
# Validate recording/alerting rules
promtool check rules rules.yaml

# Test rules with mock data
promtool test rules test.yaml
```

**Example test.yaml:**
```yaml
rule_files:
  - rules.yaml

evaluation_interval: 1m

tests:
  - interval: 1m
    input_series:
      - series: 'http_requests_total{job="api", instance="0"}'
        values: '0+10x10'
    alert_rule_test:
      - eval_time: 5m
        alertname: HighRequestRate
        exp_alerts:
          - exp_labels:
              severity: warning
              job: api
```

### 3. TSDB Benchmarking

```bash
# Analyze TSDB blocks
promtool tsdb analyze /path/to/data

# List TSDB blocks
promtool tsdb list /path/to/data

# Dump samples
promtool tsdb dump /path/to/data
```

### 4. Config Validation

```bash
# Check Prometheus config
promtool check config prometheus.yml

# Check web config
promtool check web-config web.yml
```

## Query Performance Testing

```bash
# Test query performance
time promtool query instant http://localhost:8080 \
  'sum(rate(http_requests_total[5m])) by (job)' \
  --header "X-Scope-OrgID: demo"

# Batch query testing
cat queries.txt | while read query; do
  echo "Testing: $query"
  time promtool query instant http://localhost:8080 "$query" \
    --header "X-Scope-OrgID: demo"
done
```

## Label Analysis

```bash
# Get label names
promtool query labels http://localhost:8080 \
  --header "X-Scope-OrgID: demo"

# Get label values
promtool query label http://localhost:8080 job \
  --header "X-Scope-OrgID: demo"
```

## Useful Scripts

**queries.txt** - Sample queries for testing:
```
up
rate(http_requests_total[5m])
sum(rate(http_requests_total[5m])) by (job)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
topk(10, sum(rate(http_requests_total[5m])) by (instance))
```

**test-queries.sh**:
```bash
#!/bin/bash
MIMIR_URL="http://localhost:8080"
TENANT="demo"

while IFS= read -r query; do
  echo "Query: $query"
  promtool query instant "$MIMIR_URL" "$query" \
    --header "X-Scope-OrgID: $TENANT"
  echo "---"
done < queries.txt
```

## Resources

- [Promtool Documentation](https://prometheus.io/docs/prometheus/latest/command-line/promtool/)
- [Query Testing Guide](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)
