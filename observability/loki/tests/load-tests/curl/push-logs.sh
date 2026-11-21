#!/bin/bash
# push-logs.sh - Push logs to Loki in a loop
#
# Usage: ./push-logs.sh [RATE] [DURATION]
#
# Environment variables:
#   LOKI_URL - Loki push endpoint (default: http://localhost:3100)
#   JOB - Job label value (default: curl-load-test)
#   ORG_ID - Tenant ID for multi-tenant (optional)
#
# Examples:
#   ./push-logs.sh                    # 10 logs/sec for 60 seconds
#   ./push-logs.sh 100 300            # 100 logs/sec for 5 minutes
#   LOKI_URL=http://loki:3100 ./push-logs.sh

set -e

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
JOB="${JOB:-curl-load-test}"
ORG_ID="${ORG_ID:-}"
RATE="${1:-10}"      # logs per second
DURATION="${2:-60}"  # seconds

# Build headers
HEADERS="-H 'Content-Type: application/json'"
if [ -n "$ORG_ID" ]; then
  HEADERS="$HEADERS -H 'X-Scope-OrgID: $ORG_ID'"
fi

echo "============================================"
echo "Loki Load Test - Push Logs"
echo "============================================"
echo "Loki URL: $LOKI_URL"
echo "Job: $JOB"
echo "Org ID: ${ORG_ID:-<not set>}"
echo "Rate: $RATE logs/sec"
echo "Duration: ${DURATION}s"
echo "Expected total: $((RATE * DURATION)) logs"
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

echo "Starting load test..."
start_time=$(date +%s)
end_time=$((start_time + DURATION))
count=0
errors=0
sleep_time=$(echo "scale=6; 1/$RATE" | bc)

while [ $(date +%s) -lt $end_time ]; do
  ts=$(date +%s%N)
  level="info"

  # Vary log levels
  case $((count % 10)) in
    0) level="error" ;;
    1|2) level="warn" ;;
    *) level="info" ;;
  esac

  # Push log
  response=$(curl -s -w "%{http_code}" -o /dev/null \
    -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    ${ORG_ID:+-H "X-Scope-OrgID: $ORG_ID"} \
    -d '{
      "streams": [{
        "stream": {
          "job": "'"$JOB"'",
          "level": "'"$level"'",
          "source": "curl-load-test"
        },
        "values": [
          ["'"$ts"'", "{\"level\":\"'"$level"'\",\"msg\":\"Load test log entry '"$count"'\",\"timestamp\":\"'"$(date -Iseconds)"'\",\"count\":'"$count"'}"]
        ]
      }]
    }')

  if [ "$response" != "204" ]; then
    errors=$((errors + 1))
    if [ $((errors % 100)) -eq 0 ]; then
      echo "Warning: $errors errors so far (last: HTTP $response)"
    fi
  fi

  count=$((count + 1))

  # Progress every 100 logs
  if [ $((count % 100)) -eq 0 ]; then
    elapsed=$(($(date +%s) - start_time))
    actual_rate=$((count / (elapsed + 1)))
    echo "Progress: $count logs sent, ${elapsed}s elapsed, ~${actual_rate} logs/sec"
  fi

  sleep $sleep_time
done

# Summary
elapsed=$(($(date +%s) - start_time))
actual_rate=$((count / (elapsed + 1)))

echo ""
echo "============================================"
echo "Load Test Complete"
echo "============================================"
echo "Total logs sent: $count"
echo "Total errors: $errors"
echo "Actual duration: ${elapsed}s"
echo "Actual rate: ~${actual_rate} logs/sec"
echo "Success rate: $(echo "scale=2; ($count - $errors) * 100 / $count" | bc)%"
echo "============================================"
