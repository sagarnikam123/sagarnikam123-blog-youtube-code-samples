#!/bin/bash
# cardinality-bomb.sh - Push logs with high cardinality labels
#
# Usage: ./cardinality-bomb.sh [STREAMS] [BATCH_SIZE]
#
# Environment variables:
#   LOKI_URL - Loki push endpoint (default: http://localhost:3100)
#   ORG_ID - Tenant ID for multi-tenant (optional)
#
# Examples:
#   ./cardinality-bomb.sh              # 10000 streams
#   ./cardinality-bomb.sh 50000 500    # 50000 streams, 500 per batch

set -e

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
ORG_ID="${ORG_ID:-}"
STREAMS="${1:-10000}"
BATCH_SIZE="${2:-100}"

echo "============================================"
echo "Loki Cardinality Bomb Test"
echo "============================================"
echo "Loki URL: $LOKI_URL"
echo "Org ID: ${ORG_ID:-<not set>}"
echo "Target streams: $STREAMS"
echo "Batch size: $BATCH_SIZE"
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

# Get initial stream count
initial_streams=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_ingester_memory_streams{' | awk '{sum+=$2} END {print sum}' || echo "0")
echo "Initial stream count: ${initial_streams:-0}"
echo ""

echo "Starting cardinality bomb..."
start_time=$(date +%s)
count=0
errors=0

while [ $count -lt $STREAMS ]; do
  # Build batch of streams
  streams_json=""
  batch_end=$((count + BATCH_SIZE))
  if [ $batch_end -gt $STREAMS ]; then
    batch_end=$STREAMS
  fi

  for i in $(seq $((count + 1)) $batch_end); do
    ts=$(date +%s%N)

    if [ -n "$streams_json" ]; then
      streams_json="$streams_json,"
    fi

    streams_json="$streams_json{
      \"stream\": {
        \"job\": \"cardinality-bomb\",
        \"user_id\": \"user-$i\",
        \"session_id\": \"session-$RANDOM-$i\",
        \"request_id\": \"req-$RANDOM-$i\"
      },
      \"values\": [[\"$ts\", \"High cardinality log entry $i\"]]
    }"
  done

  # Push batch
  response=$(curl -s -w "%{http_code}" -o /tmp/loki-response.txt \
    -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    ${ORG_ID:+-H "X-Scope-OrgID: $ORG_ID"} \
    -d "{\"streams\": [$streams_json]}")

  if [ "$response" != "204" ]; then
    errors=$((errors + 1))
    echo "Batch $((count / BATCH_SIZE + 1)) failed with HTTP $response"
    if [ "$response" == "429" ]; then
      echo "Rate limited! Waiting 5 seconds..."
      sleep 5
    fi
    cat /tmp/loki-response.txt 2>/dev/null | head -c 200
    echo ""
  fi

  count=$batch_end

  # Progress
  if [ $((count % 1000)) -eq 0 ] || [ $count -eq $STREAMS ]; then
    current_streams=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_ingester_memory_streams{' | awk '{sum+=$2} END {print sum}' || echo "?")
    echo "Progress: $count/$STREAMS streams pushed, Active: ${current_streams:-?}"
  fi
done

# Summary
elapsed=$(($(date +%s) - start_time))
final_streams=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_ingester_memory_streams{' | awk '{sum+=$2} END {print sum}' || echo "?")
discarded=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_discarded_samples_total' | awk '{sum+=$2} END {print sum}' || echo "0")

echo ""
echo "============================================"
echo "Cardinality Bomb Complete"
echo "============================================"
echo "Streams attempted: $STREAMS"
echo "Batch errors: $errors"
echo "Duration: ${elapsed}s"
echo "Initial streams: ${initial_streams:-0}"
echo "Final streams: ${final_streams:-?}"
echo "Discarded samples: ${discarded:-0}"
echo "============================================"

# Cleanup
rm -f /tmp/loki-response.txt
