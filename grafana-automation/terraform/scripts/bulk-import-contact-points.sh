#!/bin/bash
# =============================================================================
# Bulk Import Grafana Contact Points into Terraform State
# =============================================================================
# Works with any Grafana instance (OSS, AMG, Azure)
#
# Usage:
#   ./scripts/bulk-import-contact-points.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-contact-points.sh --url http://localhost:3000 --token xxx --dry-run
#   ./scripts/bulk-import-contact-points.sh --url http://localhost:3000 --token xxx --generate
#
# Environment variables (alternative to flags):
#   GRAFANA_URL, GRAFANA_TOKEN
# =============================================================================

set -e

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
OUTPUT_FILE="contact_points_imported.tf"
DRY_RUN=false
GENERATE_ONLY=false
RESOURCE_PREFIX="imported"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --url) GRAFANA_URL="$2"; shift 2 ;;
    --token) GRAFANA_TOKEN="$2"; shift 2 ;;
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
      echo "  --output FILE      Output .tf file (default: contact_points_imported.tf)"
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
echo "Bulk Import Contact Points"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Output: $OUTPUT_FILE"
echo ""

# Fetch contact points
echo "Fetching contact points..."
CONTACT_POINTS=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/v1/provisioning/contact-points")

# Check if response is valid JSON
if ! echo "$CONTACT_POINTS" | jq -e '.' >/dev/null 2>&1; then
  echo "Error: Invalid response from Grafana API"
  echo "$CONTACT_POINTS"
  exit 1
fi

# Check if response is an error
if echo "$CONTACT_POINTS" | jq -e 'type == "object" and has("message")' >/dev/null 2>&1; then
  echo "Error: API returned error"
  echo "$CONTACT_POINTS" | jq -r '.message'
  exit 1
fi

# Check if response is an array
if ! echo "$CONTACT_POINTS" | jq -e 'type == "array"' >/dev/null 2>&1; then
  echo "Error: Expected array response from API"
  echo "Response type: $(echo "$CONTACT_POINTS" | jq -r 'type')"
  exit 1
fi

CP_COUNT=$(echo "$CONTACT_POINTS" | jq 'length')
echo "Found $CP_COUNT contact points"

if [[ "$CP_COUNT" -eq 0 ]]; then
  echo "No contact points to import"
  exit 0
fi

# Debug: Show sample
echo ""
echo "Sample contact point:"
echo "$CONTACT_POINTS" | jq '.[0]'
echo ""

# Filter valid contact points (must have name)
VALID_CPS=$(echo "$CONTACT_POINTS" | jq '[.[] | select(.name != null and (.name | type) == "string")]')
VALID_COUNT=$(echo "$VALID_CPS" | jq 'length')

echo "Valid contact points: $VALID_COUNT"

if [[ "$VALID_COUNT" -eq 0 ]]; then
  echo "No valid contact points to import"
  exit 0
fi

# Generate Terraform file
echo ""
echo "Generating $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# Auto-generated Terraform resources for imported Grafana contact points
# Generated: $(date)
# Source: $GRAFANA_URL
# =============================================================================
# NOTE: This generates basic resource blocks. You may need to add
# specific configuration for each contact point type (webhook, email, etc.)
# =============================================================================

EOF

# Generate resource blocks
# Contact points use 'name' as the identifier for import
echo "$VALID_CPS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "resource \"grafana_contact_point\" \"\($prefix)_\(.name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase)\" {\n  name = \"\(.name | gsub("\""; "\\\""))\"\n\n  # TODO: Add specific contact point type configuration\n  # Type: \(.type // "unknown")\n}\n"' >> "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"

# Generate import commands
echo ""
echo "============================================================================="
echo "IMPORT COMMANDS"
echo "============================================================================="

# Contact points are imported by name
IMPORT_COMMANDS=$(echo "$VALID_CPS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "terraform import grafana_contact_point.\($prefix)_\(.name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase) \"\(.name)\""')

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

echo ""
echo "============================================================================="
echo "NEXT STEPS"
echo "============================================================================="
echo "1. Review generated file: $OUTPUT_FILE"
echo "2. Add specific contact point type configuration (webhook, email, slack, etc.)"
echo "3. Run: terraform plan"
echo "4. Adjust .tf file until 'No changes' is shown"
