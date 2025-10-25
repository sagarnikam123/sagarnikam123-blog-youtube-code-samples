#!/bin/bash
set -e

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🚀 Loki Distributed Microservices Deployment Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Complete automated deployment of Loki distributed microservices stack"
    echo "  on Minikube. Deploys all components with proper sequencing, health checks,"
    echo "  and configuration management."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • Validate Minikube environment"
    echo "  • Deploy infrastructure (namespace, storage, MinIO)"
    echo "  • Deploy Loki microservices with configurations"
    echo "  • Deploy supporting services (Fluent Bit, Prometheus, Grafana)"
    echo "  • Perform health checks and provide access information"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./run-on-minikube.sh        # Deploy complete stack"
    echo "  ./run-on-minikube.sh --help # Show this help"
    echo ""
    echo "📋 DEPLOYED COMPONENTS:"
    echo "  • Loki: 8 microservices + Web UI (distributor, ingester, querier, etc.)"
    echo "  • MinIO: S3-compatible object storage"
    echo "  • Fluent Bit: Log collection agent"
    echo "  • Prometheus: Metrics collection"
    echo "  • Grafana: Visualization dashboards"
    echo ""
    echo "🏷️ CURRENT VERSIONS:"
    echo "  • Loki: 3.5.5              • Grafana: 12.1.0"
    echo "  • Prometheus: v3.5.0       • MinIO: 2025-09-07"
    echo "  • Fluent Bit: 4.1.0"
    echo ""
    echo "📦 REQUIREMENTS:"
    echo "  • Minikube installed and configured"
    echo "  • kubectl configured for Minikube"
    echo "  • 6 CPUs, 12GB RAM recommended"
    echo "  • Docker for configuration validation"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Development environment setup"
    echo "  • Learning Loki architecture"
    echo "  • Testing log aggregation"
    echo "  • Blog/tutorial demonstrations"
    echo ""
    echo "📋 POST-DEPLOYMENT:"
    echo "  • Run ./scripts/check-deployment-health.sh for validation"
    echo "  • Use ./scripts/test-api.sh for API testing"
    echo "  • Access UIs via kubectl port-forward commands"
    exit 0
fi

# 🏷️ Centralized Version Management
export LOKI_VERSION="3.5.7"        # Latest stable from grafana/loki
export GRAFANA_VERSION="12.1.0"     # Latest from grafana/grafana
export PROMETHEUS_VERSION="v3.5.0" # Latest from prometheus/prometheus
export MINIO_VERSION="RELEASE.2025-09-07T16-13-09Z" # Latest from minio/minio
export FLUENT_BIT_VERSION="4.1.0"   # Latest from fluent/fluent-bit

echo "🚀 Starting Loki ${LOKI_VERSION} Distributed Microservices Deployment"

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
kubectl apply -f k8s/minio/secret.yaml

# Apply Storage
echo "💾 Creating persistent volumes..."
kubectl apply -f k8s/loki/storage/
kubectl apply -f k8s/minio/storage.yaml

# Deploy MinIO
echo "🗄️  Deploying MinIO..."
for file in k8s/minio/*.yaml; do
    envsubst < "$file" | kubectl apply -f -
done

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
kubectl wait --for=condition=ready pod -l app=minio -n loki --timeout=300s

# Create Services
echo "🌐 Creating services..."
for file in k8s/loki/services/*.yaml; do
    envsubst < "$file" | kubectl apply -f -
done


# Create ConfigMaps with all configurations
echo "⚙️  Creating Loki ConfigMaps..."
kubectl create configmap distributor-config --from-file=k8s/loki/configs/distributor.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap ingester-config --from-file=k8s/loki/configs/ingester.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap querier-config --from-file=k8s/loki/configs/querier.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap query-frontend-config --from-file=k8s/loki/configs/query-frontend.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap query-scheduler-config --from-file=k8s/loki/configs/query-scheduler.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap compactor-config --from-file=k8s/loki/configs/compactor.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap ruler-config --from-file=k8s/loki/configs/ruler.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap index-gateway-config --from-file=k8s/loki/configs/index-gateway.yaml -n loki --dry-run=client -o yaml | kubectl apply -f -

# Deploy components in proper order
echo "🔧 Deploying Loki components..."

# Deploy Loki components with version substitution
echo "  🔍 Deploying Loki components..."
export LOKI_VERSION GRAFANA_VERSION PROMETHEUS_VERSION MINIO_VERSION FLUENT_BIT_VERSION
for file in k8s/loki/deployments/*.yaml; do
    echo "    Deploying $(basename "$file")..."
    envsubst < "$file" | kubectl apply -f -
done

# Deploy Fluent Bit for log collection
echo "  📝 Deploying Fluent Bit..."
kubectl apply -f k8s/fluent-bit/rbac/
for file in k8s/fluent-bit/*.yaml; do
    echo "    Deploying $(basename "$file")..."
    envsubst < "$file" | kubectl apply -f -
done

# Deploy Prometheus for metrics collection
echo "  📈 Deploying Prometheus..."
for file in k8s/prometheus/*.yaml; do
    echo "    Deploying $(basename "$file")..."
    envsubst < "$file" | kubectl apply -f -
done

# Deploy Grafana for log visualization
echo "  📊 Deploying Grafana..."
for file in k8s/grafana/*.yaml; do
    echo "    Deploying $(basename "$file")..."
    envsubst < "$file" | kubectl apply -f -
done

# Wait for critical components
echo "⏳ Waiting for critical components to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki,app.kubernetes.io/component=ingester -n loki --timeout=120s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor -n loki --timeout=60s

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
echo "🎉 Loki ${LOKI_VERSION} Distributed Microservices Stack is Ready!"
echo ""
echo "📋 Access Information:"
echo "  🗄️  MinIO UI:"
echo "    kubectl port-forward -n loki svc/minio 9000:9000"
echo "    Open: http://localhost:9000 (minioadmin/minioadmin)"
echo ""
echo "  🔍 Loki Web UI & API (via Query Frontend):"
echo "    kubectl port-forward -n loki svc/query-frontend 3100:3100"
echo "    Web UI: http://localhost:3100"
echo "    API: http://localhost:3100/loki/api/v1/"
echo ""
echo "  📡 Loki Ingestion (via Distributor):"
echo "    kubectl port-forward -n loki svc/distributor 3102:3100"
echo "    Endpoint: http://localhost:3102"
echo ""
echo "  📊 Grafana Dashboard:"
echo "    kubectl port-forward -n loki svc/grafana 3000:3000"
echo "    Open: http://localhost:3000 (admin/admin)"
echo ""
echo "  📈 Prometheus Metrics:"
echo "    kubectl port-forward -n loki svc/prometheus 9090:9090"
echo "    Open: http://localhost:9090"
echo ""
echo "🔍 Health Check Commands:"
echo "  kubectl get pods -n loki"
echo "  kubectl logs -n loki -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor"
echo "  kubectl logs -n loki loki-ingester-0"
echo ""
echo "🧪 Next Steps:"
echo "  ./scripts/check-deployment-health.sh # 1. Check deployment health"
echo "  ./scripts/check-all-logs.sh         # 2. Check component logs"
echo "  ./scripts/test-api.sh               # 3. Test API functionality"
echo "  ./scripts/check-versions.sh         # 4. Check current versions"
