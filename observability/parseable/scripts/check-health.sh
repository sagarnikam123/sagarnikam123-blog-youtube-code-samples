#!/usr/bin/env bash
# Parseable health check script
set -euo pipefail

PARSEABLE_PORT="${PARSEABLE_PORT:-8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Parseable Health Check ==="

# Check container
if docker inspect --format='{{.State.Health.Status}}' parseable 2>/dev/null | grep -q "healthy"; then
  pass "parseable container is healthy"
elif docker inspect --format='{{.State.Status}}' parseable 2>/dev/null | grep -q "running"; then
  pass "parseable container is running"
else
  fail "parseable container not running or unhealthy"
fi

# Check liveness endpoint
if curl -sf "http://localhost:${PARSEABLE_PORT}/api/v1/liveness" > /dev/null 2>&1; then
  pass "Parseable liveness OK at :${PARSEABLE_PORT}"
else
  fail "Parseable liveness check failed"
fi

# Check OTLP traces endpoint (send empty payload)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "admin:admin" \
  -H "Content-Type: application/json" \
  -H "X-P-Stream: benchmark-traces" \
  "http://localhost:${PARSEABLE_PORT}/v1/traces" \
  -X POST -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|404)$ ]]; then
  pass "OTLP traces endpoint responding at :${PARSEABLE_PORT} (HTTP ${HTTP_CODE})"
else
  fail "OTLP traces endpoint not responding at :${PARSEABLE_PORT} (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "Parseable UI:   http://localhost:${PARSEABLE_PORT}"
echo "OTLP HTTP:      http://localhost:${PARSEABLE_PORT}/v1/{logs,metrics,traces}"
echo "Login:          admin / admin"
