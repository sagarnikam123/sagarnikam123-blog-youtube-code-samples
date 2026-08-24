#!/usr/bin/env bash
# VictoriaMetrics Full Stack health check script
set -euo pipefail

GRAFANA_PORT="${GRAFANA_PORT:-3000}"
VM_PORT="${VM_PORT:-8428}"
OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-4317}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== VictoriaMetrics Full Stack Health Check ==="

# Check all containers
for svc in vm-victoriametrics vm-victorialogs vm-victoriatraces vm-otel-collector vm-grafana; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  else
    fail "$svc is not healthy"
  fi
done

# Check VictoriaMetrics
if curl -sf "http://localhost:${VM_PORT}/health" > /dev/null 2>&1; then
  pass "VictoriaMetrics responding at :${VM_PORT}"
else
  fail "VictoriaMetrics not responding"
fi

# Check OTLP HTTP endpoint
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
echo "Grafana UI:         http://localhost:${GRAFANA_PORT} (anonymous admin)"
echo "VictoriaMetrics UI: http://localhost:${VM_PORT}/vmui"
echo "OTLP gRPC:          localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP:          localhost:${OTLP_HTTP_PORT}"
