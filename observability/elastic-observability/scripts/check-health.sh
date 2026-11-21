#!/usr/bin/env bash
# Elastic Observability health check script
set -euo pipefail

KIBANA_PORT="${KIBANA_PORT:-5601}"
ES_PORT="${ES_PORT:-9200}"
APM_PORT="${APM_PORT:-8200}"
OTLP_HTTP_PORT="${OTLP_HTTP_PORT:-4318}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== Elastic Observability Health Check ==="

# Check containers
for svc in elastic-es elastic-kibana elastic-apm; do
  if docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null | grep -q "healthy"; then
    pass "$svc is healthy"
  else
    fail "$svc is not healthy"
  fi
done

# Check ES cluster
ES_STATUS=$(curl -sf "http://localhost:${ES_PORT}/_cluster/health" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
if [[ "$ES_STATUS" =~ ^(green|yellow)$ ]]; then
  pass "Elasticsearch cluster status: ${ES_STATUS}"
else
  fail "Elasticsearch cluster status: ${ES_STATUS}"
fi

# Check APM Server
if curl -sf "http://localhost:${APM_PORT}/" > /dev/null 2>&1; then
  pass "APM Server responding at :${APM_PORT}"
else
  fail "APM Server not responding"
fi

# Check OTLP via APM Server
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:${OTLP_HTTP_PORT}/v1/traces" \
  -X POST -H "Content-Type: application/json" \
  -d '{"resourceSpans":[]}' 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" =~ ^(200|400|202)$ ]]; then
  pass "OTLP HTTP endpoint responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
else
  fail "OTLP HTTP endpoint not responding at :${OTLP_HTTP_PORT} (HTTP ${HTTP_CODE})"
fi

echo ""
echo "=== All checks passed ==="
echo "Kibana UI:   http://localhost:${KIBANA_PORT}"
echo "APM Server:  http://localhost:${APM_PORT}"
echo "OTLP gRPC:   localhost:4317"
echo "OTLP HTTP:   localhost:${OTLP_HTTP_PORT}"
