#!/bin/bash
# =============================================================================
# Create AMG API Key for Terraform
# =============================================================================
# Usage:
#   ./scripts/create-api-key.sh <workspace-id>
#   ./scripts/create-api-key.sh g-xxxxxxxxxx
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions
#   - AMG workspace already created
# =============================================================================

set -e

WORKSPACE_ID="${1:-}"
KEY_NAME="terraform-$(date +%Y%m%d-%H%M%S)"
TTL_SECONDS="${2:-3600}"  # Default: 1 hour

if [[ -z "$WORKSPACE_ID" ]]; then
  echo "Usage: $0 <workspace-id> [ttl-seconds]"
  echo ""
  echo "Example:"
  echo "  $0 g-xxxxxxxxxx"
  echo "  $0 g-xxxxxxxxxx 7200  # 2 hour TTL"
  echo ""
  echo "To find workspace ID:"
  echo "  aws grafana list-workspaces --query 'workspaces[].{name:name,id:id}'"
  exit 1
fi

echo "Creating API key for workspace: $WORKSPACE_ID"
echo "Key name: $KEY_NAME"
echo "TTL: $TTL_SECONDS seconds"
echo ""

# Create API key
API_KEY=$(aws grafana create-workspace-api-key \
  --workspace-id "$WORKSPACE_ID" \
  --key-name "$KEY_NAME" \
  --key-role ADMIN \
  --seconds-to-live "$TTL_SECONDS" \
  --query 'key' \
  --output text)

echo "============================================================================="
echo "API Key created successfully!"
echo "============================================================================="
echo ""
echo "Export for Terraform:"
echo "  export TF_VAR_grafana_auth='$API_KEY'"
echo ""
echo "Or add to terraform.tfvars:"
echo "  grafana_auth = \"$API_KEY\""
echo ""
echo "Note: This key expires in $TTL_SECONDS seconds"
echo "============================================================================="
