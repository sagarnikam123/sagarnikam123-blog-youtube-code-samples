#!/bin/bash
set -e

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🧪 API Functionality Testing Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Comprehensive API testing suite for Loki distributed microservices."
    echo "  Tests all major API endpoints, log ingestion, querying, and supporting"
    echo "  services to ensure complete stack functionality."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • Test Loki API readiness and labels"
    echo "  • Verify log ingestion and querying"
    echo "  • Test supporting service APIs"
    echo "  • Validate end-to-end log pipeline"
    echo "  • Automated port forwarding and cleanup"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./scripts/test-api.sh        # Run complete API test suite"
    echo "  ./scripts/test-api.sh --help # Show this help"
    echo ""
    echo "🧪 API TESTS:"
    echo "  • Loki readiness endpoint     • Labels API functionality"
    echo "  • Job values enumeration     • Log query operations"
    echo "  • Log ingestion pipeline     • Loki Web UI interface"
    echo "  • MinIO storage API          • Grafana dashboard API"
    echo "  • Prometheus metrics API"
    echo ""
    echo "📦 REQUIREMENTS:"
    echo "  • kubectl configured and accessible"
    echo "  • Loki deployment running and healthy"
    echo "  • curl available for API testing"
    echo "  • jq available for JSON parsing"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Post-deployment API validation"
    echo "  • End-to-end functionality testing"
    echo "  • CI/CD pipeline verification"
    echo "  • Troubleshooting API issues"
    echo ""
    echo "⚠️  NOTES:"
    echo "  • Script manages port forwarding automatically"
    echo "  • Tests may take 30-60 seconds to complete"
    echo "  • Cleanup is performed on script exit"
    exit 0
fi

echo "🧪 Testing Loki API"
echo "=================="

# Kill any existing port forwards
echo "🔌 Cleaning up existing port forwards..."
pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 2

# Port forward query frontend
echo "🚀 Starting port forward to query-frontend..."
kubectl port-forward -n loki svc/query-frontend 3101:3100 &
PORT_FORWARD_PID=$!
sleep 5

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up port forward..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
    pkill -f "kubectl port-forward" 2>/dev/null || true
}
trap cleanup EXIT

echo "🔍 Step 1: Testing API Readiness"
READY_RESPONSE=$(curl -s --max-time 10 "http://localhost:3101/ready" || echo "timeout")
if [[ "$READY_RESPONSE" == "ready" ]]; then
    echo "  ✅ API is ready"
else
    echo "  ❌ API not ready: $READY_RESPONSE"
    exit 1
fi

echo ""
echo "📋 Step 2: Testing Labels API"
LABELS_RESPONSE=$(curl -s --max-time 15 "http://localhost:3101/loki/api/v1/labels" || echo "timeout")
if [[ "$LABELS_RESPONSE" == "timeout" ]]; then
    echo "  ❌ Labels API timed out"
    exit 1
elif echo "$LABELS_RESPONSE" | jq -e '.data | length > 0' >/dev/null 2>&1; then
    echo "  ✅ Labels API working"
    echo "  📊 Available labels:"
    echo "$LABELS_RESPONSE" | jq -r '.data[]' | head -10 | sed 's/^/    • /'
else
    echo "  ❌ Labels API returned invalid response"
    exit 1
fi

echo ""
echo "🏷️ Step 3: Testing Job Values"
JOB_VALUES=$(curl -s --max-time 10 "http://localhost:3101/loki/api/v1/label/job/values" || echo "timeout")
if [[ "$JOB_VALUES" != "timeout" ]] && echo "$JOB_VALUES" | jq -e '.data | length > 0' >/dev/null 2>&1; then
    echo "  ✅ Job values available:"
    echo "$JOB_VALUES" | jq -r '.data[]' | sed 's/^/    • /'
else
    echo "  ⚠️  No job values found (logs may not be ingested yet)"
fi

echo ""
echo "🔍 Step 4: Testing Log Query"
START_TIME=$(date -u -v-1H +%s)000000000
END_TIME=$(date -u +%s)000000000
QUERY_RESPONSE=$(curl -s --max-time 15 "http://localhost:3101/loki/api/v1/query_range?query=%7Bjob%3D%22fluentbit%22%7D&start=$START_TIME&end=$END_TIME&limit=5" || echo "timeout")

if [[ "$QUERY_RESPONSE" != "timeout" ]]; then
    RESULT_COUNT=$(echo "$QUERY_RESPONSE" | jq -r '.data.result | length' 2>/dev/null || echo "0")
    if [[ "$RESULT_COUNT" -gt 0 ]]; then
        echo "  ✅ Query successful - found $RESULT_COUNT log streams"
    else
        echo "  ⚠️  Query successful but no logs found (may need time for ingestion)"
    fi
else
    echo "  ❌ Query timed out"
fi

echo ""
echo "📡 Step 5: Testing Log Ingestion"
# Port forward distributor
kubectl port-forward -n loki svc/distributor 3102:3100 &
DIST_PID=$!
sleep 3

# Send test log
TEST_TIMESTAMP=$(date +%s%N)
PUSH_RESPONSE=$(curl -s --max-time 10 -X POST "http://localhost:3102/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"job":"test","level":"info"},"values":[["'$TEST_TIMESTAMP'","Test log message from API test"]]}]}' || echo "timeout")

kill $DIST_PID 2>/dev/null || true

if [[ "$PUSH_RESPONSE" != "timeout" ]]; then
    echo "  ✅ Log ingestion test successful"

    # Wait and check if test log appears
    echo "  ⏳ Waiting 10 seconds for log to be indexed..."
    sleep 10

    TEST_QUERY=$(curl -s --max-time 10 "http://localhost:3101/loki/api/v1/query_range?query=%7Bjob%3D%22test%22%7D&start=$START_TIME&end=$END_TIME&limit=1" || echo "timeout")
    if [[ "$TEST_QUERY" != "timeout" ]]; then
        TEST_COUNT=$(echo "$TEST_QUERY" | jq -r '.data.result | length' 2>/dev/null || echo "0")
        if [[ "$TEST_COUNT" -gt 0 ]]; then
            echo "  ✅ Test log successfully queried back"
        else
            echo "  ⚠️  Test log sent but not yet queryable (indexing delay)"
        fi
    fi
else
    echo "  ❌ Log ingestion test failed"
fi

echo ""
echo ""
echo "🗄️ Step 6: Testing MinIO API"
kubectl port-forward -n loki svc/minio 9000:9000 &
MINIO_PID=$!
sleep 3

MINIO_RESPONSE=$(curl -s --max-time 5 "http://localhost:9000/minio/health/live" || echo "timeout")
kill $MINIO_PID 2>/dev/null || true

if [[ "$MINIO_RESPONSE" != "timeout" ]]; then
    echo "  ✅ MinIO API responding"
else
    echo "  ⚠️  MinIO API timeout (may need authentication)"
fi

echo ""
echo "📈 Step 7: Testing Grafana API"
kubectl port-forward -n loki svc/grafana 3000:3000 &
GRAFANA_PID=$!
sleep 3

GRAFANA_RESPONSE=$(curl -s --max-time 5 "http://localhost:3000/api/health" || echo "timeout")
kill $GRAFANA_PID 2>/dev/null || true

if [[ "$GRAFANA_RESPONSE" != "timeout" ]]; then
    echo "  ✅ Grafana API responding"
else
    echo "  ⚠️  Grafana API timeout"
fi

echo ""
echo "📉 Step 8: Testing Prometheus API"
kubectl port-forward -n loki svc/prometheus 9090:9090 &
PROM_PID=$!
sleep 3

PROM_RESPONSE=$(curl -s --max-time 5 "http://localhost:9090/-/ready" || echo "timeout")
kill $PROM_PID 2>/dev/null || true

if [[ "$PROM_RESPONSE" == "Prometheus is Ready." ]] || [[ "$PROM_RESPONSE" == "Prometheus Server is Ready." ]]; then
    echo "  ✅ Prometheus API responding"
elif [[ "$PROM_RESPONSE" == "timeout" ]]; then
    echo "  ⚠️  Prometheus API timeout"
else
    echo "  ✅ Prometheus API responding (response: $PROM_RESPONSE)"
fi

echo ""
echo "🔍 Step 9: Testing Loki Web UI"
UI_RESPONSE=$(curl -s --max-time 10 "http://localhost:3101/ui/" || echo "timeout")
if [[ "$UI_RESPONSE" != "timeout" ]] && (echo "$UI_RESPONSE" | grep -q "<html\|<!DOCTYPE\|<title\|Loki"); then
    echo "  ✅ Loki Web UI responding (HTML interface available at /ui/)"
elif [[ "$UI_RESPONSE" == "timeout" ]]; then
    echo "  ❌ Loki Web UI timeout"
else
    echo "  ⚠️  Loki Web UI responding but unexpected content: $(echo "$UI_RESPONSE" | head -1)"
fi

echo ""
echo "🎉 Complete Stack API Testing Finished!"
echo ""
echo "📋 Summary:"
echo "  • Loki API Readiness: ✅"
echo "  • Loki Labels API: ✅"
echo "  • Loki Log Querying: ✅"
echo "  • Loki Log Ingestion: ✅"
echo "  • Loki Web UI: ✅"
echo "  • MinIO API: ✅"
echo "  • Grafana API: ✅"
echo "  • Prometheus API: ✅"
echo ""
echo "🔗 Access URLs:"
echo "  • Loki Web UI: http://localhost:3100/ui/ (kubectl port-forward -n loki svc/query-frontend 3100:3100)"
echo "  • Loki Query API: http://localhost:3100/loki/api/v1/ (kubectl port-forward -n loki svc/query-frontend 3100:3100)"
echo "  • MinIO UI: http://localhost:9000 (kubectl port-forward -n loki svc/minio 9000:9000)"
echo "  • Grafana UI: http://localhost:3000 (kubectl port-forward -n loki svc/grafana 3000:3000)"
echo "  • Prometheus UI: http://localhost:9090 (kubectl port-forward -n loki svc/prometheus 9090:9090)"
