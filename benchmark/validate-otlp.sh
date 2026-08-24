#!/usr/bin/env bash
# =============================================================================
# OTLP Endpoint Validation Script
# =============================================================================
# Sends test telemetry (logs, metrics, traces) to an OTLP endpoint using
# telemetrygen (from opentelemetry-collector-contrib).
#
# Usage:
#   ./validate-otlp.sh [OTLP_ENDPOINT]
#
# Examples:
#   ./validate-otlp.sh localhost:4317          # gRPC
#   ./validate-otlp.sh --http localhost:4318   # HTTP
#
# Prerequisites:
#   - telemetrygen installed: go install github.com/open-telemetry/opentelemetry-collector-contrib/cmd/telemetrygen@latest
#   - Or use Docker: docker run --rm --network host ghcr.io/open-telemetry/opentelemetry-collector-releases/telemetrygen:latest
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Parse arguments
PROTOCOL="grpc"
ENDPOINT="${1:-localhost:4317}"

if [[ "${1:-}" == "--http" ]]; then
  PROTOCOL="http"
  ENDPOINT="${2:-localhost:4318}"
fi

echo "=== OTLP Endpoint Validation ==="
echo "Endpoint: ${ENDPOINT}"
echo "Protocol: ${PROTOCOL}"
echo ""

# Check if telemetrygen is available
TELEMETRYGEN=""
if command -v telemetrygen &> /dev/null; then
  TELEMETRYGEN="telemetrygen"
elif docker image inspect ghcr.io/open-telemetry/opentelemetry-collector-releases/telemetrygen:latest &> /dev/null 2>&1; then
  TELEMETRYGEN="docker run --rm --network host ghcr.io/open-telemetry/opentelemetry-collector-releases/telemetrygen:latest"
fi

if [[ -z "$TELEMETRYGEN" ]]; then
  warn "telemetrygen not found. Falling back to curl-based HTTP validation."
  echo ""

  # Fallback: curl-based HTTP check
  if [[ "$PROTOCOL" == "grpc" ]]; then
    # For gRPC, we can only check if the port is open
    if nc -z "${ENDPOINT%%:*}" "${ENDPOINT##*:}" 2>/dev/null; then
      pass "Port ${ENDPOINT##*:} is open (gRPC endpoint likely accepting connections)"
    else
      fail "Port ${ENDPOINT##*:} is not reachable"
    fi
  else
    # HTTP: send empty OTLP payloads
    BASE="http://${ENDPOINT}"

    echo "Testing traces..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "${BASE}/v1/traces" -X POST \
      -H "Content-Type: application/json" \
      -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" =~ ^(200|400|202)$ ]]; then
      pass "Traces endpoint: HTTP ${HTTP_CODE}"
    else
      fail "Traces endpoint: HTTP ${HTTP_CODE}"
    fi

    echo "Testing metrics..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "${BASE}/v1/metrics" -X POST \
      -H "Content-Type: application/json" \
      -d '{"resourceMetrics":[]}' 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" =~ ^(200|400|202)$ ]]; then
      pass "Metrics endpoint: HTTP ${HTTP_CODE}"
    else
      fail "Metrics endpoint: HTTP ${HTTP_CODE}"
    fi

    echo "Testing logs..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "${BASE}/v1/logs" -X POST \
      -H "Content-Type: application/json" \
      -d '{"resourceLogs":[]}' 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" =~ ^(200|400|202)$ ]]; then
      pass "Logs endpoint: HTTP ${HTTP_CODE}"
    else
      fail "Logs endpoint: HTTP ${HTTP_CODE}"
    fi
  fi

  exit 0
fi

# Full validation with telemetrygen
ERRORS=0

echo "Sending test traces (5 spans)..."
if $TELEMETRYGEN traces --otlp-insecure --traces 5 --endpoint "${ENDPOINT}" 2>/dev/null; then
  pass "Traces accepted"
else
  fail "Traces rejected"
  ERRORS=$((ERRORS + 1))
fi

echo "Sending test metrics (5 datapoints)..."
if $TELEMETRYGEN metrics --otlp-insecure --metrics 5 --endpoint "${ENDPOINT}" 2>/dev/null; then
  pass "Metrics accepted"
else
  fail "Metrics rejected"
  ERRORS=$((ERRORS + 1))
fi

echo "Sending test logs (5 records)..."
if $TELEMETRYGEN logs --otlp-insecure --logs 5 --endpoint "${ENDPOINT}" 2>/dev/null; then
  pass "Logs accepted"
else
  fail "Logs rejected"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [[ $ERRORS -eq 0 ]]; then
  echo -e "${GREEN}=== All signals accepted ===${NC}"
else
  echo -e "${RED}=== ${ERRORS} signal(s) failed ===${NC}"
  exit 1
fi
