#!/usr/bin/env bash
# Gatus health check script
set -euo pipefail

GATUS_PORT="${GATUS_PORT:-8080}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Gatus Health Check ==="

# Container health (only when run via Docker/Compose)
if docker inspect --format='{{.State.Health.Status}}' gatus 2>/dev/null | grep -q "healthy"; then
  pass "gatus container is healthy"
fi

# Health endpoint
if curl -sf "http://localhost:${GATUS_PORT}/health" > /dev/null 2>&1; then
  pass "Gatus /health responding at http://localhost:${GATUS_PORT}"
else
  fail "Gatus /health not responding at http://localhost:${GATUS_PORT}"
fi

# Prometheus metrics endpoint (present when metrics: true)
if curl -sf "http://localhost:${GATUS_PORT}/metrics" > /dev/null 2>&1; then
  pass "Gatus /metrics endpoint responding"
else
  echo "[INFO] /metrics not exposed (set 'metrics: true' in config.yaml to enable)"
fi

echo ""
echo "=== All checks passed ==="
echo "Gatus dashboard: http://localhost:${GATUS_PORT}"
