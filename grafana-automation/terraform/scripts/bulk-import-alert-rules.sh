#!/bin/bash
# =============================================================================
# Bulk Import Grafana Alert Rules into Terraform State
# =============================================================================
# Works with any Grafana instance (OSS, AMG, Azure)
#
# Usage:
#   ./scripts/bulk-import-alert-rules.sh --url http://localhost:3000 --token xxx
#   ./scripts/bulk-import-alert-rules.sh --url http://localhost:3000 --token xxx --dry-run
#   ./scripts/bulk-import-alert-rules.sh --url http://localhost:3000 --token xxx --generate
#
# Environment variables (alternative to flags):
#   GRAFANA_URL, GRAFANA_TOKEN
# =============================================================================

set -e

# Defaults
GRAFANA_URL="${GRAFANA_URL:-}"
GRAFANA_TOKEN="${GRAFANA_TOKEN:-}"
OUTPUT_FILE="alert_rules_imported.tf"
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
      echo "  --output FILE      Output .tf file (default: alert_rules_imported.tf)"
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
echo "Bulk Import Alert Rules (Rule Groups)"
echo "============================================================================="
echo "Grafana URL: $GRAFANA_URL"
echo "Output: $OUTPUT_FILE"
echo ""

# Fetch alert rules - Grafana organizes rules in groups
echo "Fetching alert rule groups..."
RULE_GROUPS=$(curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" "$GRAFANA_URL/api/v1/provisioning/alert-rules")

# Check if response is valid JSON
if ! echo "$RULE_GROUPS" | jq -e '.' >/dev/null 2>&1; then
  echo "Error: Invalid response from Grafana API"
  echo "$RULE_GROUPS"
  exit 1
fi

# Check if response is an error
if echo "$RULE_GROUPS" | jq -e 'type == "object" and has("message")' >/dev/null 2>&1; then
  echo "Error: API returned error"
  echo "$RULE_GROUPS" | jq -r '.message'
  exit 1
fi

# Check if response is an array
if ! echo "$RULE_GROUPS" | jq -e 'type == "array"' >/dev/null 2>&1; then
  echo "Error: Expected array response from API"
  echo "Response type: $(echo "$RULE_GROUPS" | jq -r 'type')"
  exit 1
fi

RULE_COUNT=$(echo "$RULE_GROUPS" | jq 'length')
echo "Found $RULE_COUNT alert rules"

if [[ "$RULE_COUNT" -eq 0 ]]; then
  echo "No alert rules to import"
  exit 0
fi

# Debug: Show sample
echo ""
echo "Sample alert rule:"
echo "$RULE_GROUPS" | jq '.[0] | {uid, title, folderUID, ruleGroup}'
echo ""

# Get unique rule groups (folder_uid + rule_group combination)
# Terraform imports rule_group resources, not individual rules
UNIQUE_GROUPS=$(echo "$RULE_GROUPS" | jq -r '[.[] | {folder_uid: .folderUID, group_name: .ruleGroup}] | unique')
GROUP_COUNT=$(echo "$UNIQUE_GROUPS" | jq 'length')

echo "Unique rule groups: $GROUP_COUNT"
echo ""

# Generate Terraform file
echo "Generating $OUTPUT_FILE..."

cat > "$OUTPUT_FILE" << EOF
# =============================================================================
# Auto-generated Terraform resources for imported Grafana alert rule groups
# Generated: $(date)
# Source: $GRAFANA_URL
# =============================================================================
# NOTE: Grafana Terraform provider imports rule_group resources, which contain
# multiple rules. Each rule_group is identified by folder_uid:group_name
# =============================================================================

EOF

# Generate resource blocks for each unique rule group
echo "$UNIQUE_GROUPS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "resource \"grafana_rule_group\" \"\($prefix)_\(.group_name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase)\" {\n  name             = \"\(.group_name)\"\n  folder_uid       = \"\(.folder_uid)\"\n  interval_seconds = 60\n\n  # TODO: Add rule blocks after import\n  # Run terraform plan to see required configuration\n}\n"' >> "$OUTPUT_FILE"

echo "Generated: $OUTPUT_FILE"

# Generate import commands
# Format: terraform import grafana_rule_group.name folder_uid:group_name
echo ""
echo "============================================================================="
echo "IMPORT COMMANDS"
echo "============================================================================="

IMPORT_COMMANDS=$(echo "$UNIQUE_GROUPS" | jq -r --arg prefix "$RESOURCE_PREFIX" '.[] |
  "terraform import grafana_rule_group.\($prefix)_\(.group_name | gsub("[^a-zA-Z0-9]"; "_") | ascii_downcase) \(.folder_uid):\(.group_name)"')

echo "$IMPORT_COMMANDS"

# Also show individual rules for reference
echo ""
echo "============================================================================="
echo "RULES BY GROUP (for reference)"
echo "============================================================================="
echo "$RULE_GROUPS" | jq -r 'group_by(.ruleGroup) | .[] | "Group: \(.[0].ruleGroup)\n  Rules: \([.[].title] | join(", "))\n"'

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
echo "2. Run: terraform plan"
echo "3. Copy the rule configuration from plan output to your .tf file"
echo "4. Adjust until 'No changes' is shown"
echo ""
echo "TIP: After import, run 'terraform state show grafana_rule_group.<name>'"
echo "     to see the full configuration of each rule group."
