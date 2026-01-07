#!/bin/bash

#############################################
# Grafana Mimir Endpoints Testing Script
# Tests all accessible HTTP endpoints
#############################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-mimir-test}"
GATEWAY_SVC="${GATEWAY_SVC:-mimir-nginx}"
GATEWAY_PORT="${GATEWAY_PORT:-80}"
COMPONENT_PORT="${COMPONENT_PORT:-8080}"
TENANT_ID="${TENANT_ID:-anonymous}"
TEST_HOST="${TEST_HOST:-localhost}"
TEST_PORT="${TEST_PORT:-}"  # If set, overrides port-forward local port

# Test results
PASSED=0
FAILED=0
SKIPPED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}Testing:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

print_skip() {
    echo -e "${YELLOW}⊘ SKIP${NC}: $1"
    ((SKIPPED++))
}

# Test endpoint function
test_endpoint() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}
    local headers=${4:-""}

    echo -e "${YELLOW}Testing:${NC} $description"

    if [[ -n "$headers" ]]; then
        response=$(curl -s -w "\n%{http_code}" -H "$headers" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    fi

    http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "$expected_code" ]]; then
        print_success "$description (HTTP $http_code)"
    else
        print_fail "$description (Expected: $expected_code, Got: $http_code)"
    fi
}

# Setup kubectl proxy
setup_proxy() {
    if [[ -z "$PROXY_STARTED" ]]; then
        echo -e "${BLUE}→${NC} Starting kubectl proxy on port 8001"
        kubectl proxy --port=8001 >/dev/null 2>&1 &
        PROXY_PID=$!
        sleep 2
        PROXY_STARTED=true
    fi
}

# Build proxy URL
get_proxy_url() {
    local target=$1
    local port=$2

    if [[ $target == svc/* ]]; then
        local svc_name=${target#svc/}
        echo "http://localhost:8001/api/v1/namespaces/$NAMESPACE/services/$svc_name:$port/proxy"
    elif [[ $target == pod/* ]]; then
        local pod_name=${target#pod/}
        echo "http://localhost:8001/api/v1/namespaces/$NAMESPACE/pods/$pod_name:$port/proxy"
    fi
}

cleanup_proxy() {
    if [[ -n "$PROXY_PID" ]]; then
        kill $PROXY_PID 2>/dev/null || true
        wait $PROXY_PID 2>/dev/null || true
    fi
}

trap cleanup_proxy EXIT

#############################################
# Main Testing
#############################################

echo -e "${GREEN}"
cat << "EOF"
  __  __ _           _      _____         _
 |  \/  (_)_ __ ___ (_)_ __|_   _|__  ___| |_
 | |\/| | | '_ ` _ \| | '__| | |/ _ \/ __| __|
 | |  | | | | | | | | | |    | |  __/\__ \ |_
 |_|  |_|_|_| |_| |_|_|_|    |_|\___||___/\__|

EOF
echo -e "${NC}"

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}curl not found. Please install curl.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} kubectl found"
echo -e "${GREEN}✓${NC} curl found"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${RED}Namespace '$NAMESPACE' not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Namespace '$NAMESPACE' exists"

#############################################
# Test Gateway Endpoints
#############################################

print_header "Testing Gateway Endpoints"
setup_proxy

BASE_URL=$(get_proxy_url "svc/$GATEWAY_SVC" "$GATEWAY_PORT")

test_endpoint "$BASE_URL/" "Root endpoint"
test_endpoint "$BASE_URL/ready" "Ready endpoint"
test_endpoint "$BASE_URL/prometheus/api/v1/status/buildinfo" "Build info" 200 "X-Scope-OrgID: $TENANT_ID"
test_endpoint "$BASE_URL/prometheus/api/v1/labels" "List labels" 200 "X-Scope-OrgID: $TENANT_ID"
test_endpoint "$BASE_URL/prometheus/api/v1/query?query=up" "Instant query" 200 "X-Scope-OrgID: $TENANT_ID"

#############################################
# Test Distributor Endpoints
#############################################

print_header "Testing Distributor Endpoints"
BASE_URL=$(get_proxy_url "svc/mimir-distributor-headless" "$COMPONENT_PORT")

test_endpoint "$BASE_URL/ready" "Distributor ready"
test_endpoint "$BASE_URL/metrics" "Distributor metrics"
test_endpoint "$BASE_URL/config" "Distributor config"
test_endpoint "$BASE_URL/services" "Distributor services"
test_endpoint "$BASE_URL/distributor/ring" "Distributor ring"
test_endpoint "$BASE_URL/memberlist" "Distributor memberlist"

#############################################
# Test Ingester Endpoints
#############################################

print_header "Testing Ingester Endpoints"
INGESTER_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=ingester -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$INGESTER_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$INGESTER_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Ingester ready"
    test_endpoint "$BASE_URL/metrics" "Ingester metrics"
    test_endpoint "$BASE_URL/config" "Ingester config"
    test_endpoint "$BASE_URL/services" "Ingester services"
    test_endpoint "$BASE_URL/ingester/ring" "Ingester ring"
    test_endpoint "$BASE_URL/memberlist" "Ingester memberlist"
else
    print_skip "Ingester endpoints (no pod found)"
fi

#############################################
# Test Querier Endpoints
#############################################

print_header "Testing Querier Endpoints"
QUERIER_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=querier -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$QUERIER_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$QUERIER_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Querier ready"
    test_endpoint "$BASE_URL/metrics" "Querier metrics"
    test_endpoint "$BASE_URL/config" "Querier config"
    test_endpoint "$BASE_URL/services" "Querier services"
    test_endpoint "$BASE_URL/memberlist" "Querier memberlist"
else
    print_skip "Querier endpoints (no pod found)"
fi

#############################################
# Test Query-Frontend Endpoints
#############################################

print_header "Testing Query-Frontend Endpoints"
BASE_URL=$(get_proxy_url "svc/mimir-query-frontend" "$COMPONENT_PORT")

test_endpoint "$BASE_URL/ready" "Query-Frontend ready"
test_endpoint "$BASE_URL/metrics" "Query-Frontend metrics"
test_endpoint "$BASE_URL/config" "Query-Frontend config"
test_endpoint "$BASE_URL/services" "Query-Frontend services"
test_endpoint "$BASE_URL/memberlist" "Query-Frontend memberlist"

#############################################
# Test Compactor Endpoints
#############################################

print_header "Testing Compactor Endpoints"
COMPACTOR_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=compactor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$COMPACTOR_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$COMPACTOR_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Compactor ready"
    test_endpoint "$BASE_URL/metrics" "Compactor metrics"
    test_endpoint "$BASE_URL/config" "Compactor config"
    test_endpoint "$BASE_URL/services" "Compactor services"
    test_endpoint "$BASE_URL/compactor/ring" "Compactor ring"
    test_endpoint "$BASE_URL/memberlist" "Compactor memberlist"
else
    print_skip "Compactor endpoints (no pod found)"
fi

#############################################
# Test Store-Gateway Endpoints
#############################################

print_header "Testing Store-Gateway Endpoints"
STORE_GATEWAY_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=store-gateway -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$STORE_GATEWAY_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$STORE_GATEWAY_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Store-Gateway ready"
    test_endpoint "$BASE_URL/metrics" "Store-Gateway metrics"
    test_endpoint "$BASE_URL/config" "Store-Gateway config"
    test_endpoint "$BASE_URL/services" "Store-Gateway services"
    test_endpoint "$BASE_URL/store-gateway/ring" "Store-Gateway ring"
    test_endpoint "$BASE_URL/memberlist" "Store-Gateway memberlist"
else
    print_skip "Store-Gateway endpoints (no pod found)"
fi

#############################################
# Test Ruler Endpoints
#############################################

print_header "Testing Ruler Endpoints"
RULER_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=ruler -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$RULER_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$RULER_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Ruler ready"
    test_endpoint "$BASE_URL/metrics" "Ruler metrics"
    test_endpoint "$BASE_URL/config" "Ruler config"
    test_endpoint "$BASE_URL/services" "Ruler services"
    test_endpoint "$BASE_URL/ruler/ring" "Ruler ring"
    test_endpoint "$BASE_URL/memberlist" "Ruler memberlist"
else
    print_skip "Ruler endpoints (no pod found)"
fi

#############################################
# Test Alertmanager Endpoints
#############################################

print_header "Testing Alertmanager Endpoints"
ALERTMANAGER_POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=alertmanager -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [[ -n "$ALERTMANAGER_POD" ]]; then
    BASE_URL=$(get_proxy_url "pod/$ALERTMANAGER_POD" "$COMPONENT_PORT")
    test_endpoint "$BASE_URL/ready" "Alertmanager ready"
    test_endpoint "$BASE_URL/metrics" "Alertmanager metrics"
    test_endpoint "$BASE_URL/config" "Alertmanager config"
    test_endpoint "$BASE_URL/services" "Alertmanager services"
    test_endpoint "$BASE_URL/alertmanager/ring" "Alertmanager ring"
    test_endpoint "$BASE_URL/memberlist" "Alertmanager memberlist"
    test_endpoint "$BASE_URL/multitenant_alertmanager/status" "Alertmanager status"
else
    print_skip "Alertmanager endpoints (no pod found)"
fi

#############################################
# Summary
#############################################

print_header "Test Summary"

TOTAL=$((PASSED + FAILED + SKIPPED))

echo -e "Total Tests:   ${BLUE}$TOTAL${NC}"
echo -e "Passed:        ${GREEN}$PASSED${NC}"
echo -e "Failed:        ${RED}$FAILED${NC}"
echo -e "Skipped:       ${YELLOW}$SKIPPED${NC}"

if [[ $FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}All tests passed! ✓${NC}\n"
    exit 0
else
    echo -e "\n${RED}Some tests failed! ✗${NC}\n"
    exit 1
fi
