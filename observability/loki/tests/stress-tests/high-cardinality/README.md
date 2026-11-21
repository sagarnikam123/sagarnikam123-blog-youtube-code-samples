# High Cardinality Stress Test

Test Loki's behavior under high label cardinality conditions.

## What is High Cardinality?

High cardinality occurs when labels have many unique values:
- `user_id` with millions of unique users
- `request_id` with unique IDs per request
- `trace_id` with unique IDs per trace

**Impact on Loki:**
- Each unique label combination creates a new stream
- Streams consume memory in ingesters
- Too many streams can cause OOM or rate limiting

## Loki Limits

| Limit | Default | Config |
|-------|---------|--------|
| Max streams per user (local) | 0 (disabled) | `max_streams_per_user` |
| Max streams per user (global) | 5000 | `max_global_streams_per_user` |
| Max label name length | 1024 | `max_label_name_length` |
| Max label value length | 2048 | `max_label_value_length` |
| Max labels per series | 15 | `max_label_names_per_series` |

## Test Scenarios

### 1. Gradual Cardinality Increase

```bash
./cardinality-ramp.sh
```

Gradually increases unique label values to find the breaking point.

### 2. Cardinality Bomb

```bash
./cardinality-bomb.sh
```

Immediately pushes logs with high cardinality to test rate limiting.

### 3. Label Value Length Test

```bash
./long-labels.sh
```

Tests behavior with very long label values.

## Scripts

### cardinality-bomb.sh

```bash
#!/bin/bash
# Push logs with high cardinality labels

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
STREAMS="${STREAMS:-10000}"

echo "Cardinality Bomb Test"
echo "Pushing $STREAMS unique streams to $LOKI_URL"

for i in $(seq 1 $STREAMS); do
  ts=$(date +%s%N)

  curl -s -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    -d '{
      "streams": [{
        "stream": {
          "job": "cardinality-test",
          "user_id": "user-'"$i"'",
          "request_id": "req-'"$RANDOM"'-'"$i"'"
        },
        "values": [["'"$ts"'", "High cardinality log entry '"$i"'"]]
      }]
    }' &

  # Batch requests
  if [ $((i % 100)) -eq 0 ]; then
    wait
    echo "Pushed $i streams..."
  fi
done

wait
echo "Done. Check Loki metrics for stream count."
```

### cardinality-ramp.sh

```bash
#!/bin/bash
# Gradually increase cardinality

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
MAX_STREAMS="${MAX_STREAMS:-50000}"
STEP="${STEP:-1000}"
DELAY="${DELAY:-5}"

echo "Cardinality Ramp Test"
echo "Ramping up to $MAX_STREAMS streams"

current=0
while [ $current -lt $MAX_STREAMS ]; do
  # Push batch of new streams
  for i in $(seq 1 $STEP); do
    stream_id=$((current + i))
    ts=$(date +%s%N)

    curl -s -X POST "$LOKI_URL/loki/api/v1/push" \
      -H "Content-Type: application/json" \
      -d '{
        "streams": [{
          "stream": {
            "job": "cardinality-ramp",
            "stream_id": "stream-'"$stream_id"'"
          },
          "values": [["'"$ts"'", "Stream '"$stream_id"' log"]]
        }]
      }' &
  done

  wait
  current=$((current + STEP))

  # Check metrics
  active_streams=$(curl -s "$LOKI_URL/metrics" | grep 'loki_ingester_memory_streams{' | awk '{print $2}')
  echo "Pushed $current streams, Active in ingester: $active_streams"

  sleep $DELAY
done

echo "Ramp complete"
```

## Monitoring

```bash
# Watch stream count
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_ingester_memory_streams'

# Watch for rate limiting
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_discarded_samples_total'

# Watch memory usage
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_ingester_memory_chunks'
```

## Expected Behavior

1. **Below limit**: All logs accepted
2. **At limit**: New streams rejected with 429
3. **Above limit**: Rate limiting kicks in, logs dropped

## Error Messages

```
# Stream limit reached
"max streams limit exceeded"

# Rate limit reached
"ingestion rate limit exceeded"
```

## Cleanup

After testing, streams will naturally expire based on `chunk_idle_period` (default 30m).

To force cleanup:
```bash
# Restart Loki (clears in-memory streams)
# Or wait for chunk_idle_period
```
