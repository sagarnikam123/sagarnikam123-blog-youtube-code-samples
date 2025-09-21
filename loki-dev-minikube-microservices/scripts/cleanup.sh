#!/bin/bash
set -e

echo "🧹 Cleaning up Loki 3.5.x Distributed Microservices Deployment"

# Stop any port forwards
echo "🔌 Stopping port forwards..."
pkill -f "kubectl port-forward" 2>/dev/null || true

# Delete Fluent Bit DaemonSet
echo "📝 Deleting Fluent Bit..."
kubectl delete daemonset fluent-bit -n loki --ignore-not-found=true

# Delete Loki component deployments
echo "🔧 Deleting Loki deployments..."
kubectl delete deployment loki-distributor -n loki --ignore-not-found=true
kubectl delete deployment loki-querier -n loki --ignore-not-found=true
kubectl delete deployment loki-query-frontend -n loki --ignore-not-found=true
kubectl delete deployment loki-query-scheduler -n loki --ignore-not-found=true
kubectl delete deployment loki-compactor -n loki --ignore-not-found=true
kubectl delete deployment loki-ruler -n loki --ignore-not-found=true
kubectl delete deployment loki-index-gateway -n loki --ignore-not-found=true

# Delete StatefulSet
echo "📊 Deleting ingester StatefulSet..."
kubectl delete statefulset loki-ingester -n loki --ignore-not-found=true

# Delete MinIO deployment
echo "🗄️  Deleting MinIO..."
kubectl delete deployment minio -n loki --ignore-not-found=true

# Delete Services
echo "🌐 Deleting services..."
kubectl delete service distributor -n loki --ignore-not-found=true
kubectl delete service ingester -n loki --ignore-not-found=true
kubectl delete service querier -n loki --ignore-not-found=true
kubectl delete service query-frontend -n loki --ignore-not-found=true
kubectl delete service query-scheduler -n loki --ignore-not-found=true
kubectl delete service compactor -n loki --ignore-not-found=true
kubectl delete service ruler -n loki --ignore-not-found=true
kubectl delete service index-gateway -n loki --ignore-not-found=true
kubectl delete service minio -n loki --ignore-not-found=true

# Delete ConfigMaps
echo "⚙️  Deleting ConfigMaps..."
kubectl delete configmap distributor-config -n loki --ignore-not-found=true
kubectl delete configmap ingester-config -n loki --ignore-not-found=true
kubectl delete configmap querier-config -n loki --ignore-not-found=true
kubectl delete configmap query-frontend-config -n loki --ignore-not-found=true
kubectl delete configmap query-scheduler-config -n loki --ignore-not-found=true
kubectl delete configmap compactor-config -n loki --ignore-not-found=true
kubectl delete configmap ruler-config -n loki --ignore-not-found=true
kubectl delete configmap index-gateway-config -n loki --ignore-not-found=true
kubectl delete configmap fluent-bit-config -n loki --ignore-not-found=true

# Delete Secrets
echo "🔐 Deleting secrets..."
kubectl delete secret minio-creds -n loki --ignore-not-found=true

# Delete PVCs
echo "💾 Deleting persistent volume claims..."
kubectl delete pvc ingester-data-loki-ingester-0 -n loki --ignore-not-found=true
kubectl delete pvc ingester-wal-loki-ingester-0 -n loki --ignore-not-found=true
kubectl delete pvc compactor-data -n loki --ignore-not-found=true
kubectl delete pvc querier-cache -n loki --ignore-not-found=true
kubectl delete pvc index-cache -n loki --ignore-not-found=true
kubectl delete pvc minio-pvc -n loki --ignore-not-found=true

# Delete namespace
echo "🗑️  Deleting namespace..."
kubectl delete namespace loki --ignore-not-found=true

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