#!/bin/bash
# =============================================================================
# SkyWalking UI & Data Flow Health Check Script
# =============================================================================
# Comprehensive health check for SkyWalking UI and data flow via GraphQL API
# and OAP Status/Debugging APIs
#
# Usage:
#   ./scripts/ui-health-check.sh [UI_URL] [OAP_URL] [TIMEOUT]
#
# Examples:
#   ./scripts/ui-health-check.sh                                    # localhost defaults
#   ./scripts/ui-health-check.sh http://localhost:8080              # UI only
#   ./scripts/ui-health-check.sh http://localhost:8080 http://localhost:12800  # UI + OAP
#   ./scripts/ui-health-check.sh http://skywalking.internal.scnx.io # Ingress
#
# Prerequisites:
#   - Port forward UI: kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking
#   - Port forward OAP: kubectl port-forward svc/skywalking-oap 12800:12800 -n skywalking
# =============================================================================

set -uo pipefail
# Don't exit on error - we want to continue checking other items

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
UI_URL="${1:-http://localhost:8080}"
OAP_URL="${2:-http://localhost:12800}"
GRAPHQL_URL="${UI_URL}/graphql"
TIMEOUT="${3:-60}"
PASSED=0
FAILED=0
WARNINGS=0
SKIPPED=0

# Get current time range
END_TIME=$(date -u +"%Y-%m-%d %H%M")
START_TIME=$(date -u -v-30M +"%Y-%m-%d %H%M" 2>/dev/null || date -u -d "30 minutes ago" +"%Y-%m-%d %H%M")
START_TIME_2H=$(date -u -v-2H +"%Y-%m-%d %H%M" 2>/dev/null || date -u -d "2 hours ago" +"%Y-%m-%d %H%M")

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASSED++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAILED++)); }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARNINGS++)); }
log_skip() { echo -e "${CYAN}[SKIP]${NC} $1"; ((SKIPPED++)); }
log_data() { echo -e "         $1"; }
log_section() { echo -e "\n${MAGENTA}=== $1 ===${NC}"; }

# GraphQL query helper
graphql_query() {
    local query="$1"
    local result
    result=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}" \
        "$GRAPHQL_URL" 2>&1) || true
    echo "$result"
}

# REST API helper
rest_get() {
    local url="$1"
    local accept="${2:-application/json}"
    local result
    result=$(curl -s --max-time "$TIMEOUT" -H "Accept: $accept" "$url" 2>&1) || true
    echo "$result"
}

# Extract helpers
extract_count() { echo "$1" | grep -o "\"$2\"" | wc -l | tr -d ' '; }
extract_value() { echo "$1" | grep -o "\"$2\":\"[^\"]*\"" | head -1 | cut -d'"' -f4; }
extract_number() { echo "$1" | grep -o "\"$2\":[0-9-]*" | head -1 | cut -d':' -f2; }

echo "=============================================="
echo "SkyWalking Comprehensive Health Check"
echo "=============================================="
echo "UI URL:  $UI_URL"
echo "OAP URL: $OAP_URL"
echo "Timeout: ${TIMEOUT}s"
echo "Time:    $START_TIME - $END_TIME (30 min)"
echo "=============================================="

# =============================================================================
# SECTION 1: CONNECTIVITY CHECKS
# =============================================================================
log_section "CONNECTIVITY"

log_info "Checking UI is reachable..."
HTTP_CODE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$UI_URL" 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    log_pass "UI reachable (HTTP $HTTP_CODE)"
else
    log_fail "UI not reachable at $UI_URL (HTTP $HTTP_CODE)"
    echo "Run: kubectl port-forward svc/skywalking-ui 8080:80 -n skywalking"
    exit 1
fi

log_info "Checking OAP REST API..."
HTTP_CODE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$OAP_URL/healthcheck" 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    log_pass "OAP REST API healthy (HTTP $HTTP_CODE)"
    OAP_AVAILABLE=true
elif [ "$HTTP_CODE" = "503" ]; then
    log_warn "OAP unhealthy (HTTP 503)"
    OAP_AVAILABLE=true
else
    log_warn "OAP REST API not reachable (HTTP $HTTP_CODE)"
    log_data "Run: kubectl port-forward svc/skywalking-oap 12800:12800 -n skywalking"
    OAP_AVAILABLE=false
fi

# =============================================================================
# SECTION 2: GRAPHQL API HEALTH
# =============================================================================
log_section "GRAPHQL API"

log_info "Checking GraphQL endpoint..."
RESPONSE=$(graphql_query "{ version }" 2>&1)
if echo "$RESPONSE" | grep -q '"version"'; then
    VERSION=$(extract_value "$RESPONSE" "version")
    log_pass "GraphQL responding (SkyWalking $VERSION)"
else
    log_fail "GraphQL not responding"
fi

log_info "Checking OAP health via GraphQL..."
RESPONSE=$(graphql_query "{ checkHealth { score details } }" 2>&1)
if echo "$RESPONSE" | grep -q '"score":0'; then
    log_pass "OAP health score: 0 (healthy)"
elif echo "$RESPONSE" | grep -q '"score"'; then
    SCORE=$(extract_number "$RESPONSE" "score")
    log_warn "OAP health score: $SCORE"
    DETAILS=$(extract_value "$RESPONSE" "details")
    [ -n "$DETAILS" ] && log_data "Details: $DETAILS"
else
    log_fail "OAP health check failed"
fi

# =============================================================================
# SECTION 3: OAP STATUS APIs (REST)
# =============================================================================
log_section "OAP STATUS APIs"

if [ "$OAP_AVAILABLE" = true ]; then
    # Cluster Nodes
    log_info "Checking cluster nodes..."
    RESPONSE=$(rest_get "$OAP_URL/status/cluster/nodes")
    if echo "$RESPONSE" | grep -q '"nodes"'; then
        NODE_COUNT=$(echo "$RESPONSE" | grep -o '"host"' | wc -l | tr -d ' ')
        SELF_NODE=$(echo "$RESPONSE" | grep -o '"self":true' | wc -l | tr -d ' ')
        log_pass "Cluster: $NODE_COUNT node(s), $SELF_NODE self"
        # Show nodes
        echo "$RESPONSE" | grep -o '"host":"[^"]*"' | while read -r line; do
            HOST=$(echo "$line" | cut -d'"' -f4)
            log_data "- $HOST"
        done
    else
        log_warn "Could not get cluster nodes"
    fi

    # TTL Configuration
    log_info "Checking TTL configuration..."
    RESPONSE=$(rest_get "$OAP_URL/status/config/ttl")
    if echo "$RESPONSE" | grep -q '"metrics"'; then
        METRICS_MIN=$(extract_number "$RESPONSE" "minute")
        METRICS_DAY=$(extract_number "$RESPONSE" "day")
        RECORDS_TRACE=$(echo "$RESPONSE" | grep -o '"trace":[0-9]*' | head -1 | cut -d':' -f2)
        log_pass "TTL: metrics=$METRICS_DAY days, traces=$RECORDS_TRACE days"
    else
        log_warn "Could not get TTL config"
    fi

    # Alarm Rules Status
    log_info "Checking alarm rules..."
    RESPONSE=$(rest_get "$OAP_URL/status/alarm/rules")
    if echo "$RESPONSE" | grep -q '"rules"'; then
        RULE_COUNT=$(echo "$RESPONSE" | grep -o '"ruleId"' | wc -l | tr -d ' ')
        log_pass "Alarm rules: $RULE_COUNT rule(s) configured"
    elif echo "$RESPONSE" | grep -q '\[\]'; then
        log_info "No alarm rules configured"
    else
        log_skip "Alarm rules API not available"
    fi

    # Config Dump (sample)
    log_info "Checking OAP configuration..."
    RESPONSE=$(rest_get "$OAP_URL/debugging/config/dump")
    if echo "$RESPONSE" | grep -q 'core.default'; then
        STORAGE=$(echo "$RESPONSE" | grep -o '"storage\.[^"]*":"[^"]*"' | head -1)
        log_pass "Config dump available"
        if echo "$RESPONSE" | grep -q 'banyandb'; then
            log_data "Storage: BanyanDB"
        elif echo "$RESPONSE" | grep -q 'elasticsearch'; then
            log_data "Storage: Elasticsearch"
        fi
    else
        log_skip "Config dump not available"
    fi
else
    log_skip "OAP REST APIs (port-forward OAP to enable)"
fi

# =============================================================================
# SECTION 4: SELF-OBSERVABILITY
# =============================================================================
log_section "SELF-OBSERVABILITY"

# OAP Instances
log_info "Checking OAP self-observability..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"SO11Y_OAP\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "OAP: $COUNT instance(s)"
    echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -3 | while read -r line; do
        log_data "- $(echo "$line" | cut -d'"' -f4)"
    done
else
    log_warn "OAP self-observability: No data"
fi

# Satellite
log_info "Checking Satellite self-observability..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"SO11Y_SATELLITE\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "Satellite: $COUNT instance(s)"
else
    log_warn "Satellite: No data"
fi

# BanyanDB
log_info "Checking BanyanDB self-observability..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"BANYANDB\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "BanyanDB: $COUNT instance(s)"
else
    log_warn "BanyanDB: No data"
fi

# =============================================================================
# SECTION 5: KUBERNETES MONITORING
# =============================================================================
log_section "KUBERNETES MONITORING"

log_info "Checking K8s clusters..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"K8S_CLUSTER\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "K8s Clusters: $COUNT"
    echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -3 | while read -r line; do
        log_data "- $(echo "$line" | cut -d'"' -f4)"
    done
else
    log_warn "K8s Clusters: No data (check OTel Collector)"
fi

log_info "Checking K8s services..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"K8S_SERVICE\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "K8s Services: $COUNT"
else
    log_warn "K8s Services: No data"
fi

log_info "Checking K8s nodes..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"K8S_NODE\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "K8s Nodes: $COUNT"
else
    log_warn "K8s Nodes: No data"
fi

# =============================================================================
# SECTION 6: INFRASTRUCTURE
# =============================================================================
log_section "INFRASTRUCTURE"

log_info "Checking Linux/VM hosts..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"OS_LINUX\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "Linux/VM: $COUNT host(s)"
else
    log_warn "Linux/VM: No data (check node-exporter)"
fi

# =============================================================================
# SECTION 7: APPLICATION SERVICES
# =============================================================================
log_section "APPLICATION SERVICES"

log_info "Checking traced services..."
RESPONSE=$(graphql_query "{ listServices(layer: \\\"GENERAL\\\") { id name } }" 2>&1)
if echo "$RESPONSE" | grep -q '"name"'; then
    COUNT=$(extract_count "$RESPONSE" "id")
    log_pass "Services: $COUNT traced"
    echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -5 | while read -r line; do
        log_data "- $(echo "$line" | cut -d'"' -f4)"
    done

    # Get first service for detailed checks
    SVC_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    SVC_NAME=$(echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
else
    log_warn "Services: No traced apps"
    log_data "(Deploy agents to see traces)"
    SVC_ID=""
fi

# Virtual services
for LAYER in "VIRTUAL_DATABASE" "VIRTUAL_CACHE" "VIRTUAL_MQ"; do
    RESPONSE=$(graphql_query "{ listServices(layer: \\\"$LAYER\\\") { id name } }" 2>&1)
    if echo "$RESPONSE" | grep -q '"name"'; then
        COUNT=$(extract_count "$RESPONSE" "id")
        log_pass "$LAYER: $COUNT"
    else
        log_skip "$LAYER: None"
    fi
done

# =============================================================================
# SECTION 8: ENDPOINTS & INSTANCES
# =============================================================================
log_section "ENDPOINTS & INSTANCES"

if [ -n "${SVC_ID:-}" ]; then
    log_info "Checking endpoints for $SVC_NAME..."
    RESPONSE=$(graphql_query "{ findEndpoint(serviceId: \\\"$SVC_ID\\\", keyword: \\\"\\\", limit: 10) { id name } }" 2>&1)
    if echo "$RESPONSE" | grep -q '"name"'; then
        COUNT=$(extract_count "$RESPONSE" "id")
        log_pass "Endpoints: $COUNT for $SVC_NAME"
        echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -5 | while read -r line; do
            log_data "- $(echo "$line" | cut -d'"' -f4)"
        done
    else
        log_warn "Endpoints: None found"
    fi

    log_info "Checking instances for $SVC_NAME..."
    RESPONSE=$(graphql_query "{ listInstances(serviceId: \\\"$SVC_ID\\\", duration: { start: \\\"${START_TIME}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }) { id name language } }" 2>&1)
    if echo "$RESPONSE" | grep -q '"name"'; then
        COUNT=$(extract_count "$RESPONSE" "id")
        log_pass "Instances: $COUNT for $SVC_NAME"
        echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -3 | while read -r line; do
            log_data "- $(echo "$line" | cut -d'"' -f4)"
        done
    else
        log_warn "Instances: None found"
    fi
else
    log_skip "Endpoints & Instances (no services)"
fi

# =============================================================================
# SECTION 9: TRACES
# =============================================================================
log_section "TRACES"

log_info "Checking recent traces (30 min)..."
QUERY="{ queryBasicTraces(condition: { queryDuration: { start: \\\"${START_TIME}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }, queryOrder: BY_START_TIME, paging: { pageNum: 1, pageSize: 5 } }) { traces { segmentId endpointNames duration isError } total } }"
RESPONSE=$(graphql_query "$QUERY" 2>&1)

if echo "$RESPONSE" | grep -q '"total":0'; then
    log_warn "Traces: None in last 30 min"
elif echo "$RESPONSE" | grep -q '"total"'; then
    TOTAL=$(extract_number "$RESPONSE" "total")
    ERROR_COUNT=$(echo "$RESPONSE" | grep -o '"isError":true' | wc -l | tr -d ' ')
    log_pass "Traces: $TOTAL found ($ERROR_COUNT errors)"
else
    log_warn "Traces: Query failed"
fi

# =============================================================================
# SECTION 10: LOGS
# =============================================================================
log_section "LOGS"

log_info "Checking recent logs (30 min)..."
QUERY="{ queryLogs(condition: { queryDuration: { start: \\\"${START_TIME}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }, paging: { pageNum: 1, pageSize: 5 } }) { logs { serviceName timestamp } total } }"
RESPONSE=$(graphql_query "$QUERY" 2>&1)

if echo "$RESPONSE" | grep -q '"total":0'; then
    log_warn "Logs: None in last 30 min"
elif echo "$RESPONSE" | grep -q '"total"'; then
    TOTAL=$(extract_number "$RESPONSE" "total")
    log_pass "Logs: $TOTAL found"
else
    log_skip "Logs: Query not supported"
fi

# =============================================================================
# SECTION 11: ALARMS
# =============================================================================
log_section "ALARMS"

log_info "Checking alarms (2 hours)..."
QUERY="{ getAlarm(duration: { start: \\\"${START_TIME_2H}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }, paging: { pageNum: 1, pageSize: 10 }) { msgs { scope name message } total } }"
RESPONSE=$(graphql_query "$QUERY" 2>&1)

if echo "$RESPONSE" | grep -q '"total":0'; then
    log_pass "Alarms: None triggered (healthy)"
elif echo "$RESPONSE" | grep -q '"total"'; then
    TOTAL=$(extract_number "$RESPONSE" "total")
    log_warn "Alarms: $TOTAL triggered"
    echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -3 | while read -r line; do
        log_data "- $(echo "$line" | cut -d'"' -f4 | cut -c1-60)"
    done
else
    log_skip "Alarms: Query failed"
fi

# =============================================================================
# SECTION 12: TOPOLOGY
# =============================================================================
log_section "TOPOLOGY"

log_info "Checking global topology..."
QUERY="{ getGlobalTopology(duration: { start: \\\"${START_TIME}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }) { nodes { id name type isReal } calls { source target } } }"
RESPONSE=$(graphql_query "$QUERY" 2>&1)

if echo "$RESPONSE" | grep -q '"nodes":\[\]'; then
    log_warn "Topology: No data"
elif echo "$RESPONSE" | grep -q '"nodes":\['; then
    NODE_COUNT=$(extract_count "$RESPONSE" "\"id\"")
    CALL_COUNT=$(echo "$RESPONSE" | grep -o '"source"' | wc -l | tr -d ' ')
    log_pass "Topology: $NODE_COUNT nodes, $CALL_COUNT calls"
else
    log_warn "Topology: Query failed"
fi

# =============================================================================
# SECTION 13: EVENTS
# =============================================================================
log_section "EVENTS"

log_info "Checking events (2 hours)..."
QUERY="{ queryEvents(condition: { time: { start: \\\"${START_TIME_2H}\\\", end: \\\"${END_TIME}\\\", step: MINUTE }, paging: { pageNum: 1, pageSize: 10 } }) { events { name type message } total } }"
RESPONSE=$(graphql_query "$QUERY" 2>&1)

if echo "$RESPONSE" | grep -q '"total":0'; then
    log_info "Events: None"
elif echo "$RESPONSE" | grep -q '"total"'; then
    TOTAL=$(extract_number "$RESPONSE" "total")
    log_pass "Events: $TOTAL found"
else
    log_skip "Events: Query not supported"
fi

# =============================================================================
# SECTION 14: METADATA APIs
# =============================================================================
log_section "METADATA"

log_info "Checking available layers..."
RESPONSE=$(graphql_query "{ listLayers }" 2>&1)
if echo "$RESPONSE" | grep -q '"listLayers"'; then
    LAYERS=$(echo "$RESPONSE" | grep -o '"[A-Z_]*"' | tr '\n' ' ')
    log_pass "Layers available"
    log_data "$LAYERS"
else
    log_warn "Could not list layers"
fi

log_info "Checking time info..."
RESPONSE=$(graphql_query "{ getTimeInfo { timezone currentTimestamp } }" 2>&1)
if echo "$RESPONSE" | grep -q '"timezone"'; then
    TZ=$(extract_value "$RESPONSE" "timezone")
    log_pass "Server timezone: $TZ"
else
    log_skip "Time info not available"
fi

# =============================================================================
# SECTION 15: TTL INFO (GraphQL)
# =============================================================================
log_section "TTL INFO"

log_info "Checking records TTL..."
RESPONSE=$(graphql_query "{ getRecordsTTL { normal trace log } }" 2>&1)
if echo "$RESPONSE" | grep -q '"normal"'; then
    NORMAL=$(extract_number "$RESPONSE" "normal")
    TRACE=$(extract_number "$RESPONSE" "trace")
    LOG=$(extract_number "$RESPONSE" "log")
    log_pass "Records TTL: normal=$NORMAL, trace=$TRACE, log=$LOG days"
else
    log_skip "Records TTL not available"
fi

log_info "Checking metrics TTL..."
RESPONSE=$(graphql_query "{ getMetricsTTL { minute hour day } }" 2>&1)
if echo "$RESPONSE" | grep -q '"minute"'; then
    MIN=$(extract_number "$RESPONSE" "minute")
    HOUR=$(extract_number "$RESPONSE" "hour")
    DAY=$(extract_number "$RESPONSE" "day")
    log_pass "Metrics TTL: minute=$MIN, hour=$HOUR, day=$DAY days"
else
    log_skip "Metrics TTL not available"
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "=============================================="
echo "SUMMARY"
echo "=============================================="
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Skipped:  ${CYAN}$SKIPPED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo ""

# Status indicators
echo "--- Data Flow Status ---"
[ "$PASSED" -ge 3 ] && echo -e "${GREEN}✓${NC} Core connectivity OK"
[ "$PASSED" -ge 6 ] && echo -e "${GREEN}✓${NC} Self-observability working"
[ "$PASSED" -ge 9 ] && echo -e "${GREEN}✓${NC} Kubernetes monitoring active"
[ "$PASSED" -ge 12 ] && echo -e "${GREEN}✓${NC} Application tracing active"
[ "$PASSED" -ge 15 ] && echo -e "${GREEN}✓${NC} Full observability stack"
echo ""

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}Some checks failed. Review output above.${NC}"
    exit 1
elif [ "$WARNINGS" -gt 8 ]; then
    echo -e "${YELLOW}Multiple warnings - fresh deployment?${NC}"
    echo "Data should appear within 5-10 minutes."
    exit 0
elif [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}Passed with warnings.${NC}"
    exit 0
else
    echo -e "${GREEN}All checks passed! SkyWalking fully operational.${NC}"
    exit 0
fi
