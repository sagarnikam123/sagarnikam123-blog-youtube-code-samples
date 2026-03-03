#!/bin/bash
#
# Run Integration Tests for SkyWalking Cluster
#
# This script runs the complete integration test suite for SkyWalking cluster deployment.
# It includes tests for full deployment workflow, marketplace features, high availability,
# and data persistence.
#
# Usage:
#   ./run-integration-tests.sh [environment] [options]
#
# Arguments:
#   environment    Target environment (minikube, eks-dev, eks-prod) [default: minikube]
#
# Options:
#   --test-suite SUITE    Run specific test suite (full, marketplace, ha, persistence, all)
#   --parallel            Run tests in parallel (faster but uses more resources)
#   --verbose             Enable verbose output
#   --help                Display this help message
#
# Examples:
#   ./run-integration-tests.sh minikube
#   ./run-integration-tests.sh eks-dev --test-suite ha
#   ./run-integration-tests.sh minikube --test-suite all --verbose
#

set -e

# Default values
ENVIRONMENT="${1:-minikube}"
TEST_SUITE="all"
PARALLEL=false
VERBOSE=false

# Parse command line arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-suite)
            TEST_SUITE="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate environment
case $ENVIRONMENT in
    minikube|eks-dev|eks-prod)
        ;;
    *)
        echo "Error: Invalid environment '$ENVIRONMENT'"
        echo "Valid environments: minikube, eks-dev, eks-prod"
        exit 1
        ;;
esac

# Validate test suite
case $TEST_SUITE in
    full|marketplace|ha|persistence|all)
        ;;
    *)
        echo "Error: Invalid test suite '$TEST_SUITE'"
        echo "Valid test suites: full, marketplace, ha, persistence, all"
        exit 1
        ;;
esac

echo "========================================="
echo "SkyWalking Integration Test Suite"
echo "========================================="
echo "Environment: $ENVIRONMENT"
echo "Test Suite: $TEST_SUITE"
echo "Parallel: $PARALLEL"
echo "Verbose: $VERBOSE"
echo "========================================="
echo ""

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS="-v --tb=short --environment=$ENVIRONMENT"

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -s"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

# Select test files based on suite
case $TEST_SUITE in
    full)
        TEST_FILES="integration_test_full_deployment.py"
        ;;
    marketplace)
        TEST_FILES="integration_test_marketplace_features.py"
        ;;
    ha)
        TEST_FILES="integration_test_high_availability.py"
        ;;
    persistence)
        TEST_FILES="integration_test_data_persistence.py"
        ;;
    all)
        TEST_FILES="integration_test_*.py"
        ;;
esac

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found. Please install requirements:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl."
    exit 1
fi

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster."
    echo "Please ensure your cluster is running and kubectl is configured."
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Run tests
echo "Running integration tests..."
echo "Command: $PYTEST_CMD $PYTEST_ARGS $TEST_FILES"
echo ""

START_TIME=$(date +%s)

# Run pytest with selected tests
$PYTEST_CMD $PYTEST_ARGS $TEST_FILES

EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "========================================="
echo "Integration Test Results"
echo "========================================="
echo "Duration: ${DURATION}s"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Status: ✓ ALL TESTS PASSED"
else
    echo "Status: ✗ SOME TESTS FAILED"
fi

echo "========================================="

exit $EXIT_CODE
