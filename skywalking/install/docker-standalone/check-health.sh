#!/bin/bash
# =============================================================================
# Health Check Script for SkyWalking with Fuzzy-Train
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.fuzzy-train.yml"

echo "🏥 SkyWalking Health Check"
echo "=========================="
echo ""

# Check container status
echo "📦 Container Status:"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Check BanyanDB health
echo "🗄️  BanyanDB Health:"
BANYANDB_HEALTH=$(curl -s http://localhost:17913/api/healthz || echo "FAILED")
if [ "$BANYANDB_HEALTH" = "SERVING" ]; then
    echo "   ✅ BanyanDB: $BANYANDB_HEALTH"
else
    echo "   ❌ BanyanDB: $BANYANDB_HEALTH"
fi
echo ""

# Check OAP health
echo "🔧 OAP Server Health:"
OAP_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:12800/healthcheck || echo "000")
if [ "$OAP_HEALTH" = "200" ]; then
    echo "   ✅ OAP: HTTP $OAP_HEALTH"
else
    echo "   ❌ OAP: HTTP $OAP_HEALTH"
fi
echo ""

# Check UI
echo "🖥️  UI Health:"
UI_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 || echo "000")
if [ "$UI_HEALTH" = "200" ]; then
    echo "   ✅ UI: HTTP $UI_HEALTH"
else
    echo "   ❌ UI: HTTP $UI_HEALTH"
fi
echo ""

# Check registered services
echo "📊 Registered Services:"
SERVICES=$(curl -s -X POST http://localhost:12800/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ listServices(layer: \"GENERAL\") { name } }"}' 2>/dev/null | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print('\n'.join(['   • ' + s['name'] for s in data['data']['listServices']]))" 2>/dev/null || echo "   ⚠️  Unable to query services")
echo "$SERVICES"
echo ""

# Check log generator activity
echo "📝 Log Generator Activity (last 5 seconds):"
PYTHON_LOGS=$(docker compose -f "$COMPOSE_FILE" logs fuzzy-train-python --since 5s 2>/dev/null | grep -c "fuzzy-train" || echo "0")
JAVA_LOGS=$(docker compose -f "$COMPOSE_FILE" logs fuzzy-train-java --since 5s 2>/dev/null | grep -c "fuzzy-train" || echo "0")

if [ "$PYTHON_LOGS" -gt 0 ]; then
    echo "   ✅ Python generator: $PYTHON_LOGS logs"
else
    echo "   ⚠️  Python generator: No recent logs"
fi

if [ "$JAVA_LOGS" -gt 0 ]; then
    echo "   ✅ Java generator: $JAVA_LOGS logs"
else
    echo "   ⚠️  Java generator: No recent logs"
fi
echo ""

echo "🔗 Access Points:"
echo "   • UI:              http://localhost:8080"
echo "   • OAP API:         http://localhost:12800"
echo "   • OAP Metrics:     http://localhost:1234/metrics"
echo "   • BanyanDB Health: http://localhost:17913/api/healthz"
echo ""
