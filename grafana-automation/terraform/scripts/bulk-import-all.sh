#!/bin/bash
# =============================================================================
# Bulk Import ALL Grafana Resources (Folders, Datasources, Dashboards)
# =============================================================================
# Convenience wrapper to import everything at once
#
# Usage:
#   ./scripts/bulk-import-all.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-all.sh --url http://localhost:3000 --token xxx --instance grafana-oss-dev
#   ./scripts/bulk-import-all.sh --url http://localhost:3000 --token xxx --dry-run
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
INSTANCE_NAME=""
DRY_RUN=""
GENERATE_ONLY=""

# Parse arguments
PASSTHROUGH_ARGS=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --url) GRAFANA_URL="$2"; PASSTHROUGH_ARGS="$PASSTHROUGH_ARGS --url $2"; shift 2 ;;
    --token) GRAFANA_TOKEN="$2"; PASSTHROUGH_ARGS="$PASSTHROUGH_ARGS --token $2"; shift 2 ;;
    --instance) INSTANCE_NAME="$2"; PASSTHROUGH_ARGS="$PASSTHROUGH_ARGS --instance $2"; shift 2 ;;
    --dry-run) DRY_RUN="--dry-run"; PASSTHROUGH_ARGS="$PASSTHROUGH_ARGS --dry-run"; shift ;;
    --generate) GENERATE_ONLY="--generate"; PASSTHROUGH_ARGS="$PASSTHROUGH_ARGS --generate"; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Imports all resources: folders, datasources, dashboards"
      echo ""
      echo "Options:"
      echo "  --url URL          Grafana URL (or set GRAFANA_URL)"
      echo "  --token TOKEN      API token (or set GRAFANA_TOKEN)"
      echo "  --instance NAME    Instance name for resource naming"
      echo "  --dry-run          Preview only, don't import"
      echo "  --generate         Generate .tf files only, don't import"
      echo "  --help             Show this help"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate
if [[ -z "$GRAFANA_URL" ]]; then
  echo "Error: --url or GRAFANA_URL required"
  exit 1
fi
if [[ -z "$GRAFANA_TOKEN" ]]; then
  echo "Error: --token or GRAFANA_TOKEN required"
  exit 1
fi

echo "============================================================================="
echo "BULK IMPORT ALL RESOURCES"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Instance: ${INSTANCE_NAME:-not specified}"
echo ""

# Import folders
echo ""
echo ">>> IMPORTING FOLDERS..."
echo ""
"$SCRIPT_DIR/bulk-import-folders.sh" $PASSTHROUGH_ARGS

# Import datasources
echo ""
echo ">>> IMPORTING DATASOURCES..."
echo ""
"$SCRIPT_DIR/bulk-import-datasources.sh" $PASSTHROUGH_ARGS

# Import dashboards
echo ""
echo ">>> IMPORTING DASHBOARDS..."
echo ""
"$SCRIPT_DIR/bulk-import-dashboards.sh" $PASSTHROUGH_ARGS

echo ""
echo "============================================================================="
echo "ALL IMPORTS COMPLETE"
echo "============================================================================="
echo ""
echo "Generated files:"
echo "  - folders_imported.tf"
echo "  - datasources_imported.tf"
echo "  - dashboards_imported.tf"
echo "  - dashboards_imported/"
echo ""
echo "Next steps:"
echo "  1. Review generated .tf files"
echo "  2. Run: terraform plan"
echo "  3. Adjust until 'No changes' is shown"
