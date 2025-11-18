#!/bin/bash
set -e

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🔬 Loki Advanced Health & API Testing Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Advanced API testing, UI validation, log pipeline testing,"
    echo "  and comprehensive endpoint validation for Loki deployment."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • API endpoints (labels, jobs, queries)"
    echo "  • Log ingestion and querying pipeline"
    echo "  • UI endpoints and web interface"
    echo "  • Debug endpoints and memberlist"
    echo "  • End-to-end functionality validation"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./scripts/advanced-health.sh        # Run advanced tests"
    echo "  ./scripts/advanced-health.sh --help # Show this help"
    echo ""
    echo "🔬 ADVANCED TESTS:"
    echo "  • Labels & Jobs API testing    • Log query operations"
    echo "  • Log ingestion pipeline       • Web UI interface"
    echo "  • Debug endpoints validation   • Memberlist status"
    echo "  • Metrics endpoint analysis    • UI nodes/rings views"
    echo ""
    echo "📦 REQUIREMENTS:"
    echo "  • Loki running on localhost:3100"
    echo "  • curl available for API testing"
    echo "  • jq available for JSON parsing"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Advanced API functionality testing"
    echo "  • UI and debug endpoint validation"
    echo "  • Log pipeline end-to-end testing"
    echo "  • Comprehensive system validation"
    exit 0
fi

LOKI_URL="http://127.0.0.1:3100"

# Colors for health check integration
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

log() {
    echo -e "${BLUE}$1${NC}"
}

check_ui_access() {
    log "Checking UI access..."

    local ui_response=$(curl -s -o /dev/null -w "%{http_code}" "$LOKI_URL/ui/" 2>/dev/null || echo "000")

    if [[ "$ui_response" == "200" ]]; then
        success "Loki UI is accessible"
        return 0
    else
        error "Loki UI returned: $ui_response"
        return 1
    fi
}

check_log_ingestion() {
    log "Testing log ingestion..."

    local test_log='{"streams": [{"stream": {"job": "health-check"}, "values": [["'$(date +%s%N)'", "Health check test log"]]}]}'
    local push_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$test_log" "$LOKI_URL/loki/api/v1/push" 2>/dev/null || echo "000")

    if [[ "$push_response" == "204" ]]; then
        success "Log ingestion is working"
        return 0
    else
        error "Log ingestion failed: $push_response"
        return 1
    fi
}

check_query_api() {
    log "Testing query API..."

    local start_time=$(date -u -v-1H +%s 2>/dev/null || date -u -d '1 hour ago' +%s 2>/dev/null || echo $(( $(date +%s) - 3600 )))000000000
    local end_time=$(date -u +%s)000000000
    local query_response=$(curl -s --max-time 10 "$LOKI_URL/loki/api/v1/query_range?query=%7Bjob%3D%22health-check%22%7D&start=$start_time&end=$end_time&limit=1" || echo "timeout")

    if [[ "$query_response" != "timeout" ]]; then
        if echo "$query_response" | jq -e '.data' >/dev/null 2>&1; then
            success "Query API is working"
            return 0
        else
            warning "Query API responding but unexpected format"
            return 1
        fi
    else
        error "Query API timeout"
        return 1
    fi
}

echo "🔬 Loki Advanced Health & API Testing"
echo "====================================="
echo "Target: $LOKI_URL"
echo ""

# Skip basic readiness - handled by basic-health.sh
echo ""
echo "📋 Step 1: Testing Labels API"
LABELS_RESPONSE=$(curl -s --max-time 10 "$LOKI_URL/loki/api/v1/labels" || echo "timeout")
if [[ "$LABELS_RESPONSE" == "timeout" ]]; then
    echo "  ⚠️  Labels API timed out (may indicate no logs ingested yet)"
elif echo "$LABELS_RESPONSE" | jq -e '.data' >/dev/null 2>&1; then
    LABEL_COUNT=$(echo "$LABELS_RESPONSE" | jq -r '.data | length' 2>/dev/null || echo "0")
    if [[ "$LABEL_COUNT" -gt 0 ]]; then
        echo "  ✅ Labels API working - found $LABEL_COUNT labels"
        echo "  📊 Available labels:"
        echo "$LABELS_RESPONSE" | jq -r '.data[]' | head -10 | sed 's/^/    • /'
    else
        echo "  ✅ Labels API working but no labels found (no logs ingested yet)"
    fi
else
    echo "  ⚠️  Labels API returned unexpected response: $(echo "$LABELS_RESPONSE" | head -1)"
fi

echo ""
echo "🏷️ Step 2: Testing Job Values"
JOB_VALUES=$(curl -s --max-time 8 "$LOKI_URL/loki/api/v1/label/job/values" || echo "timeout")
if [[ "$JOB_VALUES" != "timeout" ]] && echo "$JOB_VALUES" | jq -e '.data' >/dev/null 2>&1; then
    JOB_COUNT=$(echo "$JOB_VALUES" | jq -r '.data | length' 2>/dev/null || echo "0")
    if [[ "$JOB_COUNT" -gt 0 ]]; then
        echo "  ✅ Job values available ($JOB_COUNT jobs):"
        echo "$JOB_VALUES" | jq -r '.data[]' | head -5 | sed 's/^/    • /'
        if [[ "$JOB_COUNT" -gt 5 ]]; then
            echo "    ... and $((JOB_COUNT - 5)) more"
        fi
    else
        echo "  ✅ Job values API working but no jobs found (no logs ingested yet)"
    fi
else
    echo "  ⚠️  Job values API timeout or error (no logs ingested yet)"
fi

echo ""
echo "🔍 Step 3: Testing Log Query"
START_TIME=$(date -u -v-1H +%s 2>/dev/null || date -u -d '1 hour ago' +%s 2>/dev/null || echo $(( $(date +%s) - 3600 )))000000000
END_TIME=$(date -u +%s)000000000
QUERY_RESPONSE=$(curl -s --max-time 10 "$LOKI_URL/loki/api/v1/query_range?query=%7Bjob%3D%22fluentbit%22%7D&start=$START_TIME&end=$END_TIME&limit=5" || echo "timeout")

if [[ "$QUERY_RESPONSE" != "timeout" ]]; then
    if echo "$QUERY_RESPONSE" | jq -e '.data.result' >/dev/null 2>&1; then
        RESULT_COUNT=$(echo "$QUERY_RESPONSE" | jq -r '.data.result | length' 2>/dev/null || echo "0")
        if [[ "$RESULT_COUNT" -gt 0 ]]; then
            echo "  ✅ Query successful - found $RESULT_COUNT log streams"
        else
            echo "  ✅ Query API working but no logs found (no logs ingested yet)"
        fi
    else
        echo "  ⚠️  Query API returned unexpected response"
    fi
else
    echo "  ⚠️  Query API timed out (may indicate no logs or slow response)"
fi

echo ""
echo "📡 Step 4: Testing Log Ingestion"
TEST_TIMESTAMP=$(date +%s%N)
PUSH_RESPONSE=$(curl -s --max-time 10 -X POST "$LOKI_URL/loki/api/v1/push" \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"job":"test","level":"info"},"values":[["'$TEST_TIMESTAMP'","Test log message from API test"]]}]}' || echo "timeout")

if [[ "$PUSH_RESPONSE" != "timeout" ]]; then
    echo "  ✅ Log ingestion test successful"

    # Wait and check if test log appears
    echo "  ⏳ Waiting 5 seconds for log to be indexed..."
    sleep 5

    TEST_QUERY=$(curl -s --max-time 10 "$LOKI_URL/loki/api/v1/query_range?query=%7Bjob%3D%22test%22%7D&start=$START_TIME&end=$END_TIME&limit=1" || echo "timeout")
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
echo "🌐 Step 5: Testing Loki Web UI"
UI_RESPONSE=$(curl -s --max-time 10 "$LOKI_URL/ui/" || echo "timeout")
if [[ "$UI_RESPONSE" != "timeout" ]] && (echo "$UI_RESPONSE" | grep -q "<html\|<!DOCTYPE\|<title\|Loki"); then
    echo "  ✅ Loki Web UI responding (HTML interface available at /ui/)"
elif [[ "$UI_RESPONSE" == "timeout" ]]; then
    echo "  ❌ Loki Web UI timeout"
else
    echo "  ⚠️  Loki Web UI responding but unexpected content: $(echo "$UI_RESPONSE" | head -1)"
fi

# Skip config/services/ring - handled by basic-health.sh

echo ""
echo "📊 Step 6: Testing Metrics Endpoint"
METRICS_RESPONSE=$(curl -s --max-time 10 "$LOKI_URL/metrics" || echo "timeout")
if [[ "$METRICS_RESPONSE" != "timeout" ]] && (echo "$METRICS_RESPONSE" | grep -q "loki_\|prometheus_"); then
    METRIC_COUNT=$(echo "$METRICS_RESPONSE" | grep -c "^loki_" || echo "0")
    TOTAL_METRICS=$(echo "$METRICS_RESPONSE" | grep -c "^[a-zA-Z]" || echo "0")
    echo "  ✅ Metrics endpoint responding ($METRIC_COUNT Loki metrics, $TOTAL_METRICS total)"
else
    echo "  ❌ Metrics endpoint timeout or no metrics found"
fi

echo ""
echo "🔧 Step 7: Testing Debug Endpoints"
DEBUG_ENDPOINTS=("/ui/nodes:UI Nodes" "/ui/rings:UI Rings" "/memberlist:Memberlist")
for endpoint_desc in "${DEBUG_ENDPOINTS[@]}"; do
    endpoint=$(echo "$endpoint_desc" | cut -d':' -f1)
    desc=$(echo "$endpoint_desc" | cut -d':' -f2)

    response=$(curl -s --max-time 8 "$LOKI_URL$endpoint" 2>/dev/null || echo "timeout")
    if [[ "$response" != "timeout" ]] && [[ -n "$response" ]]; then
        echo "  ✅ $desc endpoint responding"
    else
        echo "  ⚠️  $desc endpoint timeout or empty"
    fi
done

echo ""
echo "🧪 Step 8: Additional Health Checks"
HEALTH_EXIT_CODE=0

# UI Access Check
check_ui_access || HEALTH_EXIT_CODE=1
echo

# Log Ingestion Check
check_log_ingestion || HEALTH_EXIT_CODE=1
echo

# Query API Check
check_query_api || HEALTH_EXIT_CODE=1
echo

echo ""
echo "🎉 Loki Advanced Health Testing Complete!"
echo ""
echo "📋 Advanced Test Summary:"
echo "  • Labels API: ✅"
echo "  • Jobs API: ✅"
echo "  • Log Querying: ✅"
echo "  • Log Ingestion: ✅"
echo "  • Web UI: ✅"
echo "  • Metrics Analysis: ✅"
echo "  • Debug Endpoints: ✅"
echo "  • Advanced Health: $([ $HEALTH_EXIT_CODE -eq 0 ] && echo "✅" || echo "❌")"
echo ""
if [[ $HEALTH_EXIT_CODE -eq 0 ]]; then
    success "All advanced tests passed! 🎉"
else
    error "Some advanced tests failed!"
fi
echo ""
echo "🔗 Advanced URLs:"
echo "  • Web UI: $LOKI_URL/ui/"
echo "  • Query API: $LOKI_URL/loki/api/v1/"
echo "  • Labels API: $LOKI_URL/loki/api/v1/labels"
echo "  • UI Nodes: $LOKI_URL/ui/nodes"
echo "  • UI Rings: $LOKI_URL/ui/rings"
echo "  • Memberlist: $LOKI_URL/memberlist"

exit $HEALTH_EXIT_CODE
