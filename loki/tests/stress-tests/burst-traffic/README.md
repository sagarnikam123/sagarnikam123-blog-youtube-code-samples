# Burst Traffic Stress Test

Test Loki's behavior under sudden traffic spikes.

## What is Burst Traffic?

Burst traffic simulates sudden spikes in log volume:
- Application errors causing log floods
- Deployment events
- Traffic spikes during peak hours
- Incident response logging

**Impact on Loki:**
- Ingester buffer overflow
- Rate limiting activation
- Increased latency
- Potential log drops

## Loki Limits

| Limit | Default | Config |
|-------|---------|--------|
| Ingestion rate | 4 MB/s | `ingestion_rate_mb` |
| Ingestion burst | 6 MB | `ingestion_burst_size_mb` |
| Per-stream rate | 3 MB/s | `per_stream_rate_limit` |
| Per-stream burst | 15 MB | `per_stream_rate_limit_burst` |

## Test Scenarios

### 1. Sustained Burst

```bash
./burst-test.sh
```

Push logs at maximum rate for a sustained period.

### 2. Spike Test

```bash
./spike-test.sh
```

Alternate between normal and burst traffic.

### 3. Multi-Stream Burst

```bash
./multi-stream-burst.sh
```

Burst across multiple streams simultaneously.

## Scripts

### burst-test.sh

```bash
#!/bin/bash
# Sustained burst test

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
DURATION="${DURATION:-60}"
BATCH_SIZE="${BATCH_SIZE:-1000}"

echo "Burst Traffic Test"
echo "Pushing maximum rate for ${DURATION}s"

end_time=$(($(date +%s) + DURATION))
total=0

while [ $(date +%s) -lt $end_time ]; do
  # Build large batch
  values=""
  for i in $(seq 1 $BATCH_SIZE); do
    ts=$(date +%s%N)
    if [ -n "$values" ]; then
      values="$values,"
    fi
    values="$values[\"$ts\", \"Burst log entry $total-$i with some padding to increase size: $(head -c 100 /dev/urandom | base64)\"]"
  done

  # Push as fast as possible
  curl -s -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    -d '{
      "streams": [{
        "stream": {"job": "burst-test"},
        "values": ['"$values"']
      }]
    }' &

  total=$((total + BATCH_SIZE))

  # Limit concurrent requests
  if [ $((total % 10000)) -eq 0 ]; then
    wait
    echo "Pushed $total logs..."
  fi
done

wait
echo "Total logs pushed: $total"
```

## Monitoring

```bash
# Watch ingestion rate
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_distributor_bytes_received_total'

# Watch for rate limiting
watch -n1 'curl -s http://localhost:3100/metrics | grep -E "(discarded|rate_limit)"'

# Watch latency
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_request_duration_seconds'
```

## Expected Behavior

1. **Within burst limit**: All logs accepted
2. **Exceeding burst**: Rate limiting (429 responses)
3. **Sustained overload**: Logs dropped, backpressure

## Error Messages

```
# Rate limit exceeded
"ingestion rate limit exceeded"

# Per-stream rate limit
"per-stream rate limit exceeded"
```

## Recovery

After burst:
1. Rate limiting should ease
2. Backlog should clear
3. Normal operation resumes

Monitor recovery time as a key metric.
