#!/bin/bash

# SkyWalking Full Validation Script
# This script runs all validation tests in sequence and generates a comprehensive report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-minikube}
NAMESPACE="skywalking"
REPORT_FILE="validation-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).md"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2

    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✓ ${message}${NC}"
    elif [ "$status" == "FAIL" ]; then
        echo -e "${RED}✗ ${message}${NC}"
    else
        echo -e "${YELLOW}⚠ ${message}${NC}"
    fi
}

# Function to run test and capture result
run_test() {
    local test_name=$1
    local test_script=$2

    echo ""
    echo "========================================="
    echo "Running: $test_name"
    echo "========================================="

    if [ -f "$test_script" ]; then
        if bash "$test_script"; then
            print_status "PASS" "$test_name"
            echo "- [x] $test_name: PASS" >> "$REPORT_FILE"
            return 0
        else
            print_status "FAIL" "$test_name"
            echo "- [ ] $test_name: FAIL" >> "$REPORT_FILE"
            return 1
        fi
    else
        print_status "WARN" "$test_name - Script not found: $test_script"
        echo "- [ ] $test_name: SKIPPED (script not found)" >> "$REPORT_FILE"
        return 2
    fi
}

# Initialize report
cat > "$REPORT_FILE" << EOF
# SkyWalking Full Validation Report

**Environment**: $ENVIRONMENT
**Date**: $(date)
**Kubernetes Version**: $(kubectl version --short 2>/dev/null || echo "N/A")
**Helm Version**: $(helm version --short 2>/dev/null || echo "N/A")

## Deployment Status

EOF

# Check if cluster is accessible
echo "Checking cluster accessibility..."
if ! kubectl cluster-info &>/dev/null; then
    print_status "FAIL" "Kubernetes cluster not accessible"
    echo "❌ **ERROR**: Kubernetes cluster not accessible" >> "$REPORT_FILE"
    echo ""
    echo "Please ensure:"
    echo "  1. Kubernetes cluster is running"
    echo "  2. kubectl is configured correctly"
    echo "  3. You have access to the cluster"
    exit 1
fi

print_status "PASS" "Kubernetes cluster accessible"
echo "✓ Kubernetes cluster accessible" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check if SkyWalking is deployed
echo "Checking SkyWalking deployment..."
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    print_status "FAIL" "SkyWalking namespace not found"
    echo "❌ **ERROR**: SkyWalking namespace '$NAMESPACE' not found" >> "$REPORT_FILE"
    echo ""
    echo "Please deploy SkyWalking first:"
    echo "  ./deploy-skywalking-cluster.sh $ENVIRONMENT"
    exit 1
fi

print_status "PASS" "SkyWalking namespace exists"
echo "✓ SkyWalking namespace exists" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Get pod status
echo "## Pod Status" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
kubectl get pods -n "$NAMESPACE" >> "$REPORT_FILE" 2>&1
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Get PVC status
echo "## PVC Status" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
kubectl get pvc -n "$NAMESPACE" >> "$REPORT_FILE" 2>&1
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Run validation tests
echo "## Validation Test Results" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test 1: Health Check
run_test "Health Check" "./test-health.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 2: Connectivity Check
run_test "Connectivity Check" "./test-connectivity.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 3: Data Ingestion
run_test "Data Ingestion Test" "./test-data-ingestion.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 4: Self-Observability
run_test "Self-Observability Test" "./test-self-observability.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 5: General Services Monitoring
run_test "General Services Monitoring" "./test-general-services.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 6: Kubernetes Monitoring
run_test "Kubernetes Monitoring" "./test-kubernetes-monitoring.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 7: Message Queue Monitoring
run_test "Message Queue Monitoring" "./test-mq-monitoring.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Test 8: Visualization
run_test "Visualization Test" "./test-visualization.sh"
result=$?
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $result -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ $result -eq 1 ]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
fi

# Generate summary
echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- **Total Tests**: $TOTAL_TESTS" >> "$REPORT_FILE"
echo "- **Passed**: $PASSED_TESTS" >> "$REPORT_FILE"
echo "- **Failed**: $FAILED_TESTS" >> "$REPORT_FILE"
echo "- **Skipped**: $SKIPPED_TESTS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "- **Success Rate**: ${SUCCESS_RATE}%" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Add marketplace features section
echo "## Marketplace Features Verification" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Please verify the following features manually in the SkyWalking UI:" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- [ ] Self-Observability (OAP Server, BanyanDB, Satellite)" >> "$REPORT_FILE"
echo "- [ ] Visual Database (MySQL metrics)" >> "$REPORT_FILE"
echo "- [ ] Visual Cache (Redis metrics)" >> "$REPORT_FILE"
echo "- [ ] Visual MQ (RabbitMQ metrics)" >> "$REPORT_FILE"
echo "- [ ] Kubernetes Monitoring (cluster and pod metrics)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Add access instructions
echo "## Access Instructions" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "To access the SkyWalking UI:" >> "$REPORT_FILE"
echo '```bash' >> "$REPORT_FILE"
echo "kubectl port-forward -n $NAMESPACE svc/skywalking-ui 8080:8080" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Then open: http://localhost:8080" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Add recommendations section
echo "## Recommendations" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
if [ $FAILED_TESTS -gt 0 ]; then
    echo "⚠️ **Action Required**: Some tests failed. Please review the failures above and:" >> "$REPORT_FILE"
    echo "1. Check pod logs for errors" >> "$REPORT_FILE"
    echo "2. Verify configuration settings" >> "$REPORT_FILE"
    echo "3. Review troubleshooting guide: ../docs/TROUBLESHOOTING.md" >> "$REPORT_FILE"
else
    echo "✅ All tests passed! The deployment is ready for production use." >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# Print final summary
echo ""
echo "========================================="
echo "Validation Complete"
echo "========================================="
echo ""
echo "Summary:"
echo "  Total Tests: $TOTAL_TESTS"
echo "  Passed: $PASSED_TESTS"
echo "  Failed: $FAILED_TESTS"
echo "  Skipped: $SKIPPED_TESTS"
echo ""
echo "Report saved to: $REPORT_FILE"
echo ""

if [ $FAILED_TESTS -gt 0 ]; then
    print_status "FAIL" "Validation completed with failures"
    exit 1
else
    print_status "PASS" "Validation completed successfully"
    exit 0
fi
