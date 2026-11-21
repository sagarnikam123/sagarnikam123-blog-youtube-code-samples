#!/bin/bash
# burst-test.sh - Sustained burst traffic test
#
# Usage: ./burst-test.sh [DURATION] [BATCH_SIZE]
#
# Environment variables:
#   LOKI_URL - Loki push endpoint (default: http://localhost:3100)
#   ORG_ID - Tenant ID for multi-tenant (optional)
#
# Examples:
#   ./burst-test.sh              # 60 seconds, 1000 logs per batch
#   ./burst-test.sh 300 5000     # 5 minutes, 5000 logs per batch

set -e

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
ORG_ID="${ORG_ID:-}"
DURATION="${1:-60}"
BATCH_SIZE="${2:-1000}"
CONCURRENT="${CONCURRENT:-5}"

echo "============================================"
echo "Loki Burst Traffic Test"
echo "============================================"
echo "Loki URL: $LOKI_URL"
echo "Org ID: ${ORG_ID:-<not set>}"
echo "Duration: ${DURATION}s"
echo "Batch size: $BATCH_SIZE logs"
echo "Concurrent requests: $CONCURRENT"
echo "============================================"
echo ""

# Check connectivity
echo "Checking Loki connectivity..."
if ! curl -s "$LOKI_URL/ready" > /dev/null 2>&1; then
  echo "ERROR: Cannot connect to Loki at $LOKI_URL"
  exit 1
fi
echo "✓ Loki is ready"
echo ""

# Get initial metrics
initial_bytes=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_distributor_bytes_received_total' | awk '{sum+=$2} END {print sum}' || echo "0")
initial_lines=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_distributor_lines_received_total' | awk '{sum+=$2} END {print sum}' || echo "0")

echo "Initial metrics:"
echo "  Bytes received: ${initial_bytes:-0}"
echo "  Lines received: ${initial_lines:-0}"
echo ""

echo "Starting burst test..."
start_time=$(date +%s)
end_time=$((start_time + DURATION))
total_logs=0
total_bytes=0
errors=0
rate_limits=0

# Generate padding for larger log lines (~500 bytes each)
PADDING=$(head -c 400 /dev/urandom | base64 | tr -d '\n')

push_batch() {
  local batch_num=$1
  local values=""

  for i in $(seq 1 $BATCH_SIZE); do
    ts=$(date +%s%N)
    if [ -n "$values" ]; then
      values="$values,"
    fi
    values="$values[\"$ts\", \"{\\\"level\\\":\\\"info\\\",\\\"msg\\\":\\\"Burst log batch $batch_num entry $i\\\",\\\"padding\\\":\\\"$PADDING\\\"}\"]"
  done

  response=$(curl -s -w "%{http_code}" -o /dev/null \
    -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    ${ORG_ID:+-H "X-Scope-OrgID: $ORG_ID"} \
    -d "{\"streams\": [{\"stream\": {\"job\": \"burst-test\", \"batch\": \"$batch_num\"}, \"values\": [$values]}]}")

  echo "$response"
}

batch_num=0
while [ $(date +%s) -lt $end_time ]; do
  # Launch concurrent requests
  pids=""
  for c in $(seq 1 $CONCURRENT); do
    batch_num=$((batch_num + 1))
    push_batch $batch_num > /tmp/burst-response-$c.txt &
    pids="$pids $!"
  done

  # Wait and collect results
  for pid in $pids; do
    wait $pid
  done

  # Check responses
  for c in $(seq 1 $CONCURRENT); do
    response=$(cat /tmp/burst-response-$c.txt 2>/dev/null || echo "000")
    if [ "$response" == "204" ]; then
      total_logs=$((total_logs + BATCH_SIZE))
    elif [ "$response" == "429" ]; then
      rate_limits=$((rate_limits + 1))
      errors=$((errors + 1))
    else
      errors=$((errors + 1))
    fi
  done

  # Progress every 10 batches
  if [ $((batch_num % 10)) -eq 0 ]; then
    elapsed=$(($(date +%s) - start_time))
    rate=$((total_logs / (elapsed + 1)))
    echo "Progress: $total_logs logs, ${elapsed}s elapsed, ~$rate logs/sec, $rate_limits rate limits"
  fi
done

# Final metrics
final_bytes=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_distributor_bytes_received_total' | awk '{sum+=$2} END {print sum}' || echo "0")
final_lines=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_distributor_lines_received_total' | awk '{sum+=$2} END {print sum}' || echo "0")
discarded=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_discarded_samples_total' | awk '{sum+=$2} END {print sum}' || echo "0")

elapsed=$(($(date +%s) - start_time))
bytes_pushed=$((final_bytes - initial_bytes))
lines_pushed=$((final_lines - initial_lines))

echo ""
echo "============================================"
echo "Burst Test Complete"
echo "============================================"
echo "Duration: ${elapsed}s"
echo "Batches sent: $batch_num"
echo "Logs attempted: $total_logs"
echo "Logs received by Loki: $lines_pushed"
echo "Bytes received by Loki: $bytes_pushed"
echo "Rate limits hit: $rate_limits"
echo "Other errors: $((errors - rate_limits))"
echo "Discarded samples: ${discarded:-0}"
echo "Average rate: $((lines_pushed / elapsed)) logs/sec"
echo "Average throughput: $((bytes_pushed / elapsed / 1024)) KB/sec"
echo "============================================"

# Cleanup
rm -f /tmp/burst-response-*.txt
