#!/usr/bin/env bash
# Coroot health check script
set -euo pipefail

COROOT_UI_PORT="${COROOT_UI_PORT:-8080}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Coroot Health Check ==="

# Check core containers
for svc in coroot-server coroot-clickhouse coroot-prometheus; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  elif docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null | grep -q "running"; then
    pass "$svc is running"
  else
    fail "$svc is not running or unhealthy"
  fi
done

# Check node-agent (Linux only)
if docker inspect --format='{{.State.Status}}' coroot-node-agent 2>/dev/null | grep -q "running"; then
  pass "coroot-node-agent is running (eBPF active)"
else
  warn "coroot-node-agent not running (expected on macOS — run with --profile linux on Linux)"
fi

# Check cluster-agent
if docker inspect --format='{{.State.Status}}' coroot-cluster-agent 2>/dev/null | grep -q "running"; then
  pass "coroot-cluster-agent is running"
else
  warn "coroot-cluster-agent not running"
fi

# Check Coroot UI
if curl -sf "http://localhost:${COROOT_UI_PORT}/health" > /dev/null 2>&1; then
  pass "Coroot UI responding at http://localhost:${COROOT_UI_PORT}"
else
  fail "Coroot UI not responding"
fi

echo ""
echo "=== All checks passed ==="
echo "Coroot UI:   http://localhost:${COROOT_UI_PORT}"
echo "OTLP gRPC:   localhost:${COROOT_UI_PORT} (Coroot's built-in OTLP receiver)"
echo ""
echo "Note: Send OTLP traces to Coroot directly at http://localhost:${COROOT_UI_PORT}/v1/traces"
