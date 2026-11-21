#!/usr/bin/env bash
# Highlight.io health check script
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Highlight.io Health Check ==="

# Check key containers
for svc in clickhouse kafka postgres redis; do
  if docker ps --format '{{.Names}}' | grep -q "$svc"; then
    pass "$svc container is running"
  else
    fail "$svc container not found"
  fi
done

# Check OTLP HTTP endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:4318/v1/traces" \
  -X POST -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|405)$ ]]; then
  pass "OTLP HTTP endpoint responding at :4318 (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :4318 (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "Highlight UI:  http://localhost:3000 (or :8080)"
echo "OTLP gRPC:     localhost:4317"
echo "OTLP HTTP:     localhost:4318"
