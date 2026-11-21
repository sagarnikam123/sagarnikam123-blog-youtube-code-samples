# Health Check Script Examples

This document provides practical examples of using the `test-health.sh` script in various scenarios.

## Basic Examples

### Check Health in Default Namespace

```bash
./test-health.sh
```

**Output:**
```
========================================
SkyWalking Full Cluster Health Validation
========================================

▶ OAP Server Health Checks
─────────────────────────────────────────────────────────────────
✓ PASS: OAP_Server - Pod_Status: All 3 pods running
✓ PASS: OAP_Server - Readiness_Probes: All 3 pods ready

...

✓ All critical health checks PASSED
SkyWalking cluster is HEALTHY
```

### Check Health in Custom Namespace

```bash
./test-health.sh --namespace my-skywalking
```

### Get JSON Output

```bash
./test-health.sh --output json
```

**Output:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "namespace": "skywalking",
  "summary": {
    "total_checks": 25,
    "passed": 23,
    "failed": 0,
    "warnings": 2,
    "status": "HEALTHY"
  },
  "checks": [...]
}
```

### Get YAML Output

```bash
./test-health.sh --output yaml
```

## Advanced Examples

### Save Health Report to File

```bash
# Text format
./test-health.sh > health-report-$(date +%Y%m%d-%H%M%S).txt

# JSON format
./test-health.sh --output json > health-report.json

# YAML format
./test-health.sh --output yaml > health-report.yaml
```

### Check Health and Parse Results

```bash
# Get overall status
./test-health.sh --output json | jq -r '.summary.status'

# Get failed checks count
./test-health.sh --output json | jq -r '.summary.failed'

# List all failed checks
./test-health.sh --output json | jq -r '.checks[] | select(.status=="FAIL") | "\(.component) - \(.check): \(.message)"'

# Get specific component status
./test-health.sh --output json | jq -r '.checks[] | select(.component=="OAP_Server")'
```

### Conditional Execution Based on Health

```bash
#!/bin/bash

if ./test-health.sh --output json | jq -e '.summary.failed == 0' > /dev/null; then
  echo "Cluster is healthy, proceeding with deployment"
  # Continue with deployment
else
  echo "Cluster is unhealthy, aborting"
  exit 1
fi
```

### Monitor Health Continuously

```bash
#!/bin/bash

while true; do
  clear
  echo "=== SkyWalking Health Check - $(date) ==="
  ./test-health.sh
  sleep 60
done
```

## Integration Examples

### GitHub Actions Workflow

```yaml
name: SkyWalking Health Check

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBECONFIG }}

      - name: Run Health Check
        id: health
        run: |
          cd skywalking/scripts
          ./test-health.sh --output json > health-report.json
          cat health-report.json

      - name: Check Status
        run: |
          STATUS=$(jq -r '.summary.status' health-report.json)
          if [ "$STATUS" != "HEALTHY" ]; then
            echo "::error::SkyWalking cluster is unhealthy"
            exit 1
          fi

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: health-report
          path: health-report.json

      - name: Send Notification on Failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'SkyWalking health check failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### GitLab CI Pipeline

```yaml
health_check:
  stage: test
  script:
    - cd skywalking/scripts
    - ./test-health.sh --output json > health-report.json
    - |
      STATUS=$(jq -r '.summary.status' health-report.json)
      if [ "$STATUS" != "HEALTHY" ]; then
        echo "Cluster is unhealthy"
        exit 1
      fi
  artifacts:
    reports:
      junit: health-report.json
    paths:
      - health-report.json
    expire_in: 7 days
  only:
    - schedules
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: skywalking-health-check
  namespace: skywalking
spec:
  schedule: "*/10 * * * *"  # Every 10 minutes
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: skywalking-health-checker
          containers:
          - name: health-check
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              # Download script
              curl -sL https://raw.githubusercontent.com/your-repo/skywalking/scripts/test-health.sh -o /tmp/test-health.sh
              chmod +x /tmp/test-health.sh

              # Run health check
              /tmp/test-health.sh --namespace skywalking --output json > /tmp/health.json

              # Send to monitoring system
              curl -X POST http://monitoring-api/health \
                -H "Content-Type: application/json" \
                -d @/tmp/health.json
          restartPolicy: OnFailure
```

### Prometheus Exporter Pattern

```bash
#!/bin/bash
# health-exporter.sh

METRICS_FILE="/var/lib/prometheus/node-exporter/skywalking-health.prom"

while true; do
  # Run health check
  RESULT=$(./test-health.sh --output json)

  # Extract metrics
  TOTAL=$(echo "$RESULT" | jq -r '.summary.total_checks')
  PASSED=$(echo "$RESULT" | jq -r '.summary.passed')
  FAILED=$(echo "$RESULT" | jq -r '.summary.failed')
  WARNINGS=$(echo "$RESULT" | jq -r '.summary.warnings')
  STATUS=$(echo "$RESULT" | jq -r '.summary.status')

  # Convert status to numeric (1=HEALTHY, 0=UNHEALTHY)
  STATUS_NUM=0
  [ "$STATUS" = "HEALTHY" ] && STATUS_NUM=1

  # Write Prometheus metrics
  cat > "$METRICS_FILE" <<EOF
# HELP skywalking_health_checks_total Total number of health checks
# TYPE skywalking_health_checks_total gauge
skywalking_health_checks_total $TOTAL

# HELP skywalking_health_checks_passed Number of passed health checks
# TYPE skywalking_health_checks_passed gauge
skywalking_health_checks_passed $PASSED

# HELP skywalking_health_checks_failed Number of failed health checks
# TYPE skywalking_health_checks_failed gauge
skywalking_health_checks_failed $FAILED

# HELP skywalking_health_checks_warnings Number of warning health checks
# TYPE skywalking_health_checks_warnings gauge
skywalking_health_checks_warnings $WARNINGS

# HELP skywalking_health_status Overall health status (1=HEALTHY, 0=UNHEALTHY)
# TYPE skywalking_health_status gauge
skywalking_health_status $STATUS_NUM
EOF

  sleep 60
done
```

### Slack Notification Script

```bash
#!/bin/bash
# health-check-notify.sh

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Run health check
RESULT=$(./test-health.sh --output json)
STATUS=$(echo "$RESULT" | jq -r '.summary.status')
FAILED=$(echo "$RESULT" | jq -r '.summary.failed')

if [ "$STATUS" != "HEALTHY" ]; then
  # Get failed checks
  FAILED_CHECKS=$(echo "$RESULT" | jq -r '.checks[] | select(.status=="FAIL") | "• \(.component) - \(.check): \(.message)"' | head -5)

  # Send Slack notification
  curl -X POST "$SLACK_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d @- <<EOF
{
  "text": "⚠️ SkyWalking Health Check Failed",
  "attachments": [
    {
      "color": "danger",
      "fields": [
        {
          "title": "Status",
          "value": "$STATUS",
          "short": true
        },
        {
          "title": "Failed Checks",
          "value": "$FAILED",
          "short": true
        },
        {
          "title": "Failed Components",
          "value": "$FAILED_CHECKS"
        }
      ]
    }
  ]
}
EOF
fi
```

### Email Alert Script

```bash
#!/bin/bash
# health-check-email.sh

EMAIL_TO="ops-team@example.com"
EMAIL_FROM="skywalking-monitor@example.com"

# Run health check
RESULT=$(./test-health.sh --output json)
STATUS=$(echo "$RESULT" | jq -r '.summary.status')

if [ "$STATUS" != "HEALTHY" ]; then
  FAILED=$(echo "$RESULT" | jq -r '.summary.failed')
  FAILED_CHECKS=$(echo "$RESULT" | jq -r '.checks[] | select(.status=="FAIL") | "\(.component) - \(.check): \(.message)"')

  # Send email
  mail -s "SkyWalking Health Check Failed" \
       -r "$EMAIL_FROM" \
       "$EMAIL_TO" <<EOF
SkyWalking cluster health check has failed.

Status: $STATUS
Failed Checks: $FAILED

Failed Components:
$FAILED_CHECKS

Please investigate immediately.

Timestamp: $(date)
Namespace: skywalking
EOF
fi
```

## Troubleshooting Examples

### Debug Specific Component

```bash
# Check only OAP Server health
./test-health.sh --output json | jq '.checks[] | select(.component=="OAP_Server")'

# Check only BanyanDB health
./test-health.sh --output json | jq '.checks[] | select(.component | startswith("BanyanDB"))'

# Check only API responsiveness
./test-health.sh --output json | jq '.checks[] | select(.component | endswith("_API"))'
```

### Compare Health Over Time

```bash
#!/bin/bash
# health-compare.sh

# Take baseline
./test-health.sh --output json > health-baseline.json

# Wait some time
sleep 300

# Take current snapshot
./test-health.sh --output json > health-current.json

# Compare
echo "Baseline:"
jq '.summary' health-baseline.json

echo -e "\nCurrent:"
jq '.summary' health-current.json

# Show differences
echo -e "\nNew failures:"
comm -13 \
  <(jq -r '.checks[] | select(.status=="FAIL") | .check' health-baseline.json | sort) \
  <(jq -r '.checks[] | select(.status=="FAIL") | .check' health-current.json | sort)
```

### Health Check with Retry

```bash
#!/bin/bash
# health-check-retry.sh

MAX_RETRIES=3
RETRY_DELAY=30

for i in $(seq 1 $MAX_RETRIES); do
  echo "Attempt $i of $MAX_RETRIES"

  if ./test-health.sh; then
    echo "Health check passed"
    exit 0
  else
    echo "Health check failed"

    if [ $i -lt $MAX_RETRIES ]; then
      echo "Retrying in ${RETRY_DELAY}s..."
      sleep $RETRY_DELAY
    fi
  fi
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1
```

## Performance Testing Examples

### Measure Health Check Duration

```bash
#!/bin/bash

START=$(date +%s)
./test-health.sh > /dev/null
END=$(date +%s)
DURATION=$((END - START))

echo "Health check completed in ${DURATION}s"

if [ $DURATION -gt 120 ]; then
  echo "WARNING: Health check took longer than expected"
fi
```

### Parallel Health Checks

```bash
#!/bin/bash
# Check multiple namespaces in parallel

NAMESPACES=("skywalking-dev" "skywalking-staging" "skywalking-prod")

for ns in "${NAMESPACES[@]}"; do
  (
    echo "Checking $ns..."
    ./test-health.sh --namespace "$ns" --output json > "health-${ns}.json"

    STATUS=$(jq -r '.summary.status' "health-${ns}.json")
    echo "$ns: $STATUS"
  ) &
done

wait
echo "All health checks completed"
```

## Best Practices

1. **Always save health check results for historical analysis**
2. **Use JSON output for automation and parsing**
3. **Set up regular health checks (every 5-10 minutes)**
4. **Alert on failures immediately**
5. **Compare health over time to detect degradation**
6. **Include health checks in deployment pipelines**
7. **Document expected health check results**
8. **Test health checks in non-production first**

## Related Documentation

- [Health Validation Guide](./HEALTH-VALIDATION-GUIDE.md)
- [Scripts README](./README.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
