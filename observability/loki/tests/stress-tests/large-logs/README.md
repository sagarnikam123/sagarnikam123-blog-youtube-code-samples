# Large Log Lines Stress Test

Test Loki's behavior with large log lines near the size limit.

## What are Large Logs?

Large log lines can occur from:
- Stack traces with deep call stacks
- JSON payloads with nested objects
- Base64 encoded data
- Debug dumps

**Impact on Loki:**
- Memory pressure on ingesters
- Slower chunk compression
- Potential truncation or rejection

## Loki Limits

| Limit | Default | Config |
|-------|---------|--------|
| Max line size | 256 KB | `max_line_size` |
| Truncate large lines | false | `max_line_size_truncate` |

## Behavior

- **max_line_size_truncate: false** (default): Lines exceeding limit are rejected
- **max_line_size_truncate: true**: Lines are truncated to max_line_size

## Test Scenarios

### 1. Near-Limit Lines

```bash
./large-line-test.sh
```

Push logs just under the 256KB limit.

### 2. Over-Limit Lines

```bash
./over-limit-test.sh
```

Push logs exceeding the limit to test rejection/truncation.

### 3. Mixed Size Test

```bash
./mixed-size-test.sh
```

Mix of normal and large logs.

## Scripts

### large-line-test.sh

```bash
#!/bin/bash
# Push logs near the size limit

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
LINE_SIZE="${LINE_SIZE:-250000}"  # ~250KB, just under 256KB limit
COUNT="${COUNT:-100}"

echo "Large Log Line Test"
echo "Line size: $LINE_SIZE bytes"
echo "Count: $COUNT"

# Generate large payload
PAYLOAD=$(head -c $LINE_SIZE /dev/urandom | base64 | tr -d '\n' | head -c $LINE_SIZE)

for i in $(seq 1 $COUNT); do
  ts=$(date +%s%N)

  response=$(curl -s -w "%{http_code}" -o /dev/null \
    -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    -d '{
      "streams": [{
        "stream": {"job": "large-log-test"},
        "values": [["'"$ts"'", "'"$PAYLOAD"'"]]
      }]
    }')

  echo "Log $i: HTTP $response (${LINE_SIZE} bytes)"
done
```

## Monitoring

```bash
# Watch for rejected lines
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_discarded_samples_total'

# Watch chunk sizes
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_ingester_chunk'

# Watch memory
watch -n1 'curl -s http://localhost:3100/metrics | grep loki_ingester_memory'
```

## Expected Behavior

### With max_line_size_truncate: false
- Lines > 256KB: Rejected with error
- Lines ≤ 256KB: Accepted

### With max_line_size_truncate: true
- Lines > 256KB: Truncated to 256KB, accepted
- Lines ≤ 256KB: Accepted as-is

## Error Messages

```
# Line too long (truncate disabled)
"max line size exceeded"

# With truncate enabled
# No error, but line is silently truncated
```

## Configuration

To enable truncation:
```yaml
limits_config:
  max_line_size: 256KB
  max_line_size_truncate: true
```

## Recommendations

1. **Set appropriate max_line_size** for your use case
2. **Enable truncation** if you prefer partial logs over rejection
3. **Monitor discarded samples** to detect issues
4. **Consider structured logging** to avoid large single lines
