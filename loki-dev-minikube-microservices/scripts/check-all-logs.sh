#!/bin/bash
set -e

echo "🔍 Checking All Loki Component Logs"
echo "===================================="

# Get all pod names first
echo "📊 Current Pod Status:"
kubectl get pods -n loki

echo ""
echo "📋 Component Log Analysis:"
echo ""

# Check each component individually
echo "📡 DISTRIBUTOR LOGS:"
kubectl logs -n loki -l app=loki-distributor --tail=10 2>/dev/null || echo "  ❌ No distributor pods found"

echo ""
echo "📊 INGESTER LOGS:"
kubectl logs -n loki loki-ingester-0 --tail=10 2>/dev/null || echo "  ❌ Ingester not found"

echo ""
echo "🔍 QUERIER LOGS:"
kubectl logs -n loki -l app=loki-querier --tail=10 2>/dev/null || echo "  ❌ No querier pods found"

echo ""
echo "🎯 QUERY-FRONTEND LOGS:"
kubectl logs -n loki -l app=loki-query-frontend --tail=10 2>/dev/null || echo "  ❌ No query-frontend pods found"

echo ""
echo "📅 QUERY-SCHEDULER LOGS:"
kubectl logs -n loki -l app=loki-query-scheduler --tail=10 2>/dev/null || echo "  ❌ No query-scheduler pods found"

echo ""
echo "🗜️ COMPACTOR LOGS:"
kubectl logs -n loki -l app=loki-compactor --tail=10 2>/dev/null || echo "  ❌ No compactor pods found"

echo ""
echo "📏 RULER LOGS:"
kubectl logs -n loki -l app=loki-ruler --tail=10 2>/dev/null || echo "  ❌ No ruler pods found"

echo ""
echo "🏛️ INDEX-GATEWAY LOGS:"
kubectl logs -n loki -l app=loki-index-gateway --tail=10 2>/dev/null || echo "  ❌ No index-gateway pods found"

echo ""
echo "🗄️ MINIO LOGS:"
kubectl logs -n loki -l app=minio --tail=10 2>/dev/null || echo "  ❌ MinIO not found"

echo ""
echo "📝 FLUENT BIT LOGS:"
kubectl logs -n loki -l app=fluent-bit --tail=10 2>/dev/null || echo "  ❌ No fluent-bit pods found"

echo ""
echo "✅ Log check complete!"
echo ""
echo "🔍 Health Indicators to Look For:"
echo "  • Distributor: 'memberlist cluster succeeded'"
echo "  • Ingester: 'checkpoint done', 'uploading tables'"
echo "  • Querier: 'query readiness setup completed'"
echo "  • Query-Frontend: 'Loki started'"
echo "  • Compactor: 'compactor started'"
echo "  • Fluent Bit: 'flush chunk succeeded'"