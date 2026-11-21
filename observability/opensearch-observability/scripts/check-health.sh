#!/usr/bin/env bash
# OpenSearch Observability health check script
set -euo pipefail

DASHBOARDS_PORT="${DASHBOARDS_PORT:-5601}"
OPENSEARCH_PORT="${OPENSEARCH_PORT:-9200}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== OpenSearch Observability Health Check ==="

# Check containers
for svc in opensearch-node opensearch-dashboards opensearch-data-prepper; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  else
    fail "$svc is not healthy"
  fi
done

# Check OpenSearch cluster
OS_STATUS=$(curl -sf "http://localhost:${OPENSEARCH_PORT}/_cluster/health" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
if [[ "$OS_STATUS" =~ ^(green|yellow)$ ]]; then
  pass "OpenSearch cluster status: ${OS_STATUS}"
else
  fail "OpenSearch cluster status: ${OS_STATUS}"
fi

# Check Data Prepper pipelines
if curl -sf "http://localhost:4900/list" > /dev/null 2>&1; then
  pass "Data Prepper pipelines loaded"
else
  fail "Data Prepper pipelines not responding"
fi

echo ""
echo "=== All checks passed ==="
echo "Dashboards:     http://localhost:${DASHBOARDS_PORT}"
echo "OpenSearch:     http://localhost:${OPENSEARCH_PORT}"
echo "OTLP gRPC:      localhost:4317 → Data Prepper :21890"
echo "OTLP HTTP:      localhost:${OTLP_HTTP_PORT} → Data Prepper :21891"
