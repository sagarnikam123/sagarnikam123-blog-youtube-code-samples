#!/usr/bin/env bash
# OpenObserve health check script
set -euo pipefail

OPENOBSERVE_UI_PORT="${OPENOBSERVE_UI_PORT:-5080}"
OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-5081}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-5082}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== OpenObserve Health Check ==="

# Check container health
if docker inspect --format='{{.State.Health.Status}}' openobserve 2>/dev/null | grep -q "healthy"; then
  pass "openobserve container is healthy"
else
  fail "openobserve container is not healthy"
fi

# Check UI endpoint
if curl -sf "http://localhost:${OPENOBSERVE_UI_PORT}/healthz" > /dev/null 2>&1; then
  pass "OpenObserve UI responding at http://localhost:${OPENOBSERVE_UI_PORT}"
else
  fail "OpenObserve UI not responding"
fi

# Check OTLP HTTP endpoint (send empty traces payload)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "root@example.com:Complexpass#123" \
  -H "Content-Type: application/json" \
  "http://localhost:${OTLP_HTTP_PORT}/v1/traces" \
  -X POST -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|401)$ ]]; then
  pass "OTLP HTTP endpoint responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "OpenObserve UI: http://localhost:${OPENOBSERVE_UI_PORT}"
echo "OTLP gRPC:      localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP:      localhost:${OTLP_HTTP_PORT}"
echo "Login:          root@example.com / Complexpass#123"
