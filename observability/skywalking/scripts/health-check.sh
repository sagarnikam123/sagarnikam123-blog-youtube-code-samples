#!/bin/bash
# =============================================================================
# SkyWalking Health Check Script
# =============================================================================
# Uses GraphQL API to verify SkyWalking setup health
#
# Usage:
#   ./health-check.sh                    # Check localhost:12800
#   ./health-check.sh http://oap:12800   # Check custom endpoint
# =============================================================================

# Configuration
OAP_URL="${1:-http://localhost:12800}"
GRAPHQL_ENDPOINT="${OAP_URL}/graphql"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  SkyWalking Health Check${NC}"
    echo -e "${BLUE}  Endpoint: ${OAP_URL}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────────────"
}

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

graphql_query() {
    local query="$1"
    curl -s -X POST "${GRAPHQL_ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}" 2>/dev/null
}

# =============================================================================
# Health Checks
# =============================================================================

check_oap_connectivity() {
    print_section "OAP Server Connectivity"

    if curl -s -f "${OAP_URL}/healthcheck" > /dev/null 2>&1; then
        check_pass "OAP server is reachable"
    else
        check_fail "OAP server is not reachable at ${OAP_URL}"
        echo -e "    ${RED}Cannot proceed with further checks${NC}"
        exit 1
    fi
}

check_graphql_api() {
    print_section "GraphQL API"

    local result
    result=$(graphql_query "query { version }")
    local version
    version=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('version',''))" 2>/dev/null)

    if [ -n "$version" ]; then
        check_pass "GraphQL API responding (SkyWalking v${version})"
    else
        check_fail "GraphQL API not responding"
    fi
}

check_available_layers() {
    print_section "Available Layers"

    local result
    result=$(graphql_query "query { listLayers }")
    local layers
    layers=$(echo "$result" | python3 -c "import sys,json; layers=json.load(sys.stdin).get('data',{}).get('listLayers',[]); print(len(layers))" 2>/dev/null)

    if [ -n "$layers" ] && [ "$layers" -gt 0 ] 2>/dev/null; then
        check_pass "Found ${layers} available layers"
    else
        check_fail "No layers available"
    fi
}

check_services_by_layer() {
    print_section "Services by Layer"

    local layers=("MYSQL" "POSTGRESQL" "REDIS" "MONGODB" "ELASTICSEARCH" "NGINX" "SO11Y_OAP" "SO11Y_BANYANDB" "GENERAL")

    for layer in "${layers[@]}"; do
        local result
        result=$(graphql_query "query { listServices(layer: \\\"${layer}\\\") { id name } }")
        local count
        count=$(echo "$result" | python3 -c "import sys,json; services=json.load(sys.stdin).get('data',{}).get('listServices',[]); print(len(services))" 2>/dev/null)

        if [ -n "$count" ] && [ "$count" -gt 0 ] 2>/dev/null; then
            local names
            names=$(echo "$result" | python3 -c "import sys,json; services=json.load(sys.stdin).get('data',{}).get('listServices',[]); print(', '.join([s['name'] for s in services[:3]]))" 2>/dev/null)
            check_pass "${layer}: ${count} service(s) - ${names}"
        else
            check_warn "${layer}: No services found"
        fi
    done
}

check_oap_self_observability() {
    print_section "OAP Self-Observability"

    local result
    result=$(graphql_query "query { listServices(layer: \\\"SO11Y_OAP\\\") { id name } }")
    local count
    count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('listServices',[])))" 2>/dev/null)

    if [ -n "$count" ] && [ "$count" -gt 0 ] 2>/dev/null; then
        check_pass "OAP self-observability enabled"

        local service_id
        service_id=$(echo "$result" | python3 -c "import sys,json; services=json.load(sys.stdin).get('data',{}).get('listServices',[]); print(services[0]['id'] if services else '')" 2>/dev/null)

        if [ -n "$service_id" ]; then
            local instances
            instances=$(graphql_query "query { listInstances(serviceId: \\\"${service_id}\\\") { id name } }")
            local inst_count
            inst_count=$(echo "$instances" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('listInstances',[])))" 2>/dev/null)

            if [ -n "$inst_count" ] && [ "$inst_count" -gt 0 ] 2>/dev/null; then
                check_pass "OAP instances reporting: ${inst_count}"
            fi
        fi
    else
        check_warn "OAP self-observability not detected"
    fi
}

check_storage_health() {
    print_section "Storage Backend"

    local result
    result=$(graphql_query "query { listServices(layer: \\\"SO11Y_BANYANDB\\\") { id name } }")
    local count
    count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('listServices',[])))" 2>/dev/null)

    if [ -n "$count" ] && [ "$count" -gt 0 ] 2>/dev/null; then
        check_pass "BanyanDB self-observability enabled"
    else
        check_warn "BanyanDB self-observability not detected (may be using different storage)"
    fi
}

print_summary() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  Total Checks:  ${TOTAL_CHECKS}"
    echo -e "  ${GREEN}Passed:${NC}        ${PASSED_CHECKS}"
    echo -e "  ${RED}Failed:${NC}        ${FAILED_CHECKS}"
    echo ""

    if [ "$FAILED_CHECKS" -eq 0 ]; then
        echo -e "  ${GREEN}✓ All critical checks passed!${NC}"
        exit 0
    else
        echo -e "  ${RED}✗ Some checks failed. Review the output above.${NC}"
        exit 1
    fi
}

# =============================================================================
# Main
# =============================================================================

print_header
check_oap_connectivity
check_graphql_api
check_available_layers
check_services_by_layer
check_oap_self_observability
check_storage_health
print_summary
