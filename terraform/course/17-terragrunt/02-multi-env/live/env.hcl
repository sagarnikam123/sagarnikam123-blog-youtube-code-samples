# =============================================================================
# Common environment config — overridden per environment
# =============================================================================
# Each environment directory has its own env.hcl that overrides these defaults.
# =============================================================================

locals {
  environment = "default"
  replicas    = 1
  base_port   = 9200
}
