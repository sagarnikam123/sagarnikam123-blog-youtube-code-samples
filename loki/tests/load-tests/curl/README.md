# curl - Direct Loki API Testing

Use curl for direct HTTP API testing against Loki.

## Loki Push API

### Push Single Log Entry

```bash
curl -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {
          "job": "curl-test",
          "level": "info"
        },
        "values": [
          ["'"$(date +%s)"'000000000", "Hello from curl!"]
        ]
      }
    ]
  }'
```

### Push Multiple Log Entries

```bash
curl -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {
          "job": "curl-test",
          "level": "info"
        },
        "values": [
          ["'"$(date +%s)"'000000001", "Log line 1"],
          ["'"$(date +%s)"'000000002", "Log line 2"],
          ["'"$(date +%s)"'000000003", "Log line 3"]
        ]
      }
    ]
  }'
```

### Push with Multi-Tenant

```bash
curl -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -H "X-Scope-OrgID: tenant-1" \
  -d '{
    "streams": [
      {
        "stream": {
          "job": "curl-test"
        },
        "values": [
          ["'"$(date +%s)"'000000000", "Tenant 1 log"]
        ]
      }
    ]
  }'
```

### Push JSON Log Line

```bash
curl -X POST "http://localhost:3100/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {
          "job": "curl-test",
          "format": "json"
        },
        "values": [
          ["'"$(date +%s)"'000000000", "{\"level\":\"error\",\"msg\":\"Something failed\",\"code\":500}"]
        ]
      }
    ]
  }'
```

## Loki Query API

### Query Logs

```bash
# Basic query
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="curl-test"}' \
  --data-urlencode 'limit=10'

# With time range
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="curl-test"}' \
  --data-urlencode 'start='$(date -v-1H +%s)'000000000' \
  --data-urlencode 'end='$(date +%s)'000000000' \
  --data-urlencode 'limit=100'

# With filter
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="curl-test"} |= "error"' \
  --data-urlencode 'limit=10'
```

### Instant Query

```bash
curl -G "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query=count_over_time({job="curl-test"}[1h])'
```

### List Labels

```bash
# All labels
curl "http://localhost:3100/loki/api/v1/labels"

# Label values
curl "http://localhost:3100/loki/api/v1/label/job/values"
```

### List Series

```bash
curl -G "http://localhost:3100/loki/api/v1/series" \
  --data-urlencode 'match[]={job="curl-test"}'
```

## Health & Status APIs

```bash
# Ready check
curl "http://localhost:3100/ready"

# Metrics
curl "http://localhost:3100/metrics"

# Ring status
curl "http://localhost:3100/ring"

# Config
curl "http://localhost:3100/config"

# Build info
curl "http://localhost:3100/loki/api/v1/status/buildinfo"
```

## Load Testing Scripts

### push-logs.sh

```bash
#!/bin/bash
# push-logs.sh - Push logs to Loki in a loop

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
JOB="${JOB:-curl-load-test}"
RATE="${RATE:-10}"  # logs per second
DURATION="${DURATION:-60}"  # seconds

echo "Pushing logs to $LOKI_URL"
echo "Job: $JOB, Rate: $RATE/s, Duration: ${DURATION}s"

end_time=$(($(date +%s) + DURATION))
count=0

while [ $(date +%s) -lt $end_time ]; do
  ts=$(date +%s%N)

  curl -s -X POST "$LOKI_URL/loki/api/v1/push" \
    -H "Content-Type: application/json" \
    -d '{
      "streams": [{
        "stream": {"job": "'"$JOB"'", "level": "info"},
        "values": [["'"$ts"'", "Log entry '"$count"' at '"$(date -Iseconds)"'"]]
      }]
    }' > /dev/null

  count=$((count + 1))
  sleep $(echo "scale=3; 1/$RATE" | bc)
done

echo "Pushed $count logs"
```

### burst-push.sh

```bash
#!/bin/bash
# burst-push.sh - Push burst of logs

LOKI_URL="${LOKI_URL:-http://localhost:3100}"
COUNT="${COUNT:-1000}"

echo "Pushing $COUNT logs to $LOKI_URL"

# Build batch of logs
values=""
for i in $(seq 1 $COUNT); do
  ts=$(date +%s%N)
  if [ -n "$values" ]; then
    values="$values,"
  fi
  values="$values[\"$ts\", \"Burst log entry $i\"]"
done

curl -X POST "$LOKI_URL/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [{
      "stream": {"job": "burst-test"},
      "values": ['"$values"']
    }]
  }'

echo "Done"
```

## Response Codes

| Code | Meaning |
|------|---------|
| 204 | Push successful |
| 400 | Bad request (invalid JSON, labels) |
| 429 | Rate limited |
| 500 | Internal server error |

## Troubleshooting

```bash
# Verbose output
curl -v -X POST "http://localhost:3100/loki/api/v1/push" ...

# Check response body on error
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST ...

# Test with jq
curl -s "http://localhost:3100/loki/api/v1/query_range?query={job=\"test\"}&limit=1" | jq .
```
