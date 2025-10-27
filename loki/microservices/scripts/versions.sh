#!/bin/bash
# 🔍 Version Check & Drift Detection Script
#
# DESCRIPTION:
#   Read-only utility to check version consistency between configuration
#   and deployed containers. Helps detect version drift and provides
#   update guidance without modifying any files.
#
# FUNCTIONALITY:
#   1. Display current configured versions from run-on-minikube.sh
#   2. Compare configured vs deployed container versions (drift detection)
#   3. Provide update guidance with links to latest releases
#
# USAGE:
#   ./scripts/check-versions.sh           # Show configured versions
#   ./scripts/check-versions.sh --check   # Compare deployed vs configured
#   ./scripts/check-versions.sh --update  # Show update instructions
#   ./scripts/check-versions.sh --help    # Show this help
#
# SAFETY:
#   - Read-only operations only
#   - No files modified
#   - No deployments affected
#   - Safe to run anytime

# Extract versions from deployment script
LOKI_VERSION=$(grep "^export LOKI_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)
GRAFANA_VERSION=$(grep "^export GRAFANA_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)
PROMETHEUS_VERSION=$(grep "^export PROMETHEUS_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)
MINIO_VERSION=$(grep "^export MINIO_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)
FLUENT_BIT_VERSION=$(grep "^export FLUENT_BIT_VERSION=" ./run-on-minikube.sh | cut -d'"' -f2)

echo "🔧 Current Component Versions:"
echo "  • Loki: ${LOKI_VERSION}"
echo "  • Grafana: ${GRAFANA_VERSION}"
echo "  • Prometheus: ${PROMETHEUS_VERSION}"
echo "  • MinIO: ${MINIO_VERSION}"
echo "  • Fluent Bit: ${FLUENT_BIT_VERSION}"
echo ""

if [[ "$1" == "--update" ]]; then
    echo "🚀 To update versions, check latest releases and modify run-on-minikube.sh:"
    echo ""
    echo "🔗 Latest Release Links:"
    echo "  GitHub Releases:"
    echo "    • Loki: https://github.com/grafana/loki/releases"
    echo "    • Grafana: https://github.com/grafana/grafana/releases"
    echo "    • Prometheus: https://github.com/prometheus/prometheus/releases"
    echo "    • MinIO: https://github.com/minio/minio/releases"
    echo "    • Fluent Bit: https://github.com/fluent/fluent-bit/releases"
    echo ""
    echo "  Docker Hub Tags:"
    echo "    • Loki: https://hub.docker.com/r/grafana/loki/tags"
    echo "    • Grafana: https://hub.docker.com/r/grafana/grafana/tags"
    echo "    • Prometheus: https://hub.docker.com/r/prom/prometheus/tags"
    echo "    • MinIO: https://hub.docker.com/r/minio/minio/tags"
    echo "    • Fluent Bit: https://hub.docker.com/r/fluent/fluent-bit/tags"
    echo ""
    echo "🔧 Update variables in run-on-minikube.sh:"
    echo "  export LOKI_VERSION=\"3.4.0\"        # New Loki version"
    echo "  export GRAFANA_VERSION=\"11.5.0\"    # New Grafana version"
    echo "  export PROMETHEUS_VERSION=\"v2.56.0\" # New Prometheus version"
    echo "  export MINIO_VERSION=\"RELEASE.2024-XX-XXTXX-XX-XXZ\" # New MinIO version"
    echo "  export FLUENT_BIT_VERSION=\"3.3.0\"   # New Fluent Bit version"
    echo ""
    echo "Then run: ./run-on-minikube.sh"
elif [[ "$1" == "--check" ]]; then
    echo "🔍 Checking deployed versions vs configured versions..."
    echo ""
    if kubectl get namespace loki >/dev/null 2>&1; then
        echo "📊 Deployed Image Versions:"
        kubectl get pods -n loki -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | column -t
        echo ""
        echo "⚙️  Configured Versions (run-on-minikube.sh):"
        echo "  • Loki: ${LOKI_VERSION}"
        echo "  • Grafana: ${GRAFANA_VERSION}"
        echo "  • Prometheus: ${PROMETHEUS_VERSION}"
        echo "  • MinIO: ${MINIO_VERSION}"
        echo "  • Fluent Bit: ${FLUENT_BIT_VERSION}"
    else
        echo "❌ No loki namespace found - run deployment first"
    fi
elif [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "🔍 Version Check & Drift Detection Script"
    echo ""
    echo "📋 DESCRIPTION:"
    echo "  Read-only utility for version management and drift detection."
    echo "  Compares configured versions (run-on-minikube.sh) with deployed"
    echo "  container images to identify version inconsistencies."
    echo ""
    echo "⚙️  FUNCTIONALITY:"
    echo "  • Display configured component versions"
    echo "  • Detect version drift between config and deployment"
    echo "  • Provide update guidance with release links"
    echo "  • Safe read-only operations (no modifications)"
    echo ""
    echo "🚀 USAGE:"
    echo "  ./scripts/check-versions.sh           # Show configured versions"
    echo "  ./scripts/check-versions.sh --check   # Compare deployed vs configured"
    echo "  ./scripts/check-versions.sh --update  # Show update instructions"
    echo "  ./scripts/check-versions.sh --help    # Show this help"
    echo ""
    echo "🎯 USE CASES:"
    echo "  • Troubleshooting deployment issues"
    echo "  • Verifying successful upgrades"
    echo "  • Planning version updates"
    echo "  • Auditing current deployment state"
    echo ""
    echo "⚠️  SAFETY:"
    echo "  • Read-only operations only"
    echo "  • No files or deployments modified"
    echo "  • Safe to run anytime"
else
    echo "💡 Usage:"
    echo "  ./scripts/check-versions.sh           # Show current versions"
    echo "  ./scripts/check-versions.sh --update  # Show update instructions"
    echo "  ./scripts/check-versions.sh --check   # Compare deployed vs configured versions"
    echo "  ./scripts/check-versions.sh --help    # Show detailed help"
fi
