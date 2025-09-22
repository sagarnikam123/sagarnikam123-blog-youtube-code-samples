#!/bin/bash
set -e

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🔍 Loki Configuration Validation Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Validates all Loki component configurations using Loki's built-in"
    echo "  dry-run validation. Ensures configurations are syntactically correct"
    echo "  and compatible with the target Loki version."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • Extract current Loki version from deployment script"
    echo "  • Validate each component configuration using Docker"
    echo "  • Report validation results and summary"
    echo "  • Exit with error code if any validation fails"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./scripts/validate-loki-configs.sh        # Validate all configs"
    echo "  ./scripts/validate-loki-configs.sh --help # Show this help"
    echo ""
    echo "📋 VALIDATED COMPONENTS:"
    echo "  • distributor     • ingester       • querier"
    echo "  • query-frontend  • query-scheduler • compactor"
    echo "  • ruler          • index-gateway"
    echo ""
    echo "📦 REQUIREMENTS:"
    echo "  • Docker installed and running"
    echo "  • Loki configuration files in k8s/loki/configs/"
    echo "  • run-on-minikube.sh with LOKI_VERSION defined"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Pre-deployment configuration validation"
    echo "  • Troubleshooting configuration issues"
    echo "  • CI/CD pipeline validation steps"
    echo "  • Development configuration testing"
    exit 0
fi

# Extract Loki version from deployment script
LOKI_VERSION=$(grep "^export LOKI_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)

echo "🔍 Validating Loki ${LOKI_VERSION} Configurations"

# Components to validate
COMPONENTS=(
    "distributor"
    "ingester"
    "querier"
    "query-frontend"
    "query-scheduler"
    "compactor"
    "ruler"
    "index-gateway"
)

echo "📋 Using Loki's built-in dry-run validation..."
echo ""

VALID_COUNT=0
TOTAL_COUNT=${#COMPONENTS[@]}

for component in "${COMPONENTS[@]}"; do
    echo "Validating $component..."
    
    if docker run --rm -v "$(pwd)/k8s/loki/configs:/config" grafana/loki:${LOKI_VERSION} \
        -config.file="/config/${component}.yaml" -verify-config -target="$component" 2>/dev/null; then
        echo "   ✅ $component config is valid"
        VALID_COUNT=$((VALID_COUNT + 1))
    else
        echo "   ❌ $component config has errors"
        echo "   Running detailed validation:"
        docker run --rm -v "$(pwd)/k8s/loki/configs:/config" grafana/loki:${LOKI_VERSION} \
            -config.file="/config/${component}.yaml" -verify-config -target="$component"
    fi
    echo ""
done

echo "📊 Validation Summary:"
echo "   Valid configs: $VALID_COUNT/$TOTAL_COUNT"

if [[ $VALID_COUNT -eq $TOTAL_COUNT ]]; then
    echo "   🎉 All configurations are valid!"
    echo "   ✅ Ready for deployment"
    exit 0
else
    echo "   ⚠️  Some configurations need fixing"
    exit 1
fi