#!/bin/bash
set -e

echo "🔍 Validating Loki 3.5.x Configurations"

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
    
    if docker run --rm -v "$(pwd)/config:/config" grafana/loki:3.5.5 \
        -config.file="/config/${component}.yaml" -verify-config -target="$component" 2>/dev/null; then
        echo "   ✅ $component config is valid"
        VALID_COUNT=$((VALID_COUNT + 1))
    else
        echo "   ❌ $component config has errors"
        echo "   Running detailed validation:"
        docker run --rm -v "$(pwd)/config:/config" grafana/loki:3.5.5 \
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