#!/bin/bash
# =============================================================================
# Deploy SkyWalking SWCK Operator for Java Agent Auto-Injection
# =============================================================================
# Usage:
#   ./agents/java/swck-operator/deploy.sh [install|uninstall|status]
#
# Prerequisites:
#   - cert-manager installed (recommended) OR use self-signed certs
#   - SkyWalking backend deployed in 'skywalking' namespace
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="skywalking-swck-system"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_cert_manager() {
    if kubectl get crd certificates.cert-manager.io &>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_skywalking() {
    if kubectl get svc skywalking-oap -n skywalking &>/dev/null; then
        log_success "SkyWalking backend found in 'skywalking' namespace"
        return 0
    else
        log_warn "SkyWalking backend not found. Deploy it first or agents won't be able to connect."
        return 1
    fi
}

do_install() {
    log_info "Installing SkyWalking SWCK Operator v0.9.0..."
    echo ""

    # Check SkyWalking backend
    check_skywalking || true

    # 1. Create namespace
    log_info "Creating namespace ${NAMESPACE}..."
    kubectl apply -f "${SCRIPT_DIR}/namespace.yaml"

    # 2. Apply CRDs from official SWCK repo (all 10 CRDs required)
    log_info "Applying CRDs from official SWCK repo..."
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_banyandbs.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_fetchers.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_javaagents.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_oapserverconfigs.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_oapserverdynamicconfigs.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_oapservers.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_satellites.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_storages.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_swagents.yaml
    kubectl apply -f https://raw.githubusercontent.com/apache/skywalking-swck/master/operator/config/crd/bases/operator.skywalking.apache.org_uis.yaml

    # 3. Apply RBAC
    log_info "Applying RBAC..."
    kubectl apply -f "${SCRIPT_DIR}/rbac.yaml"

    # 4. Handle certificates
    if check_cert_manager; then
        log_info "cert-manager detected, using Certificate resource..."
        kubectl apply -f "${SCRIPT_DIR}/certificate.yaml"
        # Wait for certificate to be ready
        log_info "Waiting for certificate..."
        kubectl wait --for=condition=Ready certificate/skywalking-swck-serving-cert \
            -n ${NAMESPACE} --timeout=60s 2>/dev/null || log_warn "Certificate not ready yet, continuing..."
    else
        log_warn "cert-manager not found, generating self-signed certificate..."
        source "${SCRIPT_DIR}/self-signed-cert.sh"
    fi

    # 5. Deploy operator
    log_info "Deploying operator..."
    kubectl apply -f "${SCRIPT_DIR}/operator.yaml"

    # 6. Apply webhook configuration
    log_info "Applying webhook configuration..."
    kubectl apply -f "${SCRIPT_DIR}/webhook.yaml"

    # If using self-signed cert, patch the webhook with CA bundle
    if ! check_cert_manager; then
        log_info "Patching webhook with CA bundle..."
        if [[ -n "${SWCK_CA_BUNDLE:-}" ]]; then
            kubectl patch mutatingwebhookconfiguration skywalking-swck-mutating-webhook-configuration \
                --type='json' -p="[{\"op\": \"add\", \"path\": \"/webhooks/0/clientConfig/caBundle\", \"value\": \"${SWCK_CA_BUNDLE}\"}]"
        else
            CA_BUNDLE=$(kubectl get secret skywalking-swck-controller-manager-cert -n ${NAMESPACE} \
                -o jsonpath='{.data.tls\.crt}' 2>/dev/null || echo "")
            if [[ -n "${CA_BUNDLE}" ]]; then
                kubectl patch mutatingwebhookconfiguration skywalking-swck-mutating-webhook-configuration \
                    --type='json' -p="[{\"op\": \"add\", \"path\": \"/webhooks/0/clientConfig/caBundle\", \"value\": \"${CA_BUNDLE}\"}]"
            fi
        fi
    fi

    # 7. Wait for operator to be ready
    log_info "Waiting for operator to be ready..."
    kubectl rollout status deployment/skywalking-swck-controller-manager -n ${NAMESPACE} --timeout=120s

    echo ""
    log_success "SkyWalking SWCK Operator installed successfully!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Label namespace for auto-injection:"
    echo "   kubectl label namespace hunt swck-injection=enabled"
    echo ""
    echo "2. Create SwAgent CR in target namespace (REQUIRED for injection):"
    echo "   kubectl apply -f ${SCRIPT_DIR}/java-agent-config.yaml"
    echo "   Note: Edit the file first if your namespace is not 'hunt'"
    echo ""
    echo "3. Add pod label to deployments (REQUIRED for injection):"
    echo "   kubectl patch deployment <name> -n hunt --type='json' \\"
    echo "     -p='[{\"op\": \"add\", \"path\": \"/spec/template/metadata/labels/swck-java-agent-injected\", \"value\": \"true\"}]'"
    echo ""
    echo "4. Restart deployments to trigger injection:"
    echo "   kubectl rollout restart deployment -n hunt"
    echo ""
    echo "5. Verify injection:"
    echo "   kubectl get pods -n hunt -o jsonpath='{.items[*].spec.initContainers[*].name}' | tr ' ' '\\n' | grep inject"
    echo ""
    echo "Note: SWCK requires BOTH namespace label AND pod label for injection to work"
}

do_uninstall() {
    log_warn "Uninstalling SkyWalking SWCK Operator..."
    echo ""

    kubectl delete -f "${SCRIPT_DIR}/java-agent-config.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/webhook.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/operator.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/certificate.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/rbac.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/crds.yaml" --ignore-not-found 2>/dev/null || true
    kubectl delete -f "${SCRIPT_DIR}/namespace.yaml" --ignore-not-found 2>/dev/null || true

    log_success "SkyWalking SWCK Operator uninstalled"
    echo ""
    echo "Note: Namespace labels are NOT removed. Remove manually if needed:"
    echo "  kubectl label namespace hunt swck-injection-"
}

do_status() {
    echo ""
    log_info "SkyWalking SWCK Operator Status"
    echo "================================"
    echo ""

    echo "Operator Pod:"
    kubectl get pods -n ${NAMESPACE} -l control-plane=controller-manager 2>/dev/null || echo "Not found"
    echo ""

    echo "Webhook Configuration:"
    kubectl get mutatingwebhookconfiguration skywalking-swck-mutating-webhook-configuration 2>/dev/null || echo "Not found"
    echo ""

    echo "Namespaces with injection enabled (swck-injection=enabled):"
    kubectl get namespaces -l swck-injection=enabled --no-headers 2>/dev/null || echo "None"
    echo ""

    echo "SwAgent CRs:"
    kubectl get swagents -A 2>/dev/null || echo "None"
    echo ""

    echo "JavaAgent CRs (created after injection):"
    kubectl get javaagents -A 2>/dev/null || echo "None"
}

show_help() {
    cat << 'EOF'

SkyWalking SWCK Operator Deployment
===================================

Usage: ./agents/java/swck-operator/deploy.sh [command]

Commands:
  install     Install the SWCK operator
  uninstall   Remove the SWCK operator
  status      Show operator status
  help        Show this help

After installation, enable injection on a namespace:

  1. Label namespace:
     kubectl label namespace <namespace> swck-injection=enabled

  2. Create SwAgent CR in target namespace:
     kubectl apply -f agents/java/swck-operator/java-agent-config.yaml

  3. Add pod label to deployments:
     kubectl patch deployment <name> -n <namespace> --type='json' \
       -p='[{"op": "add", "path": "/spec/template/metadata/labels/swck-java-agent-injected", "value": "true"}]'

  4. Restart pods to trigger injection:
     kubectl rollout restart deployment -n <namespace>

Note: SWCK requires BOTH namespace label AND pod label for injection.

EOF
}

# Main
case "${1:-help}" in
    install)   do_install ;;
    uninstall) do_uninstall ;;
    status)    do_status ;;
    help|*)    show_help ;;
esac
