#!/bin/bash
# =============================================================================
# SkyWalking Health Check Script
# =============================================================================
# Usage: ./scripts/health-check.sh [namespace]
# =============================================================================

NAMESPACE="${1:-skywalking}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() { echo -e "  ${GREEN}✓${NC} $1"; ((PASSED++)); }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAILED++)); }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SkyWalking Health Check - Namespace: $NAMESPACE${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# Check namespace
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' not found${NC}"
    exit 1
fi

# =============================================================================
echo -e "\n${BLUE}▶ Fetching cluster state...${NC}"
# =============================================================================

# Get all pods in one call
ALL_PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null)
ALL_SVCS=$(kubectl get endpoints -n "$NAMESPACE" -o json 2>/dev/null)

# =============================================================================
echo -e "\n${BLUE}▶ POD STATUS${NC}"
# =============================================================================

check_pods() {
    local name=$1
    local pattern=$2
    local expected=$3

    local matching=$(echo "$ALL_PODS" | grep "$pattern" || true)
    local total=$(echo "$matching" | grep -v "^$" | wc -l | tr -d ' ')
    local ready=$(echo "$matching" | grep -c "1/1\|2/2" 2>/dev/null || echo 0)

    if [[ "$ready" -eq "$total" && "$total" -gt 0 ]]; then
        pass "$name: $ready/$total ready"
    elif [[ "$total" -eq 0 ]]; then
        fail "$name: no pods found"
    else
        fail "$name: $ready/$total ready (expected $expected)"
    fi
}

check_pods "etcd" "etcd" 3
check_pods "BanyanDB Liaison" "liaison" 2
check_pods "BanyanDB Data" "data-hot" 2
check_pods "OAP Server" "oap-[a-z0-9]" 3
check_pods "Satellite" "satellite" 2
check_pods "UI" "ui-" 2

# =============================================================================
echo -e "\n${BLUE}▶ SERVICES${NC}"
# =============================================================================

check_svc() {
    local name=$1
    local count=$(echo "$ALL_SVCS" | jq -r ".items[] | select(.metadata.name==\"$name\") | .subsets[0].addresses | length" 2>/dev/null || echo 0)

    if [[ "$count" -gt 0 ]]; then
        pass "$name: $count endpoints"
    else
        fail "$name: no endpoints"
    fi
}

check_svc "skywalking-oap"
check_svc "skywalking-satellite"
check_svc "skywalking-ui"
check_svc "skywalking-banyandb-grpc"

# =============================================================================
echo -e "\n${BLUE}▶ OAP HEALTH (via kubectl exec)${NC}"
# =============================================================================

OAP_POD=$(echo "$ALL_PODS" | grep "oap-[a-z0-9]" | grep "1/1" | head -1 | awk '{print $1}')
if [[ -n "$OAP_POD" ]]; then
    echo -e "  Testing pod: $OAP_POD"

    # Health check
    health=$(kubectl exec -n "$NAMESPACE" "$OAP_POD" -- curl -s -m 10 http://localhost:12800/healthcheck 2>/dev/null)
    if [[ "$health" == *"200"* || "$health" == "OK" ]]; then
        pass "Health endpoint: OK"
    else
        fail "Health endpoint: $health"
    fi

    # GraphQL version
    version=$(kubectl exec -n "$NAMESPACE" "$OAP_POD" -- curl -s -m 10 -X POST -H "Content-Type: application/json" \
        -d '{"query":"{ version }"}' http://localhost:12800/graphql 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    if [[ -n "$version" ]]; then
        pass "GraphQL API: v$version"
    else
        fail "GraphQL API: not responding"
    fi
else
    fail "OAP: no running pod found"
fi

# =============================================================================
echo -e "\n${BLUE}▶ UI HEALTH${NC}"
# =============================================================================

UI_POD=$(echo "$ALL_PODS" | grep "ui-" | grep "1/1" | head -1 | awk '{print $1}')
if [[ -n "$UI_POD" ]]; then
    code=$(kubectl exec -n "$NAMESPACE" "$UI_POD" -- curl -s -m 10 -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null)
    if [[ "$code" == "200" ]]; then
        pass "UI accessible: HTTP 200"
    else
        fail "UI: HTTP $code"
    fi
else
    fail "UI: no running pod found"
fi

# =============================================================================
echo -e "\n${BLUE}▶ SUMMARY${NC}"
# =============================================================================

echo ""
echo -e "  Passed: ${GREEN}$PASSED${NC}"
echo -e "  Failed: ${RED}$FAILED${NC}"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED check(s) failed${NC}"
    exit 1
fi
