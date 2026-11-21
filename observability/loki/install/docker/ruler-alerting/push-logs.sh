#!/bin/sh
# Push logs from stdin (fuzzy-train JSON output) to Loki's push API
# Usage: python3 fuzzy-train.py | ./push-logs.sh
#
# Batches lines and sends every $BATCH_INTERVAL seconds or $BATCH_SIZE lines

LOKI_URL="${LOKI_URL:-http://loki:3100}"
JOB="${JOB_LABEL:-fuzzy-train}"
BATCH_SIZE="${BATCH_SIZE:-10}"
BATCH_INTERVAL="${BATCH_INTERVAL:-2}"

batch=""
count=0
last_send=$(date +%s)

send_batch() {
    if [ -z "$batch" ]; then
        return
    fi
    # Remove trailing comma
    values=$(echo "$batch" | sed 's/,$//')
    payload="{\"streams\":[{\"stream\":{\"job\":\"${JOB}\"},\"values\":[${values}]}]}"

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${LOKI_URL}/loki/api/v1/push" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null)

    if [ "$response" != "204" ] && [ "$response" != "200" ]; then
        echo "[push-logs] WARN: Loki returned HTTP $response" >&2
    fi

    batch=""
    count=0
    last_send=$(date +%s)
}

echo "[push-logs] Pushing to ${LOKI_URL} with job=${JOB}, batch_size=${BATCH_SIZE}, interval=${BATCH_INTERVAL}s"

while IFS= read -r line; do
    # Loki push API format: [nanosecond_timestamp_string, log_line]
    ts_ns=$(date +%s)000000000
    # Escape the JSON line for embedding
    escaped=$(echo "$line" | sed 's/\\/\\\\/g; s/"/\\"/g')
    batch="${batch}[\"${ts_ns}\",\"${escaped}\"],"
    count=$((count + 1))

    now=$(date +%s)
    elapsed=$((now - last_send))

    if [ "$count" -ge "$BATCH_SIZE" ] || [ "$elapsed" -ge "$BATCH_INTERVAL" ]; then
        send_batch
    fi
done

# Flush remaining
send_batch
