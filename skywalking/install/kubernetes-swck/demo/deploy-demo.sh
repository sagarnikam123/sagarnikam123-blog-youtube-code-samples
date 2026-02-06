#!/bin/bash
# =============================================================================
# Deploy Demo Application with SkyWalking Instrumentation
# =============================================================================

set -e

NAMESPACE="${NAMESPACE:-skywalking}"

GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

echo "=============================================="
echo "  SkyWalking Demo Deployment"
echo "=============================================="
echo ""

# Deploy simple demo (uses init container for agent)
log_info "Deploying instrumented demo application..."
kubectl apply -f simple-demo.yaml -n "$NAMESPACE"

log_info "Waiting for demo app to be ready..."
kubectl wait --for=condition=Available deployment/simple-demo -n "$NAMESPACE" --timeout=300s || {
    echo "Demo app taking longer to start, checking status..."
    kubectl get pods -n "$NAMESPACE" -l app=simple-demo
}

# Deploy load generator
log_info "Deploying load generator..."
kubectl apply -f load-generator.yaml -n "$NAMESPACE"

echo ""
log_info "Demo deployed! Waiting 30s for traces to appear..."
sleep 30

echo ""
echo "=============================================="
echo "  View Data in SkyWalking UI"
echo "=============================================="
echo ""
echo "1. Port forward the UI:"
echo "   kubectl port-forward svc/skywalking-ui-ui 8080:80 -n $NAMESPACE"
echo ""
echo "2. Open http://localhost:8080"
echo ""
echo "3. Navigate to:"
echo "   - General Service > Services: See 'simple-demo' service"
echo "   - Trace: View distributed traces"
echo "   - Topology: See service topology"
echo ""
echo "4. Check demo app logs for agent output:"
echo "   kubectl logs -n $NAMESPACE -l app=simple-demo -f"
echo ""
