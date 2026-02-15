#!/bin/bash
# =============================================================================
# Bulk Import Grafana Folders into Terraform State
# =============================================================================
# Works with any Grafana instance (OSS, AMG, Azure)
#
# Usage:
#   ./scripts/bulk-import-folders.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-folders.sh --url http://localhost:3000 --token xxx --instance grafana-oss-dev
#   ./scripts/bulk-import-folders.sh --url http://localhost:3000 --token xxx --dry-run
#   ./scripts/bulk-import-folders.sh --url http://localhost:3000 --token xxx --generate
#
# Environment variables (alternative to flags):
#   GRAFANA_URL, GRAFANA_TOKEN
# =============================================================================

set -e

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
INSTANCE_NAME=""
OUTPUT_FILE="folders_imported.tf"
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
      echo "  --output FILE      Output .tf file (default: folders_imported.tf)"
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
echo "Bulk Import Folders"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Instance: ${INSTANCE_NAME:-not specified}"
echo "Output: $OUTPUT_FILE"
echo ""

# Fetch folders
echo "Fetching folders..."
FOLDERS=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/folders")

# Check if response is valid JSON
if ! echo "$FOLDERS" | jq -e '.' >/dev/null 2>&1; then
  echo "Error: Invalid response from Grafana API"
  echo "$FOLDERS"
  exit 1
fi

# Check if response is an error (object with message field)
if echo "$FOLDERS" | jq -e 'type == "object" and has("message")' >/dev/null 2>&1; then
  echo "Error: API returned error"
  echo "$FOLDERS" | jq -r '.message'
  exit 1
fi

# Check if response is an array
if ! echo "$FOLDERS" | jq -e 'type == "array"' >/dev/null 2>&1; then
  echo "Error: Expected array response from API"
  echo "Response type: $(echo "$FOLDERS" | jq -r 'type')"
  echo "$FOLDERS"
  exit 1
fi

FOLDER_COUNT=$(echo "$FOLDERS" | jq 'length')
echo "Found $FOLDER_COUNT folders"

if [[ "$FOLDER_COUNT" -eq 0 ]]; then
  echo "No folders to import"
  exit 0
fi

# Debug: Show first folder structure
echo ""
echo "Sample folder structure:"
echo "$FOLDERS" | jq '.[0]'
echo ""

# Filter folders that have valid uid (string type, not null)
VALID_FOLDERS=$(echo "$FOLDERS" | jq '[.[] | select(.uid != null and (.uid | type) == "string")]')
VALID_COUNT=$(echo "$VALID_FOLDERS" | jq 'length')

echo "Valid folders with UIDs: $VALID_COUNT"

if [[ "$VALID_COUNT" -eq 0 ]]; then
  echo "No valid folders to import (all have null or invalid UIDs)"
  exit 0
fi

# Generate Terraform file
echo ""
echo "Generating $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# Auto-generated Terraform resources for imported Grafana folders
# Generated: $(date)
# Instance: ${INSTANCE_NAME:-not specified}
# Source: $GRAFANA_URL
# =============================================================================

EOF

# Generate resource blocks - use validated folders
echo "$VALID_FOLDERS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "resource \"grafana_folder\" \"\($prefix)_\(.uid | gsub("[^a-zA-Z0-9]"; "_"))\" {\n  title = \"\(.title | gsub("\""; "\\\"") | gsub("\n"; " "))\"\n  uid   = \"\(.uid)\"\n}\n"' >> "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"

# Generate import commands
echo ""
echo "============================================================================="
echo "IMPORT COMMANDS"
echo "============================================================================="

IMPORT_COMMANDS=$(echo "$VALID_FOLDERS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "terraform import grafana_folder.\($prefix)_\(.uid | gsub("[^a-zA-Z0-9]"; "_")) \(.uid)"')

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
