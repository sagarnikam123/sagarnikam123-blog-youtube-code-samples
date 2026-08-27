# Loki Ruler Alerting - Full Stack Evaluation

End-to-end evaluation of Loki's **datasource-managed alerts** (ruler component).

## Architecture

```
fuzzy-train (logs) → push-logs.sh → Loki Push API
                                         ↓
                                    Loki Ruler (evaluates LogQL alert rules every 30s)
                                         ↓
                                    Alertmanager (routes & deduplicates)
                                         ↓
                                    webhook-receiver (prints to docker logs)
```

## Quick Start

```bash
docker compose up -d
```

## Watch Alerts Fire

```bash
# See alerts being received
docker compose logs -f webhook-receiver

# See generated logs
docker compose logs -f log-generator

# Check loaded rules
curl -s http://localhost:3100/loki/api/v1/rules | jq .

# Check Alertmanager alerts
curl -s http://localhost:9093/api/v2/alerts | jq .
```

## Access Points

| Service | URL |
|---------|-----|
| Loki UI | http://localhost:3100 |
| Loki Rules API | http://localhost:3100/loki/api/v1/rules |
| Alertmanager UI | http://localhost:9093 |
| Grafana | http://localhost:3000 |

## Log Generation Options

### Option 1: Direct Push (default)

fuzzy-train generates JSON logs, `push-logs.sh` batches and POSTs to `/loki/api/v1/push`. Zero extra dependencies.

### Option 2: OTLP

Loki 3.7 accepts OpenTelemetry logs natively. Send to `http://localhost:3100/otlp/v1/logs`:

```bash
curl -X POST http://localhost:3100/otlp/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "resourceLogs": [{
      "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "my-app"}}]},
      "scopeLogs": [{
        "logRecords": [{
          "timeUnixNano": "'$(date +%s)000000000'",
          "severityText": "ERROR",
          "body": {"stringValue": "Something went wrong"}
        }]
      }]
    }]
  }'
```

The Loki config maps `service.name` → index label via `otlp_config.resource_attributes`.

### Option 3: Fluent-bit

Add a fluent-bit service to the compose:

```yaml
fluent-bit:
  image: fluent/fluent-bit:3.2
  volumes:
    - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro
  depends_on:
    loki:
      condition: service_healthy
```

With config:
```ini
[INPUT]
    Name   dummy
    Tag    test
    Rate   5

[OUTPUT]
    Name   loki
    Match  *
    Host   loki
    Port   3100
    Labels job=fluent-bit
```

## Alert Rules

Rules are mounted from `loki/observability/alerts/rules/fake/error-alerts.yaml`:

- **HighErrorRate** — >0.5 errors/sec sustained 2min
- **CriticalErrorSpike** — >5 errors/sec sustained 1min
- **OOMDetected** — any OOM pattern in logs
- **ConnectionErrors** — connection refused/timeout patterns
- **PanicOrFatal** — panic or fatal in logs
- **HTTP5xxElevated** — HTTP 5xx patterns >0.5/sec

## Troubleshooting

```bash
# Check Loki is ready
curl http://localhost:3100/ready

# Check ruler ring
curl http://localhost:3100/ruler/ring

# Check rules are loaded
curl http://localhost:3100/loki/api/v1/rules

# View Loki logs for ruler evaluation
docker compose logs loki 2>&1 | grep -i ruler
```

## Cleanup

```bash
docker compose down -v
```
