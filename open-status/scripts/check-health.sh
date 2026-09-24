#!/usr/bin/env bash
# OpenStatus health check script
set -euo pipefail

DASHBOARD_PORT="${DASHBOARD_PORT:-3002}"
STATUS_PAGE_PORT="${STATUS_PAGE_PORT:-3003}"
SERVER_PORT="${SERVER_PORT:-3001}"
INGEST_PORT="${INGEST_PORT:-8081}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== OpenStatus Health Check ==="

# Dashboard
if curl -sf "http://localhost:${DASHBOARD_PORT}" > /dev/null 2>&1; then
  pass "Dashboard responding at http://localhost:${DASHBOARD_PORT}"
else
  fail "Dashboard not responding at http://localhost:${DASHBOARD_PORT}"
fi

# Status pages
if curl -sf "http://localhost:${STATUS_PAGE_PORT}" > /dev/null 2>&1; then
  pass "Status pages responding at http://localhost:${STATUS_PAGE_PORT}"
else
  fail "Status pages not responding at http://localhost:${STATUS_PAGE_PORT}"
fi

# API server (any HTTP response means it's up)
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${SERVER_PORT}" 2>/dev/null || echo "000")
if [[ "$API_CODE" =~ ^(200|301|302|400|401|404)$ ]]; then
  pass "API server responding at http://localhost:${SERVER_PORT} (HTTP ${API_CODE})"
else
  fail "API server not responding at http://localhost:${SERVER_PORT} (HTTP ${API_CODE})"
fi

# Private-location ingest (optional in status-page-only mode)
INGEST_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${INGEST_PORT}" 2>/dev/null || echo "000")
if [[ "$INGEST_CODE" =~ ^(200|400|401|404)$ ]]; then
  pass "Private-location ingest responding at :${INGEST_PORT} (HTTP ${INGEST_CODE})"
else
  echo "[INFO] ingest not responding at :${INGEST_PORT} (expected in status-page-only mode)"
fi

echo ""
echo "=== Checks complete ==="
echo "Dashboard:    http://localhost:${DASHBOARD_PORT}"
echo "Status pages: http://localhost:${STATUS_PAGE_PORT}"
echo "API server:   http://localhost:${SERVER_PORT}"
