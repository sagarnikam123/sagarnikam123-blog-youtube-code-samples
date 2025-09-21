#!/bin/bash
set -e

echo "🔍 Validating Loki 3.5.5 Distributed Microservices Deployment"

# Check if namespace exists
echo "📋 Checking namespace..."
if kubectl get namespace loki &>/dev/null; then
    echo "  ✅ Namespace 'loki' exists"
else
    echo "  ❌ Namespace 'loki' not found"
    exit 1
fi

# Check pod status
echo ""
echo "📊 Checking pod status..."
kubectl get pods -n loki

# Count running pods
RUNNING_PODS=$(kubectl get pods -n loki --field-selector=status.phase=Running --no-headers | wc -l | tr -d ' ')
TOTAL_PODS=$(kubectl get pods -n loki --no-headers | wc -l | tr -d ' ')

echo ""
echo "📈 Pod Summary: $RUNNING_PODS/$TOTAL_PODS pods running"

# Check critical components
echo ""
echo "🔧 Checking critical components..."

# MinIO
if kubectl get pod -n loki -l app=minio --field-selector=status.phase=Running &>/dev/null; then
    echo "  ✅ MinIO is running"
else
    echo "  ❌ MinIO is not running"
fi

# Distributor
if kubectl get pod -n loki -l app=loki-distributor --field-selector=status.phase=Running &>/dev/null; then
    echo "  ✅ Distributor is running"
else
    echo "  ❌ Distributor is not running"
fi

# Ingester
if kubectl get pod -n loki -l app=loki-ingester --field-selector=status.phase=Running &>/dev/null; then
    echo "  ✅ Ingester is running"
else
    echo "  ❌ Ingester is not running"
fi

# Querier
if kubectl get pod -n loki -l app=loki-querier --field-selector=status.phase=Running &>/dev/null; then
    echo "  ✅ Querier is running"
else
    echo "  ❌ Querier is not running"
fi

# Query Frontend
if kubectl get pod -n loki -l app=loki-query-frontend --field-selector=status.phase=Running &>/dev/null; then
    echo "  ✅ Query Frontend is running"
else
    echo "  ❌ Query Frontend is not running"
fi

# Check services
echo ""
echo "🌐 Checking services..."
kubectl get svc -n loki

# Check storage
echo ""
echo "💾 Checking storage..."
kubectl get pvc -n loki

# Check memberlist coordination
echo ""
echo "🔗 Checking memberlist coordination..."
DISTRIBUTOR_POD=$(kubectl get pods -n loki -l app=loki-distributor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [[ -n "$DISTRIBUTOR_POD" ]]; then
    echo "  📡 Checking distributor memberlist..."
    kubectl logs -n loki "$DISTRIBUTOR_POD" --tail=5 | grep -i memberlist || echo "    ⚠️  No recent memberlist activity"
fi

INGESTER_POD=$(kubectl get pods -n loki -l app=loki-ingester -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [[ -n "$INGESTER_POD" ]]; then
    echo "  📊 Checking ingester memberlist..."
    kubectl logs -n loki "$INGESTER_POD" --tail=5 | grep -i memberlist || echo "    ⚠️  No recent memberlist activity"
fi

# Test DNS resolution
echo ""
echo "🌍 Testing DNS resolution..."
kubectl run test-dns --image=busybox:1.35 --rm -it --restart=Never -n loki -- nslookup minio.loki.svc.cluster.local 2>/dev/null && echo "  ✅ MinIO DNS resolution working" || echo "  ❌ MinIO DNS resolution failed"

kubectl run test-dns --image=busybox:1.35 --rm -it --restart=Never -n loki -- nslookup ingester.loki.svc.cluster.local 2>/dev/null && echo "  ✅ Ingester DNS resolution working" || echo "  ❌ Ingester DNS resolution failed"

# Check for common errors
echo ""
echo "⚠️  Checking for common issues..."

# Check for timestamp errors
TIMESTAMP_ERRORS=$(kubectl logs -n loki -l app=loki-distributor --tail=100 2>/dev/null | grep -c "timestamp too new" 2>/dev/null || echo "0")
TIMESTAMP_ERRORS=$(echo "$TIMESTAMP_ERRORS" | tr -d ' \n')
if [[ $TIMESTAMP_ERRORS -gt 0 ]]; then
    echo "  ⚠️  Found $TIMESTAMP_ERRORS timestamp errors in distributor logs"
else
    echo "  ✅ No timestamp errors found"
fi

# Check for ring errors
RING_ERRORS=$(kubectl logs -n loki -l app=loki-querier --tail=100 2>/dev/null | grep -c "empty ring" 2>/dev/null || echo "0")
RING_ERRORS=$(echo "$RING_ERRORS" | tr -d ' \n')
if [[ $RING_ERRORS -gt 0 ]]; then
    echo "  ⚠️  Found $RING_ERRORS ring errors in querier logs"
else
    echo "  ✅ No ring errors found"
fi

# Check for storage errors
STORAGE_ERRORS=$(kubectl logs -n loki loki-ingester-0 --tail=100 2>/dev/null | grep -c "no such host" 2>/dev/null || echo "0")
STORAGE_ERRORS=$(echo "$STORAGE_ERRORS" | tr -d ' \n')
if [[ $STORAGE_ERRORS -gt 0 ]]; then
    echo "  ⚠️  Found $STORAGE_ERRORS storage connection errors"
else
    echo "  ✅ No storage connection errors found"
fi

echo ""
echo "🎯 Validation Summary:"
if [[ $RUNNING_PODS -eq $TOTAL_PODS ]] && [[ $TIMESTAMP_ERRORS -eq 0 ]] && [[ $STORAGE_ERRORS -eq 0 ]]; then
    echo "  🎉 Deployment is healthy!"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Port forward services:"
    echo "     kubectl port-forward -n loki svc/query-frontend 3100:3100"
    echo "  2. Test API:"
    echo "     curl http://localhost:3100/ready"
    echo "  3. View logs:"
    echo "     kubectl logs -n loki -l app=loki-distributor"
else
    echo "  ⚠️  Deployment has issues that need attention"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  1. Check pod logs: kubectl logs -n loki [pod-name]"
    echo "  2. Check events: kubectl get events -n loki"
    echo "  3. Check configurations: kubectl get configmaps -n loki"
fi