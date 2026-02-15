#!/bin/bash
# =============================================================================
# Create Azure Managed Grafana Service Account Token for Terraform
# =============================================================================
# Usage:
#   ./scripts/create-service-account.sh <grafana-name> <resource-group>
#
# Prerequisites:
#   - Azure CLI installed and logged in
#   - amg extension: az extension add --name amg
#   - Azure Managed Grafana instance created
# =============================================================================

set -e

GRAFANA_NAME="${1:-}"
RESOURCE_GROUP="${2:-}"
SERVICE_ACCOUNT_NAME="${3:-terraform}"
TOKEN_NAME="terraform-token-$(date +%Y%m%d)"
TTL="${4:-1d}"  # Default: 1 day

if [[ -z "$GRAFANA_NAME" || -z "$RESOURCE_GROUP" ]]; then
  echo "Usage: $0 <grafana-name> <resource-group> [service-account-name] [ttl]"
  echo ""
  echo "Example:"
  echo "  $0 my-grafana my-resource-group"
  echo "  $0 my-grafana my-resource-group terraform 7d"
  echo ""
  echo "To find your Grafana instances:"
  echo "  az grafana list --query '[].{name:name,resourceGroup:resourceGroup}'"
  exit 1
fi

# Check if amg extension is installed
if ! az extension show --name amg &>/dev/null; then
  echo "Installing Azure Managed Grafana extension..."
  az extension add --name amg
fi

echo "Creating service account for: $GRAFANA_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Service Account: $SERVICE_ACCOUNT_NAME"
echo ""

# Create service account (if not exists)
echo "Creating service account..."
az grafana service-account create \
  --name "$GRAFANA_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --service-account "$SERVICE_ACCOUNT_NAME" \
  --role Admin \
  2>/dev/null || echo "Service account may already exist, continuing..."

# Create token
echo "Creating token..."
TOKEN=$(az grafana service-account token create \
  --name "$GRAFANA_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --service-account "$SERVICE_ACCOUNT_NAME" \
  --token "$TOKEN_NAME" \
  --time-to-live "$TTL" \
  --query key \
  --output tsv)

echo ""
echo "============================================================================="
echo "Service Account Token created successfully!"
echo "============================================================================="
echo ""
echo "Export for Terraform:"
echo "  export TF_VAR_grafana_auth='$TOKEN'"
echo ""
echo "Or add to terraform.tfvars:"
echo "  grafana_auth = \"$TOKEN\""
echo ""
echo "Note: This token expires in $TTL"
echo "============================================================================="
