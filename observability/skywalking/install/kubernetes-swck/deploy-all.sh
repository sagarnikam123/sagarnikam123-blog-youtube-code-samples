#!/bin/bash
# =============================================================================
# Deploy Complete SkyWalking Stack using SWCK CRs with BanyanDB
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-skywalking}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Check SWCK Operator
# =============================================================================
check_operator() {
    log_info "Checking SWCK operator..."

    if ! kubectl get crd oapservers.operator.skywalking.apache.org &> /dev/null; then
        log_error "SWCK operator not installed. Run ./install-operator.sh first."
        exit 1
    fi

    log_info "SWCK operator found"
}

# =============================================================================
# Create Namespace
# =============================================================================
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
}

# =============================================================================
# Deploy BanyanDB using BanyanDB CRD
# =============================================================================
deploy_banyandb() {
    log_info "Deploying BanyanDB storage..."

    # SkyWalking 10.3.0 with BanyanDB 0.9.0
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: operator.skywalking.apache.org/v1alpha1
kind: BanyanDB
metadata:
  name: banyandb
spec:
  version: 0.9.0
  counts: 1
  image: apache/skywalking-banyandb:0.9.0
  config:
    - "standalone"
EOF

    log_info "Waiting for BanyanDB to be ready..."

    # Wait for BanyanDB pod to be running
    for i in {1..30}; do
        POD_STATUS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=banyandb -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "Pending")
        if [[ "$POD_STATUS" == "Running" ]]; then
            log_info "BanyanDB is running"
            break
        fi
        echo -n "."
        sleep 5
    done
    echo ""

    # Get the BanyanDB gRPC service name
    BANYANDB_SVC=$(kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/component=banyandb -o jsonpath='{.items[?(@.spec.ports[0].port==17912)].metadata.name}' 2>/dev/null)
    if [[ -z "$BANYANDB_SVC" ]]; then
        BANYANDB_SVC="banyandb-banyandb-grpc"
    fi
    log_info "BanyanDB gRPC service: $BANYANDB_SVC"
}

# =============================================================================
# Deploy OAP Server with BanyanDB storage
# =============================================================================
deploy_oap() {
    log_info "Deploying OAP Server with BanyanDB storage..."

    # Get BanyanDB gRPC service name
    BANYANDB_SVC=$(kubectl get svc -n "$NAMESPACE" -l app.kubernetes.io/component=banyandb -o jsonpath='{.items[?(@.spec.ports[0].port==17912)].metadata.name}' 2>/dev/null)
    if [[ -z "$BANYANDB_SVC" ]]; then
        BANYANDB_SVC="banyandb-banyandb-grpc"
    fi
    log_info "Using BanyanDB service: ${BANYANDB_SVC}:17912"

    # Deploy OAPServer with config (env vars) for BanyanDB
    # Note: OAPServer uses spec.config for env vars, NOT spec.env
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: operator.skywalking.apache.org/v1alpha1
kind: OAPServer
metadata:
  name: skywalking-oap
spec:
  version: 10.3.0
  instances: 1
  image: apache/skywalking-oap-server:10.3.0
  config:
    - name: SW_STORAGE
      value: banyandb
    - name: SW_STORAGE_BANYANDB_TARGETS
      value: "${BANYANDB_SVC}:17912"
    - name: SW_HEALTH_CHECKER
      value: "default"
    - name: JAVA_OPTS
      value: "-Xms512m -Xmx1g"
EOF

    log_info "Waiting for OAP Server to be ready..."

    # Wait for OAP pod to be running
    for i in {1..60}; do
        POD_STATUS=$(kubectl get pods -n "$NAMESPACE" -l app=oap -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "Pending")
        if [[ "$POD_STATUS" == "Running" ]]; then
            READY=$(kubectl get pods -n "$NAMESPACE" -l app=oap -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
            if [[ "$READY" == "true" ]]; then
                log_info "OAP Server is running and ready"
                break
            fi
        fi
        echo -n "."
        sleep 5
    done
    echo ""
}

# =============================================================================
# Deploy UI
# =============================================================================
deploy_ui() {
    log_info "Deploying UI..."

    # OAP service name follows pattern: <oapserver-name>-oap
    OAP_SVC="skywalking-oap-oap"

    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: operator.skywalking.apache.org/v1alpha1
kind: UI
metadata:
  name: skywalking-ui
spec:
  version: 10.3.0
  instances: 1
  image: apache/skywalking-ui:10.3.0
  OAPServerAddress: http://${OAP_SVC}:12800
  service:
    template:
      type: ClusterIP
EOF

    log_info "UI deployed"
}

# =============================================================================
# Print Status
# =============================================================================
print_status() {
    echo ""
    echo "=============================================="
    echo "  SkyWalking SWCK Deployment Status"
    echo "=============================================="
    echo ""

    echo "BanyanDB:"
    kubectl get banyandb -n "$NAMESPACE" 2>/dev/null || echo "  No BanyanDB CR"
    echo ""

    echo "OAP Server:"
    kubectl get oapserver -n "$NAMESPACE" 2>/dev/null || echo "  No OAPServer CR"
    echo ""

    echo "UI:"
    kubectl get ui -n "$NAMESPACE" 2>/dev/null || echo "  No UI resources"
    echo ""

    echo "Pods:"
    kubectl get pods -n "$NAMESPACE"
    echo ""

    echo "Services:"
    kubectl get svc -n "$NAMESPACE"
    echo ""

    echo "=============================================="
    echo "  Access UI"
    echo "=============================================="
    echo ""
    echo "  # Port forward"
    echo "  kubectl port-forward svc/skywalking-ui-ui 8080:80 -n $NAMESPACE"
    echo "  open http://localhost:8080"
    echo ""
    echo "  # Or for Minikube"
    echo "  minikube service skywalking-ui-ui -n $NAMESPACE"
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "=============================================="
    echo "  SkyWalking SWCK Deployment"
    echo "  Storage: BanyanDB"
    echo "=============================================="
    echo ""

    check_operator
    create_namespace
    deploy_banyandb
    deploy_oap
    deploy_ui

    # Wait for pods
    log_info "Waiting for all pods to be ready..."
    sleep 15

    print_status
}

main "$@"
