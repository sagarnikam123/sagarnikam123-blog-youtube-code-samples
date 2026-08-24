#!/usr/bin/env bash
# ClickStack health check script
set -euo pipefail

CLICKSTACK_UI_PORT="${CLICKSTACK_UI_PORT:-8123}"
HYPERDX_APP_PORT="${HYPERDX_APP_PORT:-8080}"
OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-4317}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== ClickStack Health Check ==="

# Check containers
for svc in clickstack-clickhouse clickstack-mongo clickstack-otel-collector clickstack-hyperdx; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  elif docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null | grep -q "running"; then
    pass "$svc is running"
  else
    fail "$svc is not running or unhealthy"
  fi
done

# Check ClickHouse
if curl -sf "http://localhost:${CLICKSTACK_UI_PORT}/ping" > /dev/null 2>&1; then
  pass "ClickHouse responding at :${CLICKSTACK_UI_PORT}"
else
  fail "ClickHouse not responding"
fi

# Check HyperDX UI
if curl -sf "http://localhost:${HYPERDX_APP_PORT}" > /dev/null 2>&1; then
  pass "HyperDX UI responding at :${HYPERDX_APP_PORT}"
else
  fail "HyperDX UI not responding"
fi

# Check OTel Collector health
if curl -sf "http://localhost:13133/" > /dev/null 2>&1; then
  pass "OTel Collector health check passing"
else
  fail "OTel Collector health check failing"
fi

# Check OTLP HTTP endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:${OTLP_HTTP_PORT}/v1/traces" \
  -X POST -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|405)$ ]]; then
  pass "OTLP HTTP endpoint responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "HyperDX UI:     http://localhost:${HYPERDX_APP_PORT}"
echo "ClickHouse:     http://localhost:${CLICKSTACK_UI_PORT}"
echo "OTLP gRPC:      localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP:      localhost:${OTLP_HTTP_PORT}"
