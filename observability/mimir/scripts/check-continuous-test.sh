#!/bin/bash

# Script to check Mimir continuous-test health
# Usage: ./check-continuous-test.sh <namespace>

NAMESPACE=${1:-mimir-test}

echo "========================================="
echo "Mimir Continuous Test Health Check"
echo "========================================="
echo ""

# Get continuous-test pod
POD=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=continuous-test -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
    echo "❌ No continuous-test pod found in namespace: $NAMESPACE"
    exit 1
fi

echo "📦 Pod: $POD"
echo ""

# Check pod status
STATUS=$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
READY=$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].ready}')
RESTARTS=$(kubectl get pod "$POD" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}')

echo "📊 Pod Status"
echo "  Status: $STATUS"
echo "  Ready: $READY"
echo "  Restarts: $RESTARTS"
echo ""

# Get recent logs
echo "📝 Analyzing Recent Test Results (last 100 lines)..."
LOGS=$(kubectl logs -n "$NAMESPACE" "$POD" --tail=100 2>/dev/null)

if [ -z "$LOGS" ]; then
    echo "❌ Failed to fetch logs from continuous-test pod"
    exit 1
fi

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="

# Count succeeded and failed tests
SUCCEEDED=$(echo "$LOGS" | grep -c "succeeded")
FAILED=$(echo "$LOGS" | grep -c "failed" | grep -v "succeeded" || echo "0")
RANGE_CHECKS=$(echo "$LOGS" | grep -c "Range query result check succeeded")
INSTANT_CHECKS=$(echo "$LOGS" | grep -c "Instant query result check succeeded")

echo "  Range Query Checks: $RANGE_CHECKS succeeded"
echo "  Instant Query Checks: $INSTANT_CHECKS succeeded"
echo "  Total Succeeded: $SUCCEEDED"
echo ""

echo "========================================="
echo "Recent Test Activity"
echo "========================================="

# Show last 5 test results
echo "$LOGS" | grep "succeeded" | tail -5 | while read -r line; do
    TEST_TYPE=$(echo "$line" | sed -n 's/.*msg="\([^"]*\)".*/\1/p')
    echo "  ✅ $TEST_TYPE"
done

echo ""
echo "========================================="
echo "Overall Health"
echo "========================================="

if [ "$STATUS" = "Running" ] && [ "$READY" = "true" ] && [ "$SUCCEEDED" -gt 0 ]; then
    echo "✅ Continuous-test is HEALTHY"
    echo "   - Pod running and ready"
    echo "   - Tests executing successfully"
    echo "   - $SUCCEEDED successful test checks in recent logs"
    exit 0
else
    echo "⚠️  Continuous-test has issues"
    [ "$STATUS" != "Running" ] && echo "   - Pod not running"
    [ "$READY" != "true" ] && echo "   - Pod not ready"
    [ "$SUCCEEDED" -eq 0 ] && echo "   - No successful tests found"
    exit 1
fi
