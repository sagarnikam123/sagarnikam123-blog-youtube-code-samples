#!/bin/bash
set -e

# Configuration - Default values
LOG_LINES=10  # Number of log lines to display per component (default: 10)
COMPONENT=""  # Specific component to check (empty = all components)

# Valid components list
VALID_COMPONENTS=("distributor" "ingester" "querier" "query-frontend" "query-scheduler" "compactor" "ruler" "index-gateway" "minio" "fluent-bit" "grafana" "prometheus")

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--lines)
      LOG_LINES="$2"
      shift 2
      ;;
    -c|--component)
      COMPONENT="$2"
      shift 2
      ;;
    -h|--help)
      echo "🔍 Component Log Analysis Script"
      echo ""
      echo "📋 DESCRIPTION:"
      echo "  Automated log collection and analysis for all Loki distributed"
      echo "  microservices components. Provides quick overview of component"
      echo "  health through log inspection."
      echo ""
      echo "⚙️  FUNCTIONALITY:"
      echo "  • Display current pod status"
      echo "  • Collect logs from all Loki components"
      echo "  • Show logs from supporting services"
      echo "  • Highlight key health indicators"
      echo ""
      echo "🚀 USAGE:"
      echo "  ./scripts/check-all-logs.sh                    # Check all components (default: 10 lines)"
      echo "  ./scripts/check-all-logs.sh -n 20             # Show 20 lines per component"
      echo "  ./scripts/check-all-logs.sh -c distributor    # Check only distributor"
      echo "  ./scripts/check-all-logs.sh -c ingester -n 50 # Check ingester with 50 lines"
      echo "  ./scripts/check-all-logs.sh -h|--help         # Show this help"
      echo ""
      echo "📋 OPTIONS:"
      echo "  -n, --lines NUMBER      Number of log lines to display per component (default: 10)"
      echo "  -c, --component NAME    Check specific component only (default: all)"
      echo "  -h, --help             Show this help message"
      echo ""
      echo "📋 AVAILABLE COMPONENTS:"
      echo "  • Loki: distributor, ingester, querier, query-frontend"
      echo "  • Loki: query-scheduler, compactor, ruler, index-gateway"
      echo "  • Supporting: minio, fluent-bit, grafana, prometheus"
      echo ""
      echo "🔍 HEALTH INDICATORS:"
      echo "  • Distributor: 'memberlist cluster succeeded'"
      echo "  • Ingester: 'checkpoint done', 'uploading tables'"
      echo "  • Fluent Bit: 'flush chunk succeeded'"
      echo "  • General: Error patterns and startup messages"
      echo ""
      echo "📦 REQUIREMENTS:"
      echo "  • kubectl configured and accessible"
      echo "  • Loki namespace with deployed components"
      echo "  • Standard Kubernetes labels applied"
      echo ""
      echo "🎯 USE CASES:"
      echo "  • Quick health assessment"
      echo "  • Troubleshooting component issues"
      echo "  • Monitoring deployment status"
      echo "  • Log aggregation for analysis"
      exit 0
      ;;
    *)
      echo "❌ Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Validate LOG_LINES is a positive integer
if ! [[ "$LOG_LINES" =~ ^[0-9]+$ ]] || [[ "$LOG_LINES" -eq 0 ]]; then
  echo "❌ Error: LOG_LINES must be a positive integer, got: $LOG_LINES"
  exit 1
fi

# Validate component if specified
if [[ -n "$COMPONENT" ]]; then
  if [[ ! " ${VALID_COMPONENTS[*]} " =~ " ${COMPONENT} " ]]; then
    echo "❌ Error: Invalid component '$COMPONENT'"
    echo "Valid components: ${VALID_COMPONENTS[*]}"
    exit 1
  fi
fi

# Check for help flag (legacy support)
if false; then
    # This block is now handled above
    exit 0
fi

if [[ -n "$COMPONENT" ]]; then
  echo "🔍 Checking $COMPONENT Logs (showing $LOG_LINES lines)"
else
  echo "🔍 Checking All Loki Component Logs (showing $LOG_LINES lines per component)"
fi
echo "===================================="

# Get all pod names first
echo "📊 Current Pod Status:"
kubectl get pods -n loki

echo ""
if [[ -n "$COMPONENT" ]]; then
  echo "📋 $COMPONENT Log Analysis:"
else
  echo "📋 Component Log Analysis:"
fi
echo ""

# Component-specific functions
check_distributor() {
  echo "📡 DISTRIBUTOR LOGS:"
  kubectl logs -n loki -l app=loki-distributor --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No distributor pods found"
}

check_ingester() {
  echo "📊 INGESTER LOGS:"
  kubectl logs -n loki loki-ingester-0 --tail=$LOG_LINES 2>/dev/null || echo "  ❌ Ingester not found"
}

check_querier() {
  echo "🔍 QUERIER LOGS:"
  kubectl logs -n loki -l app=loki-querier --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No querier pods found"
}

check_query-frontend() {
  echo "🎯 QUERY-FRONTEND LOGS:"
  kubectl logs -n loki -l app=loki-query-frontend --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No query-frontend pods found"
}

check_query-scheduler() {
  echo "📅 QUERY-SCHEDULER LOGS:"
  kubectl logs -n loki -l app=loki-query-scheduler --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No query-scheduler pods found"
}

check_compactor() {
  echo "🗜️ COMPACTOR LOGS:"
  kubectl logs -n loki -l app=loki-compactor --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No compactor pods found"
}

check_ruler() {
  echo "📏 RULER LOGS:"
  kubectl logs -n loki -l app=loki-ruler --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No ruler pods found"
}

check_index-gateway() {
  echo "🏛️ INDEX-GATEWAY LOGS:"
  kubectl logs -n loki -l app=loki-index-gateway --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No index-gateway pods found"
}

check_minio() {
  echo "🗄️ MINIO LOGS:"
  kubectl logs -n loki -l app=minio --tail=$LOG_LINES 2>/dev/null || echo "  ❌ MinIO not found"
}

check_fluent-bit() {
  echo "📝 FLUENT BIT LOGS:"
  kubectl logs -n loki -l app=fluent-bit --tail=$LOG_LINES 2>/dev/null || echo "  ❌ No fluent-bit pods found"
}

check_grafana() {
  echo "📈 GRAFANA LOGS:"
  kubectl logs -n loki -l app=grafana --tail=$LOG_LINES 2>/dev/null || echo "  ❌ Grafana not found"
}

check_prometheus() {
  echo "📉 PROMETHEUS LOGS:"
  kubectl logs -n loki -l app=prometheus --tail=$LOG_LINES 2>/dev/null || echo "  ❌ Prometheus not found"
}

# Check specific component or all components
if [[ -n "$COMPONENT" ]]; then
  check_$COMPONENT
else
  # Check all components
  check_distributor
  echo ""
  check_ingester
  echo ""
  check_querier
  echo ""
  check_query-frontend
  echo ""
  check_query-scheduler
  echo ""
  check_compactor
  echo ""
  check_ruler
  echo ""
  check_index-gateway
  echo ""
  check_minio
  echo ""
  check_fluent-bit
  echo ""
  check_grafana
  echo ""
  check_prometheus
fi

echo ""
echo "✅ Log check complete!"
echo ""
echo "🔍 Health Indicators to Look For:"
echo "  • Distributor: 'memberlist cluster succeeded'"
echo "  • Ingester: 'checkpoint done', 'uploading tables'"
echo "  • Querier: 'query readiness setup completed'"
echo "  • Query-Frontend: 'Loki started'"
echo "  • Compactor: 'compactor started'"
echo "  • Fluent Bit: 'flush chunk succeeded'"
echo "  • Grafana: 'HTTP Server Listen'"
echo "  • Prometheus: 'Server is ready to receive web requests'"
