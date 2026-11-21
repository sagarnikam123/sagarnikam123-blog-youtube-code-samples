#!/bin/bash

NAMESPACE="${NAMESPACE:-mimir-test}"

echo "========================================="
echo "Memberlist Communication Status"
echo "========================================="
echo ""

# Start kubectl proxy in background
kubectl proxy --port=8001 >/dev/null 2>&1 &
PROXY_PID=$!
sleep 2

# Cleanup function
cleanup() {
    kill $PROXY_PID 2>/dev/null
    wait $PROXY_PID 2>/dev/null
}
trap cleanup EXIT

PODS=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[] | select(.metadata.labels."app.kubernetes.io/component" != null) | .metadata.name')

for POD in $PODS; do
    COMPONENT=$(kubectl get pod -n "$NAMESPACE" "$POD" -o jsonpath='{.metadata.labels.app\.kubernetes\.io/component}')

    echo "📦 $POD ($COMPONENT)"

    # Access pod via kubectl proxy
    RESPONSE=$(curl -s "http://localhost:8001/api/v1/namespaces/$NAMESPACE/pods/$POD:8080/proxy/memberlist" 2>/dev/null)

    if [[ -n "$RESPONSE" ]]; then
        MEMBERS=$(echo "$RESPONSE" | grep -o "mimir-[a-z-]*-[0-9a-z]*" | sort -u | wc -l | tr -d ' ')
        ALIVE=$(echo "$RESPONSE" | grep -io "alive" | wc -l | tr -d ' ')

        echo "  ✅ Memberlist accessible"
        echo "  👥 Total members: $MEMBERS"
        echo "  💚 Alive members: $ALIVE"

        # Check for actual failed/suspect members (state != 0/alive)
        ISSUES=$(echo "$RESPONSE" | grep -E "<td>(1|2|3)</td>" | wc -l | tr -d ' ')
        if [ "$ISSUES" -gt 0 ]; then
            echo "  ⚠️  Issues: $ISSUES members not alive (suspect/dead/left)"
        fi
    else
        echo "  ❌ Memberlist endpoint not responding"
    fi
    echo ""
done

echo -e "\n========================================="
echo "Status Check Complete"
echo "========================================="
