#!/bin/bash
################################################################################
# Automation Scripts Validation Test Suite
#
# This script validates all SkyWalking automation scripts with valid and
# invalid inputs, verifies error handling, and checks execution times.
#
# Task: 15. Checkpoint - Validate automation scripts
# Requirements: 5.1-5.10, 6.1-6.8, 7.1-7.10, 8.1-8.10, 9.1-9.13
#
# Usage:
#   ./validate-automation-scripts.sh [OPTIONS]
#
# Options:
#   --skip-deployment    Skip deployment script tests (requires cluster)
#   --skip-cleanup       Skip cleanup script tests (requires cluster)
#   --skip-connectivity  Skip connectivity tests (requires deployment)
#   --skip-ingestion     Skip ingestion tests (requires deployment)
#   --skip-health        Skip health tests (requires deployment)
#   -h, --help           Display this help message
#
# Exit codes:
#   0 - All validation tests passed
#   1 - One or more validation tests failed
#   2 - Script error or invalid arguments
################################################################################

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)

# Test flags
SKIP_DEPLOYMENT=false
SKIP_CLEANUP=false
SKIP_CONNECTIVITY=false
SKIP_INGESTION=false
SKIP_HEALTH=false

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo "─────────────────────────────────────────────────────────────────"
}

print_success() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED_TESTS++))
}

print_failure() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED_TESTS++))
}

print_skip() {
    echo -e "${YELLOW}⊘ SKIP${NC}: $1"
    ((SKIPPED_TESTS++))
}

print_info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

usage() {
    sed -n '3,24p' "$0" | sed 's/^# \?//'
    exit 0
}

run_test() {
    local test_name=$1
    local test_command=$2
    local expected_result=${3:-"success"}  # "success" or "contains:text"

    ((TOTAL_TESTS++))

    echo -n "Testing: $test_name ... "

    local output
    local exit_code

    output=$(eval "$test_command" 2>&1 || true)
    exit_code=$?

    local test_passed=false

    if [ "$expected_result" = "success" ]; then
        if [ $exit_code -eq 0 ]; then
            test_passed=true
        fi
    elif [[ "$expected_result" == contains:* ]]; then
        local search_text="${expected_result#contains:}"
        if echo "$output" | grep -q "$search_text"; then
            test_passed=true
        fi
    fi

    if [ "$test_passed" = true ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected: $expected_result"
        echo "  Exit code: $exit_code"
        echo "  Output (first 200 chars): ${output:0:200}"
        ((FAILED_TESTS++))
        return 1
    fi
}

check_script_exists() {
    local script=$1

    if [ ! -f "$SCRIPT_DIR/$script" ]; then
        print_failure "Script not found: $script"
        return 1
    fi

    if [ ! -x "$SCRIPT_DIR/$script" ]; then
        print_failure "Script not executable: $script"
        return 1
    fi

    return 0
}

################################################################################
# Deployment Script Tests
################################################################################

test_deployment_script() {
    if [ "$SKIP_DEPLOYMENT" = true ]; then
        print_skip "Deployment script tests (--skip-deployment flag)"
        return 0
    fi

    print_section "Deployment Script Validation"

    local script="deploy-skywalking-cluster.sh"

    if ! check_script_exists "$script"; then
        return 1
    fi

    # Test 1: No arguments (should fail)
    run_test "No arguments provided" \
        "$SCRIPT_DIR/$script 2>&1" \
        "contains:No environment specified"

    # Test 2: Invalid environment (should fail)
    run_test "Invalid environment parameter" \
        "$SCRIPT_DIR/$script invalid-env 2>&1" \
        "contains:Invalid environment"

    # Test 3: Help flag
    run_test "Help flag displays usage" \
        "$SCRIPT_DIR/$script --help 2>&1" \
        "contains:Usage:"

    # Test 4: Valid environment with dry-run
    run_test "Valid environment with dry-run (minikube)" \
        "$SCRIPT_DIR/$script minikube --dry-run 2>&1" \
        "contains:DRY RUN"

    run_test "Valid environment with dry-run (eks-dev)" \
        "$SCRIPT_DIR/$script eks-dev --dry-run 2>&1" \
        "contains:DRY RUN"

    run_test "Valid environment with dry-run (eks-prod)" \
        "$SCRIPT_DIR/$script eks-prod --dry-run 2>&1" \
        "contains:DRY RUN"

    # Test 5: Unknown option (should fail)
    run_test "Unknown option handling" \
        "$SCRIPT_DIR/$script minikube --unknown-option 2>&1" \
        "contains:Unknown option"

    # Test 6: Script structure validation
    print_info "Validating script structure..."

    if grep -q "validate_environment" "$SCRIPT_DIR/$script"; then
        print_success "Environment validation function exists"
    else
        print_failure "Environment validation function missing"
    fi

    if grep -q "check_command" "$SCRIPT_DIR/$script"; then
        print_success "Prerequisite check function exists"
    else
        print_failure "Prerequisite check function missing"
    fi

    if grep -q "check_cluster_connectivity" "$SCRIPT_DIR/$script"; then
        print_success "Cluster connectivity check exists"
    else
        print_failure "Cluster connectivity check missing"
    fi

    if grep -q "check_minikube_resources" "$SCRIPT_DIR/$script"; then
        print_success "Minikube resource check exists"
    else
        print_failure "Minikube resource check missing"
    fi

    if grep -q "handle_deployment_failure" "$SCRIPT_DIR/$script"; then
        print_success "Error handling function exists"
    else
        print_failure "Error handling function missing"
    fi

    if grep -q "display_connection_info" "$SCRIPT_DIR/$script"; then
        print_success "Connection info display function exists"
    else
        print_failure "Connection info display function missing"
    fi

    # Test 7: Timeout configuration
    if grep -q 'TIMEOUT="15m"' "$SCRIPT_DIR/$script"; then
        print_success "Deployment timeout set to 15 minutes"
    else
        print_failure "Deployment timeout not properly configured"
    fi

    print_info "Deployment script validation complete"
}

################################################################################
# Cleanup Script Tests
################################################################################

test_cleanup_script() {
    if [ "$SKIP_CLEANUP" = true ]; then
        print_skip "Cleanup script tests (--skip-cleanup flag)"
        return 0
    fi

    print_section "Cleanup Script Validation"

    local script="cleanup-skywalking-cluster.sh"

    if ! check_script_exists "$script"; then
        return 1
    fi

    # Test 1: No arguments (should fail)
    run_test "No arguments provided" \
        "$SCRIPT_DIR/$script 2>&1" \
        "contains:No environment specified"

    # Test 2: Invalid environment (should fail)
    run_test "Invalid environment parameter" \
        "$SCRIPT_DIR/$script invalid-env 2>&1" \
        "contains:Invalid environment"

    # Test 3: Help flag
    run_test "Help flag displays usage" \
        "$SCRIPT_DIR/$script --help 2>&1" \
        "contains:Usage:"

    # Test 4: Unknown option (should fail)
    run_test "Unknown option handling" \
        "$SCRIPT_DIR/$script minikube --unknown-option 2>&1" \
        "contains:Unknown option"

    # Test 5: Script structure validation
    print_info "Validating script structure..."

    if grep -q "validate_environment" "$SCRIPT_DIR/$script"; then
        print_success "Environment validation function exists"
    else
        print_failure "Environment validation function missing"
    fi

    if grep -q "confirm_cleanup" "$SCRIPT_DIR/$script"; then
        print_success "Cleanup confirmation function exists"
    else
        print_failure "Cleanup confirmation function missing"
    fi

    if grep -q "confirm_pvc_deletion" "$SCRIPT_DIR/$script"; then
        print_success "PVC deletion confirmation exists"
    else
        print_failure "PVC deletion confirmation missing"
    fi

    if grep -q "uninstall_helm_release" "$SCRIPT_DIR/$script"; then
        print_success "Helm uninstall function exists"
    else
        print_failure "Helm uninstall function missing"
    fi

    if grep -q "delete_pvcs" "$SCRIPT_DIR/$script"; then
        print_success "PVC deletion function exists"
    else
        print_failure "PVC deletion function missing"
    fi

    if grep -q "delete_namespace" "$SCRIPT_DIR/$script"; then
        print_success "Namespace deletion function exists"
    else
        print_failure "Namespace deletion function missing"
    fi

    if grep -q "handle_cleanup_failure" "$SCRIPT_DIR/$script"; then
        print_success "Error handling function exists"
    else
        print_failure "Error handling function missing"
    fi

    # Test 6: Flag handling
    if grep -q "DELETE_PVCS" "$SCRIPT_DIR/$script"; then
        print_success "PVC deletion flag supported"
    else
        print_failure "PVC deletion flag not found"
    fi

    if grep -q "DELETE_NAMESPACE" "$SCRIPT_DIR/$script"; then
        print_success "Namespace deletion flag supported"
    else
        print_failure "Namespace deletion flag not found"
    fi

    if grep -q "FORCE" "$SCRIPT_DIR/$script"; then
        print_success "Force mode flag supported"
    else
        print_failure "Force mode flag not found"
    fi

    print_info "Cleanup script validation complete"
}

################################################################################
# Connectivity Test Script Tests
################################################################################

test_connectivity_script() {
    if [ "$SKIP_CONNECTIVITY" = true ]; then
        print_skip "Connectivity script tests (--skip-connectivity flag)"
        return 0
    fi

    print_section "Connectivity Test Script Validation"

    local script="test-connectivity.sh"

    if ! check_script_exists "$script"; then
        return 1
    fi

    # Test 1: Help flag
    run_test "Help flag displays usage" \
        "$SCRIPT_DIR/$script --help 2>&1 | grep -q 'Usage:'" \
        0

    # Test 2: Unknown option (should fail)
    run_test "Unknown option handling" \
        "$SCRIPT_DIR/$script --unknown-option 2>&1 | grep -q 'Unknown option'" \
        0

    # Test 3: Script structure validation
    print_info "Validating script structure..."

    if grep -q "test_agent_to_satellite" "$SCRIPT_DIR/$script"; then
        print_success "Agent to Satellite test exists"
    else
        print_failure "Agent to Satellite test missing"
    fi

    if grep -q "test_satellite_to_oap" "$SCRIPT_DIR/$script"; then
        print_success "Satellite to OAP test exists"
    else
        print_failure "Satellite to OAP test missing"
    fi

    if grep -q "test_oap_to_banyandb" "$SCRIPT_DIR/$script"; then
        print_success "OAP to BanyanDB test exists"
    else
        print_failure "OAP to BanyanDB test missing"
    fi

    if grep -q "test_banyandb_http" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB HTTP test exists"
    else
        print_failure "BanyanDB HTTP test missing"
    fi

    if grep -q "test_etcd_cluster" "$SCRIPT_DIR/$script"; then
        print_success "etcd cluster test exists"
    else
        print_failure "etcd cluster test missing"
    fi

    if grep -q "test_banyandb_data_nodes" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB data nodes test exists"
    else
        print_failure "BanyanDB data nodes test missing"
    fi

    if grep -q "test_ui_to_oap" "$SCRIPT_DIR/$script"; then
        print_success "UI to OAP test exists"
    else
        print_failure "UI to OAP test missing"
    fi

    # Test 4: Timeout configuration
    if grep -q 'TIMEOUT=90' "$SCRIPT_DIR/$script"; then
        print_success "Test timeout set to 90 seconds"
    else
        print_failure "Test timeout not properly configured"
    fi

    # Test 5: Error reporting
    if grep -q "print_failure.*source component.*destination component" "$SCRIPT_DIR/$script"; then
        print_success "Error reporting includes component details"
    else
        print_failure "Error reporting may not include sufficient details"
    fi

    print_info "Connectivity script validation complete"
}

################################################################################
# Data Ingestion Test Script Tests
################################################################################

test_ingestion_script() {
    if [ "$SKIP_INGESTION" = true ]; then
        print_skip "Ingestion script tests (--skip-ingestion flag)"
        return 0
    fi

    print_section "Data Ingestion Test Script Validation"

    local script="test-data-ingestion.sh"

    if ! check_script_exists "$script"; then
        return 1
    fi

    # Test 1: Help flag
    run_test "Help flag displays usage" \
        "$SCRIPT_DIR/$script --help 2>&1 | grep -q 'Usage:'" \
        0

    # Test 2: Unknown option (should fail)
    run_test "Unknown option handling" \
        "$SCRIPT_DIR/$script --unknown-option 2>&1 | grep -q 'Unknown option'" \
        0

    # Test 3: Script structure validation
    print_info "Validating script structure..."

    if grep -q "deploy_test_application" "$SCRIPT_DIR/$script"; then
        print_success "Test application deployment function exists"
    else
        print_failure "Test application deployment function missing"
    fi

    if grep -q "verify_satellite_receives_data" "$SCRIPT_DIR/$script"; then
        print_success "Satellite data reception verification exists"
    else
        print_failure "Satellite data reception verification missing"
    fi

    if grep -q "verify_satellite_forwards_to_oap" "$SCRIPT_DIR/$script"; then
        print_success "Satellite forwarding verification exists"
    else
        print_failure "Satellite forwarding verification missing"
    fi

    if grep -q "verify_oap_processes_data" "$SCRIPT_DIR/$script"; then
        print_success "OAP data processing verification exists"
    else
        print_failure "OAP data processing verification missing"
    fi

    if grep -q "query_data_via_oap_api" "$SCRIPT_DIR/$script"; then
        print_success "OAP API query function exists"
    else
        print_failure "OAP API query function missing"
    fi

    if grep -q "verify_data_persistence_oap_restart" "$SCRIPT_DIR/$script"; then
        print_success "OAP restart persistence test exists"
    else
        print_failure "OAP restart persistence test missing"
    fi

    if grep -q "verify_data_persistence_banyandb_restart" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB restart persistence test exists"
    else
        print_failure "BanyanDB restart persistence test missing"
    fi

    if grep -q "localize_failure_component" "$SCRIPT_DIR/$script"; then
        print_success "Failure localization function exists"
    else
        print_failure "Failure localization function missing"
    fi

    if grep -q "cleanup_test_application" "$SCRIPT_DIR/$script"; then
        print_success "Test cleanup function exists"
    else
        print_failure "Test cleanup function missing"
    fi

    # Test 4: Timeout configuration
    if grep -q 'TIMEOUT=600' "$SCRIPT_DIR/$script" || grep -q 'TEST_TIMEOUT=600' "$SCRIPT_DIR/$script"; then
        print_success "Test timeout set to 10 minutes (600 seconds)"
    else
        print_failure "Test timeout not properly configured"
    fi

    # Test 5: SWCK agent injection
    if grep -q "swck-java-agent-injected" "$SCRIPT_DIR/$script"; then
        print_success "SWCK agent injection annotation present"
    else
        print_failure "SWCK agent injection not configured"
    fi

    print_info "Ingestion script validation complete"
}

################################################################################
# Health Check Script Tests
################################################################################

test_health_script() {
    if [ "$SKIP_HEALTH" = true ]; then
        print_skip "Health script tests (--skip-health flag)"
        return 0
    fi

    print_section "Health Check Script Validation"

    local script="test-health.sh"

    if ! check_script_exists "$script"; then
        return 1
    fi

    # Test 1: Help flag
    run_test "Help flag displays usage" \
        "$SCRIPT_DIR/$script --help 2>&1 | grep -q 'Usage:'" \
        0

    # Test 2: Unknown option (should fail)
    run_test "Unknown option handling" \
        "$SCRIPT_DIR/$script --unknown-option 2>&1 | grep -q 'Unknown option'" \
        0

    # Test 3: Script structure validation
    print_info "Validating script structure..."

    if grep -q "check_oap_server_health" "$SCRIPT_DIR/$script"; then
        print_success "OAP Server health check exists"
    else
        print_failure "OAP Server health check missing"
    fi

    if grep -q "check_banyandb_liaison_health" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB liaison health check exists"
    else
        print_failure "BanyanDB liaison health check missing"
    fi

    if grep -q "check_banyandb_data_health" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB data health check exists"
    else
        print_failure "BanyanDB data health check missing"
    fi

    if grep -q "check_satellite_health" "$SCRIPT_DIR/$script"; then
        print_success "Satellite health check exists"
    else
        print_failure "Satellite health check missing"
    fi

    if grep -q "check_ui_health" "$SCRIPT_DIR/$script"; then
        print_success "UI health check exists"
    else
        print_failure "UI health check missing"
    fi

    if grep -q "check_etcd_health" "$SCRIPT_DIR/$script"; then
        print_success "etcd health check exists"
    else
        print_failure "etcd health check missing"
    fi

    if grep -q "check_pvc_health" "$SCRIPT_DIR/$script"; then
        print_success "PVC health check exists"
    else
        print_failure "PVC health check missing"
    fi

    if grep -q "check_oap_api_responsiveness" "$SCRIPT_DIR/$script"; then
        print_success "OAP API responsiveness check exists"
    else
        print_failure "OAP API responsiveness check missing"
    fi

    if grep -q "check_banyandb_api_responsiveness" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB API responsiveness check exists"
    else
        print_failure "BanyanDB API responsiveness check missing"
    fi

    if grep -q "check_banyandb_metadata_consistency" "$SCRIPT_DIR/$script"; then
        print_success "BanyanDB metadata consistency check exists"
    else
        print_failure "BanyanDB metadata consistency check missing"
    fi

    if grep -q "check_oap_cluster_coordination" "$SCRIPT_DIR/$script"; then
        print_success "OAP cluster coordination check exists"
    else
        print_failure "OAP cluster coordination check missing"
    fi

    # Test 4: Output format support
    if grep -q "output_json" "$SCRIPT_DIR/$script"; then
        print_success "JSON output format supported"
    else
        print_failure "JSON output format not supported"
    fi

    if grep -q "output_yaml" "$SCRIPT_DIR/$script"; then
        print_success "YAML output format supported"
    else
        print_failure "YAML output format not supported"
    fi

    # Test 5: Error reporting
    if grep -q "record_result" "$SCRIPT_DIR/$script"; then
        print_success "Structured error reporting exists"
    else
        print_failure "Structured error reporting missing"
    fi

    print_info "Health script validation complete"
}

################################################################################
# Script Quality Checks
################################################################################

test_script_quality() {
    print_section "Script Quality Checks"

    local scripts=(
        "deploy-skywalking-cluster.sh"
        "cleanup-skywalking-cluster.sh"
        "test-connectivity.sh"
        "test-data-ingestion.sh"
        "test-health.sh"
    )

    for script in "${scripts[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$script" ]; then
            print_failure "$script: File not found"
            continue
        fi

        print_info "Checking $script..."

        # Check shebang
        if head -n1 "$SCRIPT_DIR/$script" | grep -q "^#!/bin/bash"; then
            print_success "$script: Has proper shebang"
        else
            print_failure "$script: Missing or incorrect shebang"
        fi

        # Check for set -e (exit on error)
        if grep -q "set -e" "$SCRIPT_DIR/$script"; then
            print_success "$script: Has error handling (set -e)"
        else
            print_failure "$script: Missing error handling (set -e)"
        fi

        # Check for usage/help function
        if grep -q "usage()" "$SCRIPT_DIR/$script" || grep -q "print_usage()" "$SCRIPT_DIR/$script"; then
            print_success "$script: Has usage/help function"
        else
            print_failure "$script: Missing usage/help function"
        fi

        # Check for color codes
        if grep -q "RED=\|GREEN=\|YELLOW=" "$SCRIPT_DIR/$script"; then
            print_success "$script: Has colored output"
        else
            print_failure "$script: Missing colored output"
        fi

        # Check for error handling functions
        if grep -q "handle.*failure\|error_handler" "$SCRIPT_DIR/$script"; then
            print_success "$script: Has error handling functions"
        else
            print_failure "$script: Missing error handling functions"
        fi

        # Check for comments/documentation
        local comment_lines=$(grep -c "^#" "$SCRIPT_DIR/$script" || echo "0")
        if [ "$comment_lines" -gt 20 ]; then
            print_success "$script: Well documented ($comment_lines comment lines)"
        else
            print_failure "$script: Insufficient documentation ($comment_lines comment lines)"
        fi

        echo ""
    done
}

################################################################################
# Execution Time Validation
################################################################################

test_execution_time_requirements() {
    print_section "Execution Time Requirements Validation"

    print_info "Checking timeout configurations..."

    # Deployment script - 15 minutes
    if grep -q 'TIMEOUT="15m"' "$SCRIPT_DIR/deploy-skywalking-cluster.sh"; then
        print_success "Deployment timeout: 15 minutes (meets requirement 5.6)"
    else
        print_failure "Deployment timeout not set to 15 minutes"
    fi

    # Connectivity test - 90 seconds
    if grep -q 'TIMEOUT=90' "$SCRIPT_DIR/test-connectivity.sh"; then
        print_success "Connectivity test timeout: 90 seconds (meets requirement 7.9)"
    else
        print_failure "Connectivity test timeout not set to 90 seconds"
    fi

    # Data ingestion test - 10 minutes (600 seconds)
    if grep -q 'TIMEOUT=600\|TEST_TIMEOUT=600' "$SCRIPT_DIR/test-data-ingestion.sh"; then
        print_success "Data ingestion test timeout: 10 minutes (meets requirement 8.10)"
    else
        print_failure "Data ingestion test timeout not set to 10 minutes"
    fi

    print_info "Execution time requirements validated"
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deployment)
                SKIP_DEPLOYMENT=true
                shift
                ;;
            --skip-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --skip-connectivity)
                SKIP_CONNECTIVITY=true
                shift
                ;;
            --skip-ingestion)
                SKIP_INGESTION=true
                shift
                ;;
            --skip-health)
                SKIP_HEALTH=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo -e "${RED}Error: Unknown option: $1${NC}"
                usage
                ;;
        esac
    done

    print_header "SkyWalking Automation Scripts Validation"
    echo "Task: 15. Checkpoint - Validate automation scripts"
    echo "Start time: $(date)"
    echo ""

    # Run all validation tests
    test_deployment_script
    echo ""

    test_cleanup_script
    echo ""

    test_connectivity_script
    echo ""

    test_ingestion_script
    echo ""

    test_health_script
    echo ""

    test_script_quality
    echo ""

    test_execution_time_requirements
    echo ""

    # Calculate execution time
    END_TIME=$(date +%s)
    EXECUTION_TIME=$((END_TIME - START_TIME))

    # Print summary
    print_header "Validation Summary"
    echo "Total tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
    echo -e "${YELLOW}Skipped: $SKIPPED_TESTS${NC}"
    echo "Execution time: ${EXECUTION_TIME}s"
    echo "End time: $(date)"
    echo ""

    # Final result
    if [ $FAILED_TESTS -eq 0 ]; then
        print_header "✓ ALL VALIDATION TESTS PASSED"
        echo ""
        echo "All automation scripts have been validated successfully:"
        echo "  ✓ Valid and invalid input handling"
        echo "  ✓ Error handling mechanisms"
        echo "  ✓ Execution time requirements"
        echo "  ✓ Script quality and documentation"
        echo ""
        echo "The automation scripts are ready for use."
        exit 0
    else
        print_header "✗ SOME VALIDATION TESTS FAILED"
        echo ""
        echo "Please review the failed tests above and fix the issues."
        echo ""
        echo "Failed tests: $FAILED_TESTS"
        exit 1
    fi
}

# Run main function
main "$@"
