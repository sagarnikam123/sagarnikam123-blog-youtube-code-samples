#!/bin/bash
# test-queries.sh - Test LogQL queries against Loki
#
# Usage: ./test-queries.sh [LOKI_ADDR] [ORG_ID]
#
# Examples:
#   ./test-queries.sh
#   ./test-queries.sh http://localhost:3100
#   ./test-queries.sh http://localhost:3100 tenant-1

set -e

LOKI_ADDR="${1:-${LOKI_ADDR:-http://localhost:3100}}"
ORG_ID="${2:-${LOKI_ORG_ID:-}}"

# Build org-id flag if set
ORG_FLAG=""
if [ -n "$ORG_ID" ]; then
  ORG_FLAG="--org-id=$ORG_ID"
fi

echo "============================================"
echo "Loki Query Performance Test"
echo "============================================"
echo "Loki Address: $LOKI_ADDR"
echo "Org ID: ${ORG_ID:-<not set>}"
echo "============================================"
echo ""

# Check connectivity
echo "Checking connectivity..."
if ! logcli labels --addr="$LOKI_ADDR" $ORG_FLAG > /dev/null 2>&1; then
  echo "ERROR: Cannot connect to Loki at $LOKI_ADDR"
  exit 1
fi
echo "✓ Connected to Loki"
echo ""

# List available labels
echo "Available labels:"
logcli labels --addr="$LOKI_ADDR" $ORG_FLAG
echo ""

# Define test queries
declare -a QUERIES=(
  # Basic queries
  '{job=~".+"}'

  # Filter queries
  '{job=~".+"} |= "error"'
  '{job=~".+"} |~ "error|warn|ERROR|WARN"'

  # Parser queries
  '{job=~".+"} | json'
  '{job=~".+"} | logfmt'

  # Metric queries
  'count_over_time({job=~".+"}[5m])'
  'rate({job=~".+"}[5m])'
  'bytes_rate({job=~".+"}[5m])'

  # Aggregation queries
  'sum by (job) (count_over_time({job=~".+"}[5m]))'
  'topk(5, sum by (job) (rate({job=~".+"}[5m])))'
)

echo "============================================"
echo "Running Query Tests"
echo "============================================"
echo ""

for query in "${QUERIES[@]}"; do
  echo "Query: $query"
  echo "---"

  # Time the query
  start_time=$(date +%s.%N)

  result=$(logcli query "$query" \
    --addr="$LOKI_ADDR" \
    $ORG_FLAG \
    --limit=10 \
    --since=1h \
    --quiet 2>&1) || true

  end_time=$(date +%s.%N)
  duration=$(echo "$end_time - $start_time" | bc)

  # Count results
  result_count=$(echo "$result" | grep -c "^" || echo "0")

  echo "Results: $result_count entries"
  echo "Duration: ${duration}s"
  echo ""
done

echo "============================================"
echo "Instant Query Tests"
echo "============================================"
echo ""

declare -a INSTANT_QUERIES=(
  'count_over_time({job=~".+"}[1h])'
  'sum(rate({job=~".+"}[5m]))'
  'sum by (job) (count_over_time({job=~".+"}[1h]))'
)

for query in "${INSTANT_QUERIES[@]}"; do
  echo "Query: $query"
  echo "---"

  start_time=$(date +%s.%N)

  result=$(logcli instant-query "$query" \
    --addr="$LOKI_ADDR" \
    $ORG_FLAG \
    --quiet 2>&1) || true

  end_time=$(date +%s.%N)
  duration=$(echo "$end_time - $start_time" | bc)

  echo "Result: $result"
  echo "Duration: ${duration}s"
  echo ""
done

echo "============================================"
echo "Test Complete"
echo "============================================"
