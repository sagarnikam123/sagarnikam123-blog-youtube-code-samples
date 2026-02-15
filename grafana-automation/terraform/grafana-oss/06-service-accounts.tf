# Step 8: Service Accounts (for API access)
# Command: terraform apply -target=grafana_service_account.terraform
# Command: terraform apply -target=grafana_service_account_token.terraform
# Destroy: terraform destroy -target=grafana_service_account_token.terraform
# Destroy: terraform destroy -target=grafana_service_account.terraform
#
# References:
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/service_account
# - https://registry.terraform.io/providers/grafana/grafana/latest/docs/resources/service_account_token

# Service Account for CI/CD or automation
resource "grafana_service_account" "terraform" {
  name        = "terraform-automation"
  role        = "Admin"
  is_disabled = false
}

# Token for the service account
resource "grafana_service_account_token" "terraform" {
  name               = "terraform-token"
  service_account_id = grafana_service_account.terraform.id
  seconds_to_live    = 86400  # 24 hours, set to 0 for no expiry
}

# Output the token (sensitive)
output "service_account_token" {
  description = "Service account token for automation"
  value       = grafana_service_account_token.terraform.key
  sensitive   = true
}

# =============================================================================
# USAGE
# =============================================================================
# After creating, get the token:
#   terraform output -raw service_account_token
#
# Use in CI/CD:
#   export TF_VAR_grafana_auth=$(terraform output -raw service_account_token)
