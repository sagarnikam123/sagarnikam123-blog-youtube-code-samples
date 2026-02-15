#!/bin/bash
# =============================================================================
# Bulk Import Grafana Data Sources into Terraform State
# =============================================================================
# Works with any Grafana instance (OSS, AMG, Azure)
#
# Usage:
#   ./scripts/bulk-import-datasources.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-datasources.sh --url http://localhost:3000 --token xxx --instance grafana-oss-dev
#   ./scripts/bulk-import-datasources.sh --url http://localhost:3000 --token xxx --dry-run
# =============================================================================

set -e

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
INSTANCE_NAME=""
OUTPUT_FILE="datasources_imported.tf"
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
    --prefix) RESOURCE_PREFIX="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --generate) GENERATE_ONLY=true; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --url URL          Grafana URL (or set GRAFANA_URL)"
      echo "  --token TOKEN      API token (or set GRAFANA_TOKEN)"
      echo "  --instance NAME    Instance name for resource naming"
      echo "  --output FILE      Output .tf file (default: datasources_imported.tf)"
      echo "  --prefix PREFIX    Resource name prefix (default: imported)"
      echo "  --dry-run          Preview only, don't import"
      echo "  --generate         Generate .tf file only, don't import"
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

# Check dependencies
command -v curl >/dev/null 2>&1 || { echo "Error: curl required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq required"; exit 1; }

echo "============================================================================="
echo "Bulk Import Data Sources"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Instance: ${INSTANCE_NAME:-not specified}"
echo "Output: $OUTPUT_FILE"
echo ""

# Fetch datasources
echo "Fetching data sources..."
DATASOURCES=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/datasources")

if ! echo "$DATASOURCES" | jq -e '.' >/dev/null 2>&1; then
  echo "Error: Invalid response from Grafana API"
  echo "$DATASOURCES"
  exit 1
fi

DS_COUNT=$(echo "$DATASOURCES" | jq 'length')
echo "Found $DS_COUNT data sources"

if [[ "$DS_COUNT" -eq 0 ]]; then
  echo "No data sources to import"
  exit 0
fi

# Generate Terraform file
echo ""
echo "Generating $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# Auto-generated Terraform resources for imported Grafana data sources
# Generated: $(date)
# Instance: ${INSTANCE_NAME:-not specified}
# Source: $GRAFANA_URL
# =============================================================================
# Note: Data sources are imported by numeric ID
# After import, review and adjust json_data_encoded as needed
# =============================================================================

EOF

echo "$DATASOURCES" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "resource \"grafana_data_source\" \"\($prefix)_\(.name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase)\" {\n  type       = \"\(.type)\"\n  name       = \"\(.name | gsub("\""; "\\\""))\"\n  url        = \"\(.url // \"\")\"\n  is_default = \(.isDefault)\n  # uid      = \"\(.uid // \"\")\"  # Uncomment if needed\n}\n"' >> "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"

# Generate import commands (datasources use numeric ID)
echo ""
echo "============================================================================="
echo "IMPORT COMMANDS"
echo "============================================================================="

IMPORT_COMMANDS=$(echo "$DATASOURCES" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "terraform import grafana_data_source.\($prefix)_\(.name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase) \(.id)"')

echo "$IMPORT_COMMANDS"

# Execute imports
if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "[DRY-RUN] Skipping import. Run commands above manually."
elif [[ "$GENERATE_ONLY" == "true" ]]; then
  echo ""
  echo "[GENERATE] Only generated $OUTPUT_FILE. Run import commands manually."
else
  echo ""
  echo "============================================================================="
  echo "EXECUTING IMPORTS"
  echo "============================================================================="

  [[ ! -d ".terraform" ]] && terraform init

  echo "$IMPORT_COMMANDS" | while read -r cmd; do
    echo "Running: $cmd"
    eval "$cmd" || echo "Warning: Import failed (may already exist)"
  done

  echo ""
  echo "Done! Run 'terraform plan' to verify."
fi
