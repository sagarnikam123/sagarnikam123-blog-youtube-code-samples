#!/bin/bash
# Removed set -e to prevent halting on namespace deletion

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🧹 Resource Cleanup Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Sequential cleanup of all Loki distributed microservices resources."
    echo "  Safely removes deployments, services, storage, and configurations"
    echo "  with proper error handling and cleanup verification."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • Stop any running port forwards"
    echo "  • Delete Loki components in proper order"
    echo "  • Remove supporting services and storage"
    echo "  • Clean up configurations and secrets"
    echo "  • Force delete stuck resources if needed"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./scripts/cleanup.sh        # Clean up all resources"
    echo "  ./scripts/cleanup.sh --help # Show this help"
    echo ""
    echo "🧹 CLEANUP ORDER:"
    echo "  1. Port forwards           2. Loki deployments"
    echo "  3. Fluent Bit DaemonSet    4. Grafana & Prometheus"
    echo "  5. MinIO & storage         6. Services & ConfigMaps"
    echo "  7. Secrets & namespace     8. Stuck pod cleanup"
    echo ""
    echo "⚠️  SAFETY FEATURES:"
    echo "  • Graceful deletion with timeouts"
    echo "  • Error handling for missing resources"
    echo "  • Force deletion for stuck pods"
    echo "  • Verification commands provided"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Complete environment cleanup"
    echo "  • Preparing for fresh deployment"
    echo "  • Troubleshooting stuck resources"
    echo "  • Development environment reset"
    echo ""
    echo "📋 VERIFICATION:"
    echo "  After cleanup, run these commands to verify:"
    echo "  • kubectl get namespaces | grep loki"
    echo "  • kubectl get pv | grep loki"
    exit 0
fi

# Extract Loki version from deployment script
LOKI_VERSION=$(grep "^export LOKI_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2 2>/dev/null || echo "3.5.x")

echo "🧹 Cleaning up Loki ${LOKI_VERSION} Distributed Microservices Deployment"

# Stop any port forwards
echo "🔌 Stopping port forwards..."
pkill -f "kubectl port-forward" 2>/dev/null || true

# Delete components using directory structure
echo "🔍 Deleting Loki components..."
kubectl delete -f k8s/loki/deployments/ --ignore-not-found=true

echo "📝 Deleting Fluent Bit..."
kubectl delete -f k8s/fluent-bit/ --ignore-not-found=true

echo "📊 Deleting Grafana..."
kubectl delete -f k8s/grafana/ --ignore-not-found=true

echo "📈 Deleting Prometheus..."
kubectl delete -f k8s/prometheus/ --ignore-not-found=true

echo "🗄️  Deleting MinIO..."
kubectl delete -f k8s/minio/ --ignore-not-found=true

# Delete Services (already handled by component deletion above)
echo "🌐 Services deleted with components..."

# Delete ConfigMaps (Loki configs are created dynamically, others deleted with components)
echo "⚙️  Deleting Loki ConfigMaps..."
kubectl delete configmap distributor-config ingester-config querier-config query-frontend-config query-scheduler-config compactor-config ruler-config index-gateway-config -n loki --ignore-not-found=true

# Delete Secrets
echo "🔐 Deleting secrets..."
kubectl delete secret minio-creds -n loki --ignore-not-found=true

# Force delete any stuck pods
echo "🔨 Force deleting any stuck pods..."
kubectl delete pods --all -n loki --force --grace-period=0 2>/dev/null || true

# Delete PVCs (already handled by component deletion above)
echo "💾 Storage deleted with components..."

# Delete namespace
echo "🗑️  Deleting namespace..."
kubectl delete namespace loki --ignore-not-found=true --timeout=30s || {
    echo "⚠️  Namespace deletion timed out, forcing cleanup..."
    kubectl delete namespace loki --force --grace-period=0 2>/dev/null || true
}

# Clean up any dangling resources
echo "🧽 Cleaning up any remaining resources..."
kubectl delete pv --selector=app=loki --ignore-not-found=true 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📋 Verification Commands:"
echo "  kubectl get namespaces | grep loki"
echo "  kubectl get pv | grep loki"
echo ""
echo "🔄 To redeploy:"
echo "  ./run-on-minikube.sh"