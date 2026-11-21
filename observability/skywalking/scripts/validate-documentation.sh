#!/bin/bash

# Documentation Validation Script
# Validates completeness and accuracy of SkyWalking documentation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="../docs"
EXAMPLES_DIR="../examples"
HELM_VALUES_DIR="../helm-values"
REPORT_FILE="documentation-validation-$(date +%Y%m%d-%H%M%S).md"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

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

# Function to check file exists
check_file() {
    local file=$1
    local description=$2

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ -f "$file" ]; then
        print_status "PASS" "$description"
        echo "- [x] $description" >> "$REPORT_FILE"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        print_status "FAIL" "$description - File not found: $file"
        echo "- [ ] $description - **Missing**: $file" >> "$REPORT_FILE"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check content in file
check_content() {
    local file=$1
    local pattern=$2
    local description=$3

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ ! -f "$file" ]; then
        print_status "FAIL" "$description - File not found: $file"
        echo "- [ ] $description - **File not found**: $file" >> "$REPORT_FILE"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi

    if grep -q "$pattern" "$file"; then
        print_status "PASS" "$description"
        echo "- [x] $description" >> "$REPORT_FILE"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        print_status "FAIL" "$description - Pattern not found in $file"
        echo "- [ ] $description - **Pattern not found**: $pattern" >> "$REPORT_FILE"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Initialize report
cat > "$REPORT_FILE" << EOF
# Documentation Validation Report

**Date**: $(date)

## Validation Results

EOF

echo "========================================="
echo "SkyWalking Documentation Validation"
echo "========================================="
echo ""

# Check Main README
echo "Checking Main README..."
echo "### Main README" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_file "../README.md" "Main README exists"
check_content "../README.md" "Architecture" "Architecture section present"
check_content "../README.md" "Prerequisites" "Prerequisites section present"
check_content "../README.md" "Installation" "Installation section present"
check_content "../README.md" "Quick Start" "Quick start guide present"

echo "" >> "$REPORT_FILE"

# Check Documentation Files
echo ""
echo "Checking Documentation Files..."
echo "### Documentation Files" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_file "$DOCS_DIR/README.md" "Documentation index"
check_file "$DOCS_DIR/CONFIGURATION.md" "Configuration documentation"
check_file "$DOCS_DIR/TROUBLESHOOTING.md" "Troubleshooting guide"
check_file "$DOCS_DIR/APPLICATION-INTEGRATION.md" "Application integration guide"
check_file "$DOCS_DIR/TESTING.md" "Testing procedures"
check_file "$DOCS_DIR/RESOURCE-SIZING.md" "Resource sizing guidelines"
check_file "$DOCS_DIR/UPGRADE-ROLLBACK.md" "Upgrade and rollback procedures"
check_file "$DOCS_DIR/MARKETPLACE-FEATURES.md" "Marketplace features documentation"
check_file "$DOCS_DIR/OTEL-COLLECTOR.md" "OTel Collector configuration"

echo "" >> "$REPORT_FILE"

# Check Helm Values Files
echo ""
echo "Checking Helm Values Files..."
echo "### Helm Values Files" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_file "$HELM_VALUES_DIR/base-values.yaml" "Base values template"
check_file "$HELM_VALUES_DIR/minikube-values.yaml" "Minikube configuration"
check_file "$HELM_VALUES_DIR/eks-values.yaml" "EKS configuration"
check_file "$HELM_VALUES_DIR/eks-storage-class.yaml" "EKS storage class"

echo "" >> "$REPORT_FILE"

# Check Example Files
echo ""
echo "Checking Example Files..."
echo "### Example Files" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_file "$EXAMPLES_DIR/swck-agent-injection.yaml" "SWCK agent injection example"
check_file "$EXAMPLES_DIR/otel-collector-general-services.yaml" "OTel Collector general services config"
check_file "$EXAMPLES_DIR/otel-collector-kubernetes.yaml" "OTel Collector Kubernetes config"
check_file "$EXAMPLES_DIR/otel-collector-message-queues.yaml" "OTel Collector message queues config"
check_file "$EXAMPLES_DIR/network-policies-complete.yaml" "Network policies example"
check_file "$EXAMPLES_DIR/servicemonitor-complete.yaml" "ServiceMonitor example"

echo "" >> "$REPORT_FILE"

# Check Scripts
echo ""
echo "Checking Scripts..."
echo "### Scripts" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_file "./deploy-skywalking-cluster.sh" "Deployment script"
check_file "./cleanup-skywalking-cluster.sh" "Cleanup script"
check_file "./test-health.sh" "Health check script"
check_file "./test-connectivity.sh" "Connectivity test script"
check_file "./test-data-ingestion.sh" "Data ingestion test script"
check_file "./test-self-observability.sh" "Self-observability test script"
check_file "./test-general-services.sh" "General services test script"
check_file "./test-kubernetes-monitoring.sh" "Kubernetes monitoring test script"
check_file "./test-mq-monitoring.sh" "Message queue monitoring test script"
check_file "./test-visualization.sh" "Visualization test script"

echo "" >> "$REPORT_FILE"

# Check Script Executability
echo ""
echo "Checking Script Permissions..."
echo "### Script Permissions" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

for script in deploy-skywalking-cluster.sh cleanup-skywalking-cluster.sh test-*.sh; do
    if [ -f "$script" ]; then
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ -x "$script" ]; then
            print_status "PASS" "$script is executable"
            echo "- [x] $script is executable" >> "$REPORT_FILE"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            print_status "FAIL" "$script is not executable"
            echo "- [ ] $script is not executable" >> "$REPORT_FILE"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    fi
done

echo "" >> "$REPORT_FILE"

# Check for broken internal links
echo ""
echo "Checking Internal Links..."
echo "### Internal Links" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

BROKEN_LINKS=0

find .. -name "*.md" -type f | while read -r file; do
    # Extract markdown links
    grep -oE '\[.*\]\([^)]+\)' "$file" 2>/dev/null | while read -r link; do
        url=$(echo "$link" | sed -E 's/.*\(([^)]+)\)/\1/')

        # Skip external URLs
        if [[ "$url" =~ ^https?:// ]]; then
            continue
        fi

        # Skip anchors
        if [[ "$url" =~ ^# ]]; then
            continue
        fi

        # Resolve relative path
        dir=$(dirname "$file")
        full_path="$dir/$url"

        # Normalize path
        full_path=$(cd "$dir" && cd "$(dirname "$url")" 2>/dev/null && pwd)/$(basename "$url") 2>/dev/null || echo "$full_path"

        if [[ ! -f "$full_path" && ! -d "$full_path" ]]; then
            echo "  ❌ Broken link in $file: $url"
            echo "- [ ] Broken link in $file: $url" >> "$REPORT_FILE"
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
        fi
    done
done

if [ $BROKEN_LINKS -eq 0 ]; then
    print_status "PASS" "No broken internal links found"
    echo "- [x] No broken internal links found" >> "$REPORT_FILE"
else
    print_status "FAIL" "Found $BROKEN_LINKS broken internal links"
fi

echo "" >> "$REPORT_FILE"

# Check Configuration Parameters Documentation
echo ""
echo "Checking Configuration Parameters..."
echo "### Configuration Parameters" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

check_content "$DOCS_DIR/CONFIGURATION.md" "oap" "OAP Server configuration documented"
check_content "$DOCS_DIR/CONFIGURATION.md" "banyandb" "BanyanDB configuration documented"
check_content "$DOCS_DIR/CONFIGURATION.md" "satellite" "Satellite configuration documented"
check_content "$DOCS_DIR/CONFIGURATION.md" "ui" "UI configuration documented"
check_content "$DOCS_DIR/CONFIGURATION.md" "etcd" "etcd configuration documented"

echo "" >> "$REPORT_FILE"

# Check Requirements Coverage
echo ""
echo "Checking Requirements Coverage..."
echo "### Requirements Coverage" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Check if key requirements are documented
check_content "$DOCS_DIR/TROUBLESHOOTING.md" "connectivity" "Connectivity troubleshooting documented"
check_content "$DOCS_DIR/TROUBLESHOOTING.md" "deployment" "Deployment troubleshooting documented"
check_content "$DOCS_DIR/APPLICATION-INTEGRATION.md" "SWCK" "SWCK Operator integration documented"
check_content "$DOCS_DIR/MARKETPLACE-FEATURES.md" "self-observability" "Self-observability documented"
check_content "$DOCS_DIR/MARKETPLACE-FEATURES.md" "Visual Database" "Visual Database documented"
check_content "$DOCS_DIR/MARKETPLACE-FEATURES.md" "Kubernetes" "Kubernetes monitoring documented"

echo "" >> "$REPORT_FILE"

# Generate Summary
echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "- **Total Checks**: $TOTAL_CHECKS" >> "$REPORT_FILE"
echo "- **Passed**: $PASSED_CHECKS" >> "$REPORT_FILE"
echo "- **Failed**: $FAILED_CHECKS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $TOTAL_CHECKS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo "- **Success Rate**: ${SUCCESS_RATE}%" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Add recommendations
echo "## Recommendations" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $FAILED_CHECKS -gt 0 ]; then
    echo "⚠️ **Action Required**: Some documentation checks failed. Please:" >> "$REPORT_FILE"
    echo "1. Create missing documentation files" >> "$REPORT_FILE"
    echo "2. Add missing content sections" >> "$REPORT_FILE"
    echo "3. Fix broken links" >> "$REPORT_FILE"
    echo "4. Make scripts executable: \`chmod +x <script>\`" >> "$REPORT_FILE"
else
    echo "✅ All documentation checks passed!" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Print final summary
echo ""
echo "========================================="
echo "Documentation Validation Complete"
echo "========================================="
echo ""
echo "Summary:"
echo "  Total Checks: $TOTAL_CHECKS"
echo "  Passed: $PASSED_CHECKS"
echo "  Failed: $FAILED_CHECKS"
echo ""
echo "Report saved to: $REPORT_FILE"
echo ""

if [ $FAILED_CHECKS -gt 0 ]; then
    print_status "FAIL" "Documentation validation completed with failures"
    exit 1
else
    print_status "PASS" "Documentation validation completed successfully"
    exit 0
fi
