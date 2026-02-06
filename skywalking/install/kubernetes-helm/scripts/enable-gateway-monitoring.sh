#!/bin/bash
# =============================================================================
# Enable Gateway Monitoring for SkyWalking
# =============================================================================
# Deploys exporters and configures OTel Collector for gateway monitoring
#
# Usage:
#   ./scripts/enable-gateway-monitoring.sh [gateway] [options]
#
# Gateways:
#   nginx     - Deploy Nginx Prometheus Exporter
#   apisix    - Show APISIX configuration (built-in metrics)
#   kong      - Show Kong configuration (built-in metrics)
#   all       - Show all configurations
#
# Options:
#   --nginx-uri <uri>   - Nginx stub_status URI (default: http://nginx.default:80/nginx_status)
#   --namespace <ns>    - Namespace for exporter (default: skywalking)
#
# Examples:
#   ./scripts/enable-gateway-monitoring.sh nginx
#   ./scripts/enable-gateway-monitoring.sh nginx --nginx-uri http://my-nginx:80/nginx_status
#   ./scripts/enable-gateway-monitoring.sh all
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# Defaults
GATEWAY="${1:-all}"
NAMESPACE="skywalking"
NGINX_URI="http://nginx.default.svc:80/nginx_status"

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --nginx-uri)
            NGINX_URI="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

show_oap_config() {
    echo ""
    echo "=============================================="
    echo "OAP Configuration Required"
    echo "=============================================="
    echo ""
    echo "Add these rules to your OAP environment:"
    echo ""
    echo "  SW_OTEL_RECEIVER_ENABLED_OC_RULES: \"oap,nginx,apisix,kong,...\""
    echo ""
    echo "Then upgrade your Helm release or restart OAP."
    echo ""
}

deploy_nginx() {
    log_info "Deploying Nginx Prometheus Exporter..."

    # Update the nginx URI in the deployment
    sed "s|http://nginx.default.svc:80/nginx_status|${NGINX_URI}|g" \
        "${BASE_DIR}/base/gateway-monitoring/nginx-exporter.yaml" | \
        kubectl apply -f - -n "${NAMESPACE}"

    log_success "Nginx exporter deployed!"
    echo ""
    echo "Add this scrape config to OTel Collector:"
    echo ""
    cat << 'EOF'
- job_name: 'nginx-monitoring'
  scrape_interval: 15s
  static_configs:
    - targets: ['nginx-exporter:9113']
  relabel_configs:
    - source_labels: [__address__]
      target_label: service
      regex: '(.+):.*'
      replacement: 'nginx::nginx'
    - target_label: layer
      replacement: NGINX
EOF
    echo ""
}

show_apisix_config() {
    log_info "APISIX Configuration"
    echo ""
    echo "APISIX has built-in Prometheus metrics. Enable it in your APISIX config:"
    echo ""
    cat << 'EOF'
# In APISIX config.yaml:
plugin_attr:
  prometheus:
    export_uri: /apisix/prometheus/metrics
    export_addr:
      ip: 0.0.0.0
      port: 9091

# Or via Helm values:
apisix:
  prometheus:
    enabled: true
    containerPort: 9091
EOF
    echo ""
    echo "Add this scrape config to OTel Collector:"
    echo ""
    cat << 'EOF'
- job_name: 'apisix-monitoring'
  scrape_interval: 15s
  static_configs:
    - targets: ['apisix-gateway.apisix:9091']
  relabel_configs:
    - source_labels: [__address__]
      target_label: service
      regex: '(.+):.*'
      replacement: 'apisix::apisix'
    - target_label: layer
      replacement: APISIX
EOF
    echo ""
}

show_kong_config() {
    log_info "Kong Configuration"
    echo ""
    echo "Kong has built-in Prometheus plugin. Enable it via Admin API:"
    echo ""
    cat << 'EOF'
curl -X POST http://kong-admin:8001/plugins \
  -d "name=prometheus" \
  -d "config.status_code_metrics=true" \
  -d "config.latency_metrics=true" \
  -d "config.bandwidth_metrics=true"
EOF
    echo ""
    echo "Add this scrape config to OTel Collector:"
    echo ""
    cat << 'EOF'
- job_name: 'kong-monitoring'
  scrape_interval: 15s
  metrics_path: /metrics
  static_configs:
    - targets: ['kong-admin.kong:8001']
  relabel_configs:
    - source_labels: [__address__]
      target_label: service
      regex: '(.+):.*'
      replacement: 'kong::kong'
    - target_label: layer
      replacement: KONG
EOF
    echo ""
}

# Main
echo ""
echo "=============================================="
echo "Gateway Monitoring Setup"
echo "=============================================="
echo ""

case $GATEWAY in
    nginx)
        deploy_nginx
        show_oap_config
        ;;
    apisix)
        show_apisix_config
        show_oap_config
        ;;
    kong)
        show_kong_config
        show_oap_config
        ;;
    all)
        echo "Available Gateway Configurations:"
        echo ""
        show_apisix_config
        echo "----------------------------------------------"
        show_kong_config
        echo "----------------------------------------------"
        log_info "For Nginx, run: ./scripts/enable-gateway-monitoring.sh nginx"
        show_oap_config
        ;;
    *)
        echo -e "${RED}Unknown gateway: ${GATEWAY}${NC}"
        echo "Available: nginx, apisix, kong, all"
        exit 1
        ;;
esac

echo ""
log_info "After updating OTel Collector config, restart it:"
echo "  kubectl rollout restart deployment/otel-collector -n skywalking"
echo ""
