#!/usr/bin/env bash
# OneUptime health check script
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== OneUptime Health Check ==="

# Check if OneUptime UI is responding
if curl -sf "http://localhost/status" > /dev/null 2>&1; then
  pass "OneUptime UI responding at http://localhost"
elif curl -sf "http://localhost:3400/status" > /dev/null 2>&1; then
  pass "OneUptime UI responding at http://localhost:3400"
else
  fail "OneUptime UI not responding (try http://localhost or http://localhost:3400)"
fi

# Check OTLP endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:4318/v1/traces" \
  -X POST -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|401|404)$ ]]; then
  pass "OTLP HTTP endpoint responding at :4318 (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :4318 (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "OneUptime UI: http://localhost"
echo "OTLP gRPC:    localhost:4317"
echo "OTLP HTTP:    localhost:4318"
