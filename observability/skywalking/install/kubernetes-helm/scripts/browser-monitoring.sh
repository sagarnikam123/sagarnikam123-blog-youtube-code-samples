#!/bin/bash
# =============================================================================
# Browser Monitoring (RUM)
# =============================================================================
# Browser monitoring is client-side - this script provides info only.
#
# Usage:
#   ./scripts/browser-monitoring.sh [action] [namespace]
#
# Actions: enable, disable, status, info
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

ACTION="${1:-info}"
NAMESPACE="${2:-skywalking}"

do_enable() {
    log_header "Browser Monitoring"
    echo ""
    log_warn "Browser monitoring requires client-side instrumentation."
    echo ""
    do_info
}

do_disable() {
    log_info "Browser monitoring is client-side only - nothing to remove from cluster."
}

do_status() {
    echo ""
    log_header "Browser Monitoring Status"
    echo "Browser monitoring is client-side. Check SkyWalking UI for data."
    echo ""
}

do_info() {
    cat << 'EOF'

Browser Monitoring (RUM)
========================

Monitors browser/frontend performance using SkyWalking Client JS.

This is CLIENT-SIDE instrumentation - no cluster components needed.

Setup:
  1. Install skywalking-client-js in your frontend app:
     npm install skywalking-client-js

  2. Initialize in your app:
     import ClientMonitor from 'skywalking-client-js';
     ClientMonitor.register({
       collector: 'http://<skywalking-oap>:12800',
       service: 'my-frontend',
       serviceVersion: '1.0.0',
       pagePath: location.href,
       useFmp: true
     });

  3. Enable in OAP (values.yaml):
     oap:
       env:
         SW_RECEIVER_BROWSER: "default"

UI Location: Browser → Browser App

Documentation: https://skywalking.apache.org/docs/skywalking-client-js/latest/readme/

EOF
}

case "${ACTION}" in
    enable)  do_enable ;;
    disable) do_disable ;;
    status)  do_status ;;
    info)    do_info ;;
    -h|--help|help) do_info ;;
    *) log_error "Unknown action: ${ACTION}. Use: enable, disable, status, info"; exit 1 ;;
esac
