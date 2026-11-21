#!/bin/bash

NAMESPACE="${NAMESPACE:-mimir-test}"
LINES="${LINES:-50}"

echo "========================================="
echo "Analyzing Pod Logs for Errors"
echo "========================================="

PODS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}')

for POD in $PODS; do
    echo -e "\n📦 Pod: $POD"

    LOGS=$(kubectl logs -n "$NAMESPACE" "$POD" --tail="$LINES" 2>&1)

    # Check for errors
    ERRORS=$(echo "$LOGS" | grep -iE "error|failed|failure|fatal|panic|exception" | grep -v "0 error" | head -10)

    if [[ -n "$ERRORS" ]]; then
        echo "  ❌ ERRORS FOUND:"
        echo "$ERRORS" | sed 's/^/    /'
    fi

    # Check for warnings
    WARNINGS=$(echo "$LOGS" | grep -iE "warn|warning" | head -5)

    if [[ -n "$WARNINGS" ]]; then
        echo "  ⚠️  WARNINGS:"
        echo "$WARNINGS" | sed 's/^/    /'
    fi

    if [[ -z "$ERRORS" ]] && [[ -z "$WARNINGS" ]]; then
        echo "  ✅ No errors or warnings"
    fi
done

echo -e "\n========================================="
echo "Analysis Complete"
echo "========================================="
