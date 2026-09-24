#!/usr/bin/env bash
# Uptime Kuma health check script
set -euo pipefail

UPTIME_KUMA_PORT="${UPTIME_KUMA_PORT:-3001}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Uptime Kuma Health Check ==="

# Container health (only when run via Docker/Compose)
if docker inspect --format='{{.State.Health.Status}}' uptime-kuma 2>/dev/null | grep -q "healthy"; then
  pass "uptime-kuma container is healthy"
fi

# UI / API endpoint. /api/entry-page returns 200 once the server is up.
if curl -sf "http://localhost:${UPTIME_KUMA_PORT}/api/entry-page" > /dev/null 2>&1; then
  pass "Uptime Kuma responding at http://localhost:${UPTIME_KUMA_PORT}"
elif curl -sf "http://localhost:${UPTIME_KUMA_PORT}" > /dev/null 2>&1; then
  pass "Uptime Kuma responding at http://localhost:${UPTIME_KUMA_PORT}"
else
  fail "Uptime Kuma not responding at http://localhost:${UPTIME_KUMA_PORT}"
fi

echo ""
echo "=== All checks passed ==="
echo "Uptime Kuma UI: http://localhost:${UPTIME_KUMA_PORT}"
