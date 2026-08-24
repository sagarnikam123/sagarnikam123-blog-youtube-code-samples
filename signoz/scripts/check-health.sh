#!/usr/bin/env bash
# SigNoz health check script
# Verifies all services are healthy and OTLP endpoint is accepting data

set -euo pipefail

OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-4317}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"
SIGNOZ_UI_PORT="${SIGNOZ_UI_PORT:-3301}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== SigNoz Health Check ==="

# Check containers are running
for svc in signoz-clickhouse-keeper signoz-clickhouse signoz-postgres signoz-otel-collector signoz-server; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  elif docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null | grep -q "running"; then
    pass "$svc is running (no healthcheck defined)"
  else
    fail "$svc is not running or unhealthy"
  fi
done

# Check schema-migrator completed
if docker inspect --format='{{.State.ExitCode}}' signoz-schema-migrator 2>/dev/null | grep -q "0"; then
  pass "schema-migrator completed successfully"
else
  fail "schema-migrator did not complete (exit code != 0)"
fi

# Check SigNoz UI
if curl -sf "http://localhost:${SIGNOZ_UI_PORT}/api/v1/health" > /dev/null 2>&1; then
  pass "SigNoz UI responding at http://localhost:${SIGNOZ_UI_PORT}"
else
  fail "SigNoz UI not responding at http://localhost:${SIGNOZ_UI_PORT}"
fi

# Check OTLP HTTP endpoint
if curl -sf "http://localhost:${OTLP_HTTP_PORT}/v1/traces" -X POST \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' > /dev/null 2>&1; then
  pass "OTLP HTTP endpoint accepting data at :${OTLP_HTTP_PORT}"
else
  # Some collectors return 400 for empty payload but that still means it's listening
  if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${OTLP_HTTP_PORT}/v1/traces" -X POST \
    -H "Content-Type: application/json" -d '{"resourceSpans":[]}' | grep -qE "200|400"; then
    pass "OTLP HTTP endpoint responding at :${OTLP_HTTP_PORT}"
  else
    fail "OTLP HTTP endpoint not responding at :${OTLP_HTTP_PORT}"
  fi
fi

echo ""
echo "=== All checks passed ==="
echo "SigNoz UI: http://localhost:${SIGNOZ_UI_PORT}"
echo "OTLP gRPC: localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP: localhost:${OTLP_HTTP_PORT}"
