#!/bin/bash
set -e

echo "🚀 Starting Loki 3.5.x Distributed Microservices Deployment"

# Check if Minikube is running
echo "📦 Checking Minikube status..."
if minikube status | grep -q "Running"; then
    echo "✅ Minikube is already running"
else
    echo "🚀 Starting Minikube..."
    minikube start --cpus=6 --memory=12288mb
fi

# Create Namespace
echo "🏗️  Creating namespace..."
kubectl create namespace loki --dry-run=client -o yaml | kubectl apply -f -

# Create Secrets
echo "🔐 Creating MinIO secrets..."
kubectl create secret generic minio-creds \
  --from-literal=accesskey=minioadmin \
  --from-literal=secretkey=minioadmin \
  -n loki --dry-run=client -o yaml | kubectl apply -f -

# Apply Storage
echo "💾 Creating persistent volumes..."
kubectl apply -f k8s/storage/

# Deploy Infrastructure (MinIO)
echo "🗄️  Deploying MinIO..."
kubectl apply -f k8s/infrastructure/minio-deployment.yaml

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n loki --timeout=300s

# Create Services
echo "🌐 Creating services..."
kubectl apply -f k8s/services.yaml

# Create ConfigMaps with all configurations
echo "⚙️  Creating ConfigMaps..."
kubectl create configmap distributor-config --from-file=config/distributor.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap ingester-config --from-file=config/ingester.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap querier-config --from-file=config/querier.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap query-frontend-config --from-file=config/query-frontend.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap query-scheduler-config --from-file=config/query-scheduler.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap compactor-config --from-file=config/compactor.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap ruler-config --from-file=config/ruler.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap index-gateway-config --from-file=config/index-gateway.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -

# Deploy components in proper order
echo "🔧 Deploying Loki components..."

# Deploy ingester first (StatefulSet)
echo "  📊 Deploying ingester..."
kubectl apply -f k8s/deployments/ingester-statefulset.yaml

# Deploy other components
echo "  📡 Deploying distributor..."
kubectl apply -f k8s/deployments/distributor-deployment.yaml

echo "  🔍 Deploying querier..."
kubectl apply -f k8s/deployments/querier-deployment.yaml

echo "  🎯 Deploying query frontend..."
kubectl apply -f k8s/deployments/query-frontend-deployment.yaml

echo "  📅 Deploying query scheduler..."
kubectl apply -f k8s/deployments/query-scheduler-deployment.yaml

echo "  🗜️  Deploying compactor..."
kubectl apply -f k8s/deployments/compactor-deployment.yaml

echo "  📏 Deploying ruler..."
kubectl apply -f k8s/deployments/ruler-deployment.yaml

echo "  🏛️  Deploying index gateway..."
kubectl apply -f k8s/deployments/index-gateway-deployment.yaml

# Deploy Fluent Bit for log collection
echo "  📝 Deploying Fluent Bit..."
kubectl apply -f k8s/fluent-bit/

# Wait for critical components
echo "⏳ Waiting for critical components to be ready..."
kubectl wait --for=condition=ready pod -l app=loki-ingester -n loki --timeout=120s
kubectl wait --for=condition=ready pod -l app=loki-distributor -n loki --timeout=60s

# Show deployment status
echo "✅ Deployment complete! Checking status..."
echo ""
echo "📊 Pod Status:"
kubectl get pods -n loki

echo ""
echo "🌐 Service Status:"
kubectl get svc -n loki

echo ""
echo "💾 Storage Status:"
kubectl get pvc -n loki

echo ""
echo "🔧 ConfigMap Status:"
kubectl get configmaps -n loki

echo ""
echo "🎉 Loki 3.5.x Distributed Microservices Stack is Ready!"
echo ""
echo "📋 Access Information:"
echo "  🗄️  MinIO UI:"
echo "    kubectl port-forward -n loki svc/minio 9000:9000"
echo "    Open: http://localhost:9000 (minioadmin/minioadmin)"
echo ""
echo "  📊 Loki API (via Query Frontend):"
echo "    kubectl port-forward -n loki svc/query-frontend 3100:3100"
echo "    Endpoint: http://localhost:3100"
echo ""
echo "  📡 Loki Ingestion (via Distributor):"
echo "    kubectl port-forward -n loki svc/distributor 3101:3100"
echo "    Endpoint: http://localhost:3101"
echo ""
echo "🔍 Health Check Commands:"
echo "  kubectl get pods -n loki"
echo "  kubectl logs -n loki -l app=loki-distributor"
echo "  kubectl logs -n loki loki-ingester-0"
echo ""
echo "🧪 Next Steps:"
echo "  ./scripts/validate-deployment.sh    # Validate all components"
echo "  ./scripts/test-api.sh             # Test API functionality"
echo "  ./scripts/check-all-logs.sh       # Check component logs"