#!/usr/bin/env bash
# Grafana LGTM Stack health check script
set -euo pipefail

GRAFANA_PORT="${GRAFANA_PORT:-3000}"
OTLP_GRPC_PORT="${OTLP_GRPC_PORT:-4317}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Grafana LGTM Stack Health Check ==="

# Check all containers
for svc in lgtm-mimir lgtm-loki lgtm-tempo lgtm-otel-collector lgtm-grafana; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  else
    fail "$svc is not healthy"
  fi
done

# Check Grafana datasources
DS_COUNT=$(curl -sf "http://localhost:${GRAFANA_PORT}/api/datasources" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [[ "$DS_COUNT" -ge 3 ]]; then
  pass "Grafana has ${DS_COUNT} datasources provisioned (Mimir, Loki, Tempo)"
else
  fail "Grafana datasources not provisioned (found ${DS_COUNT}, expected 3)"
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
echo "Grafana UI:  http://localhost:${GRAFANA_PORT} (anonymous admin)"
echo "OTLP gRPC:   localhost:${OTLP_GRPC_PORT}"
echo "OTLP HTTP:   localhost:${OTLP_HTTP_PORT}"
echo "Mimir:       http://localhost:9009 (internal)"
echo "Loki:        http://localhost:3100 (internal)"
echo "Tempo:       http://localhost:3200 (internal)"
