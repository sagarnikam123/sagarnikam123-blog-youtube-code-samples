#!/bin/bash

# Loki Debug Endpoints Script
# Checks ring status, memberlist, and debug endpoints

NAMESPACE="loki"

echo "🔍 Loki Debug Endpoints Check"
echo "Namespace: $NAMESPACE"
echo "========================================"

# Function to check endpoint
check_endpoint() {
    local component=$1
    local endpoint=$2
    local description=$3
    
    echo
    echo "📡 $description ($component$endpoint)"
    echo "----------------------------------------"
    
    kubectl -n $NAMESPACE exec deployment/loki-$component -- wget -q -O - http://localhost:3100$endpoint 2>/dev/null || echo "❌ Failed to fetch endpoint"
}

# Function to check StatefulSet endpoint
check_statefulset_endpoint() {
    local component=$1
    local endpoint=$2
    local description=$3
    
    echo
    echo "📡 $description ($component$endpoint)"
    echo "----------------------------------------"
    
    kubectl -n $NAMESPACE exec statefulset/loki-$component -- wget -q -O - http://localhost:3100$endpoint 2>/dev/null || echo "❌ Failed to fetch endpoint"
}

# Check distributor endpoints
echo "🔄 DISTRIBUTOR DEBUG ENDPOINTS"
check_endpoint "distributor" "/ring" "Distributor Ring Status"
check_endpoint "distributor" "/memberlist" "Distributor Memberlist"
check_endpoint "distributor" "/config" "Distributor Configuration"
check_endpoint "distributor" "/services" "Distributor Services"

# Check ingester endpoints
echo
echo "🔄 INGESTER DEBUG ENDPOINTS"
check_statefulset_endpoint "ingester" "/ring" "Ingester Ring Status"
check_statefulset_endpoint "ingester" "/memberlist" "Ingester Memberlist"
check_statefulset_endpoint "ingester" "/config" "Ingester Configuration"
check_statefulset_endpoint "ingester" "/services" "Ingester Services"

# Check querier endpoints
echo
echo "🔄 QUERIER DEBUG ENDPOINTS"
check_endpoint "querier" "/ring" "Querier Ring Status"
check_endpoint "querier" "/memberlist" "Querier Memberlist"
check_endpoint "querier" "/config" "Querier Configuration"

# Check query-frontend endpoints
echo
echo "🔄 QUERY-FRONTEND DEBUG ENDPOINTS"
check_endpoint "query-frontend" "/config" "Query-Frontend Configuration"
check_endpoint "query-frontend" "/services" "Query-Frontend Services"

# Check compactor endpoints
echo
echo "🔄 COMPACTOR DEBUG ENDPOINTS"
check_endpoint "compactor" "/ring" "Compactor Ring Status"
check_endpoint "compactor" "/memberlist" "Compactor Memberlist"
check_endpoint "compactor" "/config" "Compactor Configuration"

# Check ruler endpoints
echo
echo "🔄 RULER DEBUG ENDPOINTS"
check_endpoint "ruler" "/ring" "Ruler Ring Status"
check_endpoint "ruler" "/memberlist" "Ruler Memberlist"
check_endpoint "ruler" "/config" "Ruler Configuration"

echo
echo "🔍 MEMBERLIST CLUSTER STATUS"
echo "========================================"
echo "Checking memberlist from distributor:"
kubectl -n $NAMESPACE exec deployment/loki-distributor -- wget -q -O - http://localhost:3100/memberlist 2>/dev/null | grep -E "(Name|Addr|Port|Status)" || echo "❌ No memberlist data"

echo
echo "🔍 POD IP ADDRESSES"
echo "========================================"
kubectl -n $NAMESPACE get pods -o wide | grep loki-

echo
echo "🔍 SERVICE ENDPOINTS"
echo "========================================"
kubectl -n $NAMESPACE get endpoints | grep loki-

echo
echo "✅ Debug endpoints check complete!"
echo "Use 'kubectl port-forward -n loki svc/loki-<component> 3100:3100' to access web interfaces"