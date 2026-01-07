#!/bin/bash
# large-line-test.sh - Test large log line handling
#
# Usage: ./large-line-test.sh [LINE_SIZE] [COUNT]
#
# Environment variables:
#   LOKI_URL - Loki push endpoint (default: http://localhost:3100)
#   ORG_ID - Tenant ID for multi-tenant (optional)
#
# Examples:
#   ./large-line-test.sh                # 250KB lines, 100 logs
#   ./large-line-test.sh 100000 50      # 100KB lines, 50 logs
#   ./large-line-test.sh 300000 10      # 300KB lines (over limit), 10 logs

set -e

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
ORG_ID="${ORG_ID:-}"
LINE_SIZE="${1:-250000}"  # ~250KB, just under 256KB default limit
COUNT="${2:-100}"

echo "============================================"
echo "Loki Large Log Line Test"
echo "============================================"
echo "Loki URL: $LOKI_URL"
echo "Org ID: ${ORG_ID:-<not set>}"
echo "Line size: $LINE_SIZE bytes (~$((LINE_SIZE / 1024)) KB)"
echo "Count: $COUNT logs"
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
initial_discarded=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_discarded_samples_total{.*reason="line_too_long"' | awk '{sum+=$2} END {print sum}' || echo "0")

echo "Initial discarded (line_too_long): ${initial_discarded:-0}"
echo ""

# Generate large payload (base64 encoded random data)
echo "Generating ${LINE_SIZE} byte payload..."
PAYLOAD=$(head -c $LINE_SIZE /dev/urandom | base64 | tr -d '\n' | head -c $LINE_SIZE)
actual_size=${#PAYLOAD}
echo "Actual payload size: $actual_size bytes"
echo ""

echo "Starting large log test..."
start_time=$(date +%s)
success=0
rejected=0
errors=0

for i in $(seq 1 $COUNT); do
  ts=$(date +%s%N)

  # Create JSON with the large payload
  # Note: The actual log line will be larger due to JSON escaping
  response=$(curl -s -w "%{http_code}" -o /tmp/large-log-response.txt \
    -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    ${ORG_ID:+-H "X-Scope-OrgID: $ORG_ID"} \
    -d '{
      "streams": [{
        "stream": {
          "job": "large-log-test",
          "size": "'"$LINE_SIZE"'"
        },
        "values": [["'"$ts"'", "{\"msg\":\"Large log entry '"$i"'\",\"data\":\"'"$PAYLOAD"'\"}"]]
      }]
    }')

  case "$response" in
    204)
      success=$((success + 1))
      status="✓ accepted"
      ;;
    400)
      rejected=$((rejected + 1))
      status="✗ rejected (line too long?)"
      ;;
    429)
      rejected=$((rejected + 1))
      status="✗ rate limited"
      ;;
    *)
      errors=$((errors + 1))
      status="✗ error ($response)"
      ;;
  esac

  echo "Log $i/$COUNT: $status"

  # Show error details for failures
  if [ "$response" != "204" ]; then
    cat /tmp/large-log-response.txt 2>/dev/null | head -c 200
    echo ""
  fi
done

# Final metrics
final_discarded=$(curl -s "$LOKI_URL/metrics" 2>/dev/null | grep 'loki_discarded_samples_total{.*reason="line_too_long"' | awk '{sum+=$2} END {print sum}' || echo "0")
elapsed=$(($(date +%s) - start_time))

echo ""
echo "============================================"
echo "Large Log Test Complete"
echo "============================================"
echo "Duration: ${elapsed}s"
echo "Line size: $LINE_SIZE bytes"
echo "Total logs: $COUNT"
echo "Successful: $success"
echo "Rejected: $rejected"
echo "Errors: $errors"
echo "Discarded (line_too_long): $((final_discarded - initial_discarded))"
echo "============================================"

# Recommendations
echo ""
if [ $rejected -gt 0 ]; then
  echo "⚠️  Some logs were rejected. Consider:"
  echo "   - Increasing max_line_size in limits_config"
  echo "   - Enabling max_line_size_truncate: true"
  echo "   - Reducing log line size in your application"
fi

# Cleanup
rm -f /tmp/large-log-response.txt
