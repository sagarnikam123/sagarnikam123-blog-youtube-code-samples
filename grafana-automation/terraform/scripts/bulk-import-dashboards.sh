#!/bin/bash
# =============================================================================
# Bulk Import Grafana Dashboards into Terraform State
# =============================================================================
# Works with any Grafana instance (OSS, AMG, Azure)
#
# Usage:
#   ./scripts/bulk-import-dashboards.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-dashboards.sh --url http://localhost:3000 --token xxx --instance grafana-oss-dev
#   ./scripts/bulk-import-dashboards.sh --url http://localhost:3000 --token xxx --dry-run
# =============================================================================

set -e

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
INSTANCE_NAME=""
OUTPUT_FILE="dashboards_imported.tf"
DASHBOARD_DIR="dashboards_imported"
DRY_RUN=false
GENERATE_ONLY=false
RESOURCE_PREFIX="imported"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --url) GRAFANA_URL="$2"; shift 2 ;;
    --token) GRAFANA_TOKEN="$2"; shift 2 ;;
    --instance) INSTANCE_NAME="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --dashboard-dir) DASHBOARD_DIR="$2"; shift 2 ;;
    --prefix) RESOURCE_PREFIX="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --generate) GENERATE_ONLY=true; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --url URL            Grafana URL (or set GRAFANA_URL)"
      echo "  --token TOKEN        API token (or set GRAFANA_TOKEN)"
      echo "  --instance NAME      Instance name for resource naming"
      echo "  --output FILE        Output .tf file (default: dashboards_imported.tf)"
      echo "  --dashboard-dir DIR  Directory for JSON files (default: dashboards_imported)"
      echo "  --prefix PREFIX      Resource name prefix (default: imported)"
      echo "  --dry-run            Preview only, don't import"
      echo "  --generate           Generate files only, don't import"
      echo "  --help               Show this help"
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

# Check dependencies
command -v curl >/dev/null 2>&1 || { echo "Error: curl required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq required"; exit 1; }

echo "============================================================================="
echo "Bulk Import Dashboards"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Instance: ${INSTANCE_NAME:-not specified}"
echo "Output: $OUTPUT_FILE"
echo "Dashboard JSON dir: $DASHBOARD_DIR"
echo ""

# Fetch dashboard list
echo "Fetching dashboards..."
DASHBOARDS=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/search?type=dash-db")

if ! echo "$DASHBOARDS" | jq -e '.' >/dev/null 2>&1; then
  echo "Error: Invalid response from Grafana API"
  echo "$DASHBOARDS"
  exit 1
fi

DASH_COUNT=$(echo "$DASHBOARDS" | jq 'length')
echo "Found $DASH_COUNT dashboards"

if [[ "$DASH_COUNT" -eq 0 ]]; then
  echo "No dashboards to import"
  exit 0
fi

# Create dashboard directory
mkdir -p "$DASHBOARD_DIR"

# Generate Terraform file
echo ""
echo "Generating $OUTPUT_FILE and downloading dashboard JSON..."

cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# Auto-generated Terraform resources for imported Grafana dashboards
# Generated: $(date)
# Instance: ${INSTANCE_NAME:-not specified}
# Source: $GRAFANA_URL
# Dashboard JSON files: $DASHBOARD_DIR/
# =============================================================================

EOF

# Clear temp file
> /tmp/import_commands.txt

# Process each dashboard
echo "$DASHBOARDS" | jq -c '.[]' | while read -r dash; do
  UID=$(echo "$dash" | jq -r '.uid')
  TITLE=$(echo "$dash" | jq -r '.title')
  FOLDER_UID=$(echo "$dash" | jq -r '.folderUid // "general"')

  # Sanitize name
  RESOURCE_NAME=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')

  echo "  Downloading: $TITLE ($UID)"

  # Download full dashboard JSON
  DASH_JSON=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/dashboards/uid/$UID")

  # Save dashboard JSON
  echo "$DASH_JSON" | jq '.dashboard' > "$DASHBOARD_DIR/${UID}.json"

  # Add resource to .tf file
  cat >> "$OUTPUT_FILE" << EOF
resource "grafana_dashboard" "${RESOURCE_PREFIX}_${RESOURCE_NAME}" {
  config_json = file("\${path.module}/$DASHBOARD_DIR/${UID}.json")
  folder      = "$FOLDER_UID"
  overwrite   = true
}

EOF

  # Collect import command
  echo "terraform import grafana_dashboard.${RESOURCE_PREFIX}_${RESOURCE_NAME} ${UID}" >> /tmp/import_commands.txt
done

echo ""
echo "Generated: $OUTPUT_FILE"
echo "Dashboard JSON files: $DASHBOARD_DIR/"

# Show import commands
echo ""
echo "============================================================================="
echo "IMPORT COMMANDS"
echo "============================================================================="

if [[ -f /tmp/import_commands.txt ]]; then
  cat /tmp/import_commands.txt
fi

# Execute imports
if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "[DRY-RUN] Skipping import. Run commands above manually."
elif [[ "$GENERATE_ONLY" == "true" ]]; then
  echo ""
  echo "[GENERATE] Only generated files. Run import commands manually."
else
  echo ""
  echo "============================================================================="
  echo "EXECUTING IMPORTS"
  echo "============================================================================="

  [[ ! -d ".terraform" ]] && terraform init

  if [[ -f /tmp/import_commands.txt ]]; then
    while read -r cmd; do
      [[ -n "$cmd" ]] && echo "Running: $cmd" && eval "$cmd" || echo "Warning: Import failed"
    done < /tmp/import_commands.txt
  fi

  echo ""
  echo "Done! Run 'terraform plan' to verify."
fi

rm -f /tmp/import_commands.txt
