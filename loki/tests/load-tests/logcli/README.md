# logcli - Loki Command Line Interface

Official Loki CLI for querying logs and testing LogQL.

## Installation

```bash
# macOS
brew install logcli

# Linux
curl -O -L "https://github.com/grafana/loki/releases/download/v3.0.0/logcli-linux-amd64.zip"
unzip logcli-linux-amd64.zip
chmod +x logcli-linux-amd64
sudo mv logcli-linux-amd64 /usr/local/bin/logcli

# Docker
docker run grafana/logcli:latest --help
```

## Configuration

```bash
# Environment variables
export LOKI_ADDR=http://localhost:3100
export LOKI_ORG_ID=tenant-1  # For multi-tenant

# Or use flags
logcli query '{job="test"}' --addr=http://localhost:3100 --org-id=tenant-1
```

## Use Cases

### 1. Basic Queries

```bash
# Query by label
logcli query '{job="fluent-bit"}'

# Query with filter
logcli query '{job="app"} |= "error"'

# Query with regex
logcli query '{job="app"} |~ "error|warn"'

# Query with JSON parsing
logcli query '{job="app"} | json | level="error"'

# Query with logfmt parsing
logcli query '{job="app"} | logfmt | status>=500'
```

### 2. Time Range Queries

```bash
# Last 1 hour
logcli query '{job="app"}' --since=1h

# Last 24 hours
logcli query '{job="app"}' --since=24h

# Specific time range
logcli query '{job="app"}' \
  --from="2024-01-01T00:00:00Z" \
  --to="2024-01-01T01:00:00Z"
```

### 3. Output Formatting

```bash
# Default (timestamp + log line)
logcli query '{job="app"}'

# JSON output
logcli query '{job="app"}' -o json

# Raw log lines only
logcli query '{job="app"}' -o raw

# With labels
logcli query '{job="app"}' --include-label=level
```

### 4. Metric Queries

```bash
# Count logs per minute
logcli query 'count_over_time({job="app"}[1m])'

# Rate of logs
logcli query 'rate({job="app"}[5m])'

# Bytes rate
logcli query 'bytes_rate({job="app"}[5m])'

# Sum by label
logcli query 'sum by (level) (count_over_time({job="app"}[5m]))'
```

### 5. Instant Queries

```bash
# Current count
logcli instant-query 'count_over_time({job="app"}[1h])'

# Current rate
logcli instant-query 'rate({job="app"}[5m])'
```

### 6. Label Discovery

```bash
# List all labels
logcli labels

# List values for a label
logcli labels job

# List series
logcli series '{job="app"}'
```

### 7. Live Tail

```bash
# Tail logs in real-time
logcli tail '{job="app"}'

# Tail with filter
logcli tail '{job="app"} |= "error"'

# Tail with delay tolerance
logcli tail '{job="app"}' --delay-for=5s
```

## Query Performance Testing

### Test Script

```bash
#!/bin/bash
# test-queries.sh

LOKI_ADDR="${LOKI_ADDR:-http://localhost:3100}"
QUERIES=(
  '{job="test"}'
  '{job="test"} |= "error"'
  '{job="test"} | json'
  'rate({job="test"}[5m])'
  'count_over_time({job="test"}[1h])'
  'sum by (level) (count_over_time({job="test"}[5m]))'
)

echo "Testing queries against $LOKI_ADDR"
echo "=================================="

for query in "${QUERIES[@]}"; do
  echo ""
  echo "Query: $query"
  echo "---"
  time logcli query "$query" --addr="$LOKI_ADDR" --limit=10 --quiet
done
```

### Batch Query Testing

```bash
# queries.txt
{job="app"}
{job="app"} |= "error"
{job="app"} | json | level="error"
rate({job="app"}[5m])
count_over_time({job="app"}[1h])

# Run all queries
cat queries.txt | while read query; do
  echo "Query: $query"
  time logcli query "$query" --limit=100 --quiet
  echo "---"
done
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--addr` | Loki server address | http://localhost:3100 |
| `--org-id` | Tenant ID | - |
| `--limit` | Max entries to return | 30 |
| `--since` | Lookback duration | 1h |
| `--from` | Start time | - |
| `--to` | End time | - |
| `-o` | Output format (default, json, raw) | default |
| `--quiet` | Suppress info messages | false |
| `--forward` | Show oldest first | false |

## Troubleshooting

```bash
# Check connectivity
logcli labels --addr=http://localhost:3100

# Debug mode
logcli query '{job="test"}' --addr=http://localhost:3100 2>&1 | head

# Check available labels
logcli labels

# Check series count
logcli series '{job="test"}' | wc -l
```

## Resources

- [logcli Documentation](https://grafana.com/docs/loki/latest/query/logcli/)
- [LogQL Reference](https://grafana.com/docs/loki/latest/query/)
- [Loki Releases](https://github.com/grafana/loki/releases)
