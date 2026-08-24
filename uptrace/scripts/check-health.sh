#!/usr/bin/env bash
# Uptrace health check script
set -euo pipefail

UPTRACE_UI_PORT="${UPTRACE_UI_PORT:-14318}"
OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-4317}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Uptrace Health Check ==="

# Check containers
for svc in uptrace-clickhouse uptrace-postgres uptrace-redis uptrace-server uptrace-otel-collector; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  elif docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null | grep -q "running"; then
    pass "$svc is running"
  else
    fail "$svc is not running or unhealthy"
  fi
done

# Check Uptrace UI
if curl -sf "http://localhost:${UPTRACE_UI_PORT}/api/v1/health" > /dev/null 2>&1; then
  pass "Uptrace UI responding at http://localhost:${UPTRACE_UI_PORT}"
else
  fail "Uptrace UI not responding"
fi

# Check OTLP HTTP via collector
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:${OTLP_HTTP_PORT}/v1/traces" \
  -X POST -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400)$ ]]; then
  pass "OTLP HTTP endpoint responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "Uptrace UI:  http://localhost:${UPTRACE_UI_PORT}"
echo "OTLP gRPC:   localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP:   localhost:${OTLP_HTTP_PORT}"
echo "Login:       admin@uptrace.local / admin"
echo "DSN:         http://project1_secret@localhost:${UPTRACE_UI_PORT}?grpc=${OTLP_GRPC_PORT}"
