#!/bin/bash

# Quick Validation Script for SkyWalking Cluster
# This script performs essential validation checks for Task 26 final checkpoint

set -e

NAMESPACE="${NAMESPACE:-skywalking}"
ENVIRONMENT="${1:-minikube}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SkyWalking Cluster Quick Validation${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test result
print_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} ${test_name}: ${GREEN}PASS${NC}"
        ((PASSED++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}✗${NC} ${test_name}: ${RED}FAIL${NC} - ${message}"
        ((FAILED++))
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} ${test_name}: ${YELLOW}WARNING${NC} - ${message}"
        ((WARNINGS++))
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${BLUE}Phase 1: Prerequisites Check${NC}"
echo "-----------------------------------"

# Check kubectl
if command_exists kubectl; then
    print_result "kubectl installed" "PASS"
else
    print_result "kubectl installed" "FAIL" "kubectl not found"
fi

# Check helm
if command_exists helm; then
    print_result "helm installed" "PASS"
else
    print_result "helm installed" "FAIL" "helm not found"
fi

# Check cluster connectivity
if kubectl cluster-info >/dev/null 2>&1; then
    print_result "Cluster connectivity" "PASS"
else
    print_result "Cluster connectivity" "FAIL" "Cannot connect to cluster"
    exit 1
fi

echo ""
echo -e "${BLUE}Phase 2: Deployment Status${NC}"
echo "-----------------------------------"

# Check namespace exists
if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    print_result "Namespace exists" "PASS"
else
    print_result "Namespace exists" "FAIL" "Namespace $NAMESPACE not found"
    echo -e "${YELLOW}Hint: Run ./deploy-skywalking-cluster.sh ${ENVIRONMENT}${NC}"
    exit 1
fi

# Check Helm release
if helm list -n "$NAMESPACE" | grep -q skywalking; then
    print_result "Helm release installed" "PASS"
else
    print_result "Helm release installed" "FAIL" "SkyWalking Helm release not found"
fi

echo ""
echo -e "${BLUE}Phase 3: Component Health${NC}"
echo "-----------------------------------"

# Function to check pod status
check_pods() {
    local component="$1"
    local expected_replicas="$2"

    local ready_pods=$(kubectl get pods -n "$NAMESPACE" -l "app=$component" --no-headers 2>/dev/null | grep -c "Running" || echo "0")

    if [ "$ready_pods" -ge "$expected_replicas" ]; then
        print_result "$component pods" "PASS"
    elif [ "$ready_pods" -gt 0 ]; then
        print_result "$component pods" "WARN" "Only $ready_pods/$expected_replicas pods running"
    else
        print_result "$component pods" "FAIL" "No pods running"
    fi
}

# Check OAP Server pods
if [ "$ENVIRONMENT" = "minikube" ]; then
    check_pods "oap" 2
else
    check_pods "oap" 3
fi

# Check BanyanDB liaison pods
check_pods "banyandb-liaison" 2

# Check BanyanDB data pods
if [ "$ENVIRONMENT" = "minikube" ]; then
    check_pods "banyandb-data" 2
else
    check_pods "banyandb-data" 3
fi

# Check Satellite pods
check_pods "satellite" 2

# Check UI pods
check_pods "ui" 2

# Check etcd pods
if [ "$ENVIRONMENT" = "minikube" ]; then
    check_pods "etcd" 1
else
    check_pods "etcd" 3
fi

echo ""
echo -e "${BLUE}Phase 4: Storage Status${NC}"
echo "-----------------------------------"

# Check PVCs
total_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l || echo "0")
bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | grep -c "Bound" || echo "0")

if [ "$total_pvcs" -eq "$bound_pvcs" ] && [ "$total_pvcs" -gt 0 ]; then
    print_result "PVCs bound" "PASS"
else
    print_result "PVCs bound" "WARN" "$bound_pvcs/$total_pvcs PVCs bound"
fi

echo ""
echo -e "${BLUE}Phase 5: Service Endpoints${NC}"
echo "-----------------------------------"

# Function to check service exists
check_service() {
    local service_name="$1"

    if kubectl get svc -n "$NAMESPACE" "$service_name" >/dev/null 2>&1; then
        print_result "$service_name service" "PASS"
    else
        print_result "$service_name service" "FAIL" "Service not found"
    fi
}

check_service "skywalking-oap"
check_service "skywalking-ui"
check_service "skywalking-satellite"
check_service "skywalking-banyandb-liaison"

echo ""
echo -e "${BLUE}Phase 6: Configuration Files${NC}"
echo "-----------------------------------"

# Check Helm values files exist
if [ -f "../helm-values/${ENVIRONMENT}-values.yaml" ]; then
    print_result "Helm values file" "PASS"
else
    print_result "Helm values file" "FAIL" "${ENVIRONMENT}-values.yaml not found"
fi

# Check storage class file for EKS
if [ "$ENVIRONMENT" != "minikube" ]; then
    if [ -f "../helm-values/eks-storage-class.yaml" ]; then
        print_result "Storage class file" "PASS"
    else
        print_result "Storage class file" "FAIL" "eks-storage-class.yaml not found"
    fi
fi

echo ""
echo -e "${BLUE}Phase 7: Validation Scripts${NC}"
echo "-----------------------------------"

# Check validation scripts exist
scripts=(
    "test-health.sh"
    "test-connectivity.sh"
    "test-data-ingestion.sh"
    "test-self-observability.sh"
    "test-general-services.sh"
    "test-kubernetes-monitoring.sh"
    "test-mq-monitoring.sh"
    "test-visualization.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        print_result "$script" "PASS"
    elif [ -f "$script" ]; then
        print_result "$script" "WARN" "Not executable"
    else
        print_result "$script" "FAIL" "Not found"
    fi
done

echo ""
echo -e "${BLUE}Phase 8: Documentation${NC}"
echo "-----------------------------------"

# Check documentation files exist
docs=(
    "../README.md"
    "../docs/CONFIGURATION.md"
    "../docs/TROUBLESHOOTING.md"
    "../docs/APPLICATION-INTEGRATION.md"
    "../docs/TESTING.md"
    "../docs/RESOURCE-SIZING.md"
    "../docs/UPGRADE-ROLLBACK.md"
    "../docs/MARKETPLACE-FEATURES.md"
    "../docs/OTEL-COLLECTOR.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        print_result "$(basename $doc)" "PASS"
    else
        print_result "$(basename $doc)" "FAIL" "Not found"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Quick validation completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run full validation: ./run-full-validation.sh"
    echo "2. Test marketplace features via UI"
    echo "3. Run property-based tests (optional): cd ../tests && ./run-property-tests.sh"
    echo "4. Run integration tests (optional): cd ../tests && ./run-integration-tests.sh"
    exit 0
else
    echo -e "${RED}✗ Quick validation found issues that need attention${NC}"
    echo ""
    echo "Please review the failed checks above and:"
    echo "1. Ensure deployment completed successfully"
    echo "2. Check pod logs for errors: kubectl logs -n $NAMESPACE <pod-name>"
    echo "3. Review troubleshooting guide: ../docs/TROUBLESHOOTING.md"
    exit 1
fi
