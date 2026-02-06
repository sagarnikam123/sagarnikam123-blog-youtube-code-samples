#!/bin/bash
# =============================================================================
# Apache SkyWalking - Installation Validation Tests
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# Test Functions
# =============================================================================
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

test_skip() {
    echo -e "${YELLOW}○${NC} $1 (skipped)"
}

# =============================================================================
# Tests
# =============================================================================
test_banyandb_health() {
    echo "Testing BanyanDB health endpoint..."

    if curl -s http://localhost:17913/api/healthz > /dev/null 2>&1; then
        test_pass "BanyanDB health check"
    else
        test_fail "BanyanDB health check - not responding"
    fi
}

test_oap_health() {
    echo "Testing OAP Server health endpoint..."

    if curl -s http://localhost:12800/healthcheck > /dev/null 2>&1; then
        test_pass "OAP Server health check"
    else
        test_fail "OAP Server health check - not responding"
    fi
}

test_oap_grpc() {
    echo "Testing OAP gRPC port..."

    if nc -z localhost 11800 2>/dev/null; then
        test_pass "OAP gRPC port (11800) is open"
    else
        test_fail "OAP gRPC port (11800) is not accessible"
    fi
}

test_ui_accessible() {
    echo "Testing UI accessibility..."

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 2>/dev/null)

    if [[ "$HTTP_CODE" == "200" ]]; then
        test_pass "UI is accessible (HTTP 200)"
    else
        test_fail "UI returned HTTP $HTTP_CODE"
    fi
}

test_graphql_endpoint() {
    echo "Testing GraphQL endpoint..."

    RESPONSE=$(curl -s -X POST http://localhost:12800/graphql \
        -H "Content-Type: application/json" \
        -d '{"query":"{ version }"}' 2>/dev/null)

    if echo "$RESPONSE" | grep -q "version"; then
        test_pass "GraphQL endpoint responding"
    else
        test_fail "GraphQL endpoint not responding correctly"
    fi
}

test_storage_connection() {
    echo "Testing storage connection..."

    # Query services to verify storage is working
    RESPONSE=$(curl -s -X POST http://localhost:12800/graphql \
        -H "Content-Type: application/json" \
        -d '{"query":"{ getAllServices(duration: {start: \"2024-01-01\", end: \"2024-01-02\", step: DAY}) { key { name } } }"}' 2>/dev/null)

    if echo "$RESPONSE" | grep -q "getAllServices\|data"; then
        test_pass "Storage connection working"
    else
        test_fail "Storage connection issue"
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  Apache SkyWalking - Installation Tests"
    echo "=============================================="
    echo ""

    test_banyandb_health
    test_oap_health
    test_oap_grpc
    test_ui_accessible
    test_graphql_endpoint
    test_storage_connection

    echo ""
    echo "=============================================="
    echo "  Test Results"
    echo "=============================================="
    echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"
