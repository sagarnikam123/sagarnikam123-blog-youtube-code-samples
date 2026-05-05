# =============================================================================
# Web app module — depends on network
# =============================================================================
# Terragrunt automatically applies the network module first.
#
# Usage:
#   cd live
#   terragrunt run-all plan     # plans network first, then web-app
#   terragrunt run-all apply    # applies in dependency order
#   terragrunt run-all destroy  # destroys in reverse order
# =============================================================================

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/app"
}

# Declare dependency on the network module
dependency "network" {
  config_path = "../network"

  # Mock outputs for `terragrunt plan` when network hasn't been applied yet
  mock_outputs = {
    network_id   = "mock-network-id"
    network_name = "mock-network"
  }
  mock_outputs_allowed_terraform_commands = ["plan", "validate"]
}

inputs = {
  app_name      = "tg-dep-web"
  image         = "nginx:alpine"
  external_port = 9230
  network_id    = dependency.network.outputs.network_id
}
